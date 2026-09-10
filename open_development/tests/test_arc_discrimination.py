import tempfile, unittest
from pathlib import Path
from open_development.arc_discrimination import ARCAdapter,D4,develop_stream,evaluate,freeze_state,grid
from open_development.runtime import digest

def task(inp,out):return {"train":[{"input":inp,"output":out}],"test":[{"input":inp,"output":out}]}
def row(name,t):return {"task_id":name,"task_sha256":digest(t),"stratum":"fixture","task":t}

class ARCDiscriminationTests(unittest.TestCase):
    def stream(self):
        g=[[1,2],[3,4]]; crop_in=[[0,0,0],[0,1,2],[0,3,4]]
        rows=[row("reuse",task(g,[[3,1],[4,2]])),
              row("exaptation",task(crop_in,[[1,2],[3,4]])),
              row("expansion",task([[1,2]],[[1,2,2,1]])),
              row("unknown",task([[1,2]],[[9]]))]
        rows=[{**r,"task_id":f'{r["task_id"]}-{i}'} for i in range(3) for r in rows]
        body={"schema":"arc-route-neutral-stream/v1","selection_nonce":"1:1","tasks":rows,"route_labels_present":False}
        return {**body,"stream_digest":digest(body)}
    def test_all_routes_and_causal_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"state.sqlite";freeze_state(p);s=self.stream();d=develop_stream(s,p);e=evaluate(s,d)
            self.assertEqual([r["predicted_route"] for r in d["results"][:4]],["REUSE","EXAPTATION","EXPANSION","UNKNOWN"])
            self.assertEqual(e["outcome"],"DEVELOPMENTAL_DISCRIMINATION_V1_PASS")
            self.assertEqual(e["accuracy"],1.0)
            for r in d["results"][1:3]:
                self.assertEqual(r["controls"]["exact_removal"],"unknown")
                self.assertEqual(r["controls"]["restoration"],"verified")
                self.assertEqual(r["controls"]["unrelated_removal"],"verified")
                self.assertEqual(r["controls"]["ancestor_removal"],"unknown")
                self.assertEqual(r["controls"]["sham"],"unknown")
                self.assertEqual(r["controls"]["wrong_direction"],"unknown")
            self.assertTrue(all(r["ground_truth"]=="UNKNOWN" or r["held_out_verified"] for r in e["rows"]))
    def test_route_label_leakage_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"state.sqlite";freeze_state(p);s=self.stream();s["predicted_route"]="EXPANSION"
            with self.assertRaisesRegex(ValueError,"leakage"):develop_stream(s,p)

if __name__=="__main__":unittest.main()
