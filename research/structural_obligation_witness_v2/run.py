#!/usr/bin/env python3
"""Frozen V1 structure + fixed exposed-family witness catalog; fourth-source transfer."""
import datetime,hashlib,html,importlib.util,json,pathlib,re,sqlite3,urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/"structural_obligation_ir_v1"/"experiment.py"
FOURTH="https://www.sqlite.org/lang_conflict.html"
OUT=pathlib.Path(__file__).with_name("result.json")

def load_v1():
    spec=importlib.util.spec_from_file_location("frozen_structural_ir_v1",ORIGINAL)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def safe_observation_program(ir,v1):
    """Only exposed families; no untrusted SQL text is executed."""
    if ir.get("status")!="STRUCTURAL_IR":
        return {"status":"UNKNOWN_NO_VALID_IR"}
    kind=v1.classify_training(ir)
    if kind in ("CHECK_ZERO_VIOLATION","CASCADE_CHILD_DELETE"):
        return {"status":"PROGRAM_ADMITTED","family":kind,
                "outcome":v1.native_check(kind)}
    # The third family is exposed but not in V1 planner, so add a single
    # finite, *training-authorized* operation for UPDATE OF trigger.
    clause=(ir["condition"]+" "+ir["required_effect"]).lower()
    if ("update of" in clause and "trigger" in clause and
        "left-hand side" in clause and "set clause" in clause):
        db=sqlite3.connect(":memory:")
        try:
            db.execute("CREATE TABLE source(id INTEGER PRIMARY KEY,x INT,y INT)")
            db.execute("CREATE TABLE events(mark INT)")
            db.execute("CREATE TRIGGER tr AFTER UPDATE OF x ON source BEGIN INSERT INTO events VALUES(1); END")
            db.execute("INSERT INTO source VALUES(1,3,4)")
            db.commit()
            db.execute("SAVEPOINT test")
            db.execute("UPDATE source SET y=5 WHERE id=1")
            left=db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            db.execute("UPDATE source SET x=6 WHERE id=1")
            right=db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            db.execute("ROLLBACK TO test")
            db.execute("RELEASE test")
            unchanged=db.execute("SELECT x,y FROM source WHERE id=1").fetchone()==(3,4)
            return {"status":"PROGRAM_ADMITTED","family":"EXPOSED_TRIGGER_UPDATE_OF",
                    "outcome":{"non_target":left,"target":right,"pass":left==0 and right==1 and unchanged}}
        finally:
            db.close()
    return {"status":"UNKNOWN_UNSUPPORTED_WITNESS","reason":"effect not expressible by frozen witness library"}

def fetch():
    req=urllib.request.Request(FOURTH,headers={"User-Agent":"Metalogic-Obligation-Witness-V2/1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        body=r.read(2_000_001);loc=r.geturl()
    if len(body)>2_000_000 or loc!=FOURTH:raise RuntimeError("SOURCE_INTEGRITY_FAILURE")
    return body

def main():
    v1=load_v1()
    # Exposed calibration only; the witness operation family is selected from
    # previously exposed source clauses, not supplied as a truth oracle.
    controls=[]
    for name,t in v1.TRAINING.items():
        ir=v1.structural_ir(t["snippet"],{"source":t["url"],"scope":"EXPOSED"})
        result=safe_observation_program(ir,v1)
        assert result["status"]=="PROGRAM_ADMITTED" and result["outcome"]["pass"],(name,result)
        controls.append({"name":name,"program":result["family"],"pass":True})
    trigger_quote='If the "UPDATE OF column-name" syntax is used, then the trigger will only fire if column-name appears on the left-hand side of one of the terms in the SET clause of the UPDATE statement.'
    trigger_ir=v1.structural_ir(trigger_quote,{"scope":"EXPOSED_TRIGGER"})
    trigger=safe_observation_program(trigger_ir,v1)
    assert trigger["status"]=="PROGRAM_ADMITTED" and trigger["outcome"]["pass"]
    controls.append({"name":"EXPOSED_TRIGGER","program":trigger["family"],"pass":True})
    # Execute the *unchanged* structural extractor then the unchanged catalog
    # on the independent fourth source, with no keyword-targeted selection.
    raw=fetch()
    paragraphs=v1.paragraphs(raw.decode("utf-8"))
    candidate=None
    for i,para in enumerate(paragraphs):
        ir=v1.structural_ir(para,{"url":FOURTH,"paragraph_index":i})
        if ir["status"]=="STRUCTURAL_IR":
            candidate=ir
            break
    if candidate is None:
        result={"status":"UNKNOWN_INAPPLICABLE_STRUCTURAL_GRAMMAR"}
        verdict="INAPPLICABLE"
    else:
        result=safe_observation_program(candidate,v1)
        verdict=("PROSPECTIVE_NATIVE_SUCCESS" if result.get("status")=="PROGRAM_ADMITTED" and
                 result.get("outcome",{}).get("pass",False) else
                 "UNKNOWN_UNSUPPORTED_NATIVE_WITNESS")
    # Independent source topicality check; not an extractor input.
    text=re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",raw.decode("utf-8")))).lower()
    relevant=("ignore" in text and "constraint" in text)
    if verdict=="PROSPECTIVE_NATIVE_SUCCESS" and candidate and "ignore" not in
      (candidate["condition"]+" "+candidate["required_effect"]).lower():
        verdict="FALSE_TOPIC_WRONG_SEMANTIC_FAMILY"
    report={
       "scope":"fourth official SQLite semantics; frozen V1 structure and exposed-family programs",
       "source_url":FOURTH,"source_sha256":hashlib.sha256(raw).hexdigest(),
       "retrieval_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "preflight":controls,"source_topic_exists":relevant,
       "fourth":{"selected":candidate,"compiled":result,"verdict":verdict},
       "full_information_expert":"NOT_MEASURED",
       "R7_CLC_MATHGRAPH":"UNMODIFIED_AND_NOT_INVOKED"
    }
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"preflight":controls,"fourth":report["fourth"],
                      "topic_exists":relevant,"source_sha256":report["source_sha256"]},sort_keys=True))
if __name__=="__main__":main()
