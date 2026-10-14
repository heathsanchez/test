// Human-authored seedless Go regexp delta witness constructor.
// No upstream author test seed, positive example, regexp name or file path is input.
// Warrant is regex semantics only, never arbitrary native application correctness.
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
 "regexp/syntax"
 "sort"
 "strconv"
 "strings"
 "unicode/utf8"
)
const bound=768
const maxStringLen=80
func need(b bool,m string){if !b{panic(m)}}
func digest(s string)string{h:=sha256.Sum256([]byte(s));return hex.EncodeToString(h[:])}
func git(root string,args ...string)string{
 c:=exec.Command("git",append([]string{"-C",root},args...)...)
 o,e:=c.CombinedOutput()
 need(e==nil,"GIT_READ_FAILED "+strings.Join(args," ")+": "+string(o))
 return strings.TrimSpace(string(o))
}
func prune(a []string)[]string{
 seen:=map[string]bool{};o:=[]string{}
 for _,s:=range a{if len(s)>maxStringLen||!utf8.ValidString(s)||seen[s]{continue};seen[s]=true;o=append(o,s)}
 sort.Slice(o,func(i,j int)bool{if len(o[i])!=len(o[j]){return len(o[i])<len(o[j])};return o[i]<o[j]})
 if len(o)>bound{return o[:bound]};return o
}
func product(a,b []string)[]string{
 o:=[]string{};for _,x:=range a{for _,y:=range b{
  if len(x)+len(y)<=maxStringLen{o=append(o,x+y)}
  if len(o)>bound*bound{break}
 }};return prune(o)
}
func representative(cl []rune)[]string{
 o:=[]string{}
 for i:=0;i+1<len(cl);i+=2{
  lo,hi:=cl[i],cl[i+1];tests:=[]rune{lo,lo+(hi-lo)/2,hi}
  for _,a:=range []rune{'0','1','5','9','A','E','M','Z','a','e','m','z','+','-','_'}{
   if lo<=a&&a<=hi{tests=append(tests,a)}
  }
  for _,x:=range tests{
   if x>=0&&x<=utf8.MaxRune&&!(x>=0xD800&&x<=0xDFFF){o=append(o,string(x))}
  }
 };return prune(o)
}
func examples(r *syntax.Regexp,depth int)[]string{
 need(depth<40,"REGEX_AST_TOO_DEEP")
 switch r.Op {
 case syntax.OpEmptyMatch,syntax.OpBeginLine,syntax.OpEndLine,syntax.OpBeginText,
  syntax.OpEndText,syntax.OpWordBoundary,syntax.OpNoWordBoundary:return []string{""}
 case syntax.OpLiteral:return []string{string(r.Rune)}
 case syntax.OpCharClass:return representative(r.Rune)
 case syntax.OpAnyChar,syntax.OpAnyCharNotNL:return []string{"a","0","-"}
 case syntax.OpCapture:return examples(r.Sub[0],depth+1)
 case syntax.OpQuest,syntax.OpStar:
  a:=[]string{""};if len(r.Sub)>0{a=append(a,examples(r.Sub[0],depth+1)...)}
  return prune(a)
 case syntax.OpPlus:
  if len(r.Sub)==0{return nil};one:=examples(r.Sub[0],depth+1)
  return prune(append(one,product(one,one)...))
 case syntax.OpRepeat:
  if len(r.Sub)==0||r.Min>30{return nil}
  one:=examples(r.Sub[0],depth+1);v:=[]string{}
  ns:=[]int{r.Min}
  if r.Max<0||r.Min<r.Max{ns=append(ns,r.Min+1)}
  if r.Max>=0&&r.Max<=16{ns=append(ns,r.Max)}
  for _,n:=range ns{
   if n>30{continue};a:=[]string{""}
   for k:=0;k<n;k++{a=product(a,one);if len(a)==0{break}}
   v=append(v,a...)
  };return prune(v)
 case syntax.OpAlternate:
  o:=[]string{};for _,s:=range r.Sub{o=append(o,examples(s,depth+1)...)};return prune(o)
 case syntax.OpConcat:
  o:=[]string{""};for _,s:=range r.Sub{o=product(o,examples(s,depth+1))};return prune(o)
 case syntax.OpNoMatch:return nil
 default:return nil
 }
}
func candidates(p string)[]string{
 r,e:=syntax.Parse(p,syntax.Perl);if e!=nil{return nil}
 return examples(r.Simplify(),0)
}
func sourcePatterns(file string)map[string]int{
 b,e:=os.ReadFile(file);if e!=nil{return map[string]int{}}
 f,e:=parser.ParseFile(token.NewFileSet(),file,b,0);need(e==nil,"GO_SOURCE_UNPARSABLE")
 m:=map[string]int{}
 ast.Inspect(f,func(n ast.Node)bool{
  s,ok:=n.(*ast.BasicLit);if !ok||s.Kind!=token.STRING{return true}
  p,e:=strconv.Unquote(s.Value);if e!=nil{return true}
  if !strings.HasPrefix(p,"^")||!strings.HasSuffix(p,"$"){return true}
  if _,e=regexp.Compile(p);e!=nil{return true}
  m[p]++;return true
 });return m
}
type Witness struct{
 Input string `json:"input"`
 BaseAccept bool `json:"base_accept"`
 HeadAccept bool `json:"head_accept"`
}
func main(){
 base:=flag.String("base","","original predecessor git worktree")
 head:=flag.String("head","","original repaired git worktree")
 oldSha:=flag.String("base-sha","","expected original base SHA")
 headSha:=flag.String("head-sha","","expected original head SHA")
 repo:=flag.String("repo","","repository identity")
 out:=flag.String("out","","evidence path")
 ablate:=flag.Bool("ablate",false,"remove reference")
 withdraw:=flag.Bool("withdraw",false,"withdraw evidence")
 identical:=flag.Bool("identical",false,"same predicate on both sides")
 swap:=flag.Bool("swap",false,"invert old/new comparison")
 flag.Parse()
 need(*base!=""&&*head!=""&&*repo!=""&&*out!=""&&len(*oldSha)==40&&len(*headSha)==40,"SOURCE_ARGS_MISSING")
 need(git(*base,"rev-parse","HEAD")==*oldSha,"ORIGINAL_SOURCE_SHA_MISMATCH")
 need(git(*head,"rev-parse","HEAD")==*headSha,"REPAIRED_SOURCE_SHA_MISMATCH")
 changed:=strings.Split(git(*head,"diff","--name-only",*oldSha,*headSha,"--","*.go"),"\n")
 names:=[]string{};for _,f:=range changed{
  if f!=""&&strings.HasSuffix(f,".go")&&!strings.HasSuffix(f,"_test.go"){names=append(names,f)}
 };sort.Strings(names)
 a,b:=map[string]int{},map[string]int{}
 for _,file:=range names{
  for p,c:=range sourcePatterns(filepath.Join(*base,file)){a[p]+=c}
  for p,c:=range sourcePatterns(filepath.Join(*head,file)){b[p]+=c}
 }
 o,n:=[]string{},[]string{}
 for p,c:=range a{for k:=0;k<c-b[p];k++{o=append(o,p)}}
 for p,c:=range b{for k:=0;k<c-a[p];k++{n=append(n,p)}}
 sort.Strings(o);sort.Strings(n)
 result:=map[string]any{
  "schema":"metalogic.seedless-go-regex-source-witness.v1",
  "source":map[string]string{"repository":*repo,"base_sha":*oldSha,"head_sha":*headSha},
  "changed_implementation_files":names,
  "candidate_removed_regex_count":len(o),"candidate_added_regex_count":len(n),
  "regex_generator":"HUMAN_WRITTEN_GO_REGEXP_SYNTAX_REPRESENTATIVE_ENUMERATION",
  "positive_example_seed":"NONE","original_author_test_samples_used":false,
  "source_semantic_authority":"ORIGINAL_GO_REGEX_PREDICATE_ONLY",
  "native_application_bridge":"NOT_ESTABLISHED","action_authorization":"NONE",
  "baseline":"FULLY_INFORMED_CONVENTIONAL_RE2_DIFF_CAN_REPRODUCE",
  "human_reviewer_time_or_economic_gain":"NOT_MEASURED",
  "autonomous_generator_of_generators":"NOT_DEMONSTRATED",
 }
 if len(o)!=1||len(n)!=1{
  result["result"]="UNKNOWN_AMBIGUOUS_OR_MISSING_REGEX_SOURCE_PAIR"
 }else{
  p,q:=o[0],n[0]
  result["base_regex_sha256"]=digest(p);result["head_regex_sha256"]=digest(q)
  aa,e:=regexp.Compile(p);need(e==nil,"ORIGINAL_REGEX_INVALID")
  bb,e:=regexp.Compile(q);need(e==nil,"REPAIRED_REGEX_INVALID")
  if *identical{bb=aa}
  if *swap{aa,bb=bb,aa}
  samples:=prune(append(candidates(p),candidates(q)...))
  ow,nw:=[]Witness{},[]Witness{}
  for _,s:=range samples{
   v,w:=aa.MatchString(s),bb.MatchString(s)
   if v&&!w{ow=append(ow,Witness{s,v,w})}
   if !v&&w{nw=append(nw,Witness{s,v,w})}
  }
  result["generated_input_count"]=len(samples)
  result["old_only_count"]=len(ow);result["new_only_count"]=len(nw)
  if len(ow)>0{result["old_only_shortest"]=ow[0]}
  if len(nw)>0{result["new_only_shortest"]=nw[0]}
  if *withdraw{result["result"]="STALE_EVIDENCE_WITHDRAWN"
  }else if *ablate{result["result"]="UNKNOWN_REFERENCE_REMOVED"
  }else if len(ow)+len(nw)>0{result["result"]="WARRANTED_BOUNDED_SOURCE_REGEX_DELTA_WITNESS"
  }else{result["result"]="UNKNOWN_NO_SOURCE_REGEX_WITNESS_IN_BOUND"}
 }
 data,e:=json.MarshalIndent(result,"","  ");need(e==nil,"OUTPUT_MARSHAL_FAILED")
 need(os.MkdirAll(filepath.Dir(*out),0755)==nil,"OUTPUT_PATH_FAILED")
 need(os.WriteFile(*out,append(data,'\n'),0644)==nil,"OUTPUT_WRITE_FAILED")
 fmt.Println("SEEDLESS_SOURCE_REGEX "+string(data))
}
