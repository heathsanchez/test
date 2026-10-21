#!/usr/bin/env python3
"""Read-only, resumable GitHub/source coverage inventory; never a scientific qualifier.

All network requests use the configured `gh api` client. Raw API pages and exact
Git references are frozen before content scanning; failures/limits remain data.
"""
from __future__ import annotations
import argparse, concurrent.futures, datetime, gzip, hashlib, json, pathlib, re, subprocess

SCHEMA='metalogic.accessible-source-coverage.v1'
FIELDS={
 'branches':('name','commit','protected'),
 'tags':('name','commit','tarball_url','zipball_url'),
 'workflows':('id','name','path','state','created_at','updated_at','html_url'),
 'runs':('id','name','workflow_id','head_branch','head_sha','path','event','status','conclusion','run_number','run_attempt','created_at','updated_at','html_url','artifacts_url','jobs_url','logs_url'),
 'artifacts':('id','name','size_in_bytes','expired','created_at','updated_at','expires_at','digest','workflow_run','archive_download_url'),
}
def compact_inventory(inv):
 for k,fields in FIELDS.items():
  if k in inv:
   inv[k]['rows']=[{f:r.get(f) for f in fields} for r in inv[k]['rows']]
 return inv
SIGNATURES=re.compile(r'\b(WARRANTED(?:_BOUNDED)?|PROVED|EXHAUSTIVE|PROSPECTIVE|CAUSAL|QUALIFIED|GENESIS|COMPOUNDING|PHASE_CHANGE|CONSTRUCTOR|OBSTRUCTION|REUSE|EXAPTATION|REVOCATION|TRANSFER|CERTIFICATE|UNKNOWN|REJECTED|SUPERSEDED)\b',re.I)
RESEARCH_NAMES=re.compile(r'(research|experiment|result|report|proof|formal|lean|certificate|receipt|protocol|qualif|paper|theor|genesis|develop|flash|lineage|retention|persist|abgp|blind|confirmation|boundary|separator|substrate|r7\.2|lock.key)',re.I)
EXTENSIONS={'.py','.md','.lean','.json','.yml','.yaml','.toml','.txt','.csv','.js','.ts','.jl','.sh','.tex','.rst'}

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(data): return hashlib.sha256(data).hexdigest()
def write(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def run(args,**kw): return subprocess.run(args,capture_output=True,**kw)
class Inventory:
 def __init__(self,root): self.root=root;self.root.mkdir(parents=True,exist_ok=True)
 def api(self,endpoint):
  key=hashlib.sha256(endpoint.encode()).hexdigest();p=self.root/'api'/f'{key}.json.gz';meta=p.with_suffix('.meta.json')
  if p.exists() and meta.exists():
   m=json.loads(meta.read_text())
   if m.get('ok'): return json.loads(gzip.decompress(p.read_bytes())),m
  start=now()
  try:
   r=run(['gh','api',endpoint],text=True,timeout=60)
   if r.returncode: raise RuntimeError(r.stderr.strip()[:1200])
   obj=json.loads(r.stdout);data=r.stdout.encode();m={'endpoint':endpoint,'retrieved_at':start,'ok':True,'sha256':digest(data),'bytes':len(data),'cache_file':str(p.relative_to(self.root))}
   p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(gzip.compress(data,mtime=0));write(meta,m);return obj,m
  except Exception as e:
   m={'endpoint':endpoint,'retrieved_at':start,'ok':False,'error':str(e)};write(meta,m);return None,m
 def pages(self,endpoint,key=None,limit=100):
  rows=[];receipts=[];status='PAGE_LIMIT_REACHED'
  for page in range(1,limit+1):
   ep=endpoint+('&' if '?' in endpoint else '?')+f'per_page=100&page={page}'
   obj,m=self.api(ep);receipts.append(m)
   if obj is None: status='INACCESSIBLE';break
   items=obj[key] if key else obj
   if not isinstance(items,list):status='UNEXPECTED_API_SCHEMA';break
   rows.extend(items)
   if len(items)<100:status='COMPLETE_AT_OBSERVED_PAGINATION_BOUNDARY';break
  return {'endpoint':endpoint,'status':status,'pages':receipts,'rows':rows,'reported_total':obj.get('total_count') if isinstance(obj,dict) else None}
 def freeze(self,owners,max_run_pages):
  owner_pages={o:self.pages(f'users/{o}/repos?type=all') for o in owners};repos={}
  for owner,inv in owner_pages.items():
   for r in inv['rows']:
    if r['owner']['login'].lower() not in {x.lower() for x in owners}:continue
    repos[r['full_name']]={k:r.get(k) for k in ('id','full_name','default_branch','size','private','archived','fork','pushed_at','clone_url','description')}
  write(self.root/'REPOSITORIES.json',{'schema':SCHEMA,'frozen_at':now(),'owners':owners,'owner_pages':owner_pages,'repositories':list(repos.values()),'boundary':'API-visible owned repositories at recorded times; deleted/inaccessible repositories excluded, not all scientific source inspected'})
  def one(r):
   name=r['full_name'];inv={'repository':name,'frozen_at':now()}
   for k,endpoint,key,limit in [('branches',f'repos/{name}/branches',None,100),('tags',f'repos/{name}/tags',None,100),('workflows',f'repos/{name}/actions/workflows','workflows',100),('runs',f'repos/{name}/actions/runs','workflow_runs',max_run_pages),('artifacts',f'repos/{name}/actions/artifacts','artifacts',max_run_pages)]:
    inv[k]=self.pages(endpoint,key,limit)
    compact_inventory(inv)
    # Checkpoints remain useful if any subsequent repository fails.
    write(self.root/'repositories'/f"{name.replace('/','__')}.json",inv)
   return name,{k:{'rows':len(v['rows']),'status':v['status'],'reported_total':v['reported_total']} for k,v in inv.items() if isinstance(v,dict) and 'rows'in v}
  summaries={}
  with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
   for name,s in pool.map(one,repos.values()):summaries[name]=s;write(self.root/'CHECKPOINT.json',{'schema':SCHEMA,'updated_at':now(),'completed_repositories':summaries})
  write(self.root/'FROZEN_UNIVERSE.json',{'schema':SCHEMA,'frozen_at':now(),'repositories_sha256':digest((self.root/'REPOSITORIES.json').read_bytes()),'repositories':summaries,'limits':{'run_and_artifact_pages_per_repository':max_run_pages,'page_size':100},'claim':'Metadata coverage only; COMPLETE statuses enumerate the accessible returned endpoint, not qualification or exhaustive scientific recovery.'})
 def scan(self,repos_root,max_blob_bytes):
  summaries=[]
  for repo in sorted(pathlib.Path(repos_root).iterdir()):
   if not(repo/'.git').exists():continue
   rr=run(['git','-C',str(repo),'remote','get-url','origin'],text=True)
   remote=rr.stdout.strip();m=re.search(r'github.com[:/]([^/]+/[^/]+?)(?:\.git)?$',remote)
   if not m or m[1].split('/')[0].lower() not in ('heathsanchez','metalogiclabs'):continue
   name=m[1];out=self.root/'source'/name.replace('/','__');out.mkdir(parents=True,exist_ok=True)
   refs=run(['git','-C',str(repo),'for-each-ref','--format=%(refname) %(objectname)'],text=True).stdout
   (out/'refs.txt').write_text(refs)
   commits=run(['git','-C',str(repo),'log','--all','--format=%H%x09%s'],text=True).stdout.splitlines()
   cm=[{'commit':a.split('\t',1)[0],'subject':a.split('\t',1)[-1],'signatures':sorted(set(x.upper() for x in SIGNATURES.findall(a)))} for a in commits if SIGNATURES.search(a)]
   write(out/'commit-signatures.json',cm)
   objs=run(['git','-C',str(repo),'rev-list','--objects','--all'],text=True).stdout.splitlines();names={}
   for line in objs:
    oid,_,path=line.partition(' ')
    if path and pathlib.PurePosixPath(path).suffix.lower() in EXTENSIONS:names.setdefault(oid,path)
   proc=subprocess.Popen(['git','-C',str(repo),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
   matches=[];scanned=0;oversize=[];bytecount=0
   try:
    for oid,path in names.items():
     proc.stdin.write((oid+'\n').encode());proc.stdin.flush();header=proc.stdout.readline().decode().strip().split()
     if len(header)!=3:continue
     size=int(header[2]);blob=proc.stdout.read(size);proc.stdout.read(1)
     if header[1]!='blob':continue
     if size>max_blob_bytes:oversize.append({'git_blob':oid,'path':path,'bytes':size});continue
     scanned+=1;bytecount+=size
     text=blob.decode('utf-8',errors='replace');ss=sorted(set(x.upper() for x in SIGNATURES.findall(text)))
     if not ss:continue
     lines=[{'line':i,'text':s[:500]} for i,s in enumerate(text.splitlines(),1) if SIGNATURES.search(s)]
     matches.append({'git_blob':oid,'sha256':digest(blob),'path':path,'bytes':size,'signatures':ss,'research_path':bool(RESEARCH_NAMES.search(path)),'matching_lines':len(lines),'sample':lines[:4]})
   finally:proc.stdin.close();proc.wait()
   data=json.dumps(matches,separators=(',',':')).encode();(out/'blob-signatures.json.gz').write_bytes(gzip.compress(data,mtime=0));write(out/'oversize.json',oversize)
   summary={'repository':name,'local_path':str(repo),'observed_at':now(),'refs':len(refs.splitlines()),'refs_sha256':digest(refs.encode()),'reachable_commits':len(commits),'commit_signature_matches':len(cm),'candidate_unique_source_blobs':len(names),'source_blobs_scanned':scanned,'source_bytes_scanned':bytecount,'oversize_not_scanned':len(oversize),'signature_matching_blobs':len(matches),'signature_research_path_blobs':sum(x['research_path'] for x in matches),'matches_file_sha256':digest(data),'note':'All source-extension historical blobs reachable from frozen LOCAL refs, within size bound. Signature matches are candidates, not scientific results. A Git blob has one representative path; occurrence at every commit not enumerated.'}
   write(out/'SUMMARY.json',summary);summaries.append(summary);write(self.root/'SOURCE_SCAN.json',{'schema':SCHEMA,'updated_at':now(),'max_blob_bytes':max_blob_bytes,'repositories':summaries})
   print(json.dumps(summary),flush=True)

 def default_trees(self):
  frozen=json.loads((self.root/'REPOSITORIES.json').read_text())['repositories']
  scanned={r['repository'] for r in json.loads((self.root/'SOURCE_SCAN.json').read_text())['repositories']}
  results=[]
  for repo in frozen:
   name=repo['full_name']
   if name in scanned:continue
   meta=json.loads((self.root/'repositories'/f"{name.replace('/','__')}.json").read_text())
   branch=next((r for r in meta.get('branches',{}).get('rows',[]) if r['name']==repo['default_branch']),None)
   if not branch:results.append({'repository':name,'status':'DEFAULT_BRANCH_NOT_ENUMERATED'});continue
   sha=branch['commit']['sha'];tree,receipt=self.api(f'repos/{name}/git/trees/{sha}?recursive=1')
   row={'repository':name,'default_commit':sha,'tree_receipt':receipt,'historical_source_coverage':'NOT_SCANNED','inspected_files':[]}
   if not tree or 'tree'not in tree:row['status']='TREE_INACCESSIBLE';results.append(row);continue
   row.update(status='DEFAULT_TREE_ENUMERATED',tree_truncated=tree.get('truncated'),paths=len(tree['tree']))
   candidates=[r for r in tree['tree'] if r['type']=='blob' and pathlib.PurePosixPath(r['path']).suffix.lower() in EXTENSIONS and RESEARCH_NAMES.search(r['path'])]
   row['research_path_candidates']=[{'path':r['path'],'git_blob':r['sha'],'bytes':r.get('size')} for r in candidates]
   selected=[r for r in tree['tree'] if r['type']=='blob' and r['path'].lower() in ('readme.md','readme.rst','readme','authority.json','research_report.md')]
   selected+=candidates[:3]
   for f in {x['sha']:x for x in selected}.values():
    if f.get('size',0)>200000:continue
    blob,rec=self.api(f"repos/{name}/git/blobs/{f['sha']}")
    file={'path':f['path'],'git_blob':f['sha'],'receipt':rec}
    if blob and blob.get('encoding')=='base64':
     import base64
     data=base64.b64decode(blob['content']);text=data.decode('utf8',errors='replace')
     file.update(sha256=digest(data),bytes=len(data),signatures=sorted(set(x.upper() for x in SIGNATURES.findall(text))))
    row['inspected_files'].append(file)
   results.append(row);write(self.root/'DEFAULT_TREE_COVERAGE.json',{'schema':SCHEMA,'updated_at':now(),'boundary':'Additional default-branch tree and limited source inspection; not historical source closure. At most3 research-path files plus named root documents per repository.','repositories':results})

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['freeze','scan','default-trees']);p.add_argument('--output',type=pathlib.Path,default=pathlib.Path(__file__).parent);p.add_argument('--repos-root',default='/workspace/repos');p.add_argument('--max-run-pages',type=int,default=30);p.add_argument('--max-blob-bytes',type=int,default=2_000_000);a=p.parse_args();x=Inventory(a.output)
 if a.mode=='freeze':x.freeze(['heathsanchez','metalogiclabs'],a.max_run_pages)
 elif a.mode=='scan':x.scan(a.repos_root,a.max_blob_bytes)
 else:x.default_trees()
if __name__=='__main__':main()
