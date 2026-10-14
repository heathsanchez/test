package chi

import (
    "fmt"
    "net/http"
    "net/http/httptest"
    "regexp"
    "sort"
    "strings"
    "testing"
    "time"
)

// A bounded, deterministic projection of the actual route trie.
// No pointer addresses or handler code are included.
func mgTreeSignature(root *node) string {
    var b strings.Builder
    seen:=map[*node]bool{}
    var walk func(*node,int)
    walk=func(n *node,depth int) {
        if n==nil { b.WriteString("<nil>");return }
        if depth>256 { b.WriteString("<depth-bound>");return }
        if seen[n] { b.WriteString("<cycle>");return }
        seen[n]=true
        fmt.Fprintf(&b,"(typ=%d prefix=%q label=%d tail=%d rex=%t ",
            n.typ,n.prefix,n.label,n.tail,n.rex!=nil)
        keys:=make([]int,0,len(n.endpoints))
        for k:=range n.endpoints {keys=append(keys,int(k))}
        sort.Ints(keys)
        for _,k:=range keys {
            e:=n.endpoints[methodTyp(k)]
            fmt.Fprintf(&b,"endpoint=%d:%q ",k,e.pattern)
        }
        for typ,group:=range n.children {
            fmt.Fprintf(&b,"children[%d]=%d ",typ,len(group))
            for _,child:=range group {walk(child,depth+1)}
        }
        b.WriteString(")")
    }
    walk(root,0)
    return b.String()
}

func TestMathGraphNonDuplicateValidationFailureScope(t *testing.T) {
    handler:=http.HandlerFunc(func(w http.ResponseWriter,_ *http.Request){
        w.WriteHeader(http.StatusNoContent)
    })
    // Each candidate is checked by the Go regexp parser before being tested
    // against chi. The experiment is therefore not relying on a hard-coded
    // list of accepted or rejected routes.
    fragments:=[]string{"[","(","*","\\"}
    prefixes:=[]string{"/a/","/a/sta","/z/"}
    tried,changed,validControls,probeTimeouts:=0,0,0,0
    firstChanged:=""
    for _,frag:=range fragments {
        if _,err:=regexp.Compile("^"+frag+"$");err==nil {continue}
        for _,prefix:=range prefixes {
            pat:=prefix+"{x:"+frag+"}"
            // This is intentionally a DIFFERENT error family than duplicate
            // names: the independent key-admission guard must accept it.
            if mgPanic(func(){ _=patParamKeys(pat) }) {
                t.Fatalf("bad regexp candidate is also invalid key grammar: %q",pat)
            }
            mux:=NewMux()
            mux.Get("/a/stable",handler)
            before:=mgTreeSignature(mux.tree)
            var errorText string
            func(){
                defer func(){if x:=recover();x!=nil {errorText=fmt.Sprint(x)}}()
                mux.Get(pat,handler)
            }()
            if !strings.Contains(errorText,"invalid regexp pattern") {
                t.Fatalf("expected regexp validation panic for %q, got %q",pat,errorText)
            }
            after:=mgTreeSignature(mux.tree)
            tried++
            if after!=before {
                changed++
                if firstChanged=="" {firstChanged=pat}
            }
            done:=make(chan int,1)
            go func(){
                rr:=httptest.NewRecorder()
                mux.ServeHTTP(rr,httptest.NewRequest(http.MethodGet,"/a/stable",nil))
                done<-rr.Code
            }()
            select{
            case code:=<-done:
                if code==http.StatusNoContent {validControls++} else {
                    t.Logf("MATHGRAPH_EXCEPTION_OBSERVABLE unexpectedStatus=%d pattern=%q",code,pat)
                }
            case <-time.After(150*time.Millisecond):
                probeTimeouts++
            }
        }
    }
    if tried<3 {t.Fatalf("not enough independent malformed-regexp probes: %d",tried)}
    t.Logf("MATHGRAPH_OTHER_EXCEPTION samples=%d changed=%d originalRoutesStillOK=%d livenessTimeouts=%d firstChanged=%q",
        tried,changed,validControls,probeTimeouts,firstChanged)
    // Report only. The upstream PR claims only duplicate-key atomicity;
    // another exception class is not evidence that its stated fix failed.
}
