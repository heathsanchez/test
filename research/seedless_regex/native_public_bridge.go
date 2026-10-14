// A narrow human-written Go AST bridge for source-regex -> MatchString ->
// exported NewStringRuleWithError. No target symbol names or test input supplied.
// This is an observed one-library source-native follow-up, not general L7.
package main
import(
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
 "strconv"
 "strings"
 "unicode"
)
func need(ok bool,code string){if !ok{panic(code)}}
func sha(s string)string{b:=sha256.Sum256([]byte(s));return hex.EncodeToString(b[:])}
func getObj(a map[string]any,k string)map[string]any{
 o,ok:=a[k].(map[string]any);need(ok,"MISSING_OBJECT_"+k);return o
}
func getStr(a map[string]any,k string)string{
 s,ok:=a[k].(string);need(ok&&s!="","MISSING_STRING_"+k);return s
}
func git(root string,args ...string)string{
 c:=exec.Command("git",append([]string{"-C",root},args...)...)
 b,e:=c.CombinedOutput();need(e==nil,"GIT_ACCESS_FAILED_"+string(b));return strings.TrimSpace(string(b))
}
func method(c *ast.CallExpr,name string)bool{
 s,ok:=c.Fun.(*ast.SelectorExpr);return ok&&s.Sel.Name==name
}
type Bind struct{
 Package string
 File string
 Matcher string
 Predicate string
 Rule string
}
func locate(root,file,wantedSHA string)Bind{
 astFile,e:=parser.ParseFile(token.NewFileSet(),filepath.Join(root,file),nil,0)
 need(e==nil,"SOURCE_AST_PARSE_FAILED")
 matchers:=[]string{}
 ast.Inspect(astFile,func(n ast.Node)bool{
  v,ok:=n.(*ast.ValueSpec);if !ok{return true}
  for i,expr:=range v.Values{
   c,ok:=expr.(*ast.CallExpr);if !ok||!method(c,"MustCompile")||len(c.Args)!=1{continue}
   lit,ok:=c.Args[0].(*ast.BasicLit);if !ok||lit.Kind!=token.STRING{continue}
   pattern,e:=strconv.Unquote(lit.Value)
   if e!=nil||sha(pattern)!=wantedSHA{continue}
   ix:=i;if ix>=len(v.Names){ix=0}
   matchers=append(matchers,v.Names[ix].Name)
  };return true
 })
 need(len(matchers)==1,"REGEXP_MATCHER_NOT_UNIQUE")
 names:=[]string{}
 for _,decl:=range astFile.Decls{
  f,ok:=decl.(*ast.FuncDecl);if !ok||f.Body==nil{continue}
  use:=false
  ast.Inspect(f.Body,func(n ast.Node)bool{
   c,ok:=n.(*ast.CallExpr);if !ok{return true}
   s,ok:=c.Fun.(*ast.SelectorExpr);if !ok||s.Sel.Name!="MatchString"{return true}
   x,ok:=s.X.(*ast.Ident);if ok&&x.Name==matchers[0]{use=true}
   return true
  })
  if use{names=append(names,f.Name.Name)}
 }
 need(len(names)==1,"REGEXP_MATCHSTRING_PREDICATE_NOT_UNIQUE")
 rules:=[]string{}
 ast.Inspect(astFile,func(n ast.Node)bool{
  v,ok:=n.(*ast.ValueSpec);if !ok{return true}
  for i,expr:=range v.Values{
   c,ok:=expr.(*ast.CallExpr);if !ok||!method(c,"NewStringRuleWithError")||len(c.Args)<1{continue}
   x,ok:=c.Args[0].(*ast.Ident);if !ok||x.Name!=names[0]{continue}
   ix:=i;if ix>=len(v.Names){ix=0}
   rule:=v.Names[ix].Name
   if unicode.IsUpper([]rune(rule)[0]){rules=append(rules,rule)}
  };return true
 })
 need(len(rules)==1,"EXPORTED_NATIVE_VALIDATION_RULE_NOT_FOUND")
 return Bind{Package:astFile.Name.Name,File:file,Matcher:matchers[0],Predicate:names[0],Rule:rules[0]}
}
func main(){
 evidence:=flag.String("evidence","","original source-only manifest")
 base:=flag.String("base","","old Go source")
 head:=flag.String("head","","repaired Go source")
 negative:=flag.String("negative","","inverted-oracle Go source")
 pristine:=flag.String("pristine","","untouched old Go source")
 out:=flag.String("out","","bridge result")
 flag.Parse()
 need(*evidence!=""&&*base!=""&&*head!=""&&*negative!=""&&*pristine!=""&&*out!="","MISSING_BOUNDARY_INPUT")
 b,e:=os.ReadFile(*evidence);need(e==nil,"ORIGINAL_SOURCE_WITNESS_ABSENT")
 var r map[string]any;need(json.Unmarshal(b,&r)==nil,"SOURCE_WITNESS_MALFORMED")
 need(getStr(r,"schema")=="metalogic.seedless-go-regex-source-witness.v1"&&getStr(r,"result")=="WARRANTED_BOUNDED_SOURCE_REGEX_DELTA_WITNESS"&&getStr(r,"positive_example_seed")=="NONE","SOURCE_SEEDLESS_WITNESS_NOT_VERIFIED")
 identity:=getObj(r,"source")
 originalSHA,repairSHA:=getStr(identity,"base_sha"),getStr(identity,"head_sha")
 need(git(*base,"rev-parse","HEAD")==originalSHA&&git(*head,"rev-parse","HEAD")==repairSHA&&git(*negative,"rev-parse","HEAD")==repairSHA&&git(*pristine,"rev-parse","HEAD")==originalSHA,"SOURCE_SHA_MISMATCH")
 changed,ok:=r["changed_implementation_files"].([]any)
 need(ok&&len(changed)==1,"REGEX_SOURCE_FILE_NOT_UNIQUE")
 path,ok:=changed[0].(string);need(ok&&strings.HasSuffix(path,".go")&&!strings.HasSuffix(path,"_test.go"),"REGEX_SOURCE_PATH_NOT_SUPPORTED")
 old:=locate(*base,path,getStr(r,"base_regex_sha256"))
 next:=locate(*head,path,getStr(r,"head_regex_sha256"))
 need(old.Package==next.Package&&old.Matcher==next.Matcher&&old.Predicate==next.Predicate&&old.Rule==next.Rule,"EXPORTED_RULE_GRAPH_CHANGED")
 w,exists:=r["old_only_shortest"].(map[string]any)
 if !exists{w,exists=r["new_only_shortest"].(map[string]any)}
 need(exists,"NO_COMPARISON_WITNESS")
 input:=getStr(w,"input")
 before,ok:=w["base_accept"].(bool);need(ok,"BASE_BOOLEAN_UNKNOWN")
 after,ok:=w["head_accept"].(bool);need(ok&&before!=after,"REPAIRED_BOOLEAN_UNKNOWN")
 q:=strconv.Quote(input)
 nl:=string(rune(10))
 testName:="TestMathGraphSeedlessNativeRuleBinding"
 predicate:="if err := "+next.Rule+".Validate("+q+"); err == nil {t.Errorf("+
  strconv.Quote("native rule wrongly accepted a source-generated value")+")}"
 inverted:="if err := "+next.Rule+".Validate("+q+"); err != nil {t.Errorf("+
  strconv.Quote("inverted oracle wrongly assumes native acceptance")+")}"
 if after {
  predicate="if err := "+next.Rule+".Validate("+q+"); err != nil {t.Errorf("+strconv.Quote("native rule wrongly rejected source-generated value: %v")+", err)}"
  inverted="if err := "+next.Rule+".Validate("+q+"); err == nil {t.Errorf("+strconv.Quote("inverted oracle wrongly assumes native rejection")+")}"
 }
 build:=func(body string)string{
  return "package "+next.Package+nl+"import "+strconv.Quote("testing")+nl+
   "func "+testName+"(t *testing.T) {"+nl+body+nl+"}"+nl
 }
 normal,wrong:=build(predicate),build(inverted)
 target:=filepath.ToSlash(filepath.Join(filepath.Dir(path),"zz_mathgraph_generated_native_test.go"))
 for _,root:=range []string{*base,*head,*negative}{
  filename:=filepath.Join(root,target)
  _,e:=os.Stat(filename);need(os.IsNotExist(e),"EXISTING_TARGET_TEST_WOULD_BE_OVERWRITTEN")
  content:=normal;if root==*negative{content=wrong}
  need(os.WriteFile(filename,[]byte(content),0644)==nil,"GENERATED_TEST_CANNOT_WRITE")
  need(git(root,"status","--porcelain")=="?? "+target,"NON_TEST_SOURCE_MODIFICATION_DETECTED")
 }
 need(git(*pristine,"status","--porcelain")=="","PRISTINE_BASE_WAS_MODIFIED")
 result:=map[string]any{
  "schema":"metalogic.go-source-regexp-to-public-validation-rule.v1",
  "source":identity,"binding":map[string]string{
   "package":next.Package,"file":next.File,"matcher":next.Matcher,
   "predicate":next.Predicate,"rule":next.Rule},
  "test_name":testName,"test_file":target,"source_only_witness":input,
  "expected_repaired_accept":after,
  "positive_test_sha256":sha(normal),"inverted_test_sha256":sha(wrong),
  "bridge":"GO_AST_MATCHSTRING_TO_EXPORTED_NEWSTRINGRULEWITHERROR",
  "human_written_structural_family":true,"fully_general_source_to_execution":false,
  "author_test_example_reused":false,"outside_owner_code_write":false,
  "unrestricted_correctness":"UNKNOWN","action_authorization":"NONE",
 }
 outBytes,e:=json.MarshalIndent(result,"","  ");need(e==nil,"BRIDGE_REPORT_MARSHAL_FAILED")
 need(os.MkdirAll(filepath.Dir(*out),0755)==nil,"REPORT_DIR_CREATE_FAILED")
 need(os.WriteFile(*out,append(outBytes,byte(10)),0644)==nil,"BRIDGE_OUTPUT_FAILED")
 fmt.Println("SOURCE_NATIVE_PUBLIC_RULE_BRIDGE "+string(outBytes))
}
