#!/usr/bin/env python3
"""Source-blind, metadata-only V5 first-eligible PR selection.

Uses GitHub REST PR metadata and file *paths only*. GitHub's files endpoint can
send patch bodies, but this worker deliberately discards those fields and never
logs, persists, or exposes them to subsequent execution. No source clone.
UNKNOWN preserves the entire universe and exclusions.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[2]
SPEC="research/unified_consequence_runtime/G2_OBSERVATION_CHOICE_V5_PREQUERY.json"
FREEZE="fc3177b20e7508d511c32a9ec6c76d711cc8389d"
HEX=re.compile(r"[a-f0-9]{40}\Z")
SRC=re.compile(r"src/(?:[^/]+/)*[^/]+\.py\Z")
TEST=re.compile(r"tests/(?:[^/]+/)*test_[^/]+\.py\Z")
VETO=re.compile(r"(?:^|/)(?:\.github|requirements|build|ci)(?:/|$)|(?:^|/)(?:pyproject\.toml|tox\.ini|setup\.py|setup\.cfg|noxfile\.py|uv\.lock|poetry\.lock|Pipfile\.lock)\Z")

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def gitshow(commit,path):
    return subprocess.check_output(["git","show",commit+":"+path],cwd=ROOT,timeout=30)

def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True)

def read_spec():
    actual=(ROOT/SPEC).read_bytes()
    reference=gitshow(FREEZE,SPEC)
    if actual!=reference:
        raise ValueError("UNKNOWN_PREQUERY_MUTATED")
    config=json.loads(actual)
    if config.get("schema")!="UDM_G2_V5_SOURCE_BLIND_OBSERVATION_CHOICE_PREQUERY":
        raise ValueError("UNKNOWN_PROTOCOL_IDENTITY")
    repos=config["source_blind_repo_order"]
    exclusion=set(x.casefold() for x in config["historical_exclusions"])
    if len(set(x.casefold() for x in repos))!=len(repos):
        raise ValueError("UNKNOWN_DUPLICATE_REPOSITORY")
    if any(x.casefold() in exclusion for x in repos):
        raise ValueError("UNKNOWN_TRAINING_SOURCE_COLLISION")
    if any(not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",x) for x in repos):
        raise ValueError("UNKNOWN_REPOSITORY_NAME")
    return config,digest(actual)

class GitHub:
    def __init__(self,token,limit):
        if not token:raise ValueError("UNKNOWN_MISSING_READONLY_METADATA_TOKEN")
        self.token=token;self.limit=limit;self.calls=0
    def get(self,path,params=None):
        self.calls+=1
        if self.calls>self.limit:raise ValueError("UNKNOWN_METADATA_API_BUDGET")
        url="https://api.github.com/"+path.lstrip("/")
        if params:url+="?"+urlencode(params)
        req=Request(url,headers={
            "Authorization":"Bearer "+self.token,
            "Accept":"application/vnd.github+json",
            "X-GitHub-Api-Version":"2022-11-28",
            "User-Agent":"MathGraph-SourceBlind-V5"})
        try:
            with urlopen(req,timeout=35) as resp:raw=resp.read()
        except HTTPError as exc:
            # API apparatus diagnosis only: no response body, title, patch or
            # source content can reach the experimenter in the error record.
            typ=("ISSUE_SEARCH" if path=="search/issues"
                 else "PR_FILES" if path.endswith("/files")
                 else "PR_DETAIL" if "/pulls/" in path
                 else "MERGE_COMMIT" if "/commits/" in path
                 else "OTHER")
            context=(params or {}).get("q","").split("repo:",1)[-1].split(" ",1)[0] if typ=="ISSUE_SEARCH" else "NONE"
            raise ValueError("UNKNOWN_METADATA_HTTP_"+str(exc.code)+"_"+typ+"_"+context) from None
        except (URLError,TimeoutError) as exc:
            raise ValueError("UNKNOWN_METADATA_TRANSPORT") from None
        return json.loads(raw)
    def matching_prs(self,repo,max_results):
        q=f"repo:{repo} is:pr is:merged merged:2026-01-01..2026-09-30"
        data=self.get("search/issues",dict(q=q,sort="created",order="asc",per_page=max_results))
        items=data.get("items",[])
        return sorted(items,key=lambda x:(x.get("created_at",""),x.get("number",0)))
    def paths(self,repo,num,max_pages):
        paths=[]
        for page in range(1,max_pages+1):
            page_data=self.get(f"repos/{repo}/pulls/{num}/files",dict(per_page=100,page=page))
            if not isinstance(page_data,list):raise ValueError("UNKNOWN_PR_FILES_SCHEMA")
            # Crucial: deliberately project only file paths, status. Drop patch bodies.
            paths.extend({"path":x["filename"],"status":x["status"]} for x in page_data)
            if len(page_data)<100:return paths
        raise ValueError("UNKNOWN_CHANGED_FILE_PAGINATION")

def eligible_paths(files):
    if not files:return "NO_CHANGED_FILES",None
    # Treat GitHub file paths as untrusted before matching accepted regexes.
    if any(not isinstance(x.get("path"),str) or not x["path"]
           or x["path"].startswith("/") or "\\" in x["path"]
           or any(part in ("",".","..") for part in x["path"].split("/"))
           for x in files):
        return "UNSAFE_NONCANONICAL_PATH",None
    if any(VETO.search(x["path"]) for x in files):
        return "CHANGED_BUILD_OR_ENVIRONMENT",None
    if any(x["path"].endswith(".py") and not(SRC.fullmatch(x["path"]) or TEST.fullmatch(x["path"])) for x in files):
        return "OTHER_PYTHON_SOURCE_CHANGED",None
    prod=[x for x in files if SRC.fullmatch(x["path"])]
    tests=[x for x in files if TEST.fullmatch(x["path"])]
    if len(prod)!=1 or len(tests)!=1:
        return "PRODUCTION_TEST_PAIR_NOT_UNIQUE",None
    if any(x["status"] not in ("modified","added") for x in (*prod,*tests)):
        return "UNSUPPORTED_FILE_CHANGE_KIND",None
    return "ELIGIBLE",(prod[0]["path"],tests[0]["path"])

def shortlist(config,client):
    criteria=config["metadata_rule"];records=[];all_reasons={}
    for repo in config["source_blind_repo_order"]:
        if len(records)>=criteria["minimum_eligible"]:break
        reasons=Counter();found=None
        matches=client.matching_prs(repo,criteria["max_search_results_per_repo"])
        if not matches:reasons["NO_MERGED_MATCHES"]+=1
        for row in matches:
            number=row["number"]
            files=client.paths(repo,number,criteria["max_PR_file_pages"])
            reason,paths=eligible_paths(files)
            if paths is None:
                reasons[reason]+=1;continue
            pr=client.get(f"repos/{repo}/pulls/{number}")
            merge=pr.get("merge_commit_sha");head=(pr.get("head") or {}).get("sha")
            if not(pr.get("merged_at") and pr["merged_at"].startswith("2026-")
                   and isinstance(merge,str) and HEX.fullmatch(merge)
                   and isinstance(head,str) and HEX.fullmatch(head)):
                reasons["MISSING_IMMUTABLE_MERGE_OR_HEAD"]+=1;continue
            commit=client.get(f"repos/{repo}/commits/{merge}")
            parents=commit.get("parents") or []
            base=parents[0].get("sha") if parents else None
            if not isinstance(base,str) or not HEX.fullmatch(base):
                reasons["MISSING_PREMERGE_PARENT_SHA"]+=1;continue
            found={"repo":repo,"number":number,"base":base,"author_head":head,
                   "merge_commit":merge,"production":paths[0],"author_test":paths[1],
                   "merged_at":pr["merged_at"],"source":"GITHUB_METADATA_PROJECTION_ONLY"}
            break
        all_reasons[repo]={"candidates_considered":sum(reasons.values())+(1 if found else 0),
                           "refusals":dict(sorted(reasons.items())),"selected":bool(found)}
        if found:records.append(found)
    return records,all_reasons

def run(output):
    output=Path(output).absolute();output.mkdir(parents=True,exist_ok=False)
    result={"schema":"UDM_G2_V5_METADATA_RESULT","status":"UNKNOWN_NOT_EXECUTED",
            "scientific":"NO_G2_CLAIM","G2":"UNKNOWN","G3":"UNKNOWN",
            "G4":"UNKNOWN","future":"SEALED_UNOPENED",
            "source_or_test_bodies_fetched_by_scientific_stage":False}
    try:
        config,h=read_spec();result["prequery_sha256"]=h
        result["prequery_commit"]=FREEZE
        result["repository_order"]=config["source_blind_repo_order"]
        result["excluded"]=config["historical_exclusions"]
        client=GitHub(os.environ.get("GH_TOKEN"),config["budgets"]["metadata_requests_soft_cap"])
        records,reasons=shortlist(config,client)
        result["api_calls"]=client.calls
        result["metadata_screening"]=reasons
        result["eligible_count"]=len(records)
        need=config["metadata_rule"]["minimum_eligible"]
        if len(records)<need:
            result["status"]="UNKNOWN_POOL_INCOMPLETE"
            result["roles"]=[]
        else:
            result["status"]="ROLE_CANDIDATES_METADATA_ONLY_NOT_FROZEN"
            result["roles"]=[
                {**r,"role":("SEALED_FUTURE" if i==need-1 else "TRAINING_"+str(i)),
                 "source_body":"UNOPENED","native_status":"NOT_EXECUTED"}
                for i,r in enumerate(records[:need])]
        result["metadata_sha256"]=digest(canonical({
            "protocol":h,"roles":result["roles"],"screening":reasons}).encode())
    except Exception as error:
        result["status"]="UNKNOWN_METADATA_APPARATUS"
        result["reason"]=type(error).__name__+":"+str(error)
    (output/"METADATA_RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result

if __name__=="__main__":
    outcome=run(sys.argv[1])
    print(json.dumps({"status":outcome["status"],"eligible":outcome.get("eligible_count"),
                      "calls":outcome.get("api_calls"),"G2":"UNKNOWN",
                      "reason":outcome.get("reason")},sort_keys=True))
    if outcome["status"] not in ("ROLE_CANDIDATES_METADATA_ONLY_NOT_FROZEN","UNKNOWN_POOL_INCOMPLETE"):
        raise SystemExit(2)
