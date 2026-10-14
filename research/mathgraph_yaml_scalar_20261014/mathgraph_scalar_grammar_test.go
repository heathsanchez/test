package yaml_test

import (
    "encoding/json"
    "math"
    "os"
    "strconv"
    "testing"
    "github.com/goccy/go-yaml"
)
type mathGraphScalarCase struct {
    Name string `json:"name"`
    Kind string `json:"kind"`
    Scalar string `json:"scalar"`
}
func TestMathGraphScalarGrammar(t *testing.T) {
    raw,err:=os.ReadFile("mathgraph_generated_scalar_cases.json")
    if err!=nil{t.Fatalf("source-pinned fixture missing: %v",err)}
    var corpus []mathGraphScalarCase
    if err:=json.Unmarshal(raw,&corpus);err!=nil{t.Fatalf("bad frozen fixture: %v",err)}
    if len(corpus)!=392{t.Fatalf("unexpected corpus size %d",len(corpus))}
    for _,tc:=range corpus{
        t.Run(tc.Name,func(t *testing.T){
            literal:=tc.Scalar
            if tc.Kind=="quoted" {literal=strconv.Quote(tc.Scalar)}
            data:=[]byte("value: "+literal+"\n")
            var decoded map[string]any
            if err:=yaml.Unmarshal(data,&decoded);err!=nil{
                t.Fatalf("native YAML decode rejected source: %v",err)
            }
            actual,ok:=decoded["value"]
            if !ok {t.Fatal("source key disappeared")}
            switch tc.Kind {
            case "numeric":
                value,ok:=actual.(float64)
                if !ok {t.Fatalf("implicit scientific number typed %T (%v), expected float64",actual,actual)}
                expected,err:=strconv.ParseFloat(tc.Scalar,64)
                if err!=nil{t.Fatalf("independent Go numeric grammar oracle rejected %q: %v",tc.Scalar,err)}
                if math.Float64bits(value)!=math.Float64bits(expected) {
                    t.Fatalf("numeric semantics mismatch for %q, got %v want %v",tc.Scalar,value,expected)
                }
            case "malformed","quoted","control":
                s,ok:=actual.(string)
                if !ok{t.Fatalf("scalar %q was falsely coerced from string to %T (%v)",tc.Scalar,actual,actual)}
                if s!=tc.Scalar{t.Fatalf("string semantics changed: got %q want %q",s,tc.Scalar)}
            default:t.Fatalf("unsupported case label %q",tc.Kind)
            }
        })
    }
}
