#!/usr/bin/env python3
"""G2 new-pool metadata-only selection. NEVER fetch PR body, source, patch or test text."""
from __future__ import annotations
import hashlib,json,os,pathlib,subprocess,sys,time,urllib.parse,urllib.request,urllib.error
ROOT=pathlib.Path(__file__).resolve().parents[2]
PATH="research/unified_consequence_runtime/G2_SOURCE_NEUTRAL_NEW_POOL_PREQUERY_V1.json"
FREEZE="23f30b0e9bdf267da3054f81b0895f6b988baab0"
HEADERS={"Accept":"application/vnd.github+json","User-Agent":"udm-g2-metadata-only","X-GitHub-Api-Version":"2022-11-28"}
if os.getenv("GITHUB_TOKEN"): HEADERS["Authorization"]="Bearer "+os.environ["GITHUB_TOKEN"]
def get(path):
    req=urllib.request.Request("https://api.github.com"+path,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=35) as r:return json.load(r)
def eligible(files,excluded):
    names=[x["filename"] for x in files]
    if len(names)<2 or len(names)>8:return None
    if any(x.startswith(".github/") or x.endswith((".toml",".cfg",".ini",".lock",".yml",".yaml")) or "requirements" in x for x in names):return None
    py=[x for x in names if x.endswith(".py")]
    tests=[x for x in py if x.startswith(("tests/","test/")) or pathlib.PurePosixPath(x).name.startswith("test_")]
    prod=[x for x in py if x not in tests and not any(p in ("/"+x+"/") for p in ("/examples/","/docs/","/scripts/","/samples/","/benchmarks/","/generated/"))]
    if len(tests)!=1 or len(prod)!=1:return None
    if excluded:return None
    return {"production":prod[0],"author_test":tests[0]}
def main(output):
    output.mkdir(parents=True,exist_ok=False)
    raw=(ROOT/PATH).read_bytes()
    frozen=subprocess.check_output(["git","-C",str(ROOT),"show",FREEZE+":"+PATH],timeout=30)
    if raw!=frozen:raise RuntimeError("PREQUERY_MANIFEST_MUTATED")
    m=json.loads(raw);allrows=[];eligible_rows=[];start=time.monotonic()
    for repo in m["repository_order"]:
        record={"repo":repo,"status":"UNKNOWN_METADATA"}
        try:
            # Distinct original source families: exclude known previously touched repositories.
            seen={"pallets/werkzeug","pallets/click","psf/requests","urllib3/urllib3",
                  "pydantic/pydantic","pypa/packaging","python-attrs/attrs",
                  "agronholm/anyio","python-trio/trio","pytest-dev/pluggy"}
            if repo in seen:
                record["status"]="EXCLUDED_HISTORICALLY_EXPOSED_REPO"
            else:
                q=urllib.parse.quote("repo:"+repo+" is:pr is:merged fix in:title",safe="")
                hits=get("/search/issues?q="+q+"&sort=updated&order=desc&per_page=30")["items"]
                for h in hits[:12]:
                    title=h.get("title","")
                    if not title.lower().startswith(("fix","bugfix")):continue
                    num=h["number"]
                    pr=get("/repos/"+repo+"/pulls/"+str(num))
                    if not pr.get("merged_at") or not pr.get("base",{}).get("sha") or not pr.get("head",{}).get("sha"):continue
                    names=get("/repos/"+repo+"/pulls/"+str(num)+"/files?per_page=100")
                    if len(names)!=pr.get("changed_files"):continue
                    paths=eligible(names,False)
                    if paths:
                        record={"repo":repo,"pr":num,"title":title,
                           "base":pr["base"]["sha"],"head":pr["head"]["sha"],**paths,
                           "status":"METADATA_ELIGIBLE_SOURCE_UNOPENED"}
                        eligible_rows.append(record)
                        break
                if record["status"]=="UNKNOWN_METADATA":record["status"]="NO_ELIGIBLE_METADATA_WITHIN_FROZEN_SCREEN"
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,KeyError,ValueError) as e:
            record["status"]="UNKNOWN_METADATA_APPARATUS"
            record["error"]=type(e).__name__+":"+str(e)[:150]
        allrows.append(record)
        (output/"PROGRESS.json").write_text(json.dumps({"screened":allrows,"eligible_so_far":len(eligible_rows),"source_opened":False},indent=2)+"\n")
        print(repo,record["status"],flush=True)
        if len(eligible_rows)==7:break
    state="METADATA_7_ROLES_FROZEN_READY_FOR_SEPARATE_NATIVE_COMMIT" if len(eligible_rows)==7 else "UNKNOWN_POOL_INCOMPLETE_NO_SUBSTITUTION"
    result={"schema":"G2_SOURCE_NEUTRAL_METADATA_SCREEN_V1","prequery_sha256":hashlib.sha256(raw).hexdigest(),
       "status":state,"roles":{"training":[dict(x,role="TRAINING_ADMISSION",order=i) for i,x in enumerate(eligible_rows[:5])],
       "sealed_future":[dict(x,role="SEALED_FUTURE",order=i+5) for i,x in enumerate(eligible_rows[5:7])]},
       "all_screened":allrows,"source_opened":False,"native_executed":False,"future":"SEALED_UNOPENED",
       "G2":"UNKNOWN","G4":"UNKNOWN","elapsed_seconds":round(time.monotonic()-start,3)}
    (output/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("VERDICT",state,"ELIGIBLE",len(eligible_rows),flush=True)
    return result
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: metadata_screen.py NEW_OUTPUT_DIR")
    main(pathlib.Path(sys.argv[1]).resolve())
