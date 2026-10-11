#!/usr/bin/env python3
"""Read public DaRUS repository *metadata only*; never download held-out numeric files."""
from urllib.request import urlopen,Request
from urllib.parse import quote
from pathlib import Path
import json
u="https://darus.uni-stuttgart.de/api/datasets/:persistentId/?persistentId="+quote("doi:10.18419/DARUS-3262",safe="")
out=Path(__file__).resolve().parent/"public_inventory.json"
try:
 with urlopen(Request(u,headers={"User-Agent":"Research replication metadata audit"}),timeout=45) as f: raw=json.load(f)
 d=raw["data"]["latestVersion"]
 files=d["files"]
 clean=[{"label":f.get("label"),"id":f.get("dataFile",{}).get("id"),"contentType":f.get("dataFile",{}).get("contentType"),
 "size":f.get("dataFile",{}).get("filesize"),"md5":f.get("dataFile",{}).get("md5")} for f in files]
 result={"status":"SUCCESS","dataset_version":d.get("versionNumber"),
 "dataset_minor_version":d.get("versionMinorNumber"),"file_count":len(clean),"files":clean,
 "constraint":"Metadata-only retrieval. No sealed Fig3b bytes accessed."}
except Exception as ex:
 result={"status":"UNAVAILABLE","reason":repr(ex),"constraint":"No sealed data requested"}
out.write_text(json.dumps(result,indent=2)+"\n")
print("DATASET_METADATA",json.dumps(result))
