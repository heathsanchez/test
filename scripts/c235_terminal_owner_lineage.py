"""C235: read-only terminal-path audit of already qualified C234 evidence.
Only logged UNKNOWN-source edges are followed; absent edges imply UNKNOWN, not independence.
"""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ARTIFACT = "0b627334d621e0b55400cb5abc6c9430b534401e4780e167814a23d41a19eefc"
SOURCE_ARCHIVE = "5bd679fe1f7a6988575ec469264b24cab8ddf465ae064bcb79d99541658acd2f"
FUELED = "e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a"
INFER = re.compile(r"^NUCLEUS_C223_INFER_UNKNOWN:seq=(\d+):expr=ExprId\((\d+)\):frame=(\d+):ctx=(\d+):left=(\d+):reason=([^:]+):source=Some\((.+)\)$")
OWNER = re.compile(r"^NUCLEUS_C223_ARG_CONVERSION_UNKNOWN:seq=\d+:expr=ExprId\((\d+)\):frame=\d+:ctx=\d+:left=\d+:reason=([^:]+)$")
EXPR = re.compile(r"ExprId\((\d+)\)")
TERMINAL = "NUCLEUS_DOWNSTREAM:name=chain6_datF:stage=theorem.value:verdict=UNKNOWN:reason=application-function-type"

def observe(log, outer):
    lines = log.splitlines()
    if lines.count(TERMINAL) != 1 or "NUCLEUS_C233_TRUNCATED" in log:
        return {"status": "UNKNOWN_INCOMPLETE_TRACE", "outer": outer}
    nodes, owners = {}, []
    for line in lines:
        if line.startswith("NUCLEUS_C223_INFER_UNKNOWN:"):
            m = INFER.fullmatch(line)
            if not m:
                return {"status": "UNKNOWN_MALFORMED_TRACE", "outer": outer}
            seq, expr, frame, ctx, left, reason, source = m.groups()
            nodes.setdefault(int(expr), []).append({
                "seq": int(seq), "frame": int(frame), "ctx": int(ctx),
                "reason": reason, "children": [int(x) for x in EXPR.findall(source)]})
        elif line.startswith("NUCLEUS_C223_ARG_CONVERSION_UNKNOWN:"):
            m = OWNER.fullmatch(line)
            if not m:
                return {"status": "UNKNOWN_MALFORMED_OWNER", "outer": outer}
            owners.append({"expr": int(m.group(1)), "reason": m.group(2)})
    root = 7199  # C234's exact final theorem-value diagnostic, not a generic root
    if root not in nodes or not any(e["frame"] == 0 and e["ctx"] == 0 for e in nodes[root]):
        return {"status": "UNKNOWN_ROOT_MISMATCH", "outer": outer}
    seen, todo = set(), [root]
    while todo:
        n = todo.pop()
        if n in seen:
            continue
        seen.add(n)
        for e in nodes.get(n, []):
            todo.extend(e["children"])
    reached = sorted(
        [{"expr": n, "reason": e["reason"], "seq": e["seq"]}
         for n in seen & nodes.keys() for e in nodes[n]
         if e["reason"] != "application-function-type"],
        key=lambda e: e["seq"])
    return {
        "status": "BOUNDED_OBSERVED_UNKNOWN_GRAPH", "outer": outer,
        "root": root, "observed_nodes": len(nodes),
        "root_reachable_observed_nodes": len(seen & nodes.keys()),
        "unlogged_children": len(seen - nodes.keys()),
        "reached_nonapplication_unknowns": reached,
        "conversion_owner_events": owners,
        # Missing source edges do NOT prove these failures cannot affect root.
        "no_logged_path_to_root": [n for n in (5, 4778) if n not in seen],
        "has_missing_edges": bool(seen - nodes.keys())}

def test_fail_closed():
    a = "\n".join([
        "NUCLEUS_C223_INFER_UNKNOWN:seq=0:expr=ExprId(7199):frame=0:ctx=0:left=0:reason=application-function-type:source=Some(App { fun: ExprId(30), arg: ExprId(40) })",
        "NUCLEUS_C223_INFER_UNKNOWN:seq=1:expr=ExprId(30):frame=4:ctx=1:left=0:reason=conversion-exposure:source=Some(App { fun: ExprId(5), arg: ExprId(6) })",
        "NUCLEUS_C223_ARG_CONVERSION_UNKNOWN:seq=0:expr=ExprId(5):frame=3:ctx=2:left=0:reason=conversion-exposure",
        TERMINAL])
    p = observe(a, 65536)
    assert p["status"] == "BOUNDED_OBSERVED_UNKNOWN_GRAPH" and p["has_missing_edges"]
    assert [x["expr"] for x in p["reached_nonapplication_unknowns"]] == [30]
    assert observe(a + "\nNUCLEUS_C233_TRUNCATED", 65536)["status"] == "UNKNOWN_INCOMPLETE_TRACE"
    assert observe(a.replace("source=Some(", "source=None(", 1), 65536)["status"] == "UNKNOWN_MALFORMED_TRACE"
    assert observe(a.replace("ExprId(7199)", "ExprId(8000)", 1), 65536)["status"] == "UNKNOWN_ROOT_MISMATCH"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    test_fail_closed()
    digest = hashlib.sha256(args.artifact.read_bytes()).hexdigest()
    if digest != ARTIFACT:
        raise ValueError("C234 artifact SHA-256 mismatch")
    with zipfile.ZipFile(args.artifact) as z:
        c = json.loads(z.read("conclusion.json"))
        assert c["source_archive_sha256"] == SOURCE_ARCHIVE
        assert c["original_source_unchanged"] is True and c["experimental_only"] is True
        assert len(c["protected"]) == 28 and all(x["verdict"] in (0, 1) for x in c["protected"])
        assert len(c["global_cases"]) == 2
        assert {x["outer"] for x in c["global_cases"]} == {65536, 65600}
        assert all(x["verdict"] == 2 and x["source_sha256"] == FUELED for x in c["global_cases"])
        observations = [observe(z.read(f"fueled_global_reserve_outer{n}.stderr").decode(), n)
                        for n in (65536, 65600)]
    assert all(x["status"] == "BOUNDED_OBSERVED_UNKNOWN_GRAPH" and x["has_missing_edges"]
               for x in observations)
    assert [x["conversion_owner_events"][-1]["expr"] for x in observations] == [12, 4861]
    assert [x["conversion_owner_events"][-1]["reason"] for x in observations] == [
        "conversion-budget-exhausted", "conversion-exposure"]
    assert any(x["expr"] == 2156 and x["reason"] == "conversion-budget-exhausted"
               for x in observations[0]["reached_nonapplication_unknowns"])
    assert any(x["expr"] == 4862 and x["reason"] == "conversion-exposure"
               for x in observations[1]["reached_nonapplication_unknowns"])
    result = {
        "status": "WARRANTED_BOUNDED_OBSERVER_ONLY",
        "artifact_sha256": digest, "fueled_source_sha256": FUELED,
        "complete_original_verdict": "UNKNOWN",
        "missing_edges_prevent_full_causal_claim": True,
        "observations": observations,
        "next_experiment": "Trace complete original type/conversion owner edges for Expr12 and Expr4861, with unchanged inputs, to test true terminal causality."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("C235_RESULT", json.dumps(result, sort_keys=True), flush=True)

if __name__ == "__main__":
    main()
