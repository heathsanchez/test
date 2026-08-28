from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path.cwd()
SOURCE = (ROOT / "full48" / "full48_decontaminated_v1").resolve()
OUT = (ROOT / "blind_regenesis_v1").resolve()
ABL = OUT / "ablated"
REG = OUT / "regenerated"
POST = OUT / "post_ablation"
RESULT = OUT / "result.json"

AUX_OWNER = "prove_mul_eval_hom"
OLD_MAP = "natModEq_refPolyEvalRevAux_map_mul"
OLD_PRODUCT = "natModEq_refPolyEvalRevAux_convolve"
NEW_MAP = "regenesis_bridge_alpha"
NEW_PRODUCT = "regenesis_bridge_beta"
AFFECTED = {
    "prove_mul_eval_hom",
    "prove_mul_comm_eval",
    "prove_mul_assoc_eval",
    "prove_mul_add_distrib_eval",
}
FORBIDDEN = ("sorry", "admit", "axiom", "unsafe", "Classical.arbitrary")


def run(cmd: list[str], cwd: Path, timeout: int = 420) -> dict:
    cp = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    raw = cp.stdout + "\n" + cp.stderr
    return {"exit": cp.returncode, "tail": raw[-24000:]}


def marked_region(src: str, key: str, owner: str) -> tuple[int, int]:
    start_line = f"-- !benchmark @start {key} def={owner}"
    end_line = f"-- !benchmark @end {key} def={owner}"
    start = src.index(start_line)
    body_start = src.index("\n", start) + 1
    end = src.index(end_line, body_start)
    return body_start, end


def body_of(src: str, key: str, owner: str) -> str:
    a, b = marked_region(src, key, owner)
    return src[a:b]


def replace_body(src: str, key: str, owner: str, body: str) -> str:
    a, b = marked_region(src, key, owner)
    return src[:a] + body.rstrip() + "\n" + src[b:]


def prepare_ablated() -> str:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copytree(SOURCE, ABL)
    ring = ABL / "Galoistools" / "Proof" / "Ring.lean"
    src = ring.read_text()
    original_aux = body_of(src, "proof_aux", AUX_OWNER)
    src = src.replace(OLD_MAP, NEW_MAP).replace(OLD_PRODUCT, NEW_PRODUCT)
    src = replace_body(
        src,
        "proof_aux",
        AUX_OWNER,
        "-- BLIND_REGENESIS_SLOT: infer and prove the missing reusable interface from its consumers.\n",
    )
    ring.write_text(src)
    return original_aux


def proof_reference_audit(project: Path) -> dict:
    start_re = re.compile(
        r"-- !benchmark @start proof def=([A-Za-z0-9_]+) kind=prove[^\n]*\n"
    )
    entries = []
    for path in sorted((project / "Galoistools" / "Proof").glob("*.lean")):
        src = path.read_text()
        for match in start_re.finditer(src):
            name = match.group(1)
            end = src.find(f"-- !benchmark @end proof def={name}", match.end())
            entries.append((name, src[match.end():end]))
    names = {name for name, _ in entries}
    cross = []
    taint = []
    for name, body in entries:
        refs = sorted(
            other
            for other in names
            if other != name and re.search(rf"\b{re.escape(other)}\b", body)
        )
        if refs:
            cross.append({"target": name, "refs": refs})
        hits = [token for token in FORBIDDEN if token in body]
        if hits:
            taint.append({"target": name, "tokens": hits})
    return {"proof_blocks": len(entries), "cross_target_references": cross, "taint": taint}


original_aux = prepare_ablated()
original_hash = hashlib.sha256(original_aux.encode()).hexdigest()

# Gate 1: the exact amputation must produce a real Lean failure.
subprocess.run(["lake", "clean"], cwd=ABL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
cold = run(["lake", "lean", "Galoistools/Proof/Ring.lean"], ABL)

# Gate 2: give an unchanged agent only the amputated project and the verifier.
shutil.copytree(ABL, REG)
prompt = f"""
You are inside a Lean 4 benchmark project that was mechanically amputated.
Four existing, independent proof consumers no longer compile because one reusable proof
interface was erased and its semantic declaration names were anonymized.

Use Lean errors as the only authority. Repair the project by editing ONLY the interior of
the marker block:
  proof_aux def={AUX_OWNER}
in Galoistools/Proof/Ring.lean.

Do not edit any consumer proof, implementation, spec, marker line, or other file. Do not
use sorry, admit, axiom, unsafe, Classical.arbitrary, or benchmark prove_* theorems.
Do not search the internet or git history. Do not recover deleted content. Infer the
smallest reusable interface required by the consumers, state it, prove it, and run
`lake lean Galoistools/Proof/Ring.lean` followed by `lake build`.

The original declaration names are deliberately unavailable. The required anonymous
consumer names are `{NEW_MAP}` and `{NEW_PRODUCT}`. Their types and relationship must be
inferred from their uses and the frozen definitions. Keep working until both Lean commands
pass or the time budget ends.
""".strip()

agent = run(
    [
        "codex",
        "exec",
        "--dangerously-bypass-approvals-and-sandbox",
        "-C",
        str(REG),
        prompt,
    ],
    ROOT,
    timeout=360,
)

# Gate 3: the agent may only have changed the intended slot.
allowed_rel = Path("Galoistools/Proof/Ring.lean")
changed = []
for path in sorted(REG.rglob("*")):
    if not path.is_file() or ".lake" in path.parts:
        continue
    rel = path.relative_to(REG)
    base = ABL / rel
    if not base.exists() or path.read_bytes() != base.read_bytes():
        changed.append(str(rel))

reg_src = (REG / allowed_rel).read_text()
abl_src = (ABL / allowed_rel).read_text()
reg_aux = body_of(reg_src, "proof_aux", AUX_OWNER)
outside_equal = (
    replace_body(reg_src, "proof_aux", AUX_OWNER, "")
    == replace_body(abl_src, "proof_aux", AUX_OWNER, "")
)
forbidden_hits = [token for token in FORBIDDEN if token in reg_aux]
old_name_hits = [name for name in (OLD_MAP, OLD_PRODUCT) if name in reg_aux]
novel_hash = hashlib.sha256(reg_aux.encode()).hexdigest()

subprocess.run(["lake", "clean"], cwd=REG, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
regen_ring = run(["lake", "lean", "Galoistools/Proof/Ring.lean"], REG)
regen_build = run(["lake", "build"], REG)
audit = proof_reference_audit(REG)

# Gate 4: exact synthesized-interface ablation must restore the failure.
shutil.copytree(REG, POST)
post_ring = POST / allowed_rel
post_src = replace_body(
    post_ring.read_text(),
    "proof_aux",
    AUX_OWNER,
    "-- EXACT_SYNTHESIZED_INTERFACE_ABLATION\n",
)
post_ring.write_text(post_src)
subprocess.run(["lake", "clean"], cwd=POST, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
post = run(["lake", "lean", "Galoistools/Proof/Ring.lean"], POST)

# Require all four consumers to remain present and refer to the regenerated interface.
consumer_refs = {}
for name in sorted(AFFECTED):
    body = body_of(reg_src, "proof", name)
    consumer_refs[name] = sorted(
        bridge for bridge in (NEW_MAP, NEW_PRODUCT) if re.search(rf"\b{bridge}\b", body)
    )
multi_target = len(consumer_refs) == 4 and all(consumer_refs.values())

gates = {
    "cold_amputation_fails": cold["exit"] != 0,
    "agent_completed": agent["exit"] == 0,
    "only_allowed_file_changed": changed == [str(allowed_rel)],
    "only_allowed_slot_changed": outside_equal,
    "no_forbidden_tokens": not forbidden_hits,
    "no_original_names_restored": not old_name_hits,
    "not_original_text": novel_hash != original_hash,
    "ring_verifies": regen_ring["exit"] == 0,
    "full_build_verifies": regen_build["exit"] == 0,
    "four_consumers_use_interface": multi_target,
    "no_cross_target_references": not audit["cross_target_references"],
    "proof_hygiene_clean": not audit["taint"],
    "exact_ablation_restores_failure": post["exit"] != 0,
}
passed = all(gates.values())
result = {
    "schema": "msi.blind-proof-interface-regenesis.v1",
    "passed": passed,
    "gates": gates,
    "affected_consumers": consumer_refs,
    "changed_files": changed,
    "regenerated_aux_sha256": novel_hash,
    "original_aux_sha256": original_hash,
    "forbidden_hits": forbidden_hits,
    "old_name_hits": old_name_hits,
    "audit": audit,
    "cold": cold,
    "agent": agent,
    "regenerated_ring": regen_ring,
    "regenerated_build": regen_build,
    "post_ablation": post,
}
RESULT.write_text(json.dumps(result, indent=2, sort_keys=True))
print("BLIND_PROOF_INTERFACE_REGENESIS_V1", json.dumps({"passed": passed, "gates": gates}, sort_keys=True))
raise SystemExit(0 if passed else 1)
