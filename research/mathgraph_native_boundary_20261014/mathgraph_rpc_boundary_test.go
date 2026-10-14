package rpc
import (
 "context"
 "encoding/json"
 "fmt"
 "net/http"
 "net/http/httptest"
 "testing"
 "time"
)
// Source-native HTTP response binding probe: known PR fix, not blind discovery.
func TestMathGraphRPCIDBoundary(t *testing.T) {
 cases:=[]struct{name,reply string; accept bool}{
  {"matching_id","same",true},
  {"mismatched_numeric","wrong_number",false},
  {"null_id","null",false},
  {"missing_id","missing",false},
  {"wrong_type_string","other_string",false},
 }
 for _,tc:=range cases{
  t.Run(tc.name,func(t *testing.T){
   srv:=httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){
    defer r.Body.Close()
    var req struct{ ID json.RawMessage `json:"id"` }
    if err:=json.NewDecoder(r.Body).Decode(&req);err!=nil{
     t.Errorf("decode request: %v",err)
     http.Error(w,"invalid",400);return
    }
    if len(req.ID)==0 {t.Error("request ID missing");http.Error(w,"invalid",400);return}
    w.Header().Set("Content-Type","application/json")
    id:=string(req.ID)
    switch tc.reply {
    case "same":
    case "wrong_number":id="999999999"
    case "null":id="null"
    case "other_string":id=`"different-call"`
    case "missing":
     _,_=fmt.Fprint(w,"{\"jsonrpc\":\"2.0\",\"result\":\"bound\"}")
     return
    default:t.Errorf("bad fixture");return
    }
    _,_=fmt.Fprintf(w,"{\"jsonrpc\":\"2.0\",\"id\":%s,\"result\":\"bound\"}",id)
   }))
   defer srv.Close()
   c,err:=DialHTTP(srv.URL)
   if err!=nil{t.Fatal(err)}
   defer c.Close()
   ctx,cancel:=context.WithTimeout(context.Background(),5*time.Second);defer cancel()
   result:="unchanged"
   err=c.CallContext(ctx,&result,"mathgraph_identity_probe")
   if tc.accept {
    if err!=nil||result!="bound"{t.Fatalf("matching response rejected: %v %q",err,result)}
   }else{
    if err==nil{t.Errorf("accepted mismatched response identity: case=%s result=%q",tc.name,result)}
    if result!="unchanged"{t.Errorf("unmatched response contaminated result: %q",result)}
   }
  })
 }
}
