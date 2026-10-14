// Go-native source-diff to test-scope method-IR constructor.
// Source names are DISCOVERED from original native AST, not configured from PR descriptions.
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
  "path/filepath"
  "sort"
  "strings"
)

type Scope struct {
  Name string `json:"name"`
  Mode string `json:"mode"`
  Package string `json:"package"`
  File string `json:"file"`
  BeforeHash string `json:"before_ast_hash,omitempty"`
  AfterHash string `json:"after_ast_hash"`
  NativeCommand []string `json:"native_command"`
}
type Report struct {
  Schema string `json:"schema"`
  Status string `json:"status"`
  OldMethodGrammar string `json:"old_method_grammar"`
  SourceTestFile string `json:"source_test_file"`
  NewMethodLanguage string `json:"new_method_language"`
  Scopes []Scope `json:"scopes"`
}
type TestInfo struct {Hash string; Name string}
func digest(data []byte) string {
  v:=sha256.Sum256(data)
  return hex.EncodeToString(v[:])
}
func tests(path string) (map[string]TestInfo,error) {
  bytes,err:=os.ReadFile(path); if err!=nil{return nil,err}
  fset:=token.NewFileSet()
  node,err:=parser.ParseFile(fset,path,bytes,parser.ParseComments|parser.AllErrors)
  if err!=nil{return nil,err}
  result:=make(map[string]TestInfo)
  for _,d:=range node.Decls {
    fn,ok:=d.(*ast.FuncDecl);if !ok||fn.Recv!=nil||fn.Body==nil{continue}
    name:=fn.Name.Name
    if !strings.HasPrefix(name,"Test")||len(name)<5{continue}
    // AST's own lexical range is the native Go grammar oracle. Every
    // changed test function includes an original author test body.
    start:=fset.Position(fn.Pos()).Offset
    end:=fset.Position(fn.End()).Offset
    if start<0||end>len(bytes)||end<=start{return nil,fmt.Errorf("BAD_GO_AST_RANGE")}
    result[name]=TestInfo{Name:name,Hash:digest(bytes[start:end])}
  }
  return result,nil
}
func main() {
  if len(os.Args)!=4 {
    fmt.Fprintln(os.Stderr,"usage: discover_go_test_scopes <base-original-test.go> <head-test.go> <relative-test-file>")
    os.Exit(2)
  }
  base,err:=tests(os.Args[1]); if err!=nil{fmt.Fprintln(os.Stderr,err);os.Exit(1)}
  head,err:=tests(os.Args[2]);if err!=nil{fmt.Fprintln(os.Stderr,err);os.Exit(1)}
  relative:=filepath.ToSlash(filepath.Clean(os.Args[3]))
  if !strings.HasSuffix(relative,"_test.go")||strings.HasPrefix(relative,"../")||filepath.IsAbs(relative){
    fmt.Fprintln(os.Stderr,"UNSUPPORTED_SOURCE_TEST_PATH");os.Exit(1)
  }
  folder:=filepath.ToSlash(filepath.Dir(relative))
  pkg:="."
  if folder!="."{pkg="./"+folder}
  names:=make([]string,0,len(head))
  for name:=range head{names=append(names,name)}
  sort.Strings(names)
  scopes:=[]Scope{}
  for _,name:=range names {
    info:=head[name];old,exists:=base[name]
    if exists&&old.Hash==info.Hash {continue}
    mode:="ACQUIRE_NEW_GO_TEST"
    if exists {mode="REFINE_EXISTING_GO_TEST_SCOPE"}
    scopes=append(scopes,Scope{Name:name,Mode:mode,Package:pkg,File:relative,
      BeforeHash:old.Hash,AfterHash:info.Hash,
      NativeCommand:[]string{"go","test","-count=1","-run","^"+name+"$",pkg}})
  }
  r:=Report{Schema:"mathgraph.automatically-derived-native-go-scope-ir.v1",
     Status:"CANDIDATE_NEEDS_NATIVE_BEFORE_AFTER",OldMethodGrammar:"UNSUPPORTED_GO_BY_PYTHON_UNITTEST_AST",
     SourceTestFile:relative,NewMethodLanguage:"PREDECLARED_GO_AST_COMBINATORS",Scopes:scopes}
  if len(scopes)==0 {r.Status="UNKNOWN_NO_NATIVE_TEST_SCOPE_DIFFERENCE"}
  o,_:=json.MarshalIndent(r,"","  ");fmt.Println(string(o))
  if len(scopes)==0{os.Exit(1)}
}
