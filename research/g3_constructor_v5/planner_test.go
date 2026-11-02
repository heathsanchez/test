package main

import (
	"go/ast"
	"go/parser"
	"go/token"
	"testing"
)

func fileFor(t *testing.T, src string) *ast.File {
	t.Helper()
	f, err := parser.ParseFile(token.NewFileSet(), "cache.go", src, 0)
	if err != nil {
		t.Fatalf("parse fixture: %v", err)
	}
	return f
}

func TestPlannerInhabitsRequiredIntConstructor(t *testing.T) {
	f := fileFor(t, `package fixture
type Builder struct{}
func New(size int) *Builder { return &Builder{} }`)
	got := planFromFiles([]*ast.File{f})
	if got.Status != "CANDIDATE_CONSTRUCTOR" || got.Call != "pkg.New(2)" || got.Generic {
		t.Fatalf("wrong int plan: %+v", got)
	}
}

func TestPlannerOmitsVariadicGenericOptions(t *testing.T) {
	f := fileFor(t, `package fixture
type Cache[K comparable,V any] struct{}
type Option[K comparable,V any] func(*Cache[K,V])
func New[K comparable,V any](opts ...Option[K,V]) *Cache[K,V] { return &Cache[K,V]{} }`)
	got := planFromFiles([]*ast.File{f})
	if got.Status != "CANDIDATE_CONSTRUCTOR" || got.Call != "pkg.New[string,string]()" || !got.Generic {
		t.Fatalf("wrong generic variadic plan: %+v", got)
	}
}

func TestPlannerAbstainsOnUnsupportedGenericConstraint(t *testing.T) {
	f := fileFor(t, `package fixture
type Cache[T ~int] struct{}
func New[T ~int]() *Cache[T] { return &Cache[T]{} }`)
	got := planFromFiles([]*ast.File{f})
	if got.Status != "UNKNOWN_TYPE_CONSTRAINT" || got.Call != "" {
		t.Fatalf("unsupported type constraint must abstain: %+v", got)
	}
}

func TestPlannerAbstainsOnRequiredContext(t *testing.T) {
	f := fileFor(t, `package fixture
import "context"
type Cache struct{}
func New(ctx context.Context) *Cache { return &Cache{} }`)
	got := planFromFiles([]*ast.File{f})
	if got.Status != "UNKNOWN_REQUIRED_ARGUMENT" || got.Call != "" {
		t.Fatalf("unsupported required context must abstain: %+v", got)
	}
}

func TestPlannerAbstainsWhenNewMissing(t *testing.T) {
	f := fileFor(t, `package fixture
type Cache struct{}
func Make() *Cache { return &Cache{} }`)
	got := planFromFiles([]*ast.File{f})
	if got.Status != "UNKNOWN_NO_NEW" || got.Call != "" {
		t.Fatalf("missing New must abstain: %+v", got)
	}
}

func TestPlannerOmitsVariadicAfterMandatoryInt(t *testing.T) {
	f := fileFor(t, `package fixture
type Cache struct{}
func New(size int, opts ...int) *Cache { return &Cache{} }`)
	got := planFromFiles([]*ast.File{f})
	if got.Status != "CANDIDATE_CONSTRUCTOR" || got.Call != "pkg.New(2)" {
		t.Fatalf("variadic tail was incorrectly inhabited: %+v", got)
	}
}

func TestPlannerAdmitsPointerAndErrorPair(t *testing.T) {
 f:=fileFor(t,`package fixture
 type Cache[K comparable,V any] struct{}
 func New[K comparable,V any](size int)(*Cache[K,V],error){return nil,nil}`)
 got:=planFromFiles([]*ast.File{f})
 if got.Status!="CANDIDATE_CONSTRUCTOR" || !got.ReturnsError || got.Call!="pkg.New[string,string](2)" { t.Fatalf("two-result source must admit: %+v",got) }
}
func TestPlannerRefusesUntrustedSecondResult(t *testing.T){
 f:=fileFor(t,`package fixture
 type Cache struct{}
 func New()(*Cache,bool){return nil,true}`)
 got:=planFromFiles([]*ast.File{f})
 if got.Status!="UNKNOWN_CONSTRUCTOR_RESULT" {t.Fatalf("non-error pair incorrectly admitted: %+v",got)}
}
