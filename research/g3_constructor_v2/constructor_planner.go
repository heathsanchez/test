// V2 experimental AST-based constructor/input inhabitation.
// All inhabitants and generic substitutions are predefined; a generated call
// is only a CANDIDATE until the target source's compiler and runtime accept it.
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
	"strings"
)

type Plan struct {
	Schema string `json:"schema"`
	Status string `json:"status"`
	Constructor string `json:"constructor"`
	Call string `json:"call"`
	RootType string `json:"root_type"`
	HasErrorResult bool `json:"has_error_result"`
	SpeculativeGeneric bool `json:"speculative_generic"`
	Cost int `json:"cost"`
	CandidateCount int `json:"candidate_count"`
	UninhabitableCount int `json:"uninhabitable_count"`
	FailureReason string `json:"failure_reason,omitempty"`
}

type fnDef struct {
	name string
	params []ast.Expr
	results []ast.Expr
	typeParams int
}

func expandFieldExprs(fields *ast.FieldList) []ast.Expr {
	if fields==nil {return nil}
	var out []ast.Expr
	for _,f:=range fields.List {
		n:=len(f.Names)
		if n==0 {n=1}
		for i:=0;i<n;i++ {out=append(out,f.Type)}
	}
	return out
}

func formatExpr(e ast.Expr) string {
	var out bytes.Buffer
	if err:=format.Node(&out,token.NewFileSet(),e);err!=nil{return "?"}
	return out.String()
}

func identRoot(e ast.Expr) string {
	switch t:=e.(type) {
	case *ast.Ident: return t.Name
	case *ast.StarExpr: return identRoot(t.X)
	case *ast.IndexExpr: return identRoot(t.X)
	case *ast.IndexListExpr: return identRoot(t.X)
	default: return ""
	}
}

func isPointer(e ast.Expr) bool {_,ok:=e.(*ast.StarExpr);return ok}

func genericCount(params *ast.FieldList) int {
	if params==nil{return 0}
	n:=0
	for _,p:=range params.List {n+=len(p.Names)}
	return n
}

func genericSuffix(count int) string {
	if count<=0{return ""}
	xs:=make([]string,count)
	for i:=range xs {xs[i]="string"}
	return "["+strings.Join(xs,",")+"]"
}

func generifyStruct(e ast.Expr, structs map[string]bool) (string,bool) {
	base:=identRoot(e)
	if base=="" || !structs[base] {return "",false}
	switch v:=e.(type) {
	case *ast.Ident:
		return "pkg."+base,true
	case *ast.IndexExpr:
		return "pkg."+base+"[string]",true
	case *ast.IndexListExpr:
		return "pkg."+base+genericSuffix(len(v.Indices)),true
	default:
		return "",false
	}
}

// A bounded, acyclic type-directed inhabitant grammar. It does not derive
// validity of a zero-valued configuration; native runtime is the next gate.
func inhabit(e ast.Expr, helpers map[string][]fnDef, structs map[string]bool, depth int) (string,int,bool) {
	if depth>2 {return "",0,false}
	switch t:=e.(type) {
	case *ast.Ident:
		switch t.Name {
		case "string": return `"x"`,1,true
		case "int","int8","int16","int32","int64","uint","uint8","uint16","uint32","uint64","float32","float64": return "1",1,true
		case "bool": return "false",1,true
		case "any": return `"x"`,1,true
		}
		if !structs[t.Name] {return "",0,false}
		if hs:=helpers[t.Name];len(hs)==1 && depth<2 {
			args,score,ok:=inhabitParams(hs[0].params,helpers,structs,depth+1)
			if ok {return "pkg."+hs[0].name+"("+strings.Join(args,", ")+")",score+1,true}
		}
		return "pkg."+t.Name+"{}",2,true
	case *ast.InterfaceType:
		return `"x"`,2,true
	case *ast.SelectorExpr:
		x,ok:=t.X.(*ast.Ident)
		if !ok{return "",0,false}
		if x.Name=="time"&&t.Sel.Name=="Duration" {return "80*time.Millisecond",1,true}
		if x.Name=="context"&&t.Sel.Name=="Context" {return "context.Background()",1,true}
		return "",0,false
	case *ast.ArrayType:
		if t.Len==nil && formatExpr(t.Elt)=="byte" {return `[]byte("x")`,1,true}
	case *ast.StarExpr:
		if typ,ok:=generifyStruct(t.X,structs);ok{return "&"+typ+"{}",2,true}
	case *ast.IndexExpr,*ast.IndexListExpr:
		if typ,ok:=generifyStruct(e,structs);ok{return typ+"{}",2,true}
	}
	return "",0,false
}

func inhabitParams(params []ast.Expr, helpers map[string][]fnDef, structs map[string]bool, depth int) ([]string,int,bool) {
	args:=make([]string,0,len(params));score:=0
	for _,p:=range params {
		expr,cost,ok:=inhabit(p,helpers,structs,depth)
		if !ok{return nil,0,false}
		args=append(args,expr);score+=cost
	}
	return args,score,true
}

func planFromFiles(files []*ast.File) Plan {
	p:=Plan{Schema:"mathgraph.g3.typed-constructor.v2",Status:"UNKNOWN_CONSTRUCTOR_INHABITANT"}
	structs:=map[string]bool{}
	var funcs []fnDef
	for _,file:=range files {
		for _,decl:=range file.Decls {
			switch x:=decl.(type) {
			case *ast.GenDecl:
				for _,s:=range x.Specs {ts,ok:=s.(*ast.TypeSpec);if !ok{continue};if _,ok:=ts.Type.(*ast.StructType);ok&&ts.Name.IsExported(){structs[ts.Name.Name]=true}}
			case *ast.FuncDecl:
				if x.Recv!=nil || !x.Name.IsExported(){continue}
				funcs=append(funcs,fnDef{name:x.Name.Name,params:expandFieldExprs(x.Type.Params),results:expandFieldExprs(x.Type.Results),typeParams:genericCount(x.Type.TypeParams)})
			}
		}
	}
	helpers:=map[string][]fnDef{}
	for _,fn:=range funcs {
		if len(fn.results)==1 && !isPointer(fn.results[0]) {
			if typ:=identRoot(fn.results[0]);structs[typ] {helpers[typ]=append(helpers[typ],fn)}
		}
	}
	type choice struct{fn fnDef; root,call string; errorResult bool; cost int}
	var candidates []choice
	for _,fn:=range funcs {
		if len(fn.results)<1 || len(fn.results)>2 || !isPointer(fn.results[0]) {continue}
		root:=identRoot(fn.results[0])
		if !structs[root] || !ast.IsExported(root) {continue}
		hasError:=len(fn.results)==2
		if hasError && formatExpr(fn.results[1])!="error" {continue}
		p.CandidateCount++
		args,score,ok:=inhabitParams(fn.params,helpers,structs,0)
		if !ok {p.UninhabitableCount++;continue}
		call:="pkg."+fn.name+genericSuffix(fn.typeParams)+"("+strings.Join(args,", ")+")"
		candidates=append(candidates,choice{fn:fn,root:root,call:call,errorResult:hasError,cost:score})
	}
	if len(candidates)==0 {
		p.FailureReason="no pointer-returning exported constructor with inhabited arguments"
		return p
	}
	sort.Slice(candidates,func(i,j int)bool{if candidates[i].cost!=candidates[j].cost{return candidates[i].cost<candidates[j].cost};return candidates[i].fn.name<candidates[j].fn.name})
	if len(candidates)>1 && candidates[0].cost==candidates[1].cost {
		p.Status="UNKNOWN_CONSTRUCTOR_AMBIGUITY"
		p.FailureReason="equal-cost constructor candidates; no selection by lexical name"
		return p
	}
	c:=candidates[0]
	p.Status="CANDIDATE_CONSTRUCTOR"
	p.Constructor=c.fn.name
	p.RootType=c.root
	p.Call=c.call
	p.HasErrorResult=c.errorResult
	p.SpeculativeGeneric=c.fn.typeParams>0
	p.Cost=c.cost
	return p
}

func scan(dir string) (Plan,error) {
	paths,err:=filepath.Glob(filepath.Join(dir,"*.go"));if err!=nil{return Plan{},err}
	var files []*ast.File
	for _,path:=range paths {
		if strings.HasSuffix(path,"_test.go"){continue}
		f,err:=parser.ParseFile(token.NewFileSet(),path,nil,0)
		if err!=nil {return Plan{},fmt.Errorf("parse %s: %w",path,err)}
		files=append(files,f)
	}
	if len(files)==0{return Plan{},fmt.Errorf("no non-test Go files in root %s",dir)}
	return planFromFiles(files),nil
}

func main(){
	source:=flag.String("source",".","Go module source root")
	out:=flag.String("out","","JSON output path; stdout if empty")
	flag.Parse()
	p,err:=scan(*source);if err!=nil{fmt.Fprintln(os.Stderr,err);os.Exit(2)}
	b,err:=json.MarshalIndent(p,"","  ");if err!=nil{panic(err)}
	b=append(b,'\n')
	if *out=="" {_,_=os.Stdout.Write(b)}else if err:=os.WriteFile(*out,b,0644);err!=nil{fmt.Fprintln(os.Stderr,err);os.Exit(2)}
}
