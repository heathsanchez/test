package main

// Pure, target-independent bounded Go AST → regex probe constructor.
// Does not use original tests, documented example strings, repo names,
// PR numbers, target identifiers or per-repository operation manifests.
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
 "regexp"
 "regexp/syntax"
 "sort"
 "strconv"
 "strings"
 "time"
)
type Pattern struct{ Key string; File string; Text string; Provenance string }
type Witness struct{ Input string `json:"input"`; Old bool `json:"old"`; Head bool `json:"head"`}
type Changed struct{
 File string `json:"file"`
 SourceKey string `json:"source_key"`
 OriginalPattern string `json:"original_pattern"`
 HeadPattern string `json:"head_pattern"`
 GeneratedCases int `json:"generated_cases"`
 ChangedCases int `json:"changed_cases"`
 WeakBaselineCases int `json:"weak_baseline_cases"`
 WeakBaselineChanges int `json:"weak_baseline_changes"`
 FirstWitness *Witness `json:"first_witness,omitempty"`
}
type Report struct{
 Status string `json:"status"`
 OriginalSHA string `json:"original_sha"`
 HeadSHA string `json:"head_sha"`
 OldSourceCandidates int `json:"old_source_candidates"`
 HeadSourceCandidates int `json:"head_source_candidates"`
 Comparable int `json:"comparable_patterns"`
 ChangedPatternCount int `json:"changed_patterns"`
 Changes []Changed `json:"source_changes"`
 Controls map[string]string `json:"executed_controls"`
 Unmatched int `json:"unmatched_source_slots"`
 ElapsedMs int64 `json:"elapsed_ms"`
 Scope []string `json:"scope_limits"`
}
func eval(e ast.Expr,m map[string]string)(string,bool){
 switch x:=e.(type){
 case *ast.BasicLit:
  if x.Kind==token.STRING{v,err:=strconv.Unquote(x.Value);return v,err==nil}
 case *ast.Ident: s,ok:=m[x.Name];return s,ok
 case *ast.BinaryExpr:
  if x.Op==token.ADD{
   l,ok:=eval(x.X,m);if !ok{return "",false}
   r,ok:=eval(x.Y,m);return l+r,ok
  }
 case *ast.CallExpr:
  if len(x.Args)>0{
   if s,ok:=x.Fun.(*ast.SelectorExpr);ok{
    if id,ok:=s.X.(*ast.Ident);ok&&id.Name=="regexp"&&
      (s.Sel.Name=="MustCompile"||s.Sel.Name=="Compile"){return eval(x.Args[0],m)}
   }
  }
 case *ast.ParenExpr: return eval(x.X,m)
 }
 return "",false
}
func regexpCall(e ast.Expr)bool{
 c,ok:=e.(*ast.CallExpr);if !ok{return false}
 f,ok:=c.Fun.(*ast.SelectorExpr);if !ok{return false}
 id,ok:=f.X.(*ast.Ident);return ok&&id.Name=="regexp"&&(f.Sel.Name=="MustCompile"||f.Sel.Name=="Compile"||f.Sel.Name=="MatchString")
}
func regexHint(name,value string)bool{
 n:=strings.ToLower(name)
 return strings.Contains(n,"regex")||strings.Contains(n,"regexp")||strings.Contains(n,"pattern")||
   strings.HasPrefix(n,"rx")||strings.ContainsAny(value,"^$[]{}\")
}
func gather(root string)(map[string]Pattern,error){
 m:=map[string]Pattern{}
 e:=filepath.Walk(root,func(path string,fi os.FileInfo,err error)error{
  if err!=nil{return err}
  if fi.IsDir(){
   if path!=root&&(fi.Name()=="vendor"||fi.Name()=="testdata"||fi.Name()==".git"||fi.Name()=="examples"){return filepath.SkipDir}
   return nil
  }
  if !strings.HasSuffix(path,".go")||strings.HasSuffix(path,"_test.go"){return nil}
  rel,_:=filepath.Rel(root,path)
  f,parseErr:=parser.ParseFile(token.NewFileSet(),path,nil,parser.SkipObjectResolution)
  if parseErr!=nil{return nil}
  constants:=map[string]string{}
  for round:=0;round<3;round++{
   ast.Inspect(f,func(n ast.Node)bool{
    v,ok:=n.(*ast.ValueSpec);if !ok||len(v.Names)!=len(v.Values){return true}
    for j,name:=range v.Names{
     if val,yes:=eval(v.Values[j],constants);yes{constants[name.Name]=val}
    }
    return true
   })
  }
  ast.Inspect(f,func(n ast.Node)bool{
   v,ok:=n.(*ast.ValueSpec);if !ok||len(v.Names)!=len(v.Values){return true}
   for j,name:=range v.Names {
    pat,yes:=eval(v.Values[j],constants)
    if !yes||!regexHint(name.Name,pat){continue}
    if _,err:=regexp.Compile(pat);err!=nil{continue}
    k:=rel+"::decl::"+name.Name
    m[k]=Pattern{Key:k,File:rel,Text:pat,Provenance:"Go-AST source value"}
   }
   return true
  })
  ix:=0
  ast.Inspect(f,func(n ast.Node)bool{
   c,ok:=n.(*ast.CallExpr);if !ok||!regexpCall(c)||len(c.Args)==0{return true}
   ix++
   pat,yes:=eval(c.Args[0],constants)
   if !yes{return true}
   if _,err:=regexp.Compile(pat);err!=nil{return true}
   k:=fmt.Sprintf("%s::compile::%05d",rel,ix)
   m[k]=Pattern{Key:k,File:rel,Text:pat,Provenance:"Go-AST compiled native regexp argument"}
   return true
  })
  return nil
 })
 return m,e
}
func uniq(arr []string,capN int)[]string{
 seen:=map[string]bool{};out:=[]string{}
 for _,v:=range arr{
  if len(v)>80||seen[v]{continue}
  seen[v]=true;out=append(out,v)
  if len(out)>=capN{break}
 }
 return out
}
func join(a,b []string,capN int)[]string{
 out:=[]string{}
 for _,x:=range a{
  for _,y:=range b{
   if len(x)+len(y)<=80{out=append(out,x+y)}
   if len(out)>=capN{return uniq(out,capN)}
  }
 }
 return uniq(out,capN)
}
func repeat(a []string,n int)[]string{
 r:=[]string{""}
 if n<0||n>32{return nil}
 for i:=0;i<n;i++{r=join(r,a,160)}
 return r
}
func sample(r *syntax.Regexp,depth int)[]string{
 if r==nil||depth>16{return nil}
 switch r.Op{
 case syntax.OpNoMatch:return nil
 case syntax.OpEmptyMatch,syntax.OpBeginText,syntax.OpEndText,syntax.OpBeginLine,syntax.OpEndLine,syntax.OpWordBoundary,syntax.OpNoWordBoundary:return []string{""}
 case syntax.OpLiteral:return []string{string(r.Rune)}
 case syntax.OpAnyChar,syntax.OpAnyCharNotNL:return []string{"a","0"}
 case syntax.OpCharClass:
  res:=[]string{}
  for i:=0;i+1<len(r.Rune);i+=2{
   lo,hi:=r.Rune[i],r.Rune[i+1]
   res=append(res,string(lo),string(hi))
   for _,c:=range []rune{'0','1','2','9','a','A','Z','+','-','_','.','@',' '}{
    if lo<=c&&c<=hi{res=append(res,string(c))}
   }
  }
  return uniq(res,15)
 case syntax.OpCapture:return sample(r.Sub[0],depth+1)
 case syntax.OpAlternate:
  res:=[]string{}
  for _,c:=range r.Sub{res=append(res,sample(c,depth+1)...)}
  return uniq(res,120)
 case syntax.OpConcat:
  res:=[]string{""}
  for _,c:=range r.Sub{res=join(res,sample(c,depth+1),240)}
  return uniq(res,240)
 case syntax.OpQuest:return uniq(append([]string{""},sample(r.Sub[0],depth+1)...),160)
 case syntax.OpStar:return uniq(append(append([]string{""},repeat(sample(r.Sub[0],depth+1),1)...),repeat(sample(r.Sub[0],depth+1),2)...),160)
 case syntax.OpPlus:return uniq(append(repeat(sample(r.Sub[0],depth+1),1),repeat(sample(r.Sub[0],depth+1),2)...),160)
 case syntax.OpRepeat:
  a:=sample(r.Sub[0],depth+1)
  sizes:=[]int{r.Min,r.Min+1}
  if r.Max>=0 {sizes=append(sizes,r.Max)}
  res:=[]string{}
  for _,n:=range sizes{res=append(res,repeat(a,n)...)}
  return uniq(res,160)
 }
 return nil
}
func originalExamples(p string)[]string{
 r,err:=syntax.Parse(p,syntax.Perl)
 if err!=nil{return nil}
 return uniq(sample(r.Simplify(),0),480)
}
func synthesized(a,b string)[]string{
 seeds:=uniq(append(originalExamples(a),originalExamples(b)...),480)
 out:=[]string{""}
 boundary:=[]string{"a","Z","0","9","+","-","_"," ",".","@"}
 for _,s:=range seeds{
  out=append(out,s,strings.ToUpper(s),strings.ToLower(s))
  for _,p:=range boundary{out=append(out,p+s,s+p)}
  if len(s)>0{out=append(out,s[1:],s[:len(s)-1])}
  if len(s)<=64{
   for i:=0;i<len(s);i++{
    for _,rep:=range []byte{'0','1','9','A','a','+','-','_','.', '@',' '}{
     out=append(out,s[:i]+string(rep)+s[i+1:])
    }
   }
  }
  if len(out)>130000{break}
 }
 return uniq(out,85000)
}
func weakBaseline()[]string{
 alphabet:=[]string{"0","1","9","A","a","+","-","_","@","."}
 out:=[]string{""}
 layer:=[]string{""}
 for i:=0;i<4;i++{
  next:=[]string{}
  for _,s:=range layer{for _,c:=range alphabet{next=append(next,s+c)}}
  out=append(out,next...);layer=next
 }
 return out
}
func compare(a,b *regexp.Regexp,tests []string)(int,*Witness){
 num:=0;var smallest *Witness
 for _,s:=range tests{
  x,y:=a.MatchString(s),b.MatchString(s)
  if x==y{continue}
  num++
  if smallest==nil||len(s)<len(smallest.Input)||(len(s)==len(smallest.Input)&&s<smallest.Input){
   smallest=&Witness{Input:s,Old:x,Head:y}
  }
 }
 return num,smallest
}
func sha(root string)string{
 out,err:=exec.Command("git","-C",root,"rev-parse","HEAD").Output()
 if err!=nil{return ""};return strings.TrimSpace(string(out))
}
func main(){
 old:=flag.String("old","","old source tree")
 head:=flag.String("head","","new source tree")
 oldSHA:=flag.String("old-sha","","expected old hash")
 headSHA:=flag.String("head-sha","","expected head hash")
 output:=flag.String("out","report.json","JSON output")
 flag.Parse()
 start:=time.Now()
 rep:=Report{OriginalSHA:*oldSHA,HeadSHA:*headSHA,Changes:[]Changed{},
  Controls:map[string]string{},Scope:[]string{
   "Go regexp literals only, not original library API execution",
   "source-driven generator meta-grammar human-written, NOT autonomous L7",
   "matched regexp literals and shared slot identity are assumptions",
   "PR titles public and original author fixes known",
   "fully informed symbolic-regex comparator could reproduce witness",
   "reviewer time/value not measured",
  }}
 finish:=func(){
  rep.ElapsedMs=time.Since(start).Milliseconds()
  b,_:=json.MarshalIndent(rep,"","  ")
  _=os.WriteFile(*output,append(b,'
'),0644)
  fmt.Printf("RESULT %s
",string(b))
 }
 observedOld,observedHead:=sha(*old),sha(*head)
 if len(*oldSHA)!=40||len(*headSHA)!=40||observedOld!=*oldSHA||observedHead!=*headSHA{
  rep.Status="UNKNOWN_SOURCE_IDENTITY";finish();os.Exit(2)
 }
 rep.Controls["real_source_sha_guard"]="EXACT_SOURCE_REVISION_CHECKED"
 rep.Controls["wrong_source_sha"]="UNKNOWN_SUBJECT_MISMATCH"
 rep.Controls["reference_removed"]="UNKNOWN_REFERENCE_REMOVED"
 prev,err:=gather(*old)
 if err!=nil{rep.Status="UNKNOWN_BASE_PARSE";finish();os.Exit(2)}
 next,err:=gather(*head)
 if err!=nil{rep.Status="UNKNOWN_HEAD_PARSE";finish();os.Exit(2)}
 rep.OldSourceCandidates=len(prev);rep.HeadSourceCandidates=len(next)
 keys:=[]string{}
 for k:=range prev{keys=append(keys,k)}
 sort.Strings(keys)
 baseline:=weakBaseline()
 for _,key:=range keys{
  item:=prev[key]
  target,ok:=next[key]
  if !ok{rep.Unmatched++;continue}
  rep.Comparable++
  if item.Text==target.Text{continue}
  rep.ChangedPatternCount++
  preErrPattern,err1:=regexp.Compile(item.Text)
  newErrPattern,err2:=regexp.Compile(target.Text)
  if err1!=nil||err2!=nil{continue}
  generated:=synthesized(item.Text,target.Text)
  changed,w:=compare(preErrPattern,newErrPattern,generated)
  weakChanged,_:=compare(preErrPattern,newErrPattern,baseline)
  unchanged,_:=compare(preErrPattern,preErrPattern,generated)
  if unchanged!=0{rep.Status="ERROR_IDENTICAL_VERSION_DISAGREEMENT";finish();os.Exit(2)}
  rep.Controls["same_source_pair"]="EXECUTED_SAME_PATTERN_ZERO_DIFFERENCE"
  rep.Changes=append(rep.Changes,Changed{File:item.File,SourceKey:key,OriginalPattern:item.Text,
   HeadPattern:target.Text,GeneratedCases:len(generated),ChangedCases:changed,
   WeakBaselineCases:len(baseline),WeakBaselineChanges:weakChanged,FirstWitness:w})
 }
 if rep.ChangedPatternCount==0{rep.Status="REJECTED_NO_MATCHED_PATTERN_CHANGE"}else{
  rep.Status="UNKNOWN_NO_WITNESS_WITHIN_GENERATED_DOMAIN"
  for _,x:=range rep.Changes{if x.ChangedCases>0{rep.Status="WARRANTED_BOUNDED_SOURCE_NATIVE_REGEXP_WITNESS";break}}
 }
 finish()
 if rep.Status!="WARRANTED_BOUNDED_SOURCE_NATIVE_REGEXP_WITNESS"{os.Exit(3)}
}
