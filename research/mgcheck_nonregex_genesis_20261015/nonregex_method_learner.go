package main

// MathGraph research-only Go source→observation→method-plan learner.
// All extraction operators and search grammar are fixed prior to seeing the
// three source patches. No project, test, function or domain special cases.
import (
 "context"
 "encoding/json"
 "errors"
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
 "unicode"
 "unicode/utf8"
)

type Fn struct { Dir string; Pkg string; Name string; InputKind string }
type Probe struct { Input string; Op string; Seed string }
type Method struct {
 Operator string
 Observe string
 InterfaceShape string
 AcquiredFrom string
 Function string
 Witness string
 PlanLanguage string
}
type Observation struct { Function string; Index int; OK bool; Panicked bool }
type Execution struct {
 Directory string
 Functions []Fn
 OldCases int
 HeadCases int
 OldRunOK bool
 HeadRunOK bool
 OldDiagnostic string
 HeadDiagnostic string
}
type Candidate struct {
 Function Fn
 Probe Probe
 Before Observation
 After Observation
}
type Result struct {
 Status string
 Stage string
 OldSHA string
 HeadSHA string
 ExpectedOldSHA string
 ExpectedHeadSHA string
 PriorRegexState string
 FunctionCandidates int
 ChangedGoFiles []string
 InputCount int
 PerOperator map[string]int
 SourceRunes []string
 Executions []Execution
 NativeWitness *Candidate
 AcquiredMethod *Method
 RetainedMethod *Method
 WitnessCount int
 BaselineWitnessCount int
 StrongBaseline string
 FocusOld string
 FocusHead string
 FocusOldExit int
 FocusHeadExit int
 WrongOracleExit int
 NoTestAblation string
 RemovedMethodAblation string
 SourceGuard string
 FullBudgetMillis int64
 SearchMillis int64
 ReplayMillis int64
 RunErrors []string
 Qualifications []string
}

func git(root string,args ...string)(string,error) {
 cmd:=exec.Command("git",append([]string{"-C",root},args...)...)
 b,e:=cmd.CombinedOutput()
 if e!=nil {return "",fmt.Errorf("%v: %s",e,string(b))}
 return strings.TrimSpace(string(b)),nil
}
func save(path string,r Result) {
 b,e:=json.MarshalIndent(r,"","  ")
 if e!=nil{panic(e)}
 _=os.WriteFile(path,append(b,10),0644)
 fmt.Printf("MATHGRAPH_METHOD_RESULT=%s\n",string(b))
}
func skipDir(root,path string,info os.FileInfo)bool {
 if !info.IsDir(){return false}
 if path==root{return false}
 n:=info.Name()
 return n==".git"||n=="vendor"||n=="testdata"||n=="examples"||strings.HasPrefix(n,".")
}
func productionFiles(root string)[]string{
 arr:=[]string{}
 _=filepath.Walk(root,func(path string,info os.FileInfo,e error)error{
  if e!=nil {return nil}
  if skipDir(root,path,info){return filepath.SkipDir}
  if info.IsDir(){return nil}
  if strings.HasSuffix(path,".go")&&!strings.HasSuffix(path,"_test.go")&&
   !strings.HasSuffix(path,"_generated.go") {
   rel,_:=filepath.Rel(root,path);arr=append(arr,filepath.ToSlash(rel))
  }
  return nil
 })
 sort.Strings(arr);return arr
}
func inputKind(t ast.Expr)string{
 switch v:=t.(type) {
 case *ast.Ident:
  if v.Name=="string" {return "string"}
  if v.Name=="any" {return "any"}
 case *ast.InterfaceType:
  if v.Methods!=nil&&len(v.Methods.List)==0 {return "interface"}
 }
 return ""
}
func functions(root string,changes map[string]bool)[]Fn {
 result:=[]Fn{}
 seen:=map[string]bool{}
 files:=productionFiles(root)
 for _,rel:=range files {
  if !changes[rel]{continue}
  fnPath:=filepath.Join(root,filepath.FromSlash(rel))
  n,e:=parser.ParseFile(token.NewFileSet(),fnPath,nil,parser.SkipObjectResolution)
  if e!=nil{continue}
  dir,_:=filepath.Split(rel)
  dir=strings.TrimSuffix(filepath.ToSlash(dir),"/")
  if dir==""{dir="."}
  for _,dec:=range n.Decls {
   d,ok:=dec.(*ast.FuncDecl)
   if !ok||d.Recv!=nil||d.Type.TypeParams!=nil||!ast.IsExported(d.Name.Name)||
      d.Type.Params==nil||d.Type.Results==nil {continue}
   if len(d.Type.Params.List)!=1||len(d.Type.Results.List)!=2 {continue}
   a:=d.Type.Params.List[0]
   if len(a.Names)>1 {continue}
   kind:=inputKind(a.Type)
   if kind==""{continue}
   last,ok:=d.Type.Results.List[1].Type.(*ast.Ident)
   if !ok||last.Name!="error"{continue}
   f:=Fn{Dir:dir,Pkg:n.Name.Name,Name:d.Name.Name,InputKind:kind}
   k:=f.Dir+"::"+f.Name
   if !seen[k] {seen[k]=true;result=append(result,f)}
  }
 }
 sort.Slice(result,func(i,j int)bool{
  if result[i].Dir!=result[j].Dir{return result[i].Dir<result[j].Dir}
  return result[i].Name<result[j].Name
 })
 return result
}
func intersects(a,b []Fn)[]Fn{
 have:=map[string]Fn{}
 for _,f:=range b{have[f.Dir+"::"+f.Name+"::"+f.InputKind]=f}
 result:=[]Fn{}
 for _,f:=range a{
  if _,ok:=have[f.Dir+"::"+f.Name+"::"+f.InputKind];ok{result=append(result,f)}
 }
 return result
}
func sourceRunes(root string)[]string{
 seen:=map[rune]bool{}
 for _,rel:=range productionFiles(root){
  n,e:=parser.ParseFile(token.NewFileSet(),filepath.Join(root,filepath.FromSlash(rel)),nil,parser.SkipObjectResolution)
  if e!=nil {continue}
  ast.Inspect(n,func(k ast.Node)bool{
   lit,ok:=k.(*ast.BasicLit)
   if !ok||lit.Kind!=token.CHAR&&lit.Kind!=token.STRING{return true}
   s,e:=strconv.Unquote(lit.Value)
   if e!=nil||len(s)>160{return true}
   for _,ch:=range s{
    if ch>=128&&utf8.ValidRune(ch)&&unicode.IsGraphic(ch) {seen[ch]=true}
   }
   return true
  })
 }
 code:=[]rune{}
 for k:=range seen{code=append(code,k)}
 sort.Slice(code,func(i,j int)bool{return code[i]<code[j]})
 out:=[]string{}
 for _,x:=range code{
  out=append(out,string(x))
  if len(out)>=32{break}
 }
 return out
}
func sourceChangedFiles(old,head string)([]string,error){
 out,e:=git(old,"diff","--name-only",old+"..."+head)
 _=out
 _=e
 return nil,errors.New("unused")
}
func changedPaths(oldTree,oldSha,headSha string)([]string,error){
 txt,e:=git(oldTree,"diff","--name-only",oldSha,headSha,"--","*.go")
 if e!=nil{return nil,e}
 arr:=[]string{}
 for _,line:=range strings.Split(txt,"\n"){
  if line==""||strings.HasSuffix(line,"_test.go"){continue}
  arr=append(arr,filepath.ToSlash(line))
 }
 sort.Strings(arr);return arr,nil
}
func seededInputs(runes []string)([]Probe,map[string]int){
 nums:=[]string{"0","1","2","9","10","42","99","123"}
 seeds:=[]string{"","a","A","true","false","null"}
 for _,x:=range nums{
  seeds=append(seeds,x,"-"+x,"+"+x,x+".0",x+".5",x+"e2")
 }
 for _,a:=range []string{"0","1","2","9","10","42"}{
  for _,b:=range []string{"0","1","2","9"}{
   seeds=append(seeds,a+"."+b,a+"."+b+".0",a+"."+b+".3","-"+a+"."+b)
   for _,c:=range []string{"0","1","2","9"}{seeds=append(seeds,a+"."+b+"."+c)}
  }
 }
 seens:=map[string]bool{}
 seedList:=[]string{}
 for _,s:=range seeds{if len(s)<=48&&!seens[s]{seens[s]=true;seedList=append(seedList,s)}}
 probes:=[]Probe{}
 counts:=map[string]int{}
 add:=func(op,seed,s string){
  if len(s)>96{return}
  key:=op+"\x00"+s
  if seens[key]{return}
  seens[key]=true
  probes=append(probes,Probe{Input:s,Op:op,Seed:seed})
  counts[op]++
 }
 for _,s:=range seedList{add("IDENTITY",s,s)}
 for _,s:=range seedList{
  for _,space:=range []string{" ","\t","\n"}{
   add("EDGE_SPACE",s,space+s)
   add("EDGE_SPACE",s,s+space)
   add("EDGE_SPACE",s,space+s+space)
  }
 }
 for _,s:=range seedList{
  if strings.HasPrefix(s,"-") {
   for _,v:=range runes {
    add("RUNE_SUBSTITUTION",s,v+s[1:])
   }
  }
 }
 for _,s:=range seedList{
  add("CASE_VARIANT",s,strings.ToUpper(s))
  add("CASE_VARIANT",s,strings.ToLower(s))
 }
 for _,a:=range []string{"0","1","2","9","-","+","a","A"}{
  for _,b:=range []string{"0","1","2","9","0.1","a"}{
   add("CONCAT_SMALL",a+"+"+b,a+b)
  }
 }
 return probes,counts
}
func quote(s string)string{return strconv.Quote(s)}
func surveySource(pkg string,funcs []Fn,probes []Probe)string{
 var b strings.Builder
 fmt.Fprintf(&b,"package %s\n\nimport (\n \"testing\"\n \"encoding/json\"\n \"os\"\n)\n",pkg)
 b.WriteString("\ntype mgCase struct { Text string; Op string }\n")
 b.WriteString("type mgRow struct { Function string; Index int; OK bool; Panicked bool }\n")
 b.WriteString("func TestMathGraphSourceSurvey(t *testing.T) {\n")
 b.WriteString(" inputs := []mgCase{\n")
 for _,p:=range probes{fmt.Fprintf(&b,"  {Text:%s,Op:%s},\n",quote(p.Input),quote(p.Op))}
 b.WriteString(" }\n rows := []mgRow{}\n")
 b.WriteString(" for i, x := range inputs {\n")
 for _,f:=range funcs {
  fmt.Fprintf(&b,"  func() { row:=mgRow{Function:%s,Index:i}\n",quote(f.Name))
  b.WriteString("   defer func(){ if recover()!=nil {row.Panicked=true}; rows=append(rows,row) }()\n")
  fmt.Fprintf(&b,"   _,err := %s(x.Text)\n",f.Name)
  b.WriteString("   row.OK=err==nil\n  }()\n")
 }
 b.WriteString(" }\n")
 b.WriteString(" raw,err:=json.Marshal(rows); if err!=nil {t.Fatal(err)}\n")
 b.WriteString(" if err:=os.WriteFile(\"mathgraph_survey_rows.json\",raw,0600);err!=nil {t.Fatal(err)}\n")
 b.WriteString(" t.Logf(\"MG_SURVEY_NATIVE=%d\",len(rows))\n}\n")
 return b.String()
}
func focusSource(pkg,fn,input string,want bool)string{
 return fmt.Sprintf("package %s\n\nimport \"testing\"\n"+
  "func TestMathGraphSourceFocus(t *testing.T) {\n"+
  " _,err:=%s(%s)\n"+
  " got:=err==nil\n t.Logf(\"MG_NATIVE_BOOL=%%t\",got)\n"+
  " if got != %t {t.Errorf(\"frozen native observation: got %%t want %t\",got)}\n}\n",
  pkg,fn,quote(input),want,want)
}
func doGoTest(dir,matcher string,timeout time.Duration)(int,string,time.Duration){
 ctx,cancel:=context.WithTimeout(context.Background(),timeout)
 defer cancel()
 cmd:=exec.CommandContext(ctx,"go","test","-run",matcher,"-count=1","-v",".")
 cmd.Dir=dir
 env:=append(os.Environ(),"GOWORK=off","GOFLAGS=-mod=mod")
 cmd.Env=env
 begin:=time.Now()
 txt,e:=cmd.CombinedOutput()
 duration:=time.Since(begin)
 code:=0
 if e!=nil{
  if ctx.Err()!=nil{code=124}else if x,ok:=e.(*exec.ExitError);ok{code=x.ExitCode()}else{code=127}
 }
 out:=string(txt)
 if len(out)>6000 {out=out[:6000]}
 return code,out,duration
}
func collectNative(tree string,fn []Fn,probes []Probe)(map[string]map[int]Observation,[]Execution){
 grouped:=map[string][]Fn{}
 for _,f:=range fn {grouped[f.Dir]=append(grouped[f.Dir],f)}
 dirs:=[]string{}
 for d:=range grouped{dirs=append(dirs,d)}
 sort.Strings(dirs)
 results:=map[string]map[int]Observation{}
 runs:=[]Execution{}
 for _,dir:=range dirs {
  funcs:=grouped[dir]
  full:=filepath.Join(tree,filepath.FromSlash(dir))
  path:=filepath.Join(full,"mathgraph_generated_survey_test.go")
  if _,e:=os.Stat(path);e==nil {
   runs=append(runs,Execution{Directory:dir,Functions:funcs,OldDiagnostic:"COLLISION_RESERVED_TEST_FILENAME"})
   continue
  }
  _=os.WriteFile(path,[]byte(surveySource(funcs[0].Pkg,funcs,probes)),0600)
  code,log,_:=doGoTest(full,"^TestMathGraphSourceSurvey$",100*time.Second)
  _=os.Remove(path)
  recordPath:=filepath.Join(full,"mathgraph_survey_rows.json")
  by,readErr:=os.ReadFile(recordPath)
  _=os.Remove(recordPath)
  one:=Execution{Directory:dir,Functions:funcs,OldCases:len(funcs)*len(probes),
   OldRunOK:code==0 && readErr==nil,OldDiagnostic:log}
  if !one.OldRunOK{
   if readErr!=nil{one.OldDiagnostic+="|NO_OBSERVATION_FILE:"+readErr.Error()}
   runs=append(runs,one);continue
  }
  rows:=[]Observation{}
  if err:=json.Unmarshal(by,&rows);err!=nil {
   one.OldRunOK=false;one.OldDiagnostic=err.Error();runs=append(runs,one);continue
  }
  one.OldCases=len(rows)
  for _,row:=range rows {
   key:=dir+"::"+row.Function
   if results[key]==nil{results[key]=map[int]Observation{}}
   results[key][row.Index]=row
  }
  runs=append(runs,one)
 }
 return results,runs
}
func unionErrors(runs []Execution,label string)[]string{
 err:=[]string{}
 for _,r:=range runs{if !r.OldRunOK{err=append(err,label+":"+r.Directory+":"+r.OldDiagnostic)}}
 return err
}
func minCandidate(items []Candidate)(*Candidate,int){
 if len(items)==0{return nil,0}
 sort.Slice(items,func(i,j int)bool{
  a,b:=items[i],items[j]
  if a.Probe.Op!=b.Probe.Op{
   order:=map[string]int{"IDENTITY":0,"EDGE_SPACE":1,"RUNE_SUBSTITUTION":2,"CASE_VARIANT":3,"CONCAT_SMALL":4}
   return order[a.Probe.Op]<order[b.Probe.Op]
  }
  if len(a.Probe.Input)!=len(b.Probe.Input){return len(a.Probe.Input)<len(b.Probe.Input)}
  if a.Function.Name!=b.Function.Name{return a.Function.Name<b.Function.Name}
  return a.Probe.Input<b.Probe.Input
 })
 return &items[0],len(items)
}
func verifyFocused(root string,c Candidate,want bool)(int,string,int,string,time.Duration){
 dir:=filepath.Join(root,filepath.FromSlash(c.Function.Dir))
 path:=filepath.Join(dir,"mathgraph_generated_focus_test.go")
 _=os.WriteFile(path,[]byte(focusSource(c.Function.Pkg,c.Function.Name,c.Probe.Input,want)),0600)
 code,log,duration:=doGoTest(dir,"^TestMathGraphSourceFocus$",100*time.Second)
 _=os.Remove(path)
 afterCode,afterLog,_:=doGoTest(dir,"^TestMathGraphSourceFocus$",100*time.Second)
 return code,log,afterCode,afterLog,duration
}
func main(){
 mode:=flag.String("mode","acquire","acquire|transfer|challenge")
 old:=flag.String("old","","old source")
 head:=flag.String("head","","head source")
 oldSHA:=flag.String("old-sha","","SHA")
 headSHA:=flag.String("head-sha","","SHA")
 retained:=flag.String("retained","","retained plan (transfer only)")
 out:=flag.String("out","report.json","report")
 planFile:=flag.String("plan","plan.json","plan file")
 flag.Parse()
 begin:=time.Now()
 r:=Result{Status:"UNKNOWN",Stage:*mode,ExpectedOldSHA:*oldSHA,ExpectedHeadSHA:*headSHA,
  PerOperator:map[string]int{},Executions:[]Execution{},RunErrors:[]string{},
  Qualifications:[]string{"new plan within human-authored finite Go AST + input primitive grammar only",
   "no autonomous generator-language invention or future repair theorem",
   "known original PR title and author fix, not new upstream discovery",
   "strong same-information differential enumerator sees the same original input matrix",
   "no customer trial, reviewer economics or independent intent established"}}
 finish:=func(){
  r.FullBudgetMillis=time.Since(begin).Milliseconds()
  save(*out,r)
 }
 idOld,eOld:=git(*old,"rev-parse","HEAD")
 idHead,eHead:=git(*head,"rev-parse","HEAD")
 if eOld!=nil||eHead!=nil||idOld!=*oldSHA||idHead!=*headSHA{
  r.Status="UNKNOWN_SOURCE_IDENTITY";finish();os.Exit(2)
 }
 r.SourceGuard="EXACT_HEADS_REVERIFIED"
 r.OldSHA=idOld;r.HeadSHA=idHead
 var plan Method
 if *mode=="transfer" {
  bytes,e:=os.ReadFile(*retained)
  if e!=nil {
   r.Status="UNKNOWN_RETAINED_METHOD_REMOVED";r.RemovedMethodAblation=r.Status
   finish();os.Exit(2)
  }
  if e=json.Unmarshal(bytes,&plan);e!=nil||plan.Operator==""{
   r.Status="UNKNOWN_BAD_RETAINED_METHOD";finish();os.Exit(2)
  }
  r.RetainedMethod=&plan
 }
 paths,e:=changedPaths(*old,idOld,idHead)
 if e!=nil{r.Status="UNKNOWN_CHANGED_SOURCE_QUERY";r.RunErrors=append(r.RunErrors,e.Error());finish();os.Exit(2)}
 r.ChangedGoFiles=paths
 changed:=map[string]bool{}
 for _,x:=range paths{changed[x]=true}
 oldFns:=functions(*old,changed)
 headFns:=functions(*head,changed)
 fns:=intersects(oldFns,headFns)
 r.FunctionCandidates=len(fns)
 if len(fns)==0{
  r.Status="UNKNOWN_NO_SHARED_PUBLIC_PARSE_API";finish();os.Exit(3)
 }
 runes:=sourceRunes(*head)
 r.SourceRunes=runes
 probes,counts:=seededInputs(runes)
 if *mode=="transfer" {
  if plan.Operator=="IDENTITY"||plan.Operator=="EDGE_SPACE"||plan.Operator=="RUNE_SUBSTITUTION"||
    plan.Operator=="CASE_VARIANT"||plan.Operator=="CONCAT_SMALL" {
   filtered:=[]Probe{}
   for _,p:=range probes{if p.Op==plan.Operator{filtered=append(filtered,p)}}
   probes=filtered
  }else{
   r.Status="UNKNOWN_RETAINED_OPERATOR_NOT_IN_GRAMMAR";finish();os.Exit(2)
  }
 }
 if len(probes)==0{r.Status="UNKNOWN_EMPTY_PROBE_GRAMMAR";finish();os.Exit(3)}
 r.InputCount=len(probes)
 r.PerOperator=counts
 startSearch:=time.Now()
 before,oldRuns:=collectNative(*old,fns,probes)
 after,headRuns:=collectNative(*head,fns,probes)
 r.SearchMillis=time.Since(startSearch).Milliseconds()
 r.Executions=append(r.Executions,oldRuns...)
 for _,x:=range headRuns{
  x.HeadRunOK=x.OldRunOK;x.HeadCases=x.OldCases;x.HeadDiagnostic=x.OldDiagnostic
  x.OldRunOK=false;x.OldCases=0;x.OldDiagnostic=""
  r.Executions=append(r.Executions,x)
 }
 r.RunErrors=append(r.RunErrors,unionErrors(oldRuns,"old")...)
 r.RunErrors=append(r.RunErrors,unionErrors(headRuns,"head")...)
 possibles:=[]Candidate{}
 for _,f:=range fns {
  key:=f.Dir+"::"+f.Name
  o,b:=before[key],after[key]
  if len(o)==0||len(b)==0{continue}
  for i,p:=range probes{
   aa,aOk:=o[i];zz,zOk:=b[i]
   if !aOk||!zOk||aa.Panicked||zz.Panicked{continue}
   if !aa.OK&&zz.OK{
    possibles=append(possibles,Candidate{Function:f,Probe:p,Before:aa,After:zz})
   }
  }
 }
 selected,total:=minCandidate(possibles)
 r.BaselineWitnessCount=total
 r.StrongBaseline="EQUAL_INFORMATION_TIE: full conventional native differential enumeration over identical funcs and full inputs is the source of all observed witnesses, method selection has not outperformed it"
 if selected==nil{r.Status="UNKNOWN_NO_NATIVE_ERROR_TO_SUCCESS_WITNESS";finish();os.Exit(3)}
 r.NativeWitness=selected
 r.WitnessCount=total
 newMethod:=Method{Operator:selected.Probe.Op,Observe:"GO_LAST_RETURN_ERROR_NIL",
  InterfaceShape:"one_string_or_any_arg_two_returns_last_error",
  AcquiredFrom:idOld+".."+idHead,Function:selected.Function.Name,Witness:selected.Probe.Input,
  PlanLanguage:"human_fixed_primitives_composed_at_runtime"}
 if *mode=="acquire"||*mode=="challenge"{
  r.AcquiredMethod=&newMethod
  planBytes,_:=json.MarshalIndent(newMethod,"","  ")
  _=os.WriteFile(*planFile,planBytes,0600)
 }else {
  // In transfer the unchanged retained operator is the only permitted generator plan.
  if selected.Probe.Op!=plan.Operator{
   r.Status="UNKNOWN_RETAINED_METHOD_TRANSFER_FAILED";finish();os.Exit(3)
  }
 }
 replayStart:=time.Now()
 oldCode,oldLog,noTestCode,noTestLog,_:=verifyFocused(*old,*selected,true)
 headCode,headLog,_,_,_:=verifyFocused(*head,*selected,true)
 // Also check an intentionally false expected outcome at the contributor head.
 flipC:=*selected
 flip:=focusSource(selected.Function.Pkg,selected.Function.Name,selected.Probe.Input,false)
 focusDir:=filepath.Join(*head,filepath.FromSlash(selected.Function.Dir))
 flipPath:=filepath.Join(focusDir,"mathgraph_generated_focus_test.go")
 _=os.WriteFile(flipPath,[]byte(flip),0600)
 flippedCode,_,_:=doGoTest(focusDir,"^TestMathGraphSourceFocus$",100*time.Second)
 _=os.Remove(flipPath)
 _=flipC
 r.ReplayMillis=time.Since(replayStart).Milliseconds()
 r.FocusOldExit=oldCode;r.FocusHeadExit=headCode;r.WrongOracleExit=flippedCode
 r.FocusOld=oldLog;r.FocusHead=headLog
 if noTestCode==0&&!strings.Contains(noTestLog,"=== RUN   TestMathGraphSourceFocus"){
  r.NoTestAblation="EXECUTED_NO_GENERATED_TEST_NO_OBSERVATION"
 }else {r.NoTestAblation="UNKNOWN_ABLATION_DID_NOT_PROVE_REMOVAL"}
 if oldCode!=0&&headCode==0&&flippedCode!=0&&r.NoTestAblation=="EXECUTED_NO_GENERATED_TEST_NO_OBSERVATION"{
  if *mode=="transfer"{r.Status="WARRANTED_BOUNDED_RETAINED_PLAN_TRANSFER"
  }else{r.Status="WARRANTED_BOUNDED_NEW_METHOD_PLAN_ACQUISITION"}
 }else{
  r.Status="UNKNOWN_NATIVE_REPLAY_OR_ABLATION_FAILED"
 }
 finish()
 if !strings.HasPrefix(r.Status,"WARRANTED_BOUNDED"){os.Exit(3)}
}
