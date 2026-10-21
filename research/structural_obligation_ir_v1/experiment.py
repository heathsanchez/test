#!/usr/bin/env python3
"""Exposed training plus frozen third-source IR transfer. Human-coded grammar, not autonomous learning."""
from __future__ import annotations
import datetime,hashlib,html,json,re,sqlite3,urllib.request
from html.parser import HTMLParser
from pathlib import Path

TRAINING={
  "CHECK":{
    "url":"https://www.sqlite.org/lang_createtable.html",
    "snippet":"If the result is zero (integer value 0 or real value 0.0), then a constraint violation has occurred.",
    "expect_kind":"CHECK_ZERO_VIOLATION"
  },
  "CASCADE":{
    "url":"https://www.sqlite.org/foreignkeys.html",
    "snippet":'For an "ON DELETE CASCADE" action, this means that each row in the child table that was associated with the deleted parent row is also deleted.',
    "expect_kind":"CASCADE_CHILD_DELETE"
  }
}
THIRD="https://www.sqlite.org/lang_createtrigger.html"
class Paragraphs(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.current=[];self.skip=0
    def handle_starttag(self,t,a):
        if t in ("script","style"):self.skip+=1
    def handle_data(self,d):
        if self.skip==0:self.current.append(d)
    def handle_endtag(self,t):
        if t in ("script","style"):self.skip-=1
        if t in ("p","li","h2","h3","pre") and self.current:
            v=re.sub(r"\s+"," ",html.unescape(" ".join(self.current))).strip()
            if v:self.parts.append(v)
            self.current=[]
def paragraphs(data):
    p=Paragraphs();p.feed(data);return p.parts
def structural_ir(fragment,authority):
    """Source-span anchored generic conditional/effect relations. No source-specific outcome oracle."""
    s=re.sub(r"\s+"," ",fragment).strip()
    # Two limited structural connectives, learned from EXPOSED training excerpts.
    patterns=[
      r"\bIf (.{4,170}?), then (.{4,200}?)(?:\.|$)",
      r"\bFor (.{4,170}?), this means that (.{4,210}?)(?:\.|$)"
    ]
    for pat in patterns:
        m=re.search(pat,s,re.I)
        if m:
            return {"status":"STRUCTURAL_IR","authority":authority,
                    "condition":m.group(1).strip(),"required_effect":m.group(2).strip(),
                    "source_span":m.group(0),"witness":None,
                    "verification":"UNKNOWN_UNTIL_NATIVE",
                    "method":"finite human-authored connective grammar"}
    return {"status":"UNKNOWN_NO_STRUCTURAL_RELATION","authority":authority}
def classify_training(ir):
    if ir["status"]!="STRUCTURAL_IR":return "UNKNOWN"
    t=(ir["condition"]+" "+ir["required_effect"]).lower()
    if "result is zero" in t and "constraint violation" in t:return "CHECK_ZERO_VIOLATION"
    if "on delete cascade" in t and "child table" in t and "deleted" in t:return "CASCADE_CHILD_DELETE"
    return "UNKNOWN_UNSUPPORTED_WITNESS"
def native_check(kind):
    db=sqlite3.connect(":memory:")
    try:
        if kind=="CHECK_ZERO_VIOLATION":
            db.execute("CREATE TABLE v(x INTEGER CHECK(x))")
            db.execute("SAVEPOINT s")
            try:
                db.execute("INSERT INTO v VALUES(0)");out="ACCEPTED"
            except sqlite3.IntegrityError:out="REJECTED"
            db.execute("ROLLBACK TO s");db.execute("RELEASE s")
            assert db.execute("SELECT COUNT(*) FROM v").fetchone()[0]==0
            return {"outcome":out,"expected":"REJECTED","pass":out=="REJECTED","restored":True}
        if kind=="CASCADE_CHILD_DELETE":
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("CREATE TABLE parent(id INTEGER PRIMARY KEY)")
            db.execute("CREATE TABLE child(id INTEGER PRIMARY KEY, pid INTEGER REFERENCES parent(id) ON DELETE CASCADE)")
            db.execute("INSERT INTO parent VALUES(7)");db.execute("INSERT INTO child VALUES(1,7)")
            db.commit()
            db.execute("SAVEPOINT s");db.execute("DELETE FROM parent WHERE id=7")
            after=db.execute("SELECT COUNT(*) FROM child").fetchone()[0]
            db.execute("ROLLBACK TO s");db.execute("RELEASE s")
            before=db.execute("SELECT COUNT(*) FROM child").fetchone()[0]
            return {"outcome":after,"expected":0,"pass":after==0 and before==1,"restored":before==1}
        return {"status":"UNKNOWN_NO_NATIVE_WITNESS"}
    finally:db.close()
def load(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Metalogic-Obligation-IR-Research/1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        data=r.read(2_000_001); final=r.geturl()
    if len(data)>2_000_000 or final!=url:raise RuntimeError("SOURCE_IDENTITY")
    return data
def main():
    trains=[]
    for label,x in TRAINING.items():
        # Frozen exposed examples (curated from previously examined official docs).
        ir=structural_ir(x["snippet"],{"url":x["url"],"scope":"EXPOSED_CURATED_QUOTE"})
        assert ir["status"]=="STRUCTURAL_IR",(label,ir)
        kind=classify_training(ir); assert kind==x["expect_kind"],(label,kind)
        check=native_check(kind);assert check["pass"] and check["restored"]
        trains.append({"name":label,"ir":ir,"native":check})
    # Safety negative controls (no authority inferred from bare noun or negated mention)
    assert structural_ir("The CHECK constraint exists.",{"scope":"synthetic"})["status"].startswith("UNKNOWN")
    # The third source was selected and frozen before writing this parser.
    raw=load(THIRD); pages=paragraphs(raw.decode("utf-8"))
    third_candidates=[structural_ir(p,{"url":THIRD,"paragraph_index":i}) for i,p in enumerate(pages)]
    extracted=[q for q in third_candidates if q["status"]=="STRUCTURAL_IR"]
    # First hit, no post-outcome cherry-picking. No trigger-specific witness grammar.
    candidate=extracted[0] if extracted else {"status":"UNKNOWN_NO_STRUCTURAL_RELATION"}
    kind=classify_training(candidate)
    if candidate["status"]!="STRUCTURAL_IR":verdict="UNKNOWN_INAPPLICABLE_STRUCTURAL_GRAMMAR"
    elif kind=="UNKNOWN_UNSUPPORTED_WITNESS":verdict="IR_ONLY_UNSUPPORTED_NATIVE_OBLIGATION"
    else:verdict="CANDIDATE_PREPROGRAMMED_TRAINING_SEMANTICS_NOT_NEW_GRAMMAR"
    report={"source_url":THIRD,"source_sha256":hashlib.sha256(raw).hexdigest(),
       "retrieved_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "training":trains,"third":{"paragraphs":len(pages),"matching_relations":len(extracted),
          "first":candidate,"witness_kind":kind,"verdict":verdict,"native":"NOT_ATTEMPTED",
          "baseline":"FULLY_INFORMED_HUMAN_NOT_MEASURED"},
       "scope":"human-authored structural grammar; third source not yet seen at freeze"}
    Path(__file__).with_name("result.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"training":[(x["name"],x["native"]["pass"]) for x in trains],
        "third":report["third"],"source_sha256":report["source_sha256"]},sort_keys=True))
if __name__=="__main__":main()
