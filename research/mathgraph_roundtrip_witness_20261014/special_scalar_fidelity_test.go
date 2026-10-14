package yaml_test
import (
    "math"
    "testing"
    yaml "github.com/goccy/go-yaml"
)
func TestMathGraphSpecialScalarStringFidelity(t *testing.T) {
    originals:=[]string{".nan",".NaN",".NAN",".inf","-.inf"}
    for _,source:=range originals{
        t.Run("string_"+source,func(t *testing.T){
            encoded,err:=yaml.Marshal(map[string]any{"value":source})
            if err!=nil{t.Fatal(err)}
            var decoded map[string]any
            if err:=yaml.Unmarshal(encoded,&decoded);err!=nil{t.Fatal(err)}
            s,ok:=decoded["value"].(string)
            if !ok{t.Errorf("string %q encoded as %q decoded into %T, expected string",source,encoded,decoded["value"])}
            else if s!=source{t.Errorf("string %q encoded as %q round-tripped as %q",source,encoded,s)}
        })
    }
    for _,tc:=range []struct{name string;value float64}{
        {"float_nan",math.NaN()},{"float_positive_inf",math.Inf(1)},
        {"float_negative_inf",math.Inf(-1)},
    } {
        t.Run(tc.name,func(t *testing.T){
            encoded,err:=yaml.Marshal(map[string]any{"value":tc.value})
            if err!=nil{t.Fatal(err)}
            var decoded map[string]any
            if err:=yaml.Unmarshal(encoded,&decoded);err!=nil{t.Fatal(err)}
            actual,ok:=decoded["value"].(float64)
            if !ok{t.Fatalf("float source reclassified into %T",decoded["value"])}
            if math.IsNaN(tc.value){if !math.IsNaN(actual){t.Errorf("NaN changed to %v",actual)}}
            else if math.IsInf(tc.value,1){if !math.IsInf(actual,1){t.Errorf("positive infinity changed to %v",actual)}}
            else if math.IsInf(tc.value,-1){if !math.IsInf(actual,-1){t.Errorf("negative infinity changed to %v",actual)}}
        })
    }
    for _,source:=range []string{".nanny",".infinite","normal","null","true"} {
        t.Run("string_control_"+source,func(t *testing.T){
            encoded,err:=yaml.Marshal(map[string]any{"value":source})
            if err!=nil{t.Fatal(err)}
            var decoded map[string]any
            if err:=yaml.Unmarshal(encoded,&decoded);err!=nil{t.Fatal(err)}
            got,ok:=decoded["value"].(string)
            if !ok||got!=source{t.Errorf("control string %q incorrectly decoded into %T (%v)",source,decoded["value"],decoded["value"])}
        })
    }
}
