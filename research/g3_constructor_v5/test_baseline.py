"""Manually written simplest-direct baselines for exposed development fixtures.

Both arms receive the same code, source and witnesses. This is not a blind
baseline nor a claim of reduced cost. Tests should TIE on native behavior.
"""
from pathlib import Path
import subprocess, tempfile, shutil
import unittest
from test_execute import SourceBoundNativeTest, git, HERE

# Independent of planner.go, probe.go and execute.py.
DUAL = r'''package main
import ("fmt"; pkg "example.org/mg-v5/dual")
func main(){
 c,err:=pkg.New[string,string](2);if err!=nil{panic(err)}
 if _,ok:=c.Get("k");ok{panic("initial")}
 c.Add("k","first");if v,ok:=c.Get("k");!ok||v!="first"{panic("readback")}
 c.Add("k","second");if v,ok:=c.Get("k");!ok||v!="second"{panic("overwrite")}
 c.Remove("k");if _,ok:=c.Get("k");ok{panic("delete")}
 fmt.Println("DIRECT_TRACE_PASS")
}
'''
LEGACY = r'''package main
import ("fmt";"time";pkg "github.com/fixture/legacy")
func main(){
 c:=pkg.New(0,0)
 if _,ok:=c.Get("k");ok{panic("initial")}
 c.Set("k","first",time.Duration(-1));if v,ok:=c.Get("k");!ok||v!="first"{panic("readback")}
 c.Set("k","second",time.Duration(-1));if v,ok:=c.Get("k");!ok||v!="second"{panic("overwrite")}
 c.Delete("k");if _,ok:=c.Get("k");ok{panic("delete")}
 fmt.Println("DIRECT_TRACE_PASS")
}
'''

class DirectComparableBaseline(unittest.TestCase):
 def run_direct(self,name,source,legacy=False):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   repo=root/name
   shutil.copytree(HERE/'testdata'/name,repo)
   if legacy: (repo/'go.mod').write_text('module github.com/fixture/legacy\n\ngo 1.23.0\n')
   path=root/'direct.go';path.write_text(source)
   p=subprocess.run(['go','run',str(path)],cwd=repo,capture_output=True,text=True,timeout=60)
   self.assertEqual(p.returncode,0,p.stderr)
   self.assertIn('DIRECT_TRACE_PASS',p.stdout)
 def test_direct_manual_dual_equals_generated_trace(self):
  self.run_direct('dual',DUAL)
 def test_direct_manual_legacy_equals_generated_trace(self):
  self.run_direct('legacy',LEGACY,legacy=True)

if __name__=='__main__': unittest.main()
