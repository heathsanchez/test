"""Generate a typed native Go probe solely from the AST-derived method manifest.

The operation *templates* are preregistered. This is not free-form law invention.
No issue/PR/test-file content is an input to this generator.
"""

import argparse
import json
import pathlib
import re


NATIVE_PROBE = r'''package main

import (
    "encoding/json"
    "fmt"
    "time"
    pkg "__MODULE__"
)

type Case struct {
    Name string `json:"name"`
    Actions []string `json:"actions"`
    Before bool `json:"before"`
    After bool `json:"after"`
    BeforeValue interface{} `json:"before_value"`
    AfterValue interface{} `json:"after_value"`
}
type Report struct {
    Schema string `json:"schema"`
    SourceSHA string `json:"source_sha"`
    SourcePackage string `json:"source_package"`
    GeneratedOperator string `json:"generated_operator"`
    Boundary string `json:"boundary"`
    Cases []Case `json:"cases"`
}

func runCase(name string, expiry time.Duration, elapsed bool) Case {
    c := pkg.__CTOR__(0, 0)
    c.__WRITE__("k", "v", expiry)
    beforeValue, before := c.__READ__("k")
    actions := []string{"WRITE(k,v,expiry)", "READ(k)"}
    if elapsed {
        time.Sleep(300*time.Millisecond)
        actions=append(actions, "ELAPSE(300ms)")
    }
    afterValue, after := c.__READ__("k")
    actions=append(actions,"READ(k)")
    return Case{Name:name,Actions:actions,Before:before,After:after,BeforeValue:beforeValue,AfterValue:afterValue}
}

func main() {
    cases:=[]Case{
        runCase("B0_api_only_short",80*time.Millisecond,false),
        runCase("candidate_ast_clock_derived",80*time.Millisecond,true),
        runCase("negative_no_expiry",-1,false),
        runCase("negative_no_expiry_elapsed",-1,true),
        runCase("negative_no_elapse",80*time.Millisecond,false),
        runCase("B1_manual_time_aware_direct",80*time.Millisecond,true),
    }
    r:=Report{Schema:"mathgraph.g3.native-cache-grammar-probe.v1",SourceSHA:"__SHA__",SourcePackage:"__MODULE__",GeneratedOperator:"ELAPSE",Boundary:"SOURCE_ADAPTIVE_BUT_PREPROGRAMMED_TEMPLATE",Cases:cases}
    b,err:=json.MarshalIndent(r,"","  ")
    if err!=nil { panic(err) }
    fmt.Println(string(b))
}
'''


NATIVE_ADAPTER = r'''package main

import pkg "__MODULE__"

func construct() interface{} { return pkg.__CTOR__(0, 0) }
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--source-dir", required=True)
    ap.add_argument("--module", required=True)
    ap.add_argument("--sha", required=True)
    args = ap.parse_args()

    p = json.loads(pathlib.Path(args.manifest).read_text())
    if p["schema"] != "mathgraph.g3.source-adaptive-grammar.v1":
        raise SystemExit("MANIFEST_SCHEMA_MISMATCH")
    if p["status"] != "CANDIDATE_SIGNATURE_BRIDGE":
        raise SystemExit("UNKNOWN_ADAPTER: " + str(p.get("ambiguities")))
    if p["environmental_actions"] != ["ELAPSE"] or not p["has_clock"]:
        raise SystemExit("UNKNOWN_NO_CLOCK_DERIVED_ENVIRONMENT_ACTION")
    assert re.fullmatch(r"[a-f0-9]{40}", args.sha)
    assert re.fullmatch(r"[A-Za-z0-9_.\-/]+", args.module)
    replacements = {"__MODULE__": args.module, "__SHA__": args.sha}
    for key, token in (("constructor", "__CTOR__"), ("write_method", "__WRITE__"), ("read_method", "__READ__")):
        name = p[key]
        if not re.fullmatch(r"[A-Z][A-Za-z0-9_]*", name):
            raise SystemExit("UNKNOWN_UNSAFE_METHOD_NAME")
        replacements[token] = name

    source_root = pathlib.Path(args.source_dir)
    for subpath, source in (("mgprobe/main.go", NATIVE_PROBE), ("mgreplay/adapter.go", NATIVE_ADAPTER)):
        dest = source_root / "cmd" / subpath
        dest.parent.mkdir(parents=True, exist_ok=True)
        for a, b in replacements.items():
            source = source.replace(a, b)
        dest.write_text(source)


if __name__ == "__main__":
    main()
