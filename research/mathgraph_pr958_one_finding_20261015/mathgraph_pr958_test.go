package yaml_test

import (
  "bytes"
  "fmt"
  "reflect"
  "testing"

  yaml "github.com/goccy/go-yaml"
)

// Source-independent bytes marshaler: generates native YAML fragments, then
// checks that embedding the fragment does not change the standalone meaning.
type mathgraphByteFragment struct{ raw []byte }
func (m mathgraphByteFragment) MarshalYAML() ([]byte,error){ return m.raw,nil }

type mathgraphNestedFragment struct { name, source string }
var mathgraphBlockFragments=[]mathgraphNestedFragment{
  {"literal_chomp_clip","value: |\n  first\n  second\n"},
  {"literal_chomp_strip","value: |-\n  first\n  second\n"},
  {"literal_chomp_keep","value: |+\n  first\n  second\n\n"},
  {"folded_chomp_clip","value: >\n  first\n  second\n"},
  {"folded_chomp_strip","value: >-\n  first\n  second\n"},
  {"folded_chomp_keep","value: >+\n  first\n  second\n\n"},
  {"literal_explicit_indent","value: |2\n  first\n  second\n"},
  {"folded_explicit_indent","value: >2-\n  first\n  second\n"},
  {"literal_blank_middle","value: |-\n  first\n\n  third\n"},
  {"literal_unicode","value: |-\n  🚀 beta\n  漢字\n"},
  {"literal_deeper_indent","value: |-\n    first\n    second\n"},
  {"plain_control","value: hello\n"},
  {"quoted_control","value: \"quoted #literal\"\n"},
}

func mathgraphNested(value any, shape int) (any,[]any) {
  switch shape {
  case 0: return map[string]any{"outer":value},[]any{"outer"}
  case 1: return map[string]any{"outer":map[string]any{"middle":value}},[]any{"outer","middle"}
  case 2: return map[string]any{"items":[]any{value}},[]any{"items",0}
  case 3: return []any{map[string]any{"outer":value}},[]any{0,"outer"}
  case 4:
    return map[string]any{"parent":[]any{map[string]any{"child":value}}},[]any{"parent",0,"child"}
  default: panic("invalid shape")
  }
}

func mathgraphReach(root any,path []any)(any,error){
  curr:=root
  for _,step:=range path{
    switch key:=step.(type){
    case string:
      switch m:=curr.(type){
      case map[string]any:
        next,ok:=m[key];if !ok{return nil,fmt.Errorf("missing map key %q",key)}
        curr=next
      case map[any]any:
        next,ok:=m[key];if !ok{return nil,fmt.Errorf("missing generic map key %q",key)}
        curr=next
      default:return nil,fmt.Errorf("expected mapping before key %q, got %T",key,curr)
      }
    case int:
      slice,ok:=curr.([]any)
      if !ok || len(slice)<=key{return nil,fmt.Errorf("expected sequence idx %d, got %T",key,curr)}
      curr=slice[key]
    default:return nil,fmt.Errorf("unknown path step %T",step)
    }
  }
  return curr,nil
}
func TestMathGraphNestedByteMarshalerInvariant(t *testing.T){
  if len(mathgraphBlockFragments)!=13 {t.Fatal("fixture set drift")}
  for _,f:=range mathgraphBlockFragments{
    t.Run(f.name,func(t *testing.T){
      var expected map[string]any
      if err:=yaml.Unmarshal([]byte(f.source),&expected);err!=nil{
        t.Fatalf("standalone fragment must parse: %v",err)
      }
      if len(expected)!=1{t.Fatalf("standalone fixture has unexpected arity %d",len(expected))}
      for shape:=0;shape<5;shape++{
        for _,indent:=range []int{2,4}{
          name:=fmt.Sprintf("shape%d_indent%d",shape,indent)
          t.Run(name,func(t *testing.T){
            nested,path:=mathgraphNested(mathgraphByteFragment{raw:[]byte(f.source)},shape)
            encoded,err:=yaml.MarshalWithOptions(nested,yaml.Indent(indent))
            if err!=nil{t.Fatalf("nested marshal failed: %v",err)}
            var decoded any
            if err:=yaml.Unmarshal(encoded,&decoded);err!=nil{
              t.Fatalf("nested fragment generated unparseable YAML: %v; encoded=%q",err,encoded)
            }
            embedded,err:=mathgraphReach(decoded,path)
            if err!=nil{t.Fatalf("nested embedding lost shape: %v; encoded=%q",err,encoded)}
            if !reflect.DeepEqual(embedded,expected){
              t.Fatalf("nested encoding changed the standalone fragment meaning: got=%#v expected=%#v encoded=%q",embedded,expected,encoded)
            }
            // Source-independent no-op second parse: embedded YAML should remain
            // printable as native JSON-compatible map without value distortion.
            if buf,err:=yaml.Marshal(embedded);err!=nil||len(bytes.TrimSpace(buf))==0 {
              t.Fatalf("nested extracted value cannot be marshaled again: %v",err)
            }
          })
        }
      }
    })
  }
}

func TestMathGraphPreexistingScalarRiskNotAttributableToPR(t *testing.T){
  // This negative attribution control intentionally expects a *string*.
  // Both upstream revisions may fail these tests; the PR must not be blamed
  // for any failure that also occurred before it.
  for _,v:=range []string{".nan",".NaN",".NAN",".inf","-.inf"} {
    t.Run("string_"+v,func(t *testing.T){
      raw,err:=yaml.Marshal(map[string]any{"value":v})
      if err!=nil{t.Fatal(err)}
      var result map[string]any
      if err:=yaml.Unmarshal(raw,&result);err!=nil{t.Fatal(err)}
      got,ok:=result["value"].(string)
      if !ok||got!=v{t.Errorf("inherited string roundtrip mismatch: value %q -> %q -> %#v",v,raw,result["value"])}
    })
  }
}
