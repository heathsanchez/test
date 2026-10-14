// Construct source-native gopkg.in/check.v1 test method IR from a changed
// original Go global data table and its receiver Test* consumers.
// Human-authored bounded generator grammar; selectors are AST-discovered,
// never configured via PR number, table identifier or test name.
package main

import (
 "crypto/sha256"
 "encoding/hex"
 "encoding/json"
 "fmt"
 "go/ast"
 "go/parser"
 "go/token"
 "os"
 "sort"
 "strings"
)

type TestScope struct {
 Name string `json:"discovered_test_method"`
 Mode string `json:"acquired_operator"`
 Table string `json:"source_table"`
 MethodASTHash string `json:"method_ast_sha256"`
 TestFile string `json:"test_file"`
 NativeCommand []string `json:"native_command"`
}
type Report struct {
 Schema string `json:"schema"`
 Status string `json:"status"`
 ChangedOriginalGlobalTables []string `json:"changed_original_global_tables"`
 NativeRuntime string `json:"native_runtime"`
 MethodScope []TestScope `json:"generated_method_ir"`
 UnmatchedTables []string `json:"unmatched_changed_tables"`
}
type OriginalFile struct {
 bytes []byte
 fset *token.FileSet
 node *ast.File
}
func parse(path string)(OriginalFile,error){
 raw,err:=os.ReadFile(path);if err!=nil{return OriginalFile{},err}
 fs:=token.NewFileSet()
 node,err:=parser.ParseFile(fs,path,raw,parser.AllErrors|parser.ParseComments)
 if err!=nil{return OriginalFile{},err}
 return OriginalFile{bytes:raw,fset:fs,node:node},nil
}
func rawDigest(b []byte)string{h:=sha256.Sum256(b);return hex.EncodeToString(h[:])}
func sourceText(f OriginalFile,n ast.Node)string{
 i:=f.fset.Position(n.Pos()).Offset
 j:=f.fset.Position(n.End()).Offset
 if i<0||j>len(f.bytes)||i>=j{return ""}
 return string(f.bytes[i:j])
}
func globals(f OriginalFile)map[string]string{
 result:=map[string]string{}
 for _,decl:=range f.node.Decls{
  g,ok:=decl.(*ast.GenDecl);if !ok||g.Tok!=token.VAR{continue}
  for _,spec:=range g.Specs{
   v,ok:=spec.(*ast.ValueSpec);if !ok{continue}
   // Original data table is preserved as a typed Go AST ValueSpec;
   // a changed initializer changes the source-bound value-spec bytes.
   blob:=sourceText(f,v)
   for _,name:=range v.Names{result[name.Name]=rawDigest([]byte(blob))}
  }
 }
 return result
}
func main(){
 if len(os.Args)!=5{
  fmt.Fprintln(os.Stderr,"usage: table_method_gen <base-original-test> <PR-head-test> <relative-file> <original-go.mod>")
  os.Exit(2)
 }
 before,err:=parse(os.Args[1]);if err!=nil{fmt.Fprintln(os.Stderr,err);os.Exit(1)}
 after,err:=parse(os.Args[2]);if err!=nil{fmt.Fprintln(os.Stderr,err);os.Exit(1)}
 gm,err:=os.ReadFile(os.Args[4]);if err!=nil{fmt.Fprintln(os.Stderr,err);os.Exit(1)}
 // Discovery of the native test adapter is source-dependent, not a fixed
 // authority escalation for arbitrary repositories.
 if !strings.Contains(string(gm),"gopkg.in/check.v1"){
  fmt.Fprintln(os.Stderr,"UNKNOWN_UNSUPPORTED_NATIVE_GO_TEST_RUNNER")
  os.Exit(1)
 }
 oldVars,newVars:=globals(before),globals(after)
 changed:=[]string{}
 for k,v:=range newVars{
  if old,ok:=oldVars[k];!ok||old!=v{changed=append(changed,k)}
 }
 sort.Strings(changed)
 methods:=[]TestScope{}
 unmatched:=[]string{}
 for _,table:=range changed{
  count:=0
  for _,decl:=range after.node.Decls{
   fn,ok:=decl.(*ast.FuncDecl)
   if !ok||fn.Recv==nil||fn.Body==nil||!strings.HasPrefix(fn.Name.Name,"Test"){continue}
   found:=false
   ast.Inspect(fn.Body,func(n ast.Node)bool{
    if id,ok:=n.(*ast.Ident);ok&&id.Name==table{found=true}
    return true
   })
   if !found{continue}
   count++
   method:=fn.Name.Name
   methods=append(methods,TestScope{
     Name:method,Mode:"ACQUIRE_GO_GLOBAL_TABLE_TO_RECEIVER_TEST",
     Table:table,TestFile:os.Args[3],
     MethodASTHash:rawDigest([]byte(sourceText(after,fn))),
     // gopkg.in/check.v1 processes a source-native -check.f filter.
     // Actual run must independently demonstrate chosen method executed.
     NativeCommand:[]string{"go","test","-count=1","-v","-timeout=120s",".","-args","-check.f",method+"$","-check.v"},
   })
  }
  if count==0{unmatched=append(unmatched,table)}
 }
 // Sort scopes and remove exact test + table duplicates. A single receiver
 // may consume multiple tables: do not create independent evidence units.
 sort.Slice(methods,func(i,j int)bool{
  if methods[i].Name==methods[j].Name{return methods[i].Table<methods[j].Table}
  return methods[i].Name<methods[j].Name
 })
 report:=Report{Schema:"mathgraph.go-ast-test-table-receiver-plan.v1",
  Status:"CANDIDATE_NEEDS_NATIVE_VERIFIER",
  ChangedOriginalGlobalTables:changed,
  NativeRuntime:"gopkg.in/check.v1",
  MethodScope:methods,UnmatchedTables:unmatched}
 if len(methods)==0{report.Status="UNKNOWN_NO_REACHABLE_GO_RECEIVER_TEST"}
 j,_:=json.MarshalIndent(report,"","  ")
 fmt.Println(string(j))
 if len(methods)==0{os.Exit(1)}
}
