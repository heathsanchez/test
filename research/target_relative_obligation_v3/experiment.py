#!/usr/bin/env python3
"""Frozen prospective source-target relevance, NOT an intent inference engine."""
import datetime,hashlib,html,importlib.util,json,pathlib,re,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
V1=ROOT/"structural_obligation_ir_v1"/"experiment.py"
URL="https://www.sqlite.org/gencol.html"
QUESTION="is a database permitted to explicitly supply a value for a generated column in an INSERT or UPDATE statement?"
TOKENS=("generated","column","insert","update","value")
OUT=pathlib.Path(__file__).with_name("result.json")
def v1_module():
    spec=importlib.util.spec_from_file_location("unmodified_structural_ir_v1",V1)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m
def tokens(text):
    words=set(re.findall(r"[a-z]+",text.lower()))
    if "columns" in words:words.add("column")
    if "values" in words:words.add("value")
    if "generated" in words:words.add("generated")
    return words
def score(ir):
    if ir["status"]!="STRUCTURAL_IR":return -1
    clause=ir["condition"]+" "+ir["required_effect"]
    return sum(t in tokens(clause) for t in TOKENS)
def main():
    m=v1_module()
    # Finite independent selector controls on known synthetic examples:
    a=m.structural_ir("If one unrelated operation fails, then all other changes remain.",{"scope":"synthetic"})
    b=m.structural_ir("If a generated column value is supplied by INSERT, then the engine applies a check.",{"scope":"synthetic"})
    assert a["status"]=="STRUCTURAL_IR" and b["status"]=="STRUCTURAL_IR"
    assert score(b)>score(a)
    req=urllib.request.Request(URL,headers={"User-Agent":"Metalogic-Obligation-V3-Research/1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read(2_000_001);actual=r.geturl()
    if len(raw)>2_000_000 or actual!=URL:raise RuntimeError("SOURCE_INTEGRITY_FAILURE")
    paragraphs=m.paragraphs(raw.decode("utf-8"))
    candidates=[]
    for i,p in enumerate(paragraphs):
        ir=m.structural_ir(p,{"url":URL,"paragraph_index":i})
        if ir["status"]=="STRUCTURAL_IR":
            candidates.append({"index":i,"score":score(ir),"ir":ir})
    first=candidates[0] if candidates else None
    candidate=sorted(candidates,key=lambda x:(-x["score"],x["index"]))[0] if candidates else None
    if not candidate or candidate["score"]<2:
        outcome="UNKNOWN_NO_TARGET_RELEVANT_STRUCTURAL_RELATION"
    else:
        outcome="CANDIDATE_TARGET_RELEVANT_STRUCTURE_ONLY"
    # This is only a separate SOURCE suitability signal, not extracted semantics.
    text=re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",raw.decode("utf-8")))).lower()
    topic=("generated" in text and "column" in text)
    result={"source":URL,"sha256":hashlib.sha256(raw).hexdigest(),
        "retrieved_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "target_question":QUESTION,"terms":TOKENS,
        "paragraphs":len(paragraphs),"structural_matches":len(candidates),
        "first":first,"target_selected":candidate,
        "source_topic_present":topic,"target_admission":outcome,
        "witness":"UNKNOWN_UNSUPPORTED_NATIVE_WITNESS",
        "real_normative_answer":"UNKNOWN_NOT_ADJUDICATED",
        "expert_comparator":"NOT_EXECUTED","R7_CLC_MATHGRAPH":"UNCHANGED_UNINVOKED"}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"source_sha256":result["sha256"],"first":first,
       "target_selected":candidate,"target_admission":outcome,
       "source_topic_present":topic},sort_keys=True))
if __name__=="__main__":main()
