// A finite, source-independent constructor inhabitant for Go cache APIs.
// A syntactically valid plan is only a candidate until native execution.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"strings"
)

type Plan struct {
	Schema      string `json:"schema"`
	Status      string `json:"status"`
	Constructor string `json:"constructor,omitempty"`
	Call        string `json:"call,omitempty"`
	Generic     bool   `json:"generic"`
	ReturnsError bool `json:"returns_error"`
	Reason      string `json:"reason,omitempty"`
}

func typeWitnesses(params *ast.FieldList) (string, bool, bool) {
	if params == nil || len(params.List) == 0 {
		return "", false, true
	}
	var names []string
	for _, f := range params.List {
		constraint, ok := f.Type.(*ast.Ident)
		if !ok || (constraint.Name != "any" && constraint.Name != "comparable") {
			return "", false, false
		}
		for range f.Names {
			names = append(names, "string")
		}
	}
	if len(names) == 0 {
		return "", false, false
	}
	return "[" + strings.Join(names, ",") + "]", true, true
}

func argumentWitness(e ast.Expr) (string, bool) {
	switch x := e.(type) {
	case *ast.Ident:
		switch x.Name {
		case "int", "int8", "int16", "int32", "int64",
			"uint", "uint8", "uint16", "uint32", "uint64":
			return "2", true
		case "float32", "float64":
			return "2.0", true
		case "bool":
			return "false", true
		case "string", "any":
			return `"x"`, true
		}
	case *ast.InterfaceType:
		return `"x"`, true
	case *ast.SelectorExpr:
		if root, ok := x.X.(*ast.Ident); ok && root.Name == "time" && x.Sel.Name == "Duration" {
			return "0", true
		}
	}
	return "", false
}

func callArguments(params *ast.FieldList) ([]string, bool) {
	if params == nil {
		return nil, true
	}
	var args []string
	for i, p := range params.List {
		if _, variadic := p.Type.(*ast.Ellipsis); variadic {
			return args, i == len(params.List)-1
		}
		value, ok := argumentWitness(p.Type)
		if !ok {
			return nil, false
		}
		n := len(p.Names)
		if n == 0 {
			n = 1
		}
		for j := 0; j < n; j++ {
			args = append(args, value)
		}
	}
	return args, true
}

func planFromFiles(files []*ast.File) Plan {
	p := Plan{Schema: "mathgraph.g3.typed-operational.v5", Status: "UNKNOWN_NO_NEW"}
	var selected *ast.FuncDecl
	for _, f := range files {
		for _, decl := range f.Decls {
			fn, ok := decl.(*ast.FuncDecl)
			if !ok || fn.Recv != nil || fn.Name.Name != "New" {
				continue
			}
			if selected != nil {
				p.Status = "UNKNOWN_AMBIGUOUS_NEW"
				return p
			}
			selected = fn
		}
	}
	if selected == nil {
		return p
	}
	if selected.Type.Results == nil || (len(selected.Type.Results.List) != 1 && len(selected.Type.Results.List) != 2) {
		p.Status = "UNKNOWN_CONSTRUCTOR_RESULT"
		return p
	}
	if _, ok := selected.Type.Results.List[0].Type.(*ast.StarExpr); !ok {
		p.Status = "UNKNOWN_CONSTRUCTOR_RESULT"
		return p
	}
	if len(selected.Type.Results.List) == 2 {
		t, ok := selected.Type.Results.List[1].Type.(*ast.Ident)
		if !ok || t.Name != "error" {
			p.Status = "UNKNOWN_CONSTRUCTOR_RESULT"
			return p
		}
		p.ReturnsError = true
	}
	suffix, generic, ok := typeWitnesses(selected.Type.TypeParams)
	if !ok {
		p.Status = "UNKNOWN_TYPE_CONSTRAINT"
		return p
	}
	args, ok := callArguments(selected.Type.Params)
	if !ok {
		p.Status = "UNKNOWN_REQUIRED_ARGUMENT"
		return p
	}
	p.Status = "CANDIDATE_CONSTRUCTOR"
	p.Constructor = "New"
	p.Call = "pkg.New" + suffix + "(" + strings.Join(args, ",") + ")"
	p.Generic = generic
	return p
}

func planSource(dir string) (Plan, error) {
	paths, err := filepath.Glob(filepath.Join(dir, "*.go"))
	if err != nil {
		return Plan{}, err
	}
	var files []*ast.File
	for _, path := range paths {
		if strings.HasSuffix(path, "_test.go") {
			continue
		}
		f, err := parser.ParseFile(token.NewFileSet(), path, nil, 0)
		if err != nil {
			return Plan{}, err
		}
		files = append(files, f)
	}
	if len(files) == 0 {
		return Plan{}, fmt.Errorf("no Go package files in %s", dir)
	}
	return planFromFiles(files), nil
}

func main() {
	source := flag.String("source", ".", "Go package source root")
	flag.Parse()
	p, err := planSource(*source)
	if err != nil {
		fmt.Fprintln(os.Stderr, "UNKNOWN_PLAN_SOURCE", err)
		os.Exit(2)
	}
	if err := json.NewEncoder(os.Stdout).Encode(p); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
}
