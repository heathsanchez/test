#!/usr/bin/env python3
import csv, io, json, hashlib
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote

root = Path(__file__).parent / "calibration_data"
root.mkdir(exist_ok=True)
files = {
  "Fig2bdata.csv":("9","b56696a90f7e19eaf74e4efaf77371ce",24),
  "Fig2cdata.csv":("14","bd5cd2a1319e4013fb97d19bd211b5b5",45)
}
manifest={}
for name,(suffix,known_md5,required_rows) in files.items():
    doi = "doi:10.18419/DARUS-3262/"+suffix
    endpoint = "https://darus.uni-stuttgart.de/api/access/datafile/:persistentId?persistentId="+quote(doi,safe="")
    errors=[]
    for url in (endpoint+"&format=original", endpoint):
        try:
            req=Request(url,headers={"User-Agent":"research-replication-stuttgart-v11","Accept":"*/*"})
            with urlopen(req,timeout=60) as response:
                raw=response.read()
                final_url=response.geturl()
            if not raw or raw[:1] in (b"<",b"{"):
                raise ValueError("not a valid published data file")
            value=raw.decode("utf-8-sig")
            rows=list(csv.reader(io.StringIO(value),delimiter="\\t" if "\\t" in value[:120] else ","))
            if len(rows)<required_rows:
                raise ValueError("too few rows: "+str(len(rows)))
            result={"file":name,"source":doi,"byte_count":len(raw),
              "received_sha256":hashlib.sha256(raw).hexdigest(),
              "received_md5":hashlib.md5(raw).hexdigest(),
              "published_original_md5":known_md5,"md5_match":hashlib.md5(raw).hexdigest()==known_md5,
              "rows_including_header":len(rows),"first_rows":rows[:5],"final_url":final_url}
            manifest[name]=result
            (root/name).write_bytes(raw)
            print("CALIBRATION_DATA",name,value)
            print("CALIBRATION_RECEIPT",json.dumps(result))
            break
        except Exception as exc:
            errors.append(repr(exc))
    else:
        manifest[name]={"status":"UNAVAILABLE","errors":errors}
        print("CALIBRATION_FETCH_FAILED",name,errors)
(root/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
assert all("status" not in r for r in manifest.values()),"Failed calibration acquisition; holdout remains sealed"
print("CALIBRATION_DONE; holdout never requested")
