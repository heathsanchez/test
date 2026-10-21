"""Read-only source-native historical admission diagnostic against exact upstream commits."""
from pathlib import Path
from research.unified_consequence_runtime.decisive_native_verify import _test_nodes, _test_patterns
import subprocess, tempfile, json, hashlib
SUBJECTS=[
("more-itertools/more-itertools","67fcf640477c78605580f5ee703a54c73c1e7a8a","tests/test_more.py","b3a9351595a6fd7f1aa9c1e35978f08106e43df0"),
("python-attrs/attrs","91f3695fe70a6d58c95660addd5ef8d46bfebd61","tests/test_validators.py","5ad2308eb89e6dfa8b0f6362969775b69c692fd6"),
("python-attrs/cattrs","5fd1c7f89f6c5f19b91cc5f2758a0fbf7740730b","tests/test_tuples.py","c1a9562c3c25ae8e1002aeca00a1ffe34cd2bd24")]
results=[]
with tempfile.TemporaryDirectory() as base:
 for i,(repo,commit,path,blob) in enumerate(SUBJECTS):
  dest=Path(base)/str(i)
  subprocess.run(["git","init","-q",str(dest)],check=True)
  subprocess.run(["git","-C",str(dest),"fetch","-q","--depth=1","https://github.com/"+repo+".git",commit],check=True)
  head=subprocess.check_output(["git","-C",str(dest),"rev-parse","FETCH_HEAD"],text=True).strip()
  assert head==commit,(repo,head)
  raw=subprocess.check_output(["git","-C",str(dest),"show","FETCH_HEAD:"+path])
  expected=subprocess.check_output(["git","-C",str(dest),"rev-parse","FETCH_HEAD:"+path],text=True).strip()
  assert expected==blob,(repo,expected)
  try:
   tree,nodes=_test_nodes(path,raw)
   status="ADMITTED_BOUNDARY_ONLY"
  except ValueError as e:
   nodes=[];status="UNKNOWN_CONTRACT";reason=str(e)
  record={"repo":repo,"commit":commit,"test_blob":blob,"status":status,"nodes":len(nodes),"sha256":hashlib.sha256(raw).hexdigest()}
  if status!="ADMITTED_BOUNDARY_ONLY":record["reason"]=reason
  results.append(record)
print(json.dumps(results,indent=2))
Path("historical-author-tests-admission.json").write_text(json.dumps(results,indent=2))
if any(r["status"]!="ADMITTED_BOUNDARY_ONLY" for r in results):raise SystemExit(2)
