package main

import (
	"go/ast"
	"go/parser"
	"go/token"
	"testing"
)

func fixturePlan(t *testing.T, source string) Plan {
	t.Helper()
	file, err := parser.ParseFile(token.NewFileSet(), "fixture.go", source, 0)
	if err != nil { t.Fatalf("parse fixture: %v", err) }
	return planFromFiles([]*ast.File{file})
}

func TestDurationConstructorIsInhabited(t *testing.T) {
	p:=fixturePlan(t,`package cache
import "time"
type Cache struct{}
func New(a,b time.Duration)*Cache{return &Cache{}}
`)
	if p.Status!="CANDIDATE_CONSTRUCTOR" || p.Call!="pkg.New(80*time.Millisecond, 80*time.Millisecond)" || p.RootType!="Cache" || p.HasErrorResult {
		t.Fatalf("two durations must be constructible, got %+v",p)
	}
}

func TestContextPlusNamedConfigUsesUniqueInhabitableHelper(t *testing.T) {
	p:=fixturePlan(t,`package packagex
import("context";"time")
type Client struct{}
type Settings struct{ Capacity int }
func Defaults(d time.Duration)Settings{return Settings{Capacity:1}}
func Open(ctx context.Context,config Settings)(*Client,error){return &Client{},nil}
`)
	if p.Status!="CANDIDATE_CONSTRUCTOR" || p.Call!="pkg.Open(context.Background(), pkg.Defaults(80*time.Millisecond))" || !p.HasErrorResult {
		t.Fatalf("constructor must use source-provided default helper, got %+v",p)
	}
}

func TestIntegerFactoryDoesNotRequireDuration(t *testing.T){
	p:=fixturePlan(t,`package example
type Store struct{}
func Make(capacity int)*Store{return &Store{}}
`)
	if p.Status!="CANDIDATE_CONSTRUCTOR" || p.Call!="pkg.Make(1)" {
		t.Fatalf("integer parameter must be inhabited, got %+v",p)
	}
}

func TestGenericFactoryYieldsExplicitSpeculativeInstantiation(t *testing.T){
	p:=fixturePlan(t,`package cache
type Config[K comparable,V any] struct{ Maximum int }
type Cache[K comparable,V any] struct{}
func Create[K comparable,V any](cfg *Config[K,V])(*Cache[K,V],error){return &Cache[K,V]{},nil}
`)
	if p.Status!="CANDIDATE_CONSTRUCTOR" || p.Call!="pkg.Create[string,string](&pkg.Config[string,string]{})" || !p.SpeculativeGeneric {
		t.Fatalf("generic args must be marked speculative, got %+v",p)
	}
}

func TestFunctionParameterCannotBeInvented(t *testing.T){
	p:=fixturePlan(t,`package x
type Store struct{}
func Build(cb func(int)int)*Store{return &Store{}}
`)
	if p.Status!="UNKNOWN_CONSTRUCTOR_INHABITANT" || p.Call!="" {
		t.Fatalf("uninhabitable arguments must block construction, got %+v",p)
	}
}

func TestEqualCostConstructorTieRefusesChoice(t *testing.T){
	p:=fixturePlan(t,`package x
type Store struct{}
func Alpha()*Store{return &Store{}}
func Beta()*Store{return &Store{}}
`)
	if p.Status!="UNKNOWN_CONSTRUCTOR_AMBIGUITY" || p.Call!="" {
		t.Fatalf("equal-cost candidates must not be arbitrarily selected, got %+v",p)
	}
}
