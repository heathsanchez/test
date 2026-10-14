// Human-authored generic Go AST singleton test-input constructor.
// Derives the selected function and original author literal table from a
// SHA-pinned test selection manifest. Never modifies original implementation.
// This constructs NEW INPUTS, not new testing assertions or a new prover.
package main

import (
 "crypto/sha256"
 "encoding/hex"
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
)

type Selection struct { File string `json:"file"`; Package string `json:"package"`; Function string `json:"function"` }
type Manifest struct {
 Schema string `json:"schema"`
 Base string `json:"base_sha"`
 Head string `json:"head_sha"`
 Selected []Selection `json:"selected"`
}
type Candidate struct {
 ID int `json:"id"`
 OriginalLiteral string `json:"original_literal"`
 NewLiteral string `json:"new_literal"`
 MutatedTestFile string `json:"mutated_test_file"`
 MutatedTestSHA256 string `json:"mutated_test_sha256"`
}
func ensure(ok bool,why string){if !ok{panic(why)}}
func sha(b []byte)string{x:=sha256.Sum256(b);return hex.EncodeToString(x[:])}
func gitSha(dir string)string{
 b,e:=exec.Command("git","-C",dir,"rev-parse","HEAD").Output()
 ensure(e==nil,"ORIGINAL_GIT_REV_UNAVAILABLE")
 return strings.TrimSpace(string(b))
}
func main(){
 manPath:=flag.String("manifest","","source-selected original author test manifest")
 base:=flag.String("base","","old original source with original test-only patch")
 head:=flag.String("head","","author head exact original source")
 output:=flag.String("out-dir","","isolated generated test inputs")
 limit:=flag.Int("budget",40,"maximum source-derived candidate mutations")
 flag.Parse()
 ensure(*manPath!="" && *base!="" && *head!="" && *output!="","MISSING_CLAIM")
 ensure(*limit>0&&*limit<=40,"CANDIDATE_LIMIT_EXCEEDED")
 var m Manifest
 b,e:=os.ReadFile(*manPath);ensure(e==nil,"SOURCE_SELECTION_MANIFEST_MISSING")
 ensure(json.Unmarshal(b,&m)==nil && m.Schema=="metalogic.original-go-source-test-operation-extraction.v1","MANIFEST_SCHEMA_UNKNOWN")
 ensure(gitSha(*base)==m.Base && gitSha(*head)==m.Head,"ORIGINAL_SOURCE_SHA_NOT_VERIFIED")
 ensure(len(m.Selected)==1,"UNKNOWN_MULTIPLE_SELECTED_TEST_OPS")
 s:=m.Selected[0]
 ensure(strings.HasSuffix(s.File,"_test.go")&&filepath.Clean(s.File)==s.File &&
   !strings.HasPrefix(s.File,".."),"UNSAFE_ORIGIN_TEST_PATH")
 filename:=filepath.Join(*head,s.File)
 original,e:=os.ReadFile(filename);ensure(e==nil,"ORIGINAL_TEST_SOURCE_UNAVAILABLE")
 baseFile,e:=os.ReadFile(filepath.Join(*base,s.File))
 ensure(e==nil&&sha(original)==sha(baseFile),"ORIGINAL_AUTHOR_TEST_TRANSPLANT_NOT_IDENTICAL")
 fset:=token.NewFileSet()
 astFile,e:=parser.ParseFile(fset,filename,original,0);ensure(e==nil,"ORIGINAL_GO_AST_INVALID")
 var target *ast.FuncDecl
 for _,d:=range astFile.Decls{
  if fn,ok:=d.(*ast.FuncDecl);ok&&fn.Recv==nil&&fn.Name.Name==s.Function{
   ensure(target==nil,"DUPLICATE_TEST_IDENTITY")
   target=fn
  }
 }
 ensure(target!=nil,"SOURCE_SELECTED_TEST_NOT_FOUND")
 slices:=[]*ast.CompositeLit{}
 ast.Inspect(target.Body,func(n ast.Node)bool{
  lit,ok:=n.(*ast.CompositeLit)
  if !ok{return true}
  arr,ok:=lit.Type.(*ast.ArrayType)
  if !ok{return true}
  id,ok:=arr.Elt.(*ast.Ident)
  if ok&&id.Name=="string"{slices=append(slices,lit)}
  return true
 })
 // Deliberately do not guess about multiple candidate input collections.
 ensure(len(slices)==1,"UNKNOWN_UNSUPPORTED_OR_AMBIGUOUS_STRING_INPUT_GRAMMAR")
 table:=slices[0]
 literals:=[]string{}
 for _,x:=range table.Elts{
  lit,ok:=x.(*ast.BasicLit);ensure(ok&&lit.Kind==token.STRING,"NON_LITERAL_INPUT_TABLE_UNKNOWN")
  decoded,e:=strconv.Unquote(lit.Value);ensure(e==nil,"UNDECODABLE_GO_LITERAL")
  literals=append(literals,decoded)
 }
 ensure(len(literals)>0&&len(literals)<=40,"UNBOUNDED_INPUT_TABLE")
 originalSet:=map[string]bool{}
 for _,x:=range literals{originalSet[x]=true}
 a,bpos:=fset.Position(table.Pos()).Offset,fset.Position(table.End()).Offset
 ensure(a>=0&&bpos>a&&bpos<=len(original),"GO_AST_INPUT_POSITION_INVALID")
 ensure(os.MkdirAll(*output,0755)==nil,"OUTPUT_DIR_FAILED")
 candidates:=[]Candidate{}
 seen:=map[string]bool{}
 for _,literal:=range literals{
  for pos:=0;pos<len(literal);pos++{
   c:=literal[pos]
   if c<'0'||c>'9'{continue}
   mutated:=literal[:pos]+string(byte('0'+((c-'0'+1)%10)))+literal[pos+1:]
   if originalSet[mutated]||seen[mutated]{continue}
   seen[mutated]=true
   testBytes:=[]byte(string(original[:a])+"[]string{"+strconv.Quote(mutated)+"}"+string(original[bpos:]))
   id:=len(candidates)
   path:=filepath.Join(*output,fmt.Sprintf("candidate-%03d.go",id))
   ensure(os.WriteFile(path,testBytes,0644)==nil,"MUTATED_TEST_OUTPUT_FAILED")
   candidates=append(candidates,Candidate{ID:id,OriginalLiteral:literal,
     NewLiteral:mutated,MutatedTestFile:path,MutatedTestSHA256:sha(testBytes)})
   if len(candidates)>=*limit {break}
  }
  if len(candidates)>=*limit {break}
 }
 ensure(len(candidates)>0,"UNKNOWN_NO_NEW_LITERAL_CANDIDATES")
 absent:=[]byte(string(original[:a])+"[]string{}"+string(original[bpos:]))
 absentFile:=filepath.Join(*output,"empty-table-ablation.go")
 ensure(os.WriteFile(absentFile,absent,0644)==nil,"EMPTY_TABLE_ABLATION_FAILED")
 report:=map[string]any{
   "schema":"metalogic.original-Go-AST-test-input-proposal.v1",
   "base_sha":m.Base,"head_sha":m.Head,
   "test_file":s.File,"test_function":s.Function,
   "original_author_literals":literals,
   "original_head_test_sha256":sha(original),
   "generator":"HUMAN_WRITTEN_GENERIC_DIGIT_MUTATION_WITH_SINGLETON_ISOLATION",
   "test_assertion_authorship":"ORIGINAL_UPSTREAM_CONTRIBUTOR",
   "new_assertion_source_written":false,
   "candidates":candidates,
   "empty_ablation_file":absentFile,
   "empty_ablation_sha256":sha(absent),
   "action_authorization":"NONE",
 }
 encoded,e:=json.MarshalIndent(report,"","  ");ensure(e==nil,"REPORT_JSON_FAILED")
 ensure(os.WriteFile(filepath.Join(*output,"proposal.json"),append(encoded,byte(10)),0644)==nil,"WRITE_REPORT_FAILED")
 sort.Strings(literals)
 fmt.Println("GENERATED_ORIGINAL_SOURCE_INPUTS",len(candidates),"ORIGINAL_INPUTS",len(literals),
   "TEST_FILE",s.File,"FIRST_NEW_INPUT_SHA256",sha([]byte(candidates[0].NewLiteral)))
}
