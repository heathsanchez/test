#!/usr/bin/env python3
"""Frozen seventh-source bounded native compiler. Does not learn a semantic grammar."""
import datetime,hashlib,importlib.util,json,pathlib,re,sqlite3,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
DEONTIC=ROOT/"deontic_obligation_v4"/"experiment.py"
READER=ROOT/"structural_obligation_ir_v1"/"experiment.py"
URL="https://www.sqlite.org/withoutrowid.html"
QUESTION="Does a WITHOUT ROWID table require declaration of a primary key?"
TARGET=("without","rowid","table","primary","key")
OUT=pathlib.Path(__file__).with_name("result.json")

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m
def word_set(t):
    words=set(re.findall(r"[a-z]+",t.lower()))
    if "tables" in words: words.add("table")
    if "keys" in words: words.add("key")
    return words
def score(ir):
    return sum(t in word_set(ir["subject"]+" "+ir["action"]) for t in TARGET)
def select(paragraphs,deontic):
    all_items=[]
    for i,p in enumerate(paragraphs):
        for ir in deontic.deontic_ir(p,{"url":URL,"paragraph_index":i}):
            all_items.append({"index":i,"score":score(ir),"ir":ir})
    return (sorted(all_items,key=lambda v:(-v["score"],v["index"]))[0]
            if all_items else None),len(all_items)
def compile_program(item):
    if not item or item["score"]<2:
        return {"status":"UNKNOWN_NO_TARGET_ALIGNED_NORMATIVE_CLAUSE"}
    ir=item["ir"]
    if ir["polarity"]!="REQUIRED":
        return {"status":"UNKNOWN_WRONG_MODALITY","observed_modality":ir["polarity"]}
    action=word_set(ir["action"])
    if not ("primary" in action and "key" in action) or not re.search(r"\b(?:have|specify|include|contain)\b",ir["action"],re.I):
        return {"status":"UNKNOWN_UNSUPPORTED_REQUIRED_SYNTAX"}
    # The question already specified WITHOUT ROWID. No arbitrary web text becomes SQL.
    modifier="WITHOUT ROWID"
    with_key="CREATE TABLE admitted_qualified (field INT PRIMARY KEY) "+modifier
    without_key="CREATE TABLE rejected_qualified (field INT) "+modifier
    return {"status":"ADMISSIBLE_DDL_WITNESS",
            "required_syntax":"PRIMARY KEY","mode":modifier,
            "positive_sql":with_key,"negative_sql":without_key}
def native(program):
    if program["status"]!="ADMISSIBLE_DDL_WITNESS":
        return {"status":"UNKNOWN_NOT_EXECUTED"}
    db=sqlite3.connect(":memory:")
    try:
        before=tuple(db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        db.execute("SAVEPOINT isolated")
        try:
            db.execute(program["negative_sql"])
            negative="ACCEPTED"
        except sqlite3.OperationalError:
            negative="REJECTED"
        db.execute(program["positive_sql"])
        positive=tuple(db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        db.execute("ROLLBACK TO isolated")
        db.execute("RELEASE isolated")
        after=tuple(db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        return {"status":"NATIVE_CHECKED","negative":negative,"positive_table_seen":("admitted_qualified",) in positive,
                "reverted":before==after,"prediction_matches":negative=="REJECTED" and
                ("admitted_qualified",) in positive and before==after}
    finally:db.close()
def main():
    d=module(DEONTIC,"unchanged_deontic_v4")
    r=module(READER,"unchanged_structural_reader_v1")
    preflight=d.deontic_ir("Every column definition must specify a datatype for that column.",
                           {"scope":"EXPOSED_STRICT"})
    assert any(x["polarity"]=="REQUIRED" for x in preflight)
    assert not d.deontic_ir("Suppose a column must contain something.",{"scope":"NEGATIVE"})
    req=urllib.request.Request(URL,headers={"User-Agent":"Metalogic-Warranted-Obligation-V5/1"})
    with urllib.request.urlopen(req,timeout=30) as resp:
        raw=resp.read(2_000_001); destination=resp.geturl()
    if len(raw)>2_000_000 or destination!=URL:
        raise RuntimeError("SOURCE_INTEGRITY_OR_SIZE")
    paragraphs=r.paragraphs(raw.decode("utf-8"))
    selected,count=select(paragraphs,d)
    program=compile_program(selected)
    outcome=native(program)
    if program["status"]!="ADMISSIBLE_DDL_WITNESS":
        status="UNKNOWN_NOT_COMPILED"
    elif not outcome["prediction_matches"]:
        status="REJECTED_NATIVE_MISMATCH"
    else:
        status="WARRANTED_BOUNDED_PROSPECTIVE_DDL_WITNESS"
    report={
      "source_url":URL,"source_sha256":hashlib.sha256(raw).hexdigest(),
      "retrieved_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "source_paragraphs":len(paragraphs),"deontic_items":count,
      "target_question":QUESTION,"selected":selected,"program":program,
      "native":outcome,"status":status,"source_model":"source span + fixed lexical grammar",
      "baseline":"equally informed human NOT MEASURED; same DDL witness available",
      "scientific_claim":"not new grammar or general source meaning; no production R7/CLC/MathGraph integration"
    }
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":status,"selected":selected,"program":program,
                      "native":outcome,"source_sha256":report["source_sha256"]},sort_keys=True))
    if status=="REJECTED_NATIVE_MISMATCH":
        raise AssertionError("native counterexample to source-compiled witness")
if __name__=="__main__":main()
