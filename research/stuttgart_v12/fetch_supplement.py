#!/usr/bin/env python3
"""Source documentation only: retrieves public Supplementary Information, NEVER Fig3b raw."""
from urllib.request import Request,urlopen
from pathlib import Path
import hashlib,json
root=Path(__file__).parent/"supplement_source"
root.mkdir(exist_ok=True)
urls=[
 "https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-022-35045-3/MediaObjects/41467_2022_35045_MOESM1_ESM.pdf",
 "https://pmc.ncbi.nlm.nih.gov/articles/PMC9726817/bin/41467_2022_35045_MOESM1_ESM.pdf",
 "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9726817/bin/41467_2022_35045_MOESM1_ESM.pdf",
 "https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-022-35045-3/MediaObjects/41467_2022_35045_MOESM1_ESM.pdf?download=1"
]
errors=[]
for url in urls:
 try:
  req=Request(url,headers={"User-Agent":"Mozilla/5.0 (independent academic source verification)","Accept":"application/pdf,*/*;q=.5"})
  with urlopen(req,timeout=25) as r:
   blob=r.read()
   end=r.url
  if not blob.startswith(b"%PDF-"): raise ValueError("Not a PDF: prefix "+repr(blob[:40]))
  name=root/"published_supplement.pdf"
  name.write_bytes(blob)
  receipt={"status":"FETCHED","source_url":url,"final_url":end,"size":len(blob),"sha256":hashlib.sha256(blob).hexdigest()}
  (root/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
  print("SUPPLEMENT_RECEIPT",json.dumps(receipt))
  break
 except Exception as e:
  errors.append({"url":url,"error":type(e).__name__+":"+str(e)[:180]})
else:
 (root/"receipt.json").write_text(json.dumps({"status":"UNAVAILABLE","errors":errors},indent=2)+"\n")
 print("SUPPLEMENT_UNAVAILABLE",json.dumps(errors))
