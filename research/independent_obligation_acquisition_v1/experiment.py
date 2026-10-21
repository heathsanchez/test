#!/usr/bin/env python3
"""Frozen finite-grammar prospective experiment. Source acquired at runtime."""
import datetime, hashlib, html, json, re, sqlite3, urllib.request
from html.parser import HTMLParser
from pathlib import Path

URL="https://www.sqlite.org/lang_createtable.html"
OUT=Path(__file__).with_name("result.json")
class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__();self.parts=[];self.buf=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.skip+=1
        if tag in ('p','h1','h2','h3','h4','li') and self.buf:
            self.parts.append(' '.join(self.buf));self.buf=[]
    def handle_data(self,data):
        if not self.skip:self.buf.append(data)
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip=max(0,self.skip-1)
        if tag in ('p','h1','h2','h3','h4','li') and self.buf:
            self.parts.append(' '.join(self.buf));self.buf=[]

def normalize(s):return re.sub(r'\s+',' ',html.unescape(s)).strip()
def extract(text):
    """Only one explicit bounded normative semantics template, no hand-supplied truth label."""
    parser=Paragraphs();parser.feed(text)
    paragraphs=[normalize(x) for x in parser.parts]
    # A CHECK-bound requirement must itself contain the term CHECK and an explicit
    # zero-to-violation causal relation. No external list of expected facts.
    for para in paragraphs:
        low=para.lower()
        if "check" not in low or "zero" not in low or "violation" not in low:
            continue
        pattern=r'(?:if|when)\b.{0,250}?(?:result|expression).{0,250}?\bzero\b.{0,180}?\b(?:violation|violated|fails|failed)\b'
        if re.search(pattern,low,re.S):
            return dict(status="CLAUSE_EXTRACTED",kind="CHECK_ZERO_VIOLATION",source_clause=para[:900],
                        expected="REJECT_ZERO")
    return {"status":"UNKNOWN_NO_UNAMBIGUOUS_NORMATIVE_CLAUSE"}

def verify_native(obligation):
    if obligation["status"]!="CLAUSE_EXTRACTED":
        return {"status":"UNKNOWN_NOT_EXECUTED"}
    db=sqlite3.connect(":memory:")
    try:
        db.execute("CREATE TABLE witness (x INTEGER CHECK (x))")
        db.execute("SAVEPOINT trial_zero")
        try:
            db.execute("INSERT INTO witness (x) VALUES (0)")
            zero="ACCEPT"
        except sqlite3.IntegrityError:
            zero="REJECT"
        finally:
            db.execute("ROLLBACK TO trial_zero")
            db.execute("RELEASE trial_zero")
        db.execute("SAVEPOINT trial_one")
        try:
            db.execute("INSERT INTO witness (x) VALUES (1)")
            one="ACCEPT"
        except sqlite3.IntegrityError:
            one="REJECT"
        finally:
            db.execute("ROLLBACK TO trial_one")
            db.execute("RELEASE trial_one")
        assert db.execute("SELECT COUNT(*) FROM witness").fetchone()[0]==0
        return dict(status="NATIVE_VERIFIED",zero=zero,one=one,restored_empty=True,
                    prediction_correct=(zero=="REJECT" if obligation["expected"]=="REJECT_ZERO" else False))
    finally:db.close()

def main():
    # Test the parser for unsafe promotion on deliberately irrelevant strings before network input.
    controls=[
      "A CHECK constraint was discussed but no enforceable rule was stated.",
      "If the result is zero, this is merely a sample: no CHECK constraint violation is described.",
      "CHECK expressions may contain unrelated values; no violation is specified."
    ]
    # These are controls of the authored grammar, not exhaustive adversarial validation.
    control_result=[extract("<p>"+x+"</p>")["status"] for x in controls]
    # Intentionally report control failures instead of silently dropping them.
    if any(x!="UNKNOWN_NO_UNAMBIGUOUS_NORMATIVE_CLAUSE" for x in control_result):
        raise AssertionError("guard control produced false normative acquisition")
    request=urllib.request.Request(URL,headers={"User-Agent":"Metalogic-Research-Evidence-Audit/1.0"})
    with urllib.request.urlopen(request,timeout=30) as resp:
        raw=resp.read(2_000_001)
        if len(raw)>2_000_000:raise RuntimeError("SOURCE_TOO_LARGE")
        effective_url=resp.geturl()
    if effective_url != URL:raise RuntimeError("SOURCE_REDIRECTED")
    decoded=raw.decode("utf-8")
    obligation=extract(decoded)
    native=verify_native(obligation)
    report=dict(url=URL,retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
       source_sha256=hashlib.sha256(raw).hexdigest(),source_bytes=len(raw),
       obligation=obligation,native=native,guard_controls=control_result,
       method="frozen finite documented phrase grammar",prior_semantics_given_to_compiler=False,
       declared_semantics_template_is_human_written=True,
       strong_human_baseline="UNMEASURED",R7_CLC_MATHGRAPH="unchanged, not invoked")
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:report[k] for k in ("source_sha256","obligation","native","strong_human_baseline")},sort_keys=True))
    if native["status"]=="NATIVE_VERIFIED" and not native["prediction_correct"]:
        raise RuntimeError("NATIVE_CONTRADICTS_EXTRACTED_CLAUSE")
if __name__=="__main__":main()
