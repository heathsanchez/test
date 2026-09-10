import copy,tempfile,unittest
from pathlib import Path
from open_development.arc_discrimination import develop_stream,evaluate,freeze_state
from open_development.runtime import digest
from open_development.release_v4 import build,validate

def task(inp,out):return {"train":[{"input":inp,"output":out}],"test":[{"input":inp,"output":out}]}
def stream():
 rows=[]
 for i in range(3):
  for name,t in [("reuse",task([[1,2],[3,4]],[[3,1],[4,2]])),("exaptation",task([[0,0,0],[0,1,2],[0,3,4]],[[1,2],[3,4]])),("expansion",task([[1,2]],[[1,2,2,1]])),("unknown",task([[1,2]],[[9]]))]:rows.append({"task_id":f"{name}-{i}","task_sha256":digest(t),"stratum":"fixture","task":t})
 body={"schema":"arc-route-neutral-stream/v1","selection_nonce":"1:1","tasks":rows,"route_labels_present":False}
 return {**body,"stream_digest":digest(body)}

class ReleaseV4Tests(unittest.TestCase):
 def evidence(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/"s";freeze_state(p);s=stream();s.update(external_repository="fchollet/ARC-AGI",external_commit="399030444e0ab0cc8b4e199870fb20b863846f34",corpus_identity={"corpus_digest":"a"*64});s["stream_digest"]=digest({k:v for k,v in s.items()if k!="stream_digest"});d=develop_stream(s,p);e=evaluate(s,d)
   f={"canonical_parent":"003e6ccfa91205a1f0ea408656c10b8afbdb10c4","source_commit":"b"*40}
   f["freeze_digest"]=digest(f)
   return f,s,d,e
 def test_roundtrip_and_tamper(self):
  f,s,d,e=self.evidence();m=build("b"*40,1,f,s,d,e);validate(m,f,s,d,e)
  bad=copy.deepcopy(m);bad["route_counts"]["EXPANSION"]=0
  with self.assertRaisesRegex(ValueError,"stale"):validate(bad,f,s,d,e)
 def test_no_v4_for_unknown(self):
  f,s,d,e=self.evidence();e["outcome"]="UNKNOWN_EXTERNAL_ROUTE_COVERAGE";e["v4_eligible"]=False
  with self.assertRaisesRegex(ValueError,"did not qualify"):build("b"*40,1,f,s,d,e)

if __name__=="__main__":unittest.main()
