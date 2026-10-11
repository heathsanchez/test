#!/usr/bin/env python3
"""Fetch the published Figure 2 source image, not the designated Figure 3b holdout."""
from pathlib import Path
from urllib.request import Request,urlopen
import hashlib,json
url="https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41467-022-35045-3/MediaObjects/41467_2022_35045_Fig2_HTML.png"
dst=Path(__file__).parent/"source_figures"
dst.mkdir(exist_ok=True)
try:
 req=Request(url,headers={"User-Agent":"Mozilla/5.0", "Accept":"image/png,image/*;q=0.8"})
 with urlopen(req,timeout=35) as f:
  data=f.read()
 assert data[:8]==b"\x89PNG\r\n\x1a\n","Image not PNG"
 (dst/"published_Fig2.png").write_bytes(data)
 print("SOURCE_FIG2_FETCHED",json.dumps({"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"url":url}))
except Exception as e:
 print("SOURCE_FIG2_UNAVAILABLE",repr(e))
