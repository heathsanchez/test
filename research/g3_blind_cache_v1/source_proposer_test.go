package main

import (
    "go/parser"
    "go/token"
    "testing"
)

func proposalFromFixture(t *testing.T, src string) Proposal {
    t.Helper()
    f, err := parser.ParseFile(token.NewFileSet(), "fixture.go", src, 0)
    if err != nil { t.Fatalf("parse fixture: %v", err) }
    return proposeFiles(map[string]*parsedFile{"fixture.go": {File: f}})
}

func TestSourceClockInventsExternalActionOnlyWhenObserved(t *testing.T) {
    const base = `package sample
import "time"
type Store struct{ *store }
type store struct{}
func New(expiry, cleanup time.Duration) *Store { return &Store{} }
func (c *store) Set(k string, v interface{}, expiry time.Duration) {}
func (c *store) Get(k string) (interface{}, bool) { return nil, false }
func (c *store) Delete(k string) {}
`
    p := proposalFromFixture(t, base)
    if p.Status != "CANDIDATE_SIGNATURE_BRIDGE" || p.HasClock || len(p.EnvironmentalActions) != 0 {
        t.Fatalf("no source clock should prohibit external action: %+v", p)
    }
    if p.Constructor != "New" || p.WriteMethod != "Set" || p.ReadMethod != "Get" || p.DeleteMethod != "Delete" {
        t.Fatalf("signature matching failed: %+v", p)
    }

    p = proposalFromFixture(t, base+`func timer() { _ = time.Now() }`)
    if !p.HasClock || len(p.EnvironmentalActions) != 1 || p.EnvironmentalActions[0] != "ELAPSE" {
        t.Fatalf("source clock should propose one external action: %+v", p)
    }
}

func TestUnrelatedClockSelectorIsNotEvidence(t *testing.T) {
    const fixture = `package sample
type clock struct{}
func (clock) Now() int { return 0 }
var time clock
func f() { _ = time.Now() }
`
    p := proposalFromFixture(t, fixture)
    if p.HasClock || len(p.EnvironmentalActions) > 0 {
        t.Fatalf("non-stdlib time.Now is not a clock dependency: %+v", p)
    }
    if p.Status != "UNKNOWN_ADAPTER" { t.Fatalf("expected honest missing adapter: %+v", p) }
}

func TestAmbiguousSignatureRefusesToChoose(t *testing.T) {
    const fixture = `package sample
import "time"
type Store struct{}
func New(x, y time.Duration) *Store { return &Store{} }
func (s *Store) Set(k string, v interface{}, d time.Duration) {}
func (s *Store) Put(k string, v interface{}, d time.Duration) {}
func (s *Store) Get(k string) (interface{}, bool) { return nil, false }
`
    p := proposalFromFixture(t, fixture)
    if p.Status != "UNKNOWN_ADAPTER" || len(p.Ambiguities) == 0 {
        t.Fatalf("ambiguous role must not be silently selected: %+v", p)
    }
}
