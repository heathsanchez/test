from __future__ import annotations
import hashlib, json, re
from pathlib import Path

HERE=Path(__file__).resolve().parent
from kernel import Kernel
from challenge_pack import NAMES,EXPECTED,WORLDS,RELABELLED,INCOMPLETE

SCIENTIFIC_FREEZE_COMMIT="820f26c2c2a6becfbc3c3c7e2c14a81e89eab776"

def git_blob_sha(path: Path)->str:
    data=path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

def selected(result):
    if result.get("status")!="VERIFIED" or not result.get("frontier"):
        return None
    x=result["frontier"][0]
    return (x["mode"],int(x["symmetry_breaks"]),int(x["event_window"]))

def has_obstruction(result,mode):
    return any(o.get("mode")==mode and o.get("kind")=="SYMMETRY_OBSTRUCTION" and o.get("witness") for o in result.get("obstructions",[]))

def main()->int:
    freeze=json.loads((HERE/"FREEZE.json").read_text())
    observed={name:git_blob_sha(HERE/name) for name in freeze["scientific_core_paths"]}
    freeze_ok=observed==freeze["git_blob_sha"]

    k=Kernel()
    results={name:k.synthesize(WORLDS[name]) for name in NAMES}
    relabelled={name:k.synthesize(RELABELLED[name]) for name in NAMES}
    incomplete=k.synthesize(INCOMPLETE)
    nover=k.synthesize(WORLDS["framed2"],verification_enabled=False)

    G={}
    G["E1_frozen_core_byte_identical"]=freeze_ok
    G["E2_one_kernel_exactly_classifies_all_postfreeze_worlds"]=all(
        r.get("status")=="VERIFIED" and selected(r)==EXPECTED[name]
        for name,r in results.items()
    )
    G["E3_constant_retains_no_frame_and_zero_event"]=selected(results["constant"])==("UNFRAMED",0,0)
    G["E4_dihedral_invariant_single_symbol_event_needs_no_frame"]=selected(results["unframed1"])==("UNFRAMED",0,1)
    G["E5_larger_dihedral_event_expands_window_without_frame_break"]=(
        selected(results["unframed3"])==("UNFRAMED",0,3)
        and selected(results["unframed6"])==("UNFRAMED",0,6)
    )
    G["E6_reversal_sensitive_consequence_earns_orientation_only"]=(
        selected(results["oriented4"])==("ORIENTED",1,4)
        and has_obstruction(results["oriented4"],"UNFRAMED")
    )
    G["E7_cut_sensitive_direction_insensitive_consequence_earns_anchor_only"]=(
        selected(results["anchored2"])==("ANCHORED",1,2)
        and has_obstruction(results["anchored2"],"UNFRAMED")
        and has_obstruction(results["anchored2"],"ORIENTED")
    )
    G["E8_cut_and_direction_sensitive_consequence_earns_full_frame"]=(
        selected(results["framed2"])==("FRAMED",2,2)
        and has_obstruction(results["framed2"],"UNFRAMED")
        and has_obstruction(results["framed2"],"ORIENTED")
        and has_obstruction(results["framed2"],"ANCHORED")
    )
    G["E9_event_span_increases_without_changing_required_frame"]=(
        selected(results["anchored2"])[:2]==selected(results["anchored3"])[:2]
        and selected(results["anchored2"])[2] < selected(results["anchored3"])[2]
        and selected(results["framed2"])[:2]==selected(results["framed3"])[:2]
        and selected(results["framed2"])[2] < selected(results["framed3"])[2]
    )
    G["E10_reversal_obstruction_has_explicit_conflicting_orbit_witness"]=has_obstruction(results["oriented4"],"UNFRAMED")
    G["E11_cut_obstruction_has_explicit_conflicting_rotation_witness"]=has_obstruction(results["anchored2"],"ORIENTED")
    G["E12_consequence_label_relabelling_preserves_frame_and_event_span"]=all(
        selected(results[name])==selected(relabelled[name]) for name in NAMES
    )
    G["E13_incomplete_authority_stays_unknown"]=incomplete.get("status")=="UNKNOWN_AUTHORITY"
    G["E14_verifier_ablation_authorizes_no_frame_or_event"]=(
        nover.get("status")=="UNKNOWN_NO_VERIFIER" and nover.get("tested_frame_modes")==0
    )

    source_raw=((HERE/"basis.py").read_text()+"\n"+(HERE/"kernel.py").read_text())
    source_lower=source_raw.lower()
    forbidden_domains=(
        "channel","history","joint","contextual","interventional",
        "oriented4","anchored2","framed2"
    )
    forbidden_legacy_constructors=("READ","ATOM","PAIR","TUPLE3","SWITCH","APPLY")
    G["E15_named_domains_and_old_constructors_absent_from_frozen_kernel"]=(
        all(re.search(r"\b"+re.escape(tok)+r"\b",source_lower) is None for tok in forbidden_domains)
        and all(re.search(r"\b"+re.escape(tok)+r"\b",source_raw) is None for tok in forbidden_legacy_constructors)
    )
    G["E16_only_supplied_developmental_dimensions_are_symmetry_and_window"]=(
        tuple(Kernel.FRAME_MODES)==(
            ("UNFRAMED",0),("ORIENTED",1),("ANCHORED",1),("FRAMED",2)
        )
        and all(set(x.keys())=={"mode","symmetry_breaks","event_window"} for r in results.values() for x in r["available_solutions"])
    )

    evidence={
        "experiment":"event_frame_genesis_v35",
        "scientific_freeze_commit":SCIENTIFIC_FREEZE_COMMIT,
        "freeze_manifest":freeze,
        "observed_git_blob_sha":observed,
        "results":results,
        "relabelled_results":relabelled,
        "incomplete":incomplete,
        "no_verifier":nover,
        "gates":G,
    }
    evidence["full_pass"]=all(G.values())
    evidence["verdict"]=(
        "VERIFIED_EVENT_FRAME_AND_WINDOW_GENESIS_FROM_BOUNDARY_SYMMETRY_OBSTRUCTION"
        if evidence["full_pass"] else "EVENT_FRAME_V35_GAPS_EXPOSED"
    )
    (HERE/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence["full_pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
