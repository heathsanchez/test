#!/usr/bin/env python3
"""Source-directed bounded HTTP status retry observer; not autonomous L7 method invention."""
import hashlib
import json
import pathlib
import re
import sys

source_path = pathlib.Path(sys.argv[1])
out_path = pathlib.Path(sys.argv[2])
source = source_path.read_text(encoding="utf-8")

# Fixed human-written meta-rule discovers a call cycle; no Lima-specific
# function names are hard-coded in its selector.
branch = re.search(
    r"case\s+[A-Za-z_]\w*\.StatusCode\s*==\s*http\.StatusRequestedRangeNotSatisfiable\s*:\s*"
    r"(?:[^\n]*\n){0,5}?\s*return\s+(\w+)\(", source)
if branch is None:
    print(json.dumps({"epistemic":"UNKNOWN","reason":"NO_HTTP_416_RETRY_TRANSITION"}))
    sys.exit(3)
helper = branch.group(1)
helper_pos = re.search(r"func\s+" + re.escape(helper) + r"\s*\([^\n]*", source)
if helper_pos is None:
    print(json.dumps({"epistemic":"UNKNOWN","reason":"NO_HELPER_SOURCE"}))
    sys.exit(3)
helper_text = source[helper_pos.start():helper_pos.start()+1500]
next_call = re.search(r"return\s+(\w+)\(ctx\s*,", helper_text)
if next_call is None:
    print(json.dumps({"epistemic":"UNKNOWN","reason":"NO_OBSERVED_RETRY_CALL"}))
    sys.exit(3)
callee = next_call.group(1)
if not re.search(r"func\s+" + re.escape(callee) + r"\s*\(", source):
    print(json.dumps({"epistemic":"UNKNOWN","reason":"NO_NATIVE_RETRY_TARGET"}))
    sys.exit(3)

method = {
    "source_sha256":hashlib.sha256(source.encode()).hexdigest(),
    "selector":"HTTP_416_STATUS_BRANCH_TO_RETRY_CALL",
    "helper_symbol":helper,
    "retry_symbol":callee,
    "observer":"repeat_response(416); watch_GET_count; require_termination",
    "guarded_contract":"on repeated upstream 416, no unbounded redispatch; return error",
    "predefined_meta_grammar":True,
    "source_derived_instance":True,
    "autonomous_language_genesis":"NOT_TESTED",
}

# The test is new and emitted by the selector; the HTTP integration grammar is
# written by a human and does not qualify as autonomous L7 method invention.
# Repeated 416 without a Range request is an adversarial (noncompliant) server.
body = r'''package downloader

import (
 "bytes"
 "context"
 "net/http"
 "net/http/httptest"
 "os"
 "path/filepath"
 "sync/atomic"
 "testing"
 "time"
)

func TestMathGraphGeneratedNormal200(t *testing.T) {
 ctx,cancel := context.WithTimeout(context.Background(), 8*time.Second)
 defer cancel()
 expected := bytes.Repeat([]byte("mg-canonical-blob\n"), 7)
 ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
  if r.Method != http.MethodGet {t.Errorf("unexpected method: %s",r.Method)}
  w.WriteHeader(http.StatusOK)
  _,_ = w.Write(expected)
 }))
 defer ts.Close()
 dest := filepath.Join(t.TempDir(),"downloaded")
 res,err := Download(ctx,dest,ts.URL,WithCacheDir(filepath.Join(t.TempDir(),"cache")))
 if err != nil {t.Fatalf("MG_GEN_CONTROL: 200 download failed: %v",err)}
 if res == nil {t.Fatal("MG_GEN_CONTROL: nil success result")}
 got,err := os.ReadFile(dest)
 if err != nil || !bytes.Equal(got,expected) {t.Fatalf("MG_GEN_CONTROL: bad complete bytes, read err=%v",err)}
}

func TestMathGraphGeneratedRetryCycle(t *testing.T) {
 ctx,cancel := context.WithTimeout(context.Background(), 6*time.Second)
 defer cancel()
 var observed atomic.Int32
 ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
  if r.Method != http.MethodGet {return}
  n := observed.Add(1)
  w.WriteHeader(http.StatusRequestedRangeNotSatisfiable)
  if n >= 5 {cancel()} // finite hard stop, avoiding CI recursion exhaustion
 }))
 defer ts.Close()
 out := filepath.Join(t.TempDir(),"downloaded")
 _,err := Download(ctx,out,ts.URL,WithCacheDir(filepath.Join(t.TempDir(),"cache")))
 if err == nil {t.Fatal("MG_GEN_RETRY_LOOP: accepted repeated HTTP 416 as successful download")}
 if n := observed.Load(); n > 2 {
  t.Fatalf("MG_GEN_RETRY_LOOP: HTTP 416 triggered %d GET requests (no bounded non-progress guard)",n)
 }
}
'''
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(body, encoding="utf-8")
method["generated_test_sha256"]=hashlib.sha256(body.encode()).hexdigest()
out_path.with_suffix(".method.json").write_text(json.dumps(method,indent=2,sort_keys=True)+"\n")
print(json.dumps(method,sort_keys=True))
