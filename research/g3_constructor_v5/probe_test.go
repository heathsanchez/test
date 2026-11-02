package main

import (
	"testing"
	"time"
)

type traceCache struct{ entries map[string]string }

func (c *traceCache) Set(key, value string) error {
	if c.entries == nil {
		c.entries = map[string]string{}
	}
	c.entries[key] = value
	return nil
}
func (c *traceCache) Get(key string) (string, bool) {
	v, ok := c.entries[key]
	return v, ok
}
func (c *traceCache) Delete(key string) { delete(c.entries, key) }

type traceBuilder struct{}

func (*traceBuilder) Build() *traceCache { return &traceCache{} }

type brokenTraceCache struct{}

func (*brokenTraceCache) Set(string, string) error  { return nil }
func (*brokenTraceCache) Get(string) (string, bool) { return "", false }
func (*brokenTraceCache) Delete(string)             {}

type ttlTraceCache struct{ traceCache }

func (c *ttlTraceCache) Set(key, value string, ttl time.Duration) error {
	if ttl != time.Duration(-1) {
		return errTTLNotSupported{}
	}
	return c.traceCache.Set(key, value)
}

type errTTLNotSupported struct{}

func (errTTLNotSupported) Error() string { return "unsupported TTL" }

type absentTraceCache struct{}

func (*absentTraceCache) Count() int { return 0 }

func TestNativeDirectCacheStateTransitions(t *testing.T) {
	got := probe(&traceCache{}, true)
	if got.Status != "NATIVE_CACHE_TRACE_PASS" || got.UsedBuild || len(got.Steps) != 6 {
		t.Fatalf("direct cache semantic trace not proved: %+v", got)
	}
}

func TestNativeBuilderTransitionIsNecessary(t *testing.T) {
	full := probe(&traceBuilder{}, true)
	without := probe(&traceBuilder{}, false)
	restored := probe(&traceBuilder{}, true)
	if full.Status != "NATIVE_CACHE_TRACE_PASS" || !full.UsedBuild {
		t.Fatalf("builder reachability failed: %+v", full)
	}
	if without.Status != "UNKNOWN_NO_OPERATIONAL_REACHABILITY" {
		t.Fatalf("builder withdrawal did not lose trace: %+v", without)
	}
	if restored.Status != "NATIVE_CACHE_TRACE_PASS" || !restored.UsedBuild {
		t.Fatalf("builder restoration failed: %+v", restored)
	}
}

func TestNativeObserverRejectsNoOpSet(t *testing.T) {
	got := probe(&brokenTraceCache{}, true)
	if got.Status != "UNKNOWN_READBACK_MISMATCH" {
		t.Fatalf("false positive on no-op Set: %+v", got)
	}
}

func TestNativeObserverSuppliesNoExpiryTTL(t *testing.T) {
	got := probe(&ttlTraceCache{}, true)
	if got.Status != "NATIVE_CACHE_TRACE_PASS" {
		t.Fatalf("duration witness was not supported: %+v", got)
	}
}

func TestNativeObserverAbstainsOnUnrelatedObject(t *testing.T) {
	got := probe(&absentTraceCache{}, true)
	if got.Status != "UNKNOWN_NO_OPERATIONAL_REACHABILITY" {
		t.Fatalf("unrelated object accepted: %+v", got)
	}
}

func TestNativeObserverAbstainsOnNilPointer(t *testing.T) {
	var c *traceCache
	got := probe(c, true)
	if got.Status != "UNKNOWN_NIL_CONSTRUCTOR" {
		t.Fatalf("nil pointer accepted: %+v", got)
	}
}

type addCache struct{ entries map[string]string }
func (c *addCache) Add(k,v string) bool {if c.entries==nil {c.entries=map[string]string{}};c.entries[k]=v;return false}
func (c *addCache) Get(k string)(string,bool){v,ok:=c.entries[k];return v,ok}
func (c *addCache) Remove(k string)bool{_,ok:=c.entries[k];delete(c.entries,k);return ok}
func TestAddReadRemoveTrace(t *testing.T){
 got:=probe(&addCache{},true)
 if got.Status!="NATIVE_CACHE_TRACE_PASS" || len(got.Steps)!=6 {t.Fatalf("Add trace failed: %+v",got)}
}

type variadicSetCache struct{ entries map[string]string }
func (c *variadicSetCache) Set(k,v string,opts ...string){if c.entries==nil{c.entries=map[string]string{}};c.entries[k]=v}
func (c *variadicSetCache) Get(k string,opts ...string)(string,bool){v,ok:=c.entries[k];return v,ok}
func (c *variadicSetCache) Delete(k string){delete(c.entries,k)}
func TestVariadicSetOptionsOmitted(t *testing.T){
 got:=probe(&variadicSetCache{},true)
 if got.Status!="NATIVE_CACHE_TRACE_PASS"{t.Fatalf("variadic operation not covered: %+v",got)}
}
