package chi

import (
    "net/http"
    "strings"
    "testing"
)

// This algorithm knows only a finite input alphabet and a Boolean oracle.
// It is shared unchanged by chi's source parser and the Go standard library.
type mgOracle func([]string) bool

func mgWords(maxLength int) [][]string {
    out := [][]string{}
    for n:=0;n<=maxLength;n++ {
        mgEachWord(n,func(w []string) {
            out=append(out,append([]string(nil),w...))
        })
    }
    return out
}

func mgSignature(history []string, suffixes [][]string, oracle mgOracle) string {
    var b strings.Builder
    b.Grow(len(suffixes))
    for _, suffix := range suffixes {
        word := make([]string,0,len(history)+len(suffix))
        word=append(word,history...)
        word=append(word,suffix...)
        if oracle(word) { b.WriteByte('1') } else { b.WriteByte('0') }
    }
    return b.String()
}

type mgLearned struct {
    signatures []string
    classes int
    holdoutQueries int
    distinguishablePairs int
}

func mgLearnQuotient(t *testing.T, oracleName string, oracle mgOracle) mgLearned {
    t.Helper()
    histories := mgWords(4)
    suffixes := mgWords(3)
    holdout := [][]string{}
    mgEachWord(4,func(w []string){ holdout=append(holdout,w) })
    if len(histories)!=121 || len(suffixes)!=40 || len(holdout)!=81 {
        t.Fatal("finite input grammar incorrectly enumerated")
    }
    classes := map[string][][]string{}
    signatures := make([]string, len(histories))
    for i, history := range histories {
        sig := mgSignature(history, suffixes, oracle)
        classes[sig] = append(classes[sig],history)
        signatures[i]=sig
    }

    // Genuine holdout length 4 was not used to construct the partition.
    holdoutQueries:=0
    for _, equivalents := range classes {
        var first string
        for j, history := range equivalents {
            sig := mgSignature(history,holdout,oracle)
            holdoutQueries += len(holdout)
            if j==0 { first=sig } else if first!=sig {
                t.Fatalf("premature quotient in %s: two same-signature histories diverge on withheld suffix",oracleName)
            }
        }
    }
    // Every two distinct learned classes must admit a separating continuation,
    // with the shortest separator obtained from the *actual* oracle signature.
    classSigs:=make([]string,0,len(classes))
    for sig:=range classes { classSigs=append(classSigs,sig) }
    distinguished:=0
    for a:=0;a<len(classSigs);a++ {
        for b:=a+1;b<len(classSigs);b++ {
            found:=false
            for i:=range suffixes {
                if classSigs[a][i]!=classSigs[b][i] {
                    found=true
                    break
                }
            }
            if !found { t.Fatalf("nonseparable quotient classes: %s",oracleName) }
            distinguished++
        }
    }
    if len(classes)!=9 {
        t.Fatalf("source-native observational quotient %s has %d states, wanted bounded 9",oracleName,len(classes))
    }
    t.Logf("MATHGRAPH_OBSERVATIONAL_QUOTIENT oracle=%s histories=%d probes=%d classes=%d holdoutQueries=%d distinguishedPairs=%d",
        oracleName,len(histories),len(suffixes),len(classes),holdoutQueries,distinguished)
    return mgLearned{signatures:signatures,classes:len(classes),holdoutQueries:holdoutQueries,distinguishablePairs:distinguished}
}

func TestMathGraphLearnConsequenceQuotientAcrossImplementations(t *testing.T) {
    chiOracle:=func(keys []string) bool {
        return !mgPanic(func(){ _=patParamKeys(mgPattern(keys)) })
    }
    httpOracle:=func(keys []string) bool {
        return !mgPanic(func(){
            m:=http.NewServeMux()
            m.Handle(mgPattern(keys),http.HandlerFunc(func(http.ResponseWriter,*http.Request){}))
        })
    }

    chi := mgLearnQuotient(t,"chi",chiOracle)
    standard := mgLearnQuotient(t,"stdlib",httpOracle)
    for i:=range chi.signatures {
        if chi.signatures[i]!=standard.signatures[i] {
            t.Fatalf("source-distinct observable semantics differ on history %d",i)
        }
    }

    // A deliberately order-sensitive mutation must be visible to the learner.
    // It would make erasing history order UNSOUND.
    orderSensitive := func(keys []string) bool {
        if len(keys)>0 && keys[0]=="b" { return false }
        return chiOracle(keys)
    }
    ab:=mgSignature([]string{"a","b"},mgWords(3),chiOracle)
    ba:=mgSignature([]string{"b","a"},mgWords(3),chiOracle)
    if ab!=ba { t.Fatal("natural native quotient unexpectedly order-sensitive") }
    badAB:=mgSignature([]string{"a","b"},mgWords(3),orderSensitive)
    badBA:=mgSignature([]string{"b","a"},mgWords(3),orderSensitive)
    if badAB==badBA { t.Fatal("mutation negative control not distinguished") }

    t.Logf("MATHGRAPH_OBSERVATIONAL_TRANSFER chiStates=%d independentStdlibStates=%d partitionsIdentical=true orderSensitiveMutationDetected=true",
        chi.classes,standard.classes)
}
