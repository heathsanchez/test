#!/usr/bin/env python3
"""Read-only cross-repository GitHub evidence census. No external dependencies."""
import os, json, re, time, urllib.request, urllib.error, pathlib, collections, datetime
TOKEN=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
ROOT="https://api.github.com"
OUT=pathlib.Path("evidence-census"); OUT.mkdir(exist_ok=True)
HEAD={"Accept":"application/vnd.github+json","User-Agent":"metalogic-evidence-census","X-GitHub-Api-Version":"2022-11-28"}
if TOKEN: HEAD["Authorization"]="Bearer "+TOKEN
PAT=re.compile(r"consequen|verified|warrant|genesis|develop|compound|closure|reclosure|qckn?|rgrs|flash|transfer|causal|ablation|constructor|grammar|authorit|qualification|obstruction|unknown|reject|supersed|replay|lineage|meta|capabilit",re.I)
EVID=re.compile(r"(?:RESULT|REPORT|EVIDENCE|AUTHORITY|QUALIF|SUMMARY|PROTOCOL|VERDICT|README|SNAPSHOT|MANIFEST)",re.I)
RUN=re.compile(r"(?:actions/runs/)([0-9]+)")
VERDICT=re.compile(r"PASS[_A-Z0-9-]*|VERIFIED[_A-Z0-9-]*|WARRANTED[_A-Z0-9-]*|UNKNOWN[_A-Z0-9-]*|REJECTED[_A-Z0-9-]*|FAIL[_A-Z0-9-]*",re.I)
MAX_BRANCHES=int(os.environ.get("MAX_BRANCHES_PER_REPO","0"))
MAX_TREES=int(os.environ.get("MAX_TREES_PER_REPO","50"))
MAX_CONTENT=int(os.environ.get("MAX_CONTENT_FILES","180"))
MAX_REPOS=int(os.environ.get("MAX_REPOS","0"))
calls=0; errors=[]; results=[]; branch_rows=[]; evidence=[]; inspected=0
def api(path):
 global calls
 for retry in range(4):
  try:
   req=urllib.request.Request(ROOT+path,headers=HEAD)
   with urllib.request.urlopen(req,timeout=35) as f:
    calls+=1
    return json.load(f)
  except urllib.error.HTTPError as e:
   if e.code in (403,429) and retry<3:
    delay=min(60,5*(2**retry));time.sleep(delay);continue
   errors.append({"path":path,"status":e.code,"error":str(e)});return None
  except Exception as e:
   errors.append({"path":path,"error":str(e)});return None
 return None
def pages(path,cap=200):
 allrows=[]
 for page in range(1,cap+1):
  sep="&" if "?" in path else "?"
  rows=api(path+sep+"per_page=100&page="+str(page))
  if not isinstance(rows,list):break
  allrows.extend(rows)
  if len(rows)<100:break
 return allrows
repos=[]
for account,kind in [("heathsanchez","users"),("metalogiclabs","orgs")]:
 for item in pages("/"+kind+"/"+account+"/repos?type=all",20):
  if not item.get("archived") and not item.get("fork"):
   repos.append(item)
repos=sorted(repos,key=lambda x:x["full_name"])
if MAX_REPOS:repos=repos[:MAX_REPOS]
for repo in repos:
 name=repo["full_name"]; base=repo["default_branch"]
 branches=pages("/repos/"+name+"/branches",100)
 if MAX_BRANCHES:branches=branches[:MAX_BRANCHES]
 candidates=sorted(branches,key=lambda b:(-len(PAT.findall(b["name"])),b["name"]))
 selected=candidates[:MAX_TREES]
 selected_names={x["name"] for x in selected}
 summary={"repo":name,"default_branch":base,"branches_enumerated":len(branches),"branches_tree_inspected":0,"candidate_branches":sum(bool(PAT.search(x["name"])) for x in branches),"tree_truncated":len(branches)>MAX_TREES,"errors":0}
 for b in branches:
  branch_rows.append({"repo":name,"branch":b["name"],"commit":b["commit"]["sha"],"keywords":sorted(set(z.lower() for z in PAT.findall(b["name"]))),"tree_inspected":b["name"] in selected_names})
 for b in selected:
  sha=b["commit"]["sha"]; branch=b["name"]
  tree=api("/repos/"+name+"/git/trees/"+sha+"?recursive=1")
  if not isinstance(tree,dict) or "tree" not in tree:continue
  summary["branches_tree_inspected"]+=1
  for f in tree["tree"]:
   path=f.get("path","")
   if f.get("type")!="blob" or not PAT.search(path) or not EVID.search(path):continue
   row={"repo":name,"branch":branch,"commit":sha,"path":path,"blob_sha":f.get("sha"),"size":f.get("size"),"url":"https://github.com/"+name+"/blob/"+sha+"/"+path,"keywords":sorted(set(z.lower() for z in PAT.findall(path))),"status":"CANDIDATE_UNQUALIFIED","run_ids":[],"verdict_tokens":[]}
   if inspected<MAX_CONTENT and path.lower().endswith((".md",".json",".txt")) and (f.get("size") or 0)<80000:
    from urllib.parse import quote
    data=api("/repos/"+name+"/contents/"+quote(path,safe="/")+"?ref="+sha)
    if isinstance(data,dict) and data.get("content") and data.get("encoding")=="base64":
     import base64
     try:
      body=base64.b64decode(data["content"]).decode("utf8","replace");inspected+=1
      row["run_ids"]=sorted(set(RUN.findall(body)))[:12]
      row["verdict_tokens"]=sorted(set(VERDICT.findall(body)))[:15]
      row["status"]="EVIDENCE_TEXT_FOUND_NEEDS_RUN_VERIFICATION" if row["run_ids"] else "CLAIM_FOUND_NEEDS_VERIFICATION"
     except Exception:pass
   evidence.append(row)
 summary["errors"]=sum(x.get("path","").startswith("/repos/"+name+"/") for x in errors)
 results.append(summary)
 print(json.dumps({"repo":name,"branches":len(branches),"trees":summary["branches_tree_inspected"],"evidence":sum(x["repo"]==name for x in evidence)}),flush=True)
def write(name,data):
 (OUT/name).write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
write("repositories.json",results);write("branches.json",branch_rows);write("evidence_candidates.json",evidence);write("errors.json",errors)
ranked=sorted(evidence,key=lambda x:(-len(x["run_ids"]),-len(x["verdict_tokens"]),-len(x["keywords"]),x["repo"],x["path"]))
write("shortlist.json",ranked[:300])
meta={"generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"repos":len(results),"branches":len(branch_rows),"trees":sum(x["branches_tree_inspected"] for x in results),"evidence_candidates":len(evidence),"text_files_read":inspected,"api_calls":calls,"errors":len(errors),"limitations":["Branch listing covers current refs, not deleted refs or unreachable commits.","Tree inspection capped per repository; see tree_truncated.","Text scan does not establish independent verification or scientific warrant.","Run links extracted from prose are not checked for conclusion in this phase.","Repository listing excludes forks and archived repositories."]}
write("manifest.json",meta)
(OUT/"README.md").write_text("# Cross-GitHub evidence census\n\n"+json.dumps(meta,indent=2)+"\n\nNo candidate is automatically WARRANTED. Inspect original run/artifact and declared verification boundary.\n")
print(json.dumps(meta),flush=True)
