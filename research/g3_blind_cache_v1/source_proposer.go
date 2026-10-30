// Command source_proposer builds a bounded operation grammar from a Go package's
// non-test AST. No repository names, methods, issue titles or patch patterns are
// hard-coded. The ELAPSE rule is a PREDECLARED template, not genuine invention.
package main

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
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

type parsedFile struct{ File *ast.File }

type Proposal struct {
	Schema               string   `json:"schema"`
	Status               string   `json:"status"`
	Package              string   `json:"package"`
	SourceFileCount       int      `json:"source_file_count"`
	ExportedMethodCount  int      `json:"exported_method_count"`
	ClockCallCount       int      `json:"clock_call_count"`
	HasClock             bool     `json:"has_clock"`
	Constructor          string   `json:"constructor,omitempty"`
	WriteMethod          string   `json:"write_method,omitempty"`
	ReadMethod           string   `json:"read_method,omitempty"`
	DeleteMethod         string   `json:"delete_method,omitempty"`
	ReachableReceivers   []string `json:"reachable_receivers"`
	EnvironmentPrimitive string  `json:"environment_primitive,omitempty"`
	EnvironmentalActions []string `json:"environmental_actions"`
	Ambiguities          []string `json:"ambiguities"`
	GenerationBoundary   string   `json:"generation_boundary"`
}

func typeOf(x ast.Expr) string {
	var buf bytes.Buffer
	if err := format.Node(&buf, token.NewFileSet(), x); err != nil { return "?" }
	return buf.String()
}

func fieldTypes(fs *ast.FieldList) []string {
	if fs == nil { return nil }
	var out []string
	for _, f := range fs.List {
		n := len(f.Names)
		if n == 0 { n = 1 }
		for i:=0; i<n; i++ { out=append(out,typeOf(f.Type)) }
	}
	return out
}

func matches(have []string, want ...string) bool {
	if len(have)!=len(want) { return false }
	for i := range have { if have[i]!=want[i] { return false } }
	return true
}

func exactlyOne(xs []string, role string, p *Proposal) string {
	sort.Strings(xs)
	if len(xs)!=1 {
		p.Ambiguities=append(p.Ambiguities,fmt.Sprintf("%s candidates=%v",role,xs))
		return ""
	}
	return xs[0]
}

// We inspect only receiver types reachable from a public constructor's
// returned type via anonymous same-package struct embeddings. Merely finding
// a matching signature elsewhere in the package is not evidence that callers
// can execute that method on the constructed object.
func localType(expr ast.Expr) string {
	switch v:=expr.(type) {
	case *ast.Ident: return v.Name
	case *ast.StarExpr: return localType(v.X)
	default: return ""
	}
}

type candidateMethod struct {
	name string
	receiver string
	params []string
	results []string
}

func proposeFiles(files map[string]*parsedFile) Proposal {
	p:=Proposal{Schema:"mathgraph.g3.source-adaptive-grammar.v1",Status:"UNKNOWN_ADAPTER",SourceFileCount:len(files),
		EnvironmentalActions:[]string{},Ambiguities:[]string{},ReachableReceivers:[]string{},GenerationBoundary:"POST_FAILURE_PUBLIC_CONSTRUCTOR_EMBEDDING_REACHABILITY_PLUS_PREPROGRAMMED_CLOCK_TEMPLATE"}
	var ctor, write, read, del []string
	ctorReturns:=map[string]string{}
	embeddings:=map[string][]string{}
	var methods []candidateMethod
	for _, entry := range files {
		f:=entry.File
		if p.Package=="" { p.Package=f.Name.Name }
		for _,decl:=range f.Decls {
			gen,ok:=decl.(*ast.GenDecl);if !ok {continue}
			for _,spec:=range gen.Specs {
				ts,ok:=spec.(*ast.TypeSpec);if !ok {continue}
				st,ok:=ts.Type.(*ast.StructType);if !ok {continue}
				for _,field:=range st.Fields.List {
					if len(field.Names)==0 {
						if emb:=localType(field.Type);emb!="" {embeddings[ts.Name.Name]=append(embeddings[ts.Name.Name],emb)}
					}
				}
			}
		}
		timeAliases:=map[string]bool{}
		for _, im:=range f.Imports {
			path,err:=strconv.Unquote(im.Path.Value)
			if err!=nil || path!="time" { continue }
			alias:="time"
			if im.Name!=nil { alias=im.Name.Name }
			if alias!="_" && alias!="." { timeAliases[alias]=true }
		}
		ast.Inspect(f,func(n ast.Node)bool{
			call,ok:=n.(*ast.CallExpr);if !ok{return true}
			selector,ok:=call.Fun.(*ast.SelectorExpr);if !ok{return true}
			x,ok:=selector.X.(*ast.Ident)
			if ok && timeAliases[x.Name] && (selector.Sel.Name=="Now"||selector.Sel.Name=="Since"||selector.Sel.Name=="Until") {p.ClockCallCount++}
			return true
		})
		for _,decl:=range f.Decls {
			fn,ok:=decl.(*ast.FuncDecl);if !ok || !fn.Name.IsExported() {continue}
			params:=fieldTypes(fn.Type.Params)
			results:=fieldTypes(fn.Type.Results)
			if fn.Recv==nil {
				if matches(params,"time.Duration","time.Duration") && len(results)==1 && strings.HasPrefix(results[0],"*") {
					ctor=append(ctor,fn.Name.Name)
					ctorReturns[fn.Name.Name]=localType(fn.Type.Results.List[0].Type)
				}
				continue
			}
			p.ExportedMethodCount++
			receiver:=localType(fn.Recv.List[0].Type)
			methods=append(methods,candidateMethod{name:fn.Name.Name,receiver:receiver,params:params,results:results})
		}
	}
	p.Constructor=exactlyOne(ctor,"constructor",&p)
	if p.Constructor!="" {
		reachable:=map[string]bool{}
		var visit func(string)
		visit=func(typ string){
			if typ=="" || reachable[typ] {return}
			reachable[typ]=true
			for _,embedded:=range embeddings[typ] {visit(embedded)}
		}
		visit(ctorReturns[p.Constructor])
		for k:=range reachable {p.ReachableReceivers=append(p.ReachableReceivers,k)}
		sort.Strings(p.ReachableReceivers)
		for _,m:=range methods {
			if !reachable[m.receiver] {continue}
			if matches(m.params,"string","interface{}","time.Duration") && len(m.results)==0 {write=append(write,m.name)}
			if matches(m.params,"string") && matches(m.results,"interface{}","bool") {read=append(read,m.name)}
			if matches(m.params,"string") && len(m.results)==0 {del=append(del,m.name)}
		}
	}
	p.WriteMethod=exactlyOne(write,"write",&p)
	p.ReadMethod=exactlyOne(read,"read",&p)
	// Delete is optional: ambiguity must not admit one, but does not block the
	// three-operation test when constructor, write and read are unambiguous.
	if len(del)==1 {p.DeleteMethod=del[0]} else if len(del)>1 {sort.Strings(del);p.Ambiguities=append(p.Ambiguities,fmt.Sprintf("optional delete candidates=%v",del))}
	p.HasClock=p.ClockCallCount>0
	if p.HasClock {p.EnvironmentalActions=append(p.EnvironmentalActions,"ELAPSE");p.EnvironmentPrimitive="wall_clock_wait"}
	if p.Constructor!=""&&p.WriteMethod!=""&&p.ReadMethod!="" {
		p.Status="CANDIDATE_SIGNATURE_BRIDGE"
	}
	return p
}

func scanDirectory(dir string) (Proposal,error) {
	paths,err:=filepath.Glob(filepath.Join(dir,"*.go"));if err!=nil{return Proposal{},err}
	files:=map[string]*parsedFile{}
	for _,path:=range paths {
		if strings.HasSuffix(path,"_test.go") {continue}
		f,err:=parser.ParseFile(token.NewFileSet(),path,nil,0)
		if err!=nil{return Proposal{},fmt.Errorf("%s: %w",path,err)}
		files[path]=&parsedFile{File:f}
	}
	if len(files)==0 {return Proposal{},fmt.Errorf("no Go source files in %s",dir)}
	return proposeFiles(files),nil
}

func main(){
	dir:=flag.String("source",".","source module root (non-test Go source only)")
	out:=flag.String("out","","JSON output file, stdout when empty")
	flag.Parse()
	p,err:=scanDirectory(*dir);if err!=nil{fmt.Fprintln(os.Stderr,err);os.Exit(2)}
	data,err:=json.MarshalIndent(p,"","  ");if err!=nil{panic(err)}
	data=append(data,'\n')
	if *out=="" {_,_=os.Stdout.Write(data)}else if err:=os.WriteFile(*out,data,0644);err!=nil{fmt.Fprintln(os.Stderr,err);os.Exit(2)}
}
