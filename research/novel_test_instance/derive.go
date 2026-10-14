// Source-derived NEW native test-instance generation. Generic Go regex-map delta
// + upstream author's boolean test-table grammar, not a target-specific detector.
// All expected outcomes are checked again by compiling/running original Go packages.
// HUMAN-CODED operation: new input/assertion instance, not autonomous L7 invention.
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
 "regexp"
 "sort"
 "strconv"
 "strings"
 "unicode"
)

type Rule struct {Pattern string; File string}
type Discovery struct {
 Key string `json:"key"`
 TestFile string `json:"test_file"`
 TestFunction string `json:"test_function"`
 SourceFile string `json:"source_file"`
 OriginalSeed string `json:"original_seed"`
 NewWitness string `json:"new_witness"`
 InvalidControl string `json:"invalid_control"`
 OldRuleSHA256 string `json:"old_rule_sha256"`
 NewRuleSHA256 string `json:"new_rule_sha256"`
 OriginalTestSHA256 string `json:"original_test_sha256"`
}
func fatal(v bool,why string){if !v {panic(why)}}
func hash(x []byte)string {b:=sha256.Sum256(x);return hex.EncodeToString(b[:])}
func git(root string,args ...string)string{
 a:=append([]string{"-C",root},args...)
 c:=exec.Command("git",a...)
 out,err:=c.CombinedOutput()
 fatal(err==nil,"GIT_READ_FAILED_"+strings.Join(args,"_")+": "+string(out))
 return strings.TrimSpace(string(out))
}
func fileAST(path string)(*token.FileSet,*ast.File,[]byte){
 data,e:=os.ReadFile(path);fatal(e==nil,"GO_SOURCE_NOT_FOUND_"+path)
 fs:=token.NewFileSet()
 node,e:=parser.ParseFile(fs,path,data,0)
 fatal(e==nil,"GO_SOURCE_SYNTAX_NOT_SUPPORTED_"+path)
 return fs,node,data
}
func decodeBasic(x ast.Expr)(string,bool){
 b,ok:=x.(*ast.BasicLit);if !ok||b.Kind!=token.STRING{return "",false}
 s,e:=strconv.Unquote(b.Value);return s,e==nil
}
func rules(root string,changed []string)map[string]Rule {
 all:=map[string]Rule{}
 for _,name:=range changed{
  if !strings.HasSuffix(name,".go")||strings.HasSuffix(name,"_test.go") {continue}
  _,node,_:=fileAST(filepath.Join(root,name))
  ast.Inspect(node,func(n ast.Node)bool{
   c,ok:=n.(*ast.CompositeLit);if !ok{return true}
   for _,v:=range c.Elts {
    pair,ok:=v.(*ast.KeyValueExpr);if !ok{continue}
    key,goodKey:=decodeBasic(pair.Key)
    value,goodValue:=decodeBasic(pair.Value)
    if !goodKey||!goodValue||!strings.HasPrefix(value,"^")||!strings.Contains(value,"$"){continue}
    if _,e:=regexp.Compile(value);e!=nil{continue}
    all[key]=Rule{Pattern:value,File:name}
   }
   return true
  })
 }
 return all
}
func newCandidates(seed string)[]string{
 out:=[]string{}
 chars:=[]rune(seed)
 for i,c:=range chars{
  replacements:=[]rune{}
  if c>='0'&&c<='9'{replacements=[]rune{'0','1','2','3','4','5','6','7','8','9'}}
  if c>='A'&&c<='Z'{replacements=[]rune{'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'}}
  if c>='a'&&c<='z'{replacements=[]rune{'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'}}
  for _,d:=range replacements {
   if d==c{continue}
   candidate:=append([]rune{},chars...);candidate[i]=d
   out=append(out,string(candidate))
  }
 }
 return out
}
type Table struct {Key,NextKey,Function string; ValueLbrace int; Seeds []string}
func inFunction(node *ast.File,pos token.Pos)string{
 for _,d:=range node.Decls {
  f,ok:=d.(*ast.FuncDecl)
  if !ok||f.Recv!=nil||!strings.HasPrefix(f.Name.Name,"Test"){continue}
  if f.Pos()<=pos&&pos<f.End(){
   after:=[]rune(strings.TrimPrefix(f.Name.Name,"Test"))
   if len(after)>0&&!unicode.IsLower(after[0]) {return f.Name.Name}
  }
 }
 return ""
}
func testTable(path,key string)*Table {
 fs,node,_:=fileAST(path)
 var found *Table
 ast.Inspect(node,func(n ast.Node)bool{
  if found!=nil{return false}
  c,ok:=n.(*ast.CompositeLit);if !ok{return true}
  for i,part:=range c.Elts{
   kv,ok:=part.(*ast.KeyValueExpr);if !ok{continue}
   this,isString:=decodeBasic(kv.Key)
   if !isString||this!=key{continue}
   v,ok:=kv.Value.(*ast.CompositeLit);if !ok{continue}
   fun:=inFunction(node,kv.Pos())
   if fun==""{continue}
   if i+1>=len(c.Elts){continue}
   following,ok:=c.Elts[i+1].(*ast.KeyValueExpr);if !ok{continue}
   next,isNext:=decodeBasic(following.Key);if !isNext{continue}
   seeds:=[]string{}
   for _,entry:=range v.Elts{
    caseExpr,ok:=entry.(*ast.CompositeLit)
    if !ok||len(caseExpr.Elts)<2{continue}
    s,isS:=decodeBasic(caseExpr.Elts[0])
    if !isS{continue}
    expected,ok:=caseExpr.Elts[1].(*ast.Ident)
    if !ok||expected.Name!="true"{continue}
    seeds=append(seeds,s)
   }
   if len(seeds)<1{continue}
   found=&Table{Key:key,NextKey:next,Function:fun,
     ValueLbrace:fs.Position(v.Lbrace).Offset,Seeds:seeds}
   return false
  }
  return true
 })
 return found
}
func baseAnchor(root,name,function,nextKey string)int {
 fs,node,bytes:=fileAST(filepath.Join(root,name))
 var offset=-1
 for _,decl:=range node.Decls {
  f,ok:=decl.(*ast.FuncDecl);if !ok||f.Name.Name!=function{continue}
  ast.Inspect(f,func(n ast.Node)bool{
   if offset>=0{return false}
   comp,ok:=n.(*ast.CompositeLit);if !ok{return true}
   for _,elt:=range comp.Elts{
    kv,ok:=elt.(*ast.KeyValueExpr);if !ok{continue}
    key,valid:=decodeBasic(kv.Key)
    if valid&&key==nextKey {
      offset=fs.Position(kv.Pos()).Offset
      return false
    }
   }
   return true
  })
 }
 fatal(offset>0&&offset<len(bytes),"ORIGINAL_BASE_TABLE_ANCHOR_NOT_FOUND")
 for offset>0 && bytes[offset-1]!='
'{offset--}
 return offset
}
func restrictDiff(root,allowed string){
 out:=git(root,"diff","--name-only")
 for _,file:=range strings.Split(out,"
") {
  fatal(file==""||file==allowed,"IMPLEMENTATION_SOURCE_MUTATED_"+file)
 }
}
func main(){
 base:=flag.String("base","","immutable original predecessor worktree")
 head:=flag.String("head","","immutable original author head worktree")
 negative:=flag.String("negative","","independent original author head negative worktree")
 out:=flag.String("out","","output")
 oldPin:=flag.String("old-sha","","frozen source pin")
 newPin:=flag.String("new-sha","","frozen source pin")
 flag.Parse()
 fatal(*base!=""&&*head!=""&&*negative!=""&&*out!=""&&len(*oldPin)==40&&len(*newPin)==40,
   "EXPECTED_EXPLICIT_SOURCE_ARGS")
 fatal(git(*base,"rev-parse","HEAD")==*oldPin&&git(*head,"rev-parse","HEAD")==*newPin&&
       git(*negative,"rev-parse","HEAD")==*newPin,"SOURCE_IDENTITY_CHANGED")
 changed:=strings.Split(git(*head,"diff","--name-only",*oldPin,*newPin)," 
")
 // Git emits one changed path per line.
 changed=strings.Split(strings.Join(changed,""),"
")
 oldRules:=rules(*base,changed);newRules:=rules(*head,changed)
 keys:=[]string{}
 for key,nr:=range newRules {
  old,ok:=oldRules[key]
  if ok&&old.Pattern!=nr.Pattern{keys=append(keys,key)}
 }
 sort.Strings(keys)
 var found *Discovery
 var payloadBase,payloadHead,payloadNegative []byte
 for _,key:=range keys {
  old,new:=oldRules[key],newRules[key]
  oldRx,e:=regexp.Compile(old.Pattern);if e!=nil{continue}
  newRx,e:=regexp.Compile(new.Pattern);if e!=nil{continue}
  for _,testFile:=range changed {
   if !strings.HasSuffix(testFile,"_test.go"){continue}
   hfs,hnode,hbytes:=fileAST(filepath.Join(*head,testFile))
   _=hfs;_=hnode
   t:=testTable(filepath.Join(*head,testFile),key)
   if t==nil{continue}
   bBytes,e:=os.ReadFile(filepath.Join(*base,testFile));if e!=nil{continue}
   nBytes,e:=os.ReadFile(filepath.Join(*negative,testFile));if e!=nil{continue}
   if string(nBytes)!=string(hbytes){continue}
   if strings.Contains(string(bBytes),strconv.Quote(key)+": {"){continue}
   pos:=baseAnchor(*base,testFile,t.Function,t.NextKey)
   for _,seed:=range t.Seeds{
    if !newRx.MatchString(seed)||oldRx.MatchString(seed){continue}
    for _,candidate:=range newCandidates(seed){
     if strings.Contains(string(hbytes),strconv.Quote(candidate))||
        !newRx.MatchString(candidate)||oldRx.MatchString(candidate) {continue}
     invalid:=""
     for i,r:=range []rune(candidate) {
      if r>='A'&&r<='Z'||r>='0'&&r<='9' {
       copyChars:=[]rune(candidate);copyChars[i]='@'
       x:=string(copyChars)
       if !newRx.MatchString(x){invalid=x;break}
      }
     }
     if invalid==""{continue}
     generated:=fmt.Sprintf("			{%s, true}, // MathGraph source-derived, not in upstream author tests
",
       strconv.Quote(candidate))
     bad:=fmt.Sprintf("			{%s, true}, // deliberately false mutant, must reject
",
       strconv.Quote(invalid))
     originalBaseBlock:=fmt.Sprintf("		%s: {
%s		},
",strconv.Quote(key),generated)
     payloadBase=append(append([]byte{},bBytes[:pos]...),append([]byte(originalBaseBlock),bBytes[pos:]...)...)
     hpos:=t.ValueLbrace+1
     payloadHead=append(append([]byte{},hbytes[:hpos]...),append([]byte("
"+generated),hbytes[hpos:]...)...)
     payloadNegative=append(append([]byte{},nBytes[:hpos]...),append([]byte("
"+bad),nBytes[hpos:]...)...)
     found=&Discovery{Key:key,TestFile:testFile,TestFunction:t.Function,SourceFile:new.File,
       OriginalSeed:seed,NewWitness:candidate,InvalidControl:invalid,
       OldRuleSHA256:hash([]byte(old.Pattern)),NewRuleSHA256:hash([]byte(new.Pattern)),
       OriginalTestSHA256:hash(hbytes)}
     break
    }
    if found!=nil{break}
   }
   if found!=nil{break}
  }
  if found!=nil{break}
 }
 fatal(found!=nil,"UNKNOWN_NO_SOURCE_DERIVED_NOVEL_REGEX_WITNESS")
 fatal(os.WriteFile(filepath.Join(*base,found.TestFile),payloadBase,0644)==nil,
   "BASE_TEST_PROBE_CANNOT_WRITE")
 fatal(os.WriteFile(filepath.Join(*head,found.TestFile),payloadHead,0644)==nil,
   "HEAD_TEST_PROBE_CANNOT_WRITE")
 fatal(os.WriteFile(filepath.Join(*negative,found.TestFile),payloadNegative,0644)==nil,
   "NEGATIVE_TEST_PROBE_CANNOT_WRITE")
 restrictDiff(*base,found.TestFile);restrictDiff(*head,found.TestFile);restrictDiff(*negative,found.TestFile)
 result:=map[string]any{
  "schema":"metalogic.source-diff-derived-new-regex-assertion.v1",
  "original_repo":"go-playground/validator",
  "base_sha":*oldPin,"head_sha":*newPin,
  "discovery":found,
  "new_generated_native_assertion":true,
  "oracle_derivation":"HEAD_REGEX_MATCH_AND_BASE_REGEX_NONMATCH",
  "head_correctness_versus_external_spec":"NOT_VERIFIED",
  "test_harness_inherited_from_upstream_author":true,
  "operation_generator_human_written":true,
  "semantic_method_self_invented":false,
  "expected_three_native_arms":["ORIGINAL_BASE_PLUS_NEW_CASE_RED",
                                "ORIGINAL_HEAD_PLUS_NEW_CASE_GREEN",
                                "ORIGINAL_HEAD_PLUS_FALSE_CASE_RED"],
  "action_authorization":"NONE",
 }
 data,e:=json.MarshalIndent(result,"","  ");fatal(e==nil,"REPORT_MARSHAL_FAILURE")
 fatal(os.MkdirAll(filepath.Dir(*out),0755)==nil,"OUTPUT_DIR_CREATION_FAILURE")
 fatal(os.WriteFile(*out,append(data,'
'),0644)==nil,"REPORT_WRITE_FAILURE")
 fmt.Printf("SOURCE_DERIVED_NEW_TEST_ASSERTION %s
",data)
}
