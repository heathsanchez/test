#!/usr/bin/env python3
"""Explicitly bounded publication ABSTRACT canonicalization; not a generic science parser."""
from html.parser import HTMLParser
from html import unescape
from pathlib import Path
import hashlib,re,subprocess,unicodedata,json,time
URL="https://journals.aps.org/prc/abstract/10.1103/f6gq-ghvh"
class ArticleHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta=[]
        self.parts=[]
        self.ignore=0
    def handle_starttag(self,t,attrs):
        d=dict(attrs)
        if t in ("style","script"): self.ignore+=1
        if t=="meta":
            k=(d.get("name") or d.get("property") or "").lower()
            if k in ("citation_abstract","description","og:description","twitter:description","dc.description"):
                self.meta.append((k,unescape(d.get("content") or "")))
    def handle_endtag(self,t):
        if t in ("style","script") and self.ignore: self.ignore-=1
    def handle_data(self,data):
        if not self.ignore:self.parts.append(data)
def norm(s):
    return re.sub(r"\s+"," ",unicodedata.normalize("NFKC",unescape(s))).strip()
def extract(raw):
    h=ArticleHTML();h.feed(raw.decode("utf8",errors="replace"))
    keys=("0.854","0.851","stat","sys")
    meta=sorted([norm(text) for label,text in h.meta if all(t in norm(text).lower() for t in keys)],
                key=len,reverse=True)
    if meta:
        return {"strategy":"PUBLISHER_DESCRIPTION_META","abstract":meta[0],"length":len(meta[0])}
    text=norm(" ".join(h.parts))
    start=text.lower().find("for the first approach")
    end=text.lower().find("both approaches yield",start)
    if start < 0 or end < 0:
        return {"strategy":"SOURCE_EXCERPT_NOT_AVAILABLE","length":len(text)}
    sub=text[start:end+min(len(text)-end,190)]
    if not all(t in sub.lower() for t in keys):
        return {"strategy":"SOURCE_EXCERPT_ANCHORS_MISSING","length":len(sub)}
    return {"strategy":"ABSTRACT_TEXT_FRAGMENT_FALLBACK","abstract":sub,"length":len(sub)}
def get(i):
    p=Path(f"/tmp/scatter_probe_{i}.html")
    x=subprocess.run(["curl","-L","--fail","--silent","--show-error",
         "-A","Mozilla/5.0","--max-time","40","-o",str(p),URL],
        capture_output=True,text=True,timeout=52)
    if x.returncode or not p.exists():
        return {"error":x.stderr[-220:]}
    raw=p.read_bytes();s=extract(raw)
    rec={"url":URL,"byte_length":len(raw),"raw_sha256":hashlib.sha256(raw).hexdigest(),
         "strategy":s["strategy"],"abstract_length":s["length"]}
    if "abstract" in s:
        paragraph=s["abstract"]
        rec["canonical_sha256"]=hashlib.sha256(paragraph.encode()).hexdigest()
        rec["holds_reported_values"]={
           "first_charge_fit":("0.854" in paragraph),
           "second_charge_fit":("0.851" in paragraph),
           "stat":("stat" in paragraph.lower()),
           "sys":("sys" in paragraph.lower())}
    return rec
def main():
    a=get(1);time.sleep(2);b=get(2)
    report={"first":a,"second":b,
      "stable_canonical_abstract":a.get("canonical_sha256") is not None and
        a.get("canonical_sha256")==b.get("canonical_sha256"),
      "same_raw_transport_bytes":a.get("raw_sha256")==b.get("raw_sha256"),
      "authority":"CANDIDATE_SOURCE_CONTENT_NOT_FULL_RAW_DOCUMENT"}
    path=Path("research/nist_scattering_rounding/evidence/canonical_probe.json")
    path.parent.mkdir(exist_ok=True,parents=True)
    path.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
