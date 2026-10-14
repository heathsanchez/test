package main

// Post-freeze bridge: infer a native Go bool(string) consumer of a changed,
// previously frozen source regexp; execute the same generated test on original
// base and contributor head. No repository or operation-specific names.
import(
 "encoding/json"
 "flag"
 "fmt"
 "go/ast"
 "go/parser"
 "go/token"
 "os"
 "os/exec"
 "path/filepath"
 "sort"
 "strconv"
 "strings"
 "time"
)
type Witness struct { Input string `json:"input"`;Old bool `json:"old"`; Head bool `json:"head"` }
type Diff struct {
 SourceKey string `json:"source_key"`
 Original string `json:"original_pattern"`
 Head string `json:"head_pattern"`
 First Witness `json:"first_witness"`
}
type Frozen struct {
 OriginalSHA string `json:"original_sha"`
 HeadSHA string `json:"head_sha"`
 SourceChanges []Diff `json:"source_changes"`
}
type Candidate struct {
 Directory string `json:"directory"`
 Package string `json:"package"`
 Function string `json:"function"`
 MatchedSymbol string `json:"matched_symbol"`
}
type Result struct {
 Candidate Candidate `json:"candidate"`
 Input string `json:"input"`
 OriginalExpected bool `json:"original_expected"`
 AuthorExpected bool `json:"author_expected"`
 OldNativeExit int `json:"old_native_exit"`
 HeadNativeExit int `json:"head_native_exit"`
 OldNativeValue string `json:"old_native_value"`
 HeadNativeValue string `json:"head_native_value"`
 OriginalObserved string `json:"original_observation"`
 HeadObserved string `json:"head_observation"`
 Status string `json:"status"`
}
type Report struct {
 Status string `json:"status"`
 BaseSHA string `json:"base_sha"`
 HeadSHA string `json:"head_sha"`
 SourceWitnessDigest string `json:"source_witness_source"`
 PredicateCandidates int `json:"predicate_candidates"`
 Results []Result `json:"native_predicate_results"`
 EvidenceGate string `json:"evidence_gate"`
 Scope []string `json:"scope"`
 ElapsedMs int64 `json:"elapsed_ms"`
}
type Source struct {
 Package string
 File string
 Tree *ast.File
}
func walk(root string)[]Source{
 out:=[]Source{}
 _=filepath.Walk(root,func(path string,fi os.FileInfo,err error)error{
  if err!=nil{return nil}
  if fi.IsDir(){
   if path!=root && (fi.Name()=="vendor"||fi.Name()=="testdata"||fi.Name()==".git"||fi.Name()=="examples"){return filepath.SkipDir}
   return nil
  }
  if !strings.HasSuffix(path,".go")||strings.HasSuffix(path,"_test.go"){return nil}
  parsed,e:=parser.ParseFile(token.NewFileSet(),path,nil,parser.SkipObjectResolution)
  if e!=nil{return nil}
  out=append(out,Source{Package:parsed.Name.Name,File:path,Tree:parsed})
  return nil
 })
 return out
}
func value(e ast.Expr,env map[string]string,depth int)(string,bool){
 if depth>12{return "",false}
 switch x:=e.(type){
 case *ast.BasicLit:
  if x.Kind==token.STRING{s,e:=strconv.Unquote(x.Value);return s,e==nil}
 case *ast.ParenExpr:return value(x.X,env,depth+1)
 case *ast.Ident:r,ok:=env[x.Name];return r,ok
 case *ast.BinaryExpr:
  if x.Op==token.ADD {
   a,ok:=value(x.X,env,depth+1);if !ok{return "",false}
   b,ok:=value(x.Y,env,depth+1);return a+b,ok
  }
 case *ast.CallExpr:
  if len(x.Args)>0{
   s,ok:=x.Fun.(*ast.SelectorExpr)
   if ok {if id,ok:=s.X.(*ast.Ident);ok&&id.Name=="regexp"&&
     (s.Sel.Name=="Compile"||s.Sel.Name=="MustCompile"){
      return value(x.Args[0],env,depth+1)
   }}
  }
 }
 return "",false
}
func semanticConsumers(root,pattern string)[]Candidate{
 src:=walk(root)
 vars:=map[string]map[string]string{}
 for _,f:=range src {
  dir:=filepath.Dir(f.File)
  if vars[dir]==nil{vars[dir]=map[string]string{}}
 }
 for i:=0;i<4;i++{
  for _,f:=range src {
   env:=vars[filepath.Dir(f.File)]
   ast.Inspect(f.Tree,func(n ast.Node)bool{
    v,ok:=n.(*ast.ValueSpec)
    if !ok||len(v.Names)!=len(v.Values){return true}
    for j,id:=range v.Names{
     if s,ok:=value(v.Values[j],env,0);ok{env[id.Name]=s}
    }
    return true
   })
  }
 }
 matching:=map[string]map[string]bool{}
 for dir,env:=range vars{
  for name,s:=range env{
   if s==pattern {
    if matching[dir]==nil {matching[dir]=map[string]bool{}}
    matching[dir][name]=true
   }
  }
 }
 out:=[]Candidate{}
 for _,f:=range src {
  dir:=filepath.Dir(f.File)
  m:=matching[dir]
  if len(m)==0{continue}
  for _,dec:=range f.Tree.Decls{
   fn,ok:=dec.(*ast.FuncDecl)
   if !ok||fn.Recv!=nil||fn.Body==nil||fn.Type.Params==nil||fn.Type.Results==nil{continue}
   if len(fn.Type.Params.List)!=1||len(fn.Type.Params.List[0].Names)!=1||len(fn.Type.Results.List)!=1{continue}
   x,okX:=fn.Type.Params.List[0].Type.(*ast.Ident)
   y,okY:=fn.Type.Results.List[0].Type.(*ast.Ident)
   if !okX||!okY||x.Name!="string"||y.Name!="bool"{continue}
   hit:=""
   ast.Inspect(fn.Body,func(n ast.Node)bool{
    if id,ok:=n.(*ast.Ident);ok&&m[id.Name]{hit=id.Name}
    return true
   })
   if hit==""{continue}
   relative,_:=filepath.Rel(root,dir)
   out=append(out,Candidate{Directory:relative,Package:f.Package,Function:fn.Name.Name,MatchedSymbol:hit})
  }
 }
 sort.Slice(out,func(i,j int)bool{
  a,b:=out[i],out[j]
  if a.Directory!=b.Directory{return a.Directory<b.Directory}
  return a.Function<b.Function
 })
 return out
}
func getSha(root string)string{
 out,err:=exec.Command("git","-C",root,"rev-parse","HEAD").Output()
 if err!=nil{return ""}
 return strings.TrimSpace(string(out))
}
func nativeTest(dir string)(int,string,string){
 cmd:=exec.Command("go","test","-run","^TestMathGraphDerivedPredicate$","-v","-count=1",".")
 cmd.Dir=dir
 cmd.Env=append(os.Environ(),"GOWORK=off")
 bytes,err:=cmd.CombinedOutput()
 code:=0
 if err!=nil{
  if e,ok:=err.(*exec.ExitError);ok{code=e.ExitCode()}else{code=127}
 }
 msg:=string(bytes)
 return code,msg,readMarker(msg)
}
func readMarker(log string)string {
 n:=strings.Index(log,"MATHGRAPH_NATIVE_BOOLEAN=")
 if n<0{return ""}
 s:=log[n+len("MATHGRAPH_NATIVE_BOOLEAN="):]
 if strings.HasPrefix(s,"true"){return "true"}
 if strings.HasPrefix(s,"false"){return "false"}
 return "INVALID_MARKER"
}
func writeGenerated(path string,c Candidate,input string,expected bool)error{
 // No dependency on user-authored tests: this test is created from original
 // AST predicate identity + frozen source-regexp generated input only.
 code:=fmt.Sprintf(`package %s

import "testing"

func TestMathGraphDerivedPredicate(t *testing.T) {
 got := %s(%q)
 t.Logf("MATHGRAPH_NATIVE_BOOLEAN=%%t", got)
 if got != %t { t.Errorf("source-derived behavior: got %%t want %t", got) }
}
`, c.Package,c.Function,input,expected,expected)
 return os.WriteFile(filepath.Join(path,"mathgraph_derived_predicate_test.go"),[]byte(code),0644)
}
func main(){
 orig:=flag.String("old","","old checkout")
 head:=flag.String("head","","contributor checkout")
 manifest:=flag.String("witness","","original immutable source-regexp result")
 result:=flag.String("out","native-bridge.json","output")
 flag.Parse()
 start:=time.Now()
 rep:=Report{Status:"UNKNOWN_NOT_RUN",Results:[]Result{},Scope:[]string{
   "original Go library functions are compiled and run; no upstream repository writes",
   "a single named Go native predicate test is generated, not an original author test",
   "source function selection and test form are human-authored generic Go AST method",
   "retrospective source after public PR title, not blind discovery",
   "unknown open-world requirements, error paths, review value, and autonomous L7",
 }}
 save:=func(){
  rep.ElapsedMs=time.Since(start).Milliseconds()
  b,_:=json.MarshalIndent(rep,"","  ")
  _=os.WriteFile(*result,b,0644)
  fmt.Println("APP_BRIDGE_REPORT",string(b))
 }
 data,err:=os.ReadFile(*manifest)
 if err!=nil{rep.Status="UNKNOWN_NO_FROZEN_SOURCE_WITNESS";save();os.Exit(2)}
 var frozen Frozen
 if e:=json.Unmarshal(data,&frozen);e!=nil{rep.Status="UNKNOWN_BAD_FROZEN_MANIFEST";save();os.Exit(2)}
 rep.BaseSHA=frozen.OriginalSHA;rep.HeadSHA=frozen.HeadSHA
 rep.SourceWitnessDigest=filepath.Base(*manifest)
 if getSha(*orig)!=frozen.OriginalSHA||getSha(*head)!=frozen.HeadSHA {
  rep.Status="UNKNOWN_SOURCE_IDENTITY";save();os.Exit(2)
 }
 discovered:=map[string]bool{}
 for _,ch:=range frozen.SourceChanges{
  if ch.First.Input==""||ch.First.Old==ch.First.Head{continue}
  for _,c:=range semanticConsumers(*orig,ch.Original){
   key:=c.Directory+"::"+c.Function+"::"+ch.First.Input
   if discovered[key]{continue}
   discovered[key]=true
   rep.PredicateCandidates++
   left:=filepath.Join(*orig,c.Directory)
   right:=filepath.Join(*head,c.Directory)
   relTestFile:="mathgraph_derived_predicate_test.go"
   if e:=writeGenerated(left,c,ch.First.Input,ch.First.Head);e!=nil{continue}
   if e:=writeGenerated(right,c,ch.First.Input,ch.First.Head);e!=nil{continue}
   oldCode,oldOut,oldValue:=nativeTest(left)
   newCode,newOut,newValue:=nativeTest(right)
   _=os.Remove(filepath.Join(left,relTestFile))
   _=os.Remove(filepath.Join(right,relTestFile))
   p:=Result{Candidate:c,Input:ch.First.Input,OriginalExpected:ch.First.Old,AuthorExpected:ch.First.Head,
    OldNativeExit:oldCode,HeadNativeExit:newCode,OldNativeValue:oldValue,HeadNativeValue:newValue,
    OriginalObserved:firstLines(oldOut),HeadObserved:firstLines(newOut),Status:"UNKNOWN"}
   if oldCode!=0&&newCode==0&&oldValue==strconv.FormatBool(ch.First.Old)&&
     newValue==strconv.FormatBool(ch.First.Head) {
    p.Status="WARRANTED_BOUNDED_SOURCE_TO_NATIVE_APPLICATION_PREDICATE"
   }else if oldValue!=""&&newValue!="" {
    p.Status="REJECTED_NO_CAUSAL_NATIVE_APPLICATION_DELTA"
   }else{p.Status="UNKNOWN_NATIVE_COMPILE_OR_TEST_SCOPE"}
   rep.Results=append(rep.Results,p)
  }
 }
 for _,p:=range rep.Results{
  if p.Status=="WARRANTED_BOUNDED_SOURCE_TO_NATIVE_APPLICATION_PREDICATE"{
   rep.Status=p.Status;break
  }
 }
 if rep.Status=="UNKNOWN_NOT_RUN"{rep.Status="UNKNOWN_NO_NATIVE_PREDICATE_PROVED"}
 save()
 if rep.Status!="WARRANTED_BOUNDED_SOURCE_TO_NATIVE_APPLICATION_PREDICATE"{os.Exit(3)}
}
func firstLines(s string)string{
 if len(s)>5000{return s[:5000]}
 return s
}
