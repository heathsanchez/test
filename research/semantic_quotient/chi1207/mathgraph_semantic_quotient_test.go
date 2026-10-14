package chi

import (
    "fmt"
    "net/http"
    "net/http/httptest"
    "reflect"
    "strings"
    "testing"
    "time"
)

// All witness inputs are generated from a bounded route-key grammar.
// This file does not import or execute any contributor-authored test code.
var mgAlphabet = []string{"a", "b", "c"}

func mgEachWord(n int, visit func([]string)) {
    if n == 0 { visit(nil); return }
    word := make([]string, n)
    var rec func(int)
    rec = func(i int) {
        if i == n { visit(append([]string(nil), word...)); return }
        for _, k := range mgAlphabet { word[i] = k; rec(i+1) }
    }
    rec(0)
}

func mgHasDuplicate(keys []string) bool {
    seen := map[string]bool{}
    for _, k := range keys {
        if seen[k] { return true }
        seen[k] = true
    }
    return false
}

func mgPattern(keys []string) string {
    if len(keys) == 0 { return "/" }
    return "/{" + strings.Join(keys, "}/{") + "}"
}

func mgPanic(fn func()) (panicked bool) {
    defer func() {
        if recover() != nil { panicked = true }
    }()
    fn()
    return false
}

func TestMathGraphKeyAdmissionNativeBridge(t *testing.T) {
    tested := 0
    for n := 0; n <= 4; n++ {
        mgEachWord(n, func(keys []string) {
            pattern := mgPattern(keys)
            nativeReject := mgPanic(func() { _ = patParamKeys(pattern) })
            wantReject := mgHasDuplicate(keys)
            if nativeReject != wantReject {
                t.Fatalf("native key parser disagrees with independent seen-set quotient: %q: got reject %t want %t",
                    pattern, nativeReject, wantReject)
            }
            tested++
        })
    }
    if tested != 121 { t.Fatalf("incomplete grammar: %d / 121", tested) }
    t.Logf("MATHGRAPH_NATIVE_KEY_QUOTIENT cases=%d alphabet=3 maxKeys=4 mismatch=0", tested)
}

func TestMathGraphRecoveredRouteMutation(t *testing.T) {
    tested := 0
    dirty := 0
    first := ""
    shortest := -1
    handler := http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
        w.WriteHeader(http.StatusNoContent)
    })
    for n := 2; n <= 4; n++ {
        mgEachWord(n, func(keys []string) {
            if !mgHasDuplicate(keys) { return }
            pattern := mgPattern(keys)
            m := NewMux()
            if !reflect.DeepEqual(m.tree, &node{}) {
                t.Fatal("invalid initial fresh mux state")
            }
            p := mgPanic(func(){ m.Get(pattern, handler) })
            if !p { t.Fatalf("duplicate route was unexpectedly accepted: %s", pattern) }
            changed := !reflect.DeepEqual(m.tree, &node{})
            tested++
            if changed {
                dirty++
                if shortest < 0 { shortest=n; first=pattern }
            } else {
                // Test independent future operation on the unmodified tree.
                m.Get("/good", handler)
                rr := httptest.NewRecorder()
                m.ServeHTTP(rr, httptest.NewRequest("GET", "/good", nil))
                if rr.Code != http.StatusNoContent {
                    t.Fatalf("clean post-error router broke a valid route: status=%d pattern=%q",
                        rr.Code, pattern)
                }
            }
        })
    }
    if tested < 1 { t.Fatal("missing duplicate grammar controls") }
    if shortest == -1 { shortest=0 }
    t.Logf("MATHGRAPH_NATIVE_RECOVERY cases=%d dirty=%d clean=%d minDirtyKeys=%d minDirtyPattern=%q",
        tested, dirty, tested-dirty, shortest, first)
    // No hard-coded verdict: CI compares this source's result across frozen revisions.
}

func TestMathGraphRecoveredRouteLivenessBound(t *testing.T) {
    // A separate bounded behavioral control: a timeout is NEVER proof of infinity.
    handler := http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
        w.WriteHeader(http.StatusNoContent)
    })
    firstSlow := 0
    tested := 0
    for n:=2;n<=29;n++ {
        m := NewMux()
        pat := "/" + strings.Repeat("{}", n) + "0"
        if !mgPanic(func(){m.Get(pat,handler)}) {
            t.Fatalf("expected duplicate-key rejection: n=%d",n)
        }
        done := make(chan int,1)
        go func() {
            w := httptest.NewRecorder()
            m.ServeHTTP(w, httptest.NewRequest("GET", "/{", nil))
            done <- w.Code
        }()
        tested++
        select {
        case <-done:
        case <-time.After(150*time.Millisecond):
            firstSlow=n
        }
        if firstSlow!=0 { break }
    }
    t.Logf("MATHGRAPH_NATIVE_LIVENESS tested=%d firstNotReturnedWithin150ms=%d scope=bounded_probe_only",
        tested,firstSlow)
    if firstSlow!=0 && firstSlow<2 { t.Fatal(fmt.Sprint("invalid witness index",firstSlow)) }
}
