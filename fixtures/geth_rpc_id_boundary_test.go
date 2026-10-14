package rpc

import (
 "context"
 "encoding/json"
 "fmt"
 "net/http"
 "net/http/httptest"
 "strings"
 "errors"
 "testing"
)

func TestMathGraphHTTPResponseIDBoundary(t *testing.T) {
 for _, tc := range []struct{name, responseID string; wantError bool}{
  {"matching", "same", false},
  {"mismatched", "different", true},
  {"malformed_type", "object", true},
 } {
  t.Run(tc.name,func(t *testing.T){
   server:=httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){
    defer r.Body.Close()
    var req struct{ ID json.RawMessage `json:"id"` }
    if err:=json.NewDecoder(r.Body).Decode(&req);err!=nil {t.Errorf("decode request: %v",err);return}
    id:=string(req.ID)
    if tc.responseID=="different" {id="999999999"}
    if tc.responseID=="object" {id=`{"unexpected":"type"}`}
    w.Header().Set("Content-Type","application/json")
    fmt.Fprintf(w,`{"jsonrpc":"2.0","id":%s,"result":"ok"}`,id)
   }))
   defer server.Close()
   client,err:=DialHTTP(server.URL)
   if err!=nil {t.Fatal(err)}
   defer client.Close()
   var result string
   err=client.CallContext(context.Background(),&result,"web3_clientVersion")
   if tc.wantError {
    if err==nil {t.Fatalf("expected response ID rejection, got result %q",result)}
    if !strings.Contains(err.Error(),"response id mismatch") {t.Fatalf("unexpected rejection: %v",err)}
   }else if err!=nil || result!="ok" {t.Fatalf("valid response failed: result=%q err=%v",result,err)}
  })
 }
}

func TestMathGraphHeaderContextWithValidResponseIDs(t *testing.T) {
 server:=httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){
  defer r.Body.Close()
  var req struct {ID json.RawMessage `json:"id"`}
  if err:=json.NewDecoder(r.Body).Decode(&req);err!=nil {t.Errorf("decode: %v",err);return}
  if r.Header.Get("X-MathGraph")!="expected" {t.Errorf("header missing")}
  w.Header().Set("Content-Type","application/json")
  fmt.Fprintf(w,`{"jsonrpc":"2.0","id":%s}`,req.ID)
 }))
 defer server.Close()
 client,err:=DialHTTP(server.URL);if err!=nil {t.Fatal(err)};defer client.Close()
 ctx:=NewContextWithHeaders(context.Background(),http.Header{"X-MathGraph":[]string{"expected"}})
 if err:=client.CallContext(ctx,nil,"test");!errors.Is(err,ErrNoResult){t.Fatalf("expected ErrNoResult, got %v",err)}
}
