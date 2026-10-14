// Select native Go test operations from the exact upstream source delta.
// Target test names, package paths and semantic operation keywords are NOT
// supplied by the caller. Original contributor-authored test source is reused.
// This is a HUMAN-CODED generic selector, not autonomous test invention.
package main
import (
 "bytes"
 "crypto/sha256"
 "encoding/hex"
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
 "regexp"
 "sort"
 "strings"
 "unicode"
)
func git(where string, input []byte, args ...string)([]byte,error){
 cmd:=exec.Command("git",append([]string{"-C",where},args...)...)
 if input!=nil {cmd.Stdin=bytes.NewReader(input)}
 out,err:=cmd.CombinedOutput()
 if err!=nil {return nil,fmt.Errorf("GIT_OPERATION_FAILED %s: %w: %s",strings.Join(args," "),err,strings.TrimSpace(string(out)))}
 return out,nil
}
func require(ok bool,why string){if !ok {panic(why)}}
func originalTests(source []byte,file string)(map[string]bool,error){
 if len(source)==0 {return map[string]bool{},nil}
 parsed,e:=parser.ParseFile(token.NewFileSet(),file,source,0)
 if e!=nil{return nil,e}
 found:=map[string]bool{}
 for _,d:=range parsed.Decls{
  f,ok:=d.(*ast.FuncDecl)
  if !ok || f.Recv!=nil || f.Type==nil || f.Type.Params==nil || len(f.Type.Params.List)!=1 {continue}
  name:=f.Name.Name
  if !strings.HasPrefix(name,"Test") || len(name)==4 {continue}
  after:=[]rune(name[4:]);if len(after)==0||unicode.IsLower(after[0]){continue}
  star,ok:=f.Type.Params.List[0].Type.(*ast.StarExpr);if !ok {continue}
  selector,ok:=star.X.(*ast.SelectorExpr);if !ok||selector.Sel.Name!="T"{continue}
  qualifier,ok:=selector.X.(*ast.Ident);if !ok||qualifier.Name!="testing"{continue}
  found[name]=true
 }
 return found,nil
}
func shaBytes(b []byte)string {x:=sha256.Sum256(b);return hex.EncodeToString(x[:])}
type Selection struct {
 File string `json:"file"`
 Package string `json:"package"`
 Function string `json:"function"`
}
type FileOrigin struct {
 File string `json:"file"`
 HeadTestSHA256 string `json:"head_test_sha256"`
}
func main(){
 base:=flag.String("base","","original predecessor Git directory")
 head:=flag.String("head","","original author revision Git directory")
 out:=flag.String("out","","manifest output JSON file")
 sourceRepo:=flag.String("source-repo","","original independent upstream owner/repo")
 wantedBase:=flag.String("base-sha","","frozen expected base source")
 wantedHead:=flag.String("head-sha","","frozen expected author source")
 flag.Parse()
 require(*base!="" && *head!="" && *out!="","MISSING_ARG")
 require(regexp.MustCompile("^[a-f0-9]{40}$").MatchString(*wantedBase) &&
   regexp.MustCompile("^[a-f0-9]{40}$").MatchString(*wantedHead) &&
   regexp.MustCompile("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$").MatchString(*sourceRepo) &&
   *wantedBase!=*wantedHead,"BAD_SOURCE_IDENTITY_PINS")
 rev0,e:=git(*base,nil,"rev-parse","HEAD");require(e==nil&&strings.TrimSpace(string(rev0))==*wantedBase,"BASE_SOURCE_IDENTITY_INVALID")
 rev1,e:=git(*head,nil,"rev-parse","HEAD");require(e==nil&&strings.TrimSpace(string(rev1))==*wantedHead,"HEAD_SOURCE_IDENTITY_INVALID")
 changed,e:=git(*head,nil,"diff","--name-only",*wantedBase,*wantedHead,"--","*_test.go")
 require(e==nil,"SOURCE_DIFF_UNAVAILABLE")
 selected:=[]Selection{}
 files:=[]FileOrigin{}
 for _,name:=range strings.Split(strings.TrimSpace(string(changed)),"\n") {
  if name==""{continue}
  require(strings.HasSuffix(name,"_test.go")&&!strings.HasPrefix(name,"../"),"TEST_SOURCE_PATH_UNSAFE")
  after,e:=git(*head,nil,"show",*wantedHead+":"+name);require(e==nil,"HEAD_TEST_BYTES_MISSING")
  before,e:=git(*head,nil,"show",*wantedBase+":"+name)
  if e!=nil {before=nil}
  newest,e:=originalTests(after,name);require(e==nil,"GO_AST_INVALID_HEAD")
  older,e:=originalTests(before,name);require(e==nil,"GO_AST_INVALID_BASE")
  names:=[]string{}
  for n:=range newest {if !older[n] {names=append(names,n)}}
  sort.Strings(names)
  if len(names)==0 {continue}
  pkg:=filepath.ToSlash(filepath.Dir(name))
  if pkg=="." {pkg="."} else {pkg="./"+pkg}
  for _,n:=range names{selected=append(selected,Selection{File:name,Package:pkg,Function:n})}
  files=append(files,FileOrigin{File:name,HeadTestSHA256:shaBytes(after)})
 }
 sort.Slice(selected,func(i,j int)bool{return selected[i].File+selected[i].Function<selected[j].File+selected[j].Function})
 require(len(selected)>0&&len(selected)<30,"UNKNOWN_NO_NEW_NATIVE_TEST_OPERATION")
 changedFiles:=[]string{}
 for _,f:=range files{changedFiles=append(changedFiles,f.File)}
 patch,e:=git(*head,nil,append([]string{"diff","--binary",*wantedBase,*wantedHead,"--"},changedFiles...)...)
 require(e==nil&&len(patch)>0,"TEST_ONLY_PATCH_UNAVAILABLE")
 _,e=git(*base,patch,"apply","--check","-");require(e==nil,"TEST_ONLY_PATCH_CANNOT_APPLY")
 _,e=git(*base,patch,"apply","-");require(e==nil,"TEST_ONLY_PATCH_FAILED")
 for _,f:=range files{
  applied,e:=os.ReadFile(filepath.Join(*base,f.File))
  require(e==nil&&shaBytes(applied)==f.HeadTestSHA256,"APPLIED_TEST_SOURCE_NOT_IDENTICAL_TO_AUTHOR_HEAD")
 }
 differences,e:=git(*base,nil,"diff","--name-only");require(e==nil,"PATCH_SCOPE_UNOBSERVED")
 allowed:=map[string]bool{}
 for _,f:=range files{allowed[f.File]=true}
 for _,f:=range strings.Split(strings.TrimSpace(string(differences)),"\n") {
  if f!=""&&!allowed[f]{panic("NON_TEST_IMPLEMENTATION_MODIFIED")}
 }
 result:=map[string]any{
  "schema":"metalogic.original-go-source-test-operation-extraction.v1",
  "repo":*sourceRepo,"base_sha":*wantedBase,"head_sha":*wantedHead,
  "source_test_operation_selection":"GO_AST_NEW_AUTHOR_TEST_FUNCTIONS",
  "test_source_authorship":"ORIGINAL_UPSTREAM_CONTRIBUTOR",
  "selector_implementation_authorship":"HUMAN_WRITTEN_GENERIC_GO_AST",
  "selected":selected,"files":files,"patch_sha256":shaBytes(patch),
  "source_test_patch_only":true,"action_authorization":"NONE",
  "new_test_generation":"NO_ORIGINAL_AUTHOR_SUPPLIED_TESTS",
 }
 bytes,e:=json.MarshalIndent(result,"","  ");require(e==nil,"SERIALIZE_FAILED")
 require(os.MkdirAll(filepath.Dir(*out),0755)==nil,"OUTPUT_DIR_ERROR")
 require(os.WriteFile(*out,append(bytes,'\n'),0644)==nil,"OUTPUT_FILE_ERROR")
 fmt.Printf("SOURCE_TEST_OPERATION_GENESIS %s\n",string(bytes))
}
var _=errors.Is
var _=regexp.MustCompile
