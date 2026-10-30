"""Compile-time typed call bridge for bounded V2 constructor candidates.

The source AST planner decides which call expression to try. This script only
emits a Go program that compiles and executes that call on an exact-pinned
native module. Compiler/runtime errors are UNKNOWN, not source defects.
"""

import argparse
import json
from pathlib import Path
import re


TEMPLATE = r'''package main

import (
    "context"
    "encoding/json"
    "fmt"
    "os"
    "reflect"
    "time"
    pkg "__MODULE__"
)

type Result struct {
    Schema string `json:"schema"`
    SourceSHA string `json:"source_sha"`
    Status string `json:"status"`
    Type string `json:"constructed_type"`
    Call string `json:"call"`
    SpeculativeGeneric bool `json:"speculative_generic"`
}

func main(){
    // Every import is permitted by the fixed type-inhabitant alphabet. Keep
    // unused ones from making an otherwise valid generated program fail.
    _=context.Background
    _=time.Millisecond
    var object interface{}
    __CONSTRUCT__
    if object==nil {fmt.Fprintln(os.Stderr,"UNKNOWN_NATIVE_NIL_CONSTRUCTOR");os.Exit(3)}
    v:=reflect.ValueOf(object)
    if (v.Kind()==reflect.Ptr||v.Kind()==reflect.Interface)&&v.IsNil() {
        fmt.Fprintln(os.Stderr,"UNKNOWN_NATIVE_NIL_CONSTRUCTOR")
        os.Exit(3)
    }
    r:=Result{Schema:"mathgraph.g3.constructor-native.v2",SourceSHA:"__SHA__",Status:"CONSTRUCTED_NONNIL",Type:reflect.TypeOf(object).String(),Call:"__CALL_JSON__",SpeculativeGeneric:__SPECULATIVE__}
    if err:=json.NewEncoder(os.Stdout).Encode(r);err!=nil {panic(err)}
}
'''


def create(manifest: dict, module: str, sha: str, source_dir: Path) -> Path:
    if manifest.get("schema") != "mathgraph.g3.typed-constructor.v2":
        raise ValueError("UNKNOWN_MANIFEST_SCHEMA")
    if manifest.get("status") != "CANDIDATE_CONSTRUCTOR":
        raise ValueError("UNKNOWN_NOT_ADMITTED_BY_PLANNER")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("UNKNOWN_SOURCE_SHA")
    if not re.fullmatch(r"[A-Za-z0-9_.\-/]+", module):
        raise ValueError("UNKNOWN_MODULE_PATH")
    call = manifest["call"]
    # AST candidates are assembled from identifiers and a small fixed set of
    # inhabitants. Never allow injected statements to reach generated Go code.
    if not re.fullmatch(r'[A-Za-z0-9_.,&(){}\[\]"*+ /-]+', call) or not call.startswith("pkg."):
        raise ValueError("UNKNOWN_UNSAFE_CONSTRUCTOR_EXPRESSION")
    if manifest["has_error_result"]:
        construct = f"instance, constructErr := {call}\n    if constructErr!=nil {{fmt.Fprintln(os.Stderr,\"UNKNOWN_NATIVE_CONSTRUCTOR_ERROR\",constructErr);os.Exit(4)}}\n    object=instance"
    else:
        construct = f"object={call}"
    body = TEMPLATE.replace("__MODULE__", module)
    body = body.replace("__SHA__", sha)
    body = body.replace("__CONSTRUCT__", construct)
    body = body.replace("__CALL_JSON__", call.replace('\\', '\\\\').replace('"', '\\"'))
    body = body.replace("__SPECULATIVE__", str(bool(manifest["speculative_generic"])).lower())
    dest = source_dir / "cmd" / "mgconstructor" / "main.go"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(body)
    return dest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--source-dir", required=True)
    ap.add_argument("--module", required=True)
    ap.add_argument("--sha", required=True)
    args = ap.parse_args()
    manifest = json.loads(Path(args.manifest).read_text())
    create(manifest, args.module, args.sha, Path(args.source_dir))


if __name__ == "__main__":
    main()
