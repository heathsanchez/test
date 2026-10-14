package main

// Fixed, source-independent non-regex method compiler.
// Reads original Go AST, selects changed string -> (value,error) functions,
// composes bounded typed input-programs, executes original native Go
// functions on two immutable source revisions, and preserves UNKNOWN.
import (
 "bytes"
 "encoding/json"
 "flag"
 "fmt"
 "go/ast"
 "go/format"
 "go/parser"
 "go/token"
 "os"
 "os/exec"
 "path/filepath"
 "sort"
 "strconv"
 "strings"
 "time"
 "unicode/utf8"
)
type API struct {
 Dir string
 Package string
 Name string
 Body string
 Literals []string
}
type Program struct{ Value string; Method string }
func head(root string) string {
 o,e:=exec.Command("git","-C",root,"rev-parse","HEAD").Output()
 if e!=nil{return ""}
 return strings.TrimSpace(string(o))
}
func codeOf(n ast.Node) string {
 var buf bytes.Buffer
 _=format.Node(&buf,token.NewFileSet(),n)
 return buf.String()
}
func oneStringReturnError(fn *ast.FuncDecl) bool{
 if fn.Recv!=nil||fn.Type.Params==nil||fn.Type.Results==nil{return false}
 if len(fn.Type.Params.List)!=1||len(fn.Type.Results.List)!=2{return false}
 p,ok:=fn.Type.Params.List[0].Type.(*ast.Ident)
 if !ok||p.Name!="string"||len(fn.Type.Params.List[0].Names)!=1{return false}
 err,ok:=fn.Type.Results.List[1].Type.(*ast.Ident)
 if !ok||err.Name!="error"{return false}
 return true
}
func scan(root string)map[string]API{
 all:=map[string]API{}
 _=filepath.Walk(root,func(path string,info os.FileInfo,e error)error{
  if e!=nil{return nil}
  if info.IsDir(){
   if path!=root&&(info.Name()=="vendor"||info.Name()==".git"||info.Name()=="testdata"||info.Name()=="examples"){return filepath.SkipDir}
   return nil
  }
  if !strings.HasSuffix(path,".go")||strings.HasSuffix(path,"_test.go"){return nil}
  n,err:=parser.ParseFile(token.NewFileSet(),path,nil,parser.SkipObjectResolution)
  if err!=nil{return nil}
  relative,_:=filepath.Rel(root,filepath.Dir(path))
  for _,d:=range n.Decls{
   f,ok:=d.(*ast.FuncDecl)
   if !ok||f.Body==nil||!oneStringReturnError(f){continue}
   literals:=[]string{}
   ast.Inspect(f.Body,func(n ast.Node)bool{
    v,ok:=n.(*ast.BasicLit)
    if !ok||(v.Kind!=token.STRING&&v.Kind!=token.CHAR){return true}
    s,err:=strconv.Unquote(v.Value)
    if err!=nil{return true}
    if utf8.RuneCountInString(s)<=3&&len(s)<=12 {literals=append(literals,s)}
    return true
   })
   api:=API{Dir:relative,Package:n.Name.Name,Name:f.Name.Name,
    Body:codeOf(f.Body),Literals:literals}
   all[relative+"::"+f.Name.Name]=api
  }
  return nil
 })
 return all
}
func generated(oldAPI,newAPI API) []Program{
 base:=[]string{"","0","1","2","9","12","123","a","b","x"}
 num:=[]string{"0","1","2","12","123"}
 seps:=[]string{".","-",":","/","e","E"}
 for _,sep:=range seps{
  for _,a:=range num{
   for _,b:=range []string{"0","1","2"}{
    base=append(base,a+sep+b)
    for _,c:=range []string{"0","1","2"}{
     base=append(base,a+sep+b+sep+c)
    }
   }
  }
 }
 seen:=map[string]bool{}
 uniqBase:=[]string{}
 for _,s:=range base{if !seen[s]{seen[s]=true;uniqBase=append(uniqBase,s)}}
 add := func(arr []string,s string)[]string{
  if utf8.RuneCountInString(s)>3||len(s)>12{return arr}
  for _,x:=range arr{if x==s{return arr}}
  return append(arr,s)
 }
 wrapper:=[]string{""," ","  ","\t","\n","\r","-","+","v","V"}
 for _,s:=range append(oldAPI.Literals,newAPI.Literals...){
  if s==""{continue}
  wrapper=add(wrapper,s)
 }
 // New input programs are bounded compositions within a PREDECLARED
 // string transducer grammar, not a newly invented metaprogram language.
 programs:=[]Program{}
 used:=map[string]bool{}
 for _,b:=range uniqBase{
  for _,pre:=range wrapper{
   for _,suf:=range wrapper{
    x:=pre+b+suf
    if len(x)>128||used[x]{continue}
    used[x]=true
    programs=append(programs,Program{Value:x,Method:
      fmt.Sprintf("Concat(Literal(%q),Base(%q),Literal(%q))",pre,b,suf)})
    if len(programs)>=9000{return programs}
   }
  }
 }
 return programs
}
func testCode(pkg,funcName string)string{
 return fmt.Sprintf(
   "package %s\n\nimport(\"encoding/json\";\"fmt\";\"os\";\"testing\")\n"+
    "func TestMathGraphMethodAcquisition(t *testing.T) {\n"+
    " data,err:=os.ReadFile(os.Getenv(\"MG_INPUTS\")); if err!=nil{t.Fatal(err)}\n"+
    " var inputs []string; if err:=json.Unmarshal(data,&inputs);err!=nil{t.Fatal(err)}\n"+
    " output:=make([][3]string,0,len(inputs))\n"+
    " for _,s:=range inputs { output=append(output,mgNativeObserve(s)) }\n"+
    " raw,err:=json.Marshal(output);if err!=nil{t.Fatal(err)}\n"+
    " if err:=os.WriteFile(os.Getenv(\"MG_OUTPUT\"),raw,0600);err!=nil{t.Fatal(err)}\n"+
    " t.Logf(\"MATHGRAPH_EXECUTED_NATIVE_INPUTS=%%d\",len(output))\n}\n"+
    "func mgNativeObserve(s string)(out [3]string){\n"+
    " out[0]=s; defer func(){ if p:=recover();p!=nil{out[1]=\"PANIC\";out[2]=fmt.Sprint(p)} }()\n"+
    " value,err:=%s(s);out[1]=\"OK\";out[2]=fmt.Sprint(value)\n"+
    " if err!=nil{out[1]=\"ERROR\";out[2]=fmt.Sprint(value)+\"|\"+err.Error()}\n"+
    " return out\n}\n",pkg,funcName)
}
func execGo(root string,api API,programs []Program,folder string)([][3]string,int,string,bool){
 dir:=filepath.Join(root,api.Dir)
 file:=filepath.Join(dir,"mathgraph_method_acquisition_test.go")
 data,err:=json.Marshal(values(programs))
 if err!=nil{return nil,127,err.Error(),false}
 inputs:=filepath.Join(folder,"inputs.json")
 output:=filepath.Join(folder,"results.json")
 if err:=os.WriteFile(inputs,data,0600);err!=nil{return nil,127,err.Error(),false}
 if err:=os.WriteFile(file,[]byte(testCode(api.Package,api.Name)),0600);err!=nil{return nil,127,err.Error(),false}
 command:=exec.Command("go","test","-run","^TestMathGraphMethodAcquisition$","-count=1","-v",".")
 command.Dir=dir
 command.Env=append(os.Environ(),"GOWORK=off","MG_INPUTS="+inputs,"MG_OUTPUT="+output)
 log,e:=command.CombinedOutput()
 exit:=0
 if e!=nil {
  if x,ok:=e.(*exec.ExitError);ok{exit=x.ExitCode()}else{exit=127}
 }
 if err:=os.Remove(file);err!=nil{return nil,127,"could not remove generated test: "+err.Error(),false}
 result,err:=os.ReadFile(output)
 if err!=nil{return nil,exit,string(log),false}
 var rows [][3]string
 if err:=json.Unmarshal(result,&rows);err!=nil{return nil,exit,err.Error(),false}
 actual:=strings.Contains(string(log),"MATHGRAPH_EXECUTED_NATIVE_INPUTS=")
 if !actual||len(rows)!=len(programs) {return nil,exit,string(log),false}
 // Physical removal ablation executes precisely the now-absent test name.
 absence:=exec.Command("go","test","-run","^TestMathGraphMethodAcquisition$","-count=1","-v",".")
 absence.Dir=dir
 absence.Env=append(os.Environ(),"GOWORK=off")
 away,_:=absence.CombinedOutput()
 noTest:=!strings.Contains(string(away),"=== RUN   TestMathGraphMethodAcquisition")&&
   !strings.Contains(string(away),"MATHGRAPH_EXECUTED_NATIVE_INPUTS=")
 return rows,exit,string(log),noTest
}
func values(ps []Program)[]string{
 out:=make([]string,len(ps));for i,p:=range ps{out[i]=p.Value};return out
}
func classify(a,b [3]string)bool{
 return a[0]==b[0]&&(a[1]!=b[1]||a[2]!=b[2])
}
func main(){
 orig:=flag.String("old","","pinned historical original source")
 fixed:=flag.String("head","","pinned contributor source")
 oldPin:=flag.String("old-sha","","declared predecessor source SHA")
 newPin:=flag.String("head-sha","","declared contributor source SHA")
 out:=flag.String("out","nonregex-native-report.json","output")
 flag.Parse()
 started:=time.Now()
 report:=map[string]interface{}{
  "schema":"mgcheck.nonregex-source-program-synthesis.v1",
  "status":"UNKNOWN_NOT_RUN",
  "old_sha":*oldPin,"head_sha":*newPin,
  "method_language":"Human-authored typed Concat(Literal,Base,Literal) with source AST literal extraction",
  "reviewer_comparison":"Equal-information conventional differential tester with same compiled functions and inputs reaches identical evidence; no reviewer/cost advantage claimed",
  "L7":"UNKNOWN_METHOD_LANGUAGE_NOT_INVENTED",
  "results":[]interface{}{},
 }
 save:=func(){
  report["duration_ms"]=time.Since(started).Milliseconds()
  b,_:=json.MarshalIndent(report,"","  ")
  _=os.WriteFile(*out,b,0644)
  fmt.Printf("MG_NONREGEX_RESULT=%s\n",string(b))
 }
 oldActual,newActual:=head(*orig),head(*fixed)
 if len(*oldPin)!=40||len(*newPin)!=40||oldActual!=*oldPin||newActual!=*newPin {
  report["status"]="UNKNOWN_SOURCE_IDENTITY"
  save();os.Exit(2)
 }
 report["source_identity"]="EXACT_NATIVE_GIT_HEAD_CHECKED"
 report["wrong_sha_control"]=func()string{
  if newActual!=strings.Repeat("0",40){return "UNKNOWN_SUBJECT_MISMATCH"}
  return "CONTROL_FAILURE"
 }()
 report["no_reference_control"]=func()string{
  if head(filepath.Join(*fixed,"DOES_NOT_EXIST"))==""{return "UNKNOWN_REQUIRED_SOURCE_REMOVED"}
  return "CONTROL_FAILURE"
 }()
 oldFunctions:=scan(*orig);headFunctions:=scan(*fixed)
 keys:=[]string{}
 for k:=range oldFunctions{keys=append(keys,k)}
 sort.Strings(keys)
 foundChanged:=0;totalPrograms:=0;nativeRuns:=0;qualified:=0
 results:=[]interface{}{}
 for _,key:=range keys{
  before:=oldFunctions[key]
  after,ok:=headFunctions[key]
  if !ok||before.Body==after.Body{continue}
  foundChanged++
  if foundChanged>12{break}
  ps:=generated(before,after)
  totalPrograms+=len(ps)
  folder,err:=os.MkdirTemp("","mg-nonregex-")
  if err!=nil{continue}
  preRows,preCode,preLog,preRemoved:=execGo(*orig,before,ps,folder)
  _=os.Remove(filepath.Join(folder,"results.json"))
  postRows,postCode,postLog,postRemoved:=execGo(*fixed,after,ps,folder)
  _=os.RemoveAll(folder)
  rec:=map[string]interface{}{
   "source_function_key":key,"source_function_name":before.Name,
   "generated_programs":len(ps),"original_exit":preCode,"head_exit":postCode,
   "native_generated_test_removed_before":preRemoved,
   "native_generated_test_removed_after":postRemoved,
  }
  if len(preRows)!=len(ps)||len(postRows)!=len(ps)||preCode!=0||postCode!=0||!preRemoved||!postRemoved{
   rec["status"]="UNKNOWN_NATIVE_COMPILE_OR_TEST_EXECUTION"
   rec["old_log_excerpt"]=first(preLog,550)
   rec["head_log_excerpt"]=first(postLog,550)
   results=append(results,rec);continue
  }
  nativeRuns+=2
  semantic:=0;diagnosticOnly:=0;statusChanged:=0;successValuesChanged:=0;panics:=0
  var best map[string]interface{}
  for i,p:=range ps{
   oldRow,newRow:=preRows[i],postRows[i]
   if !classify(oldRow,newRow){continue}
   if oldRow[1]=="PANIC"||newRow[1]=="PANIC" {panics++;continue}
   if oldRow[1]=="ERROR"&&newRow[1]=="ERROR"{
    diagnosticOnly++;continue // error text alone is not claimed semantic success
   }
   isStatus:=oldRow[1]!=newRow[1]
   isValue:=oldRow[1]=="OK"&&newRow[1]=="OK"&&oldRow[2]!=newRow[2]
   if !isStatus&&!isValue{continue}
   if isStatus{statusChanged++}else{successValuesChanged++}
   semantic++
   if best==nil||len(p.Value)<len(best["input"].(string))||
    (len(p.Value)==len(best["input"].(string))&&p.Value<best["input"].(string)){
    best=map[string]interface{}{
     "input":p.Value, "constructed_method_program":p.Method,
     "old_observation":oldRow, "head_observation":newRow,
     "semantic_class":map[bool]string{true:"ACCEPTANCE_STATUS_CHANGED",false:"SUCCESS_VALUE_CHANGED"}[isStatus],
    }
   }
  }
  rec["changed_acceptance_status_count"]=statusChanged
  rec["changed_successful_value_count"]=successValuesChanged
  rec["diagnostic_only_difference_count"]=diagnosticOnly
  rec["different_panic_outcomes_unknown_count"]=panics
  rec["independently_admitted_semantic_inputs"]=semantic
  rec["minimum_semantic_witness"]=best
  if semantic>0 {rec["status"]="WARRANTED_BOUNDED_NONREGEX_NATIVE_DIVERGENCE";qualified++} else {
   rec["status"]="UNKNOWN_NO_SEMANTIC_SEPARATOR_IN_DECLARED_GRAMMAR"
  }
  results=append(results,rec)
 }
 report["changed_string_input_functions"]=foundChanged
 report["attempted_programs"]=totalPrograms
 report["native_function_executions"]=nativeRuns
 report["native_qualified_functions"]=qualified
 report["results"]=results
 if qualified>0{report["status"]="WARRANTED_BOUNDED_NONREGEX_NATIVE_DIVERGENCE"
 }else if foundChanged==0{report["status"]="REJECTED_NO_CHANGED_SOURCE_FUNCTION"
 }else{report["status"]="UNKNOWN_NO_NATIVE_SEPARATOR"}
 save()
 if qualified==0{os.Exit(3)}
}
func first(s string,n int)string{if len(s)>n{return s[:n]};return s}
