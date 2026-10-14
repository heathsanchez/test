package yaml_test
import ("testing";"github.com/goccy/go-yaml")
// Alias must resolve to its historical preceding binding, not a later rebinding.
func TestMathGraphYAMLAliasBoundary(t *testing.T){
 t.Run("matching_unique_binding",func(t *testing.T){
  var v struct{A any `yaml:"a"`;B string `yaml:"b"`}
  err:=yaml.Unmarshal([]byte("a: &x first\nb: *x\n"),&v)
  if err!=nil||v.B!="first"{t.Fatalf("unique alias: %v; %q",err,v.B)}
 })
 t.Run("mapping_prior_binding",func(t *testing.T){
  var v struct{A any `yaml:"a"`;B string `yaml:"b"`;C any `yaml:"c"`}
  err:=yaml.Unmarshal([]byte("a: &x first\nb: *x\nc: &x second\n"),&v)
  if err!=nil||v.B!="first"{t.Fatalf("mapping alias: %v; got %q want first",err,v.B)}
 })
 t.Run("sequence_prior_binding",func(t *testing.T){
  var v []struct{A any `yaml:"a"`;B string `yaml:"b"`}
  err:=yaml.Unmarshal([]byte("- a: &x first\n- b: *x\n- a: &x second\n"),&v)
  if err!=nil{t.Fatalf("sequence decode: %v",err)}
  if len(v)!=3||v[1].B!="first"{t.Fatalf("sequence prior alias wrong: len %d, values %#v",len(v),v)}
 })
}
