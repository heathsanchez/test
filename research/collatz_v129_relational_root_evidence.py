"""V129 exact typed class-identity ledger, logically separate from LowerMerge.

This code is a verifier of individual class-identity witnesses; the
universal completeness theorem is independently checked by Lean.
An odd-three-root may exceed its source. No class-identity edge is
inserted into the V124 typed LOWER source-join state.
"""
import hashlib,json,pathlib
from research.collatz_v126_three_root_normal_form import T,replay,normalize

SOURCE_STATE="research/collatz_ros_state_v124.json"
FORMAL_PINS={
 "V125_REVERSE_ROOT":{"run":37981885036,"sha":"07d1b9f428c95a589bf195f540769472ee90e21c"},
 "V126_BOUNDED_ROOT_SECTION":{"run":37982730204,"sha":"808d214c538c806b5ebc2c7407c9ba25336a8fbe"},
 "V127_ODD_ROOT_QUOTIENT":{"run":37983264734,"sha":"5d02e486f11b5c05a86db427b804832b86c5830c"},
 "V128_MULTI_ROOT_SEPARATOR":{"run":37983621550,"sha":"2bda4439b015f4ac6e3aa901b84a6097776881a9"}
}

def class_witness(n,root,a,b,support):
    if not (n>0 and root>0 and root%6==3 and a>=0 and b>=0):
        raise ValueError("Not a typed positive odd-three-root class witness")
    x,y=replay(n,a),replay(root,b)
    if x!=y:
        raise ValueError("The actual two-clock future classes differ")
    if support not in FORMAL_PINS:
        raise ValueError("Unknown semantic support")
    return dict(source=n,root=root,source_clock=a,root_clock=b,
                common=x,support=support,
                KIND="CLASS_EQUIVALENCE_NOT_LOWER_MERGE")

def audit():
    v124=pathlib.Path(SOURCE_STATE).read_bytes()
    old=json.loads(v124)
    assert old["admission_schema"]=="COLLATZ_ROS_V124_TYPED_WARRANT_ADMISSION"
    assert len(old["joins"])==7 and old["global_collatz"]=="UNKNOWN"
    before=hashlib.sha256(v124).hexdigest()
    assert before=="bb8ccf524dffff9b4bad973d3bf09f60114b114240d77cd59b331a0f2366f16e"
    roots=[
        class_witness(8,3,0,2,"V127_ODD_ROOT_QUOTIENT"),
        class_witness(8,21,0,3,"V128_MULTI_ROOT_SEPARATOR"),
        class_witness(6,3,1,0,"V125_REVERSE_ROOT"),
        class_witness(1,21,0,6,"V126_BOUNDED_ROOT_SECTION"),
        class_witness(21,3,3,2,"V128_MULTI_ROOT_SEPARATOR"),
    ]
    assert len({r["root"] for r in roots if r["source"]==8})==2
    assert [r for r in roots if r["source"]==6][0]["source_clock"]>0
    assert [r for r in roots if r["source"]==1][0]["root"]>1
    assert [r for r in roots if r["source"]==21][0]["root"]<21
    env={21,32,16,8,4,2,1}
    assert all(T(x) in env for x in env)
    assert all(normalize(x)[0]==21 for x in env)
    x=21
    for _ in range(1000):
        assert normalize(x)[0]==21
        x=T(x)
    assert pathlib.Path(SOURCE_STATE).read_bytes()==v124
    result=dict(
        schema="COLLATZ_V129_TYPED_RELATIONAL_ROOT_CLASSES",
        status="BOUNDED_EXACT_RELATIONAL_EVIDENCE_FORMAL_CANDIDATE",
        formal_provenance=FORMAL_PINS,
        parent_v124_raw_sha256=before,
        class_identity_edges=roots,
        source_eight_valid_distinct_roots=2,
        source_six_requires_asynchronous_clock=True,
        source_twentyone_selected_root_stutters_all_clocks="LEAN_V128",
        selected_root_of_one_is_larger=True,
        v124_lower_source_join_count_unchanged=len(old["joins"]),
        no_root_transport_promoted_to_lower_merge=True,
        universal_root_class_event_producer=False,
        global_collatz="UNKNOWN",qed=False)
    blob=json.dumps(result,sort_keys=True,separators=(",",":"))
    result["payload_sha256"]=hashlib.sha256(blob.encode()).hexdigest()
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=="__main__":
    audit()
