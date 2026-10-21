#!/usr/bin/env python3
"""Finite human-authored deontic grammar; sixth-source transfer with no native claim."""
import datetime,hashlib,html,importlib.util,json,pathlib,re,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
V1=ROOT/"structural_obligation_ir_v1"/"experiment.py"
URL="https://www.sqlite.org/stricttables.html"
QUESTION="What constraints do STRICT tables impose on the declarations of their columns?"
TARGET=("strict","table","column","declaration")
OUT=pathlib.Path(__file__).with_name("result.json")

def v1_module():
    spec=importlib.util.spec_from_file_location("frozen_source_reader_v1",V1)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj

def deontic_ir(text,authority):
    clean=re.sub(r"\s+"," ",html.unescape(text)).strip()
    # Defined from EXPOSED examples only: prohibit, oblige and permit.
    clauses=re.split(r"(?<=[.;])\s+|,\s+but\s+|\s+but\s+",clean,flags=re.I)
    candidates=[]
    for clause in clauses:
        pat=(r"(?P<subject>[A-Za-z][A-Za-z0-9 '\-()]{2,130}?)\s+"
             r"(?P<modal>must not|may not|can not|cannot|must|are required to|is required to|are allowed to|is allowed to|can)"
             r"\s+(?P<action>[A-Za-z][^.?!;]{3,180})")
        match=re.search(pat,clause,re.I)
        if not match:continue
        modal=match.group("modal").lower()
        if modal in ("must not","may not","can not","cannot"):
            polarity="PROHIBITED"
        elif modal in ("must","are required to","is required to"):
            polarity="REQUIRED"
        else:polarity="PERMITTED"
        # A source sentence marked as a conjecture, example, or negated narration
        # is not promoted to normative source authority.
        if re.search(r"\b(?:suppose|hypothetically|imagine|example only|not actually)\b",clause,re.I):
            continue
        candidates.append({"status":"DEONTIC_IR","authority":authority,
          "subject":match.group("subject").strip(),"modality":modal,
          "polarity":polarity,"action":match.group("action").strip(),
          "source_span":match.group(0),"witness":"UNKNOWN_NOT_CONSTRUCTED"})
    return candidates

def lexical_score(ir):
    terms=set(re.findall(r"[a-z]+",ir["subject"].lower()+" "+ir["action"].lower()))
    if "tables" in terms:terms.add("table")
    if "columns" in terms:terms.add("column")
    if "declarations" in terms or "definition" in terms or "definitions" in terms:terms.add("declaration")
    return sum(k in terms for k in TARGET)

def main():
    exposed="Generated columns can be read, but their values can not be directly written."
    controls=deontic_ir(exposed,{"scope":"EXPOSED_GENERATED"})
    assert any(x["polarity"]=="PROHIBITED" and "written" in x["action"] for x in controls),controls
    assert deontic_ir("Suppose columns must be ignored.",{"scope":"synthetic"})==[]
    assert deontic_ir("This documentation describes several kinds of tables.",{"scope":"synthetic"})==[]
    request=urllib.request.Request(URL,headers={"User-Agent":"Metalogic-Deontic-IR-V4/1"})
    with urllib.request.urlopen(request,timeout=30) as r:
        raw=r.read(2_000_001);actual=r.geturl()
    if len(raw)>2_000_000 or actual!=URL:raise RuntimeError("SOURCE_INTEGRITY_FAILURE")
    p=v1_module()
    paragraphs=p.paragraphs(raw.decode("utf-8"))
    found=[]
    for i,para in enumerate(paragraphs):
        for ir in deontic_ir(para,{"url":URL,"paragraph_index":i}):
            found.append({"paragraph_index":i,"score":lexical_score(ir),"ir":ir})
    selected=sorted(found,key=lambda x:(-x["score"],x["paragraph_index"]))[0] if found else None
    if not selected or selected["score"]<2:
        verdict="UNKNOWN_NO_TARGET_ALIGNED_DEONTIC_OBLIGATION"
    else:verdict="CANDIDATE_DEONTIC_STRUCTURE_ONLY"
    # Content source suitability only; independent semantic adjudication pending.
    rawtext=re.sub(r"<[^>]+>"," ",raw.decode("utf-8")).lower()
    topic="strict" in rawtext and "column" in rawtext
    report={"source":URL,"sha256":hashlib.sha256(raw).hexdigest(),
      "retrieved_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "question":QUESTION,"target_terms":TARGET,"source_topic_exists":topic,
      "exposed_controls":controls,"paragraph_count":len(paragraphs),"candidate_count":len(found),
      "selected":selected,"verdict":verdict,
      "native_witness":"UNKNOWN_UNSUPPORTED_NATIVE_WITNESS",
      "independent_intent_adjudication":"NOT_PERFORMED",
      "expert_comparator":"UNMEASURED","R7_CLC_MATHGRAPH":"UNCHANGED_NOT_INVOKED"}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"sha256":report["sha256"],"candidate_count":len(found),
      "selected":selected,"verdict":verdict,"source_topic_exists":topic},sort_keys=True))
if __name__=="__main__":main()
