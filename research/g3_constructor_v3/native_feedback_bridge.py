"""Bounded source-independent retry from exact public field names in errors.

The V2 bridge remains the input validator. V3 may only change an exported
scalar field when the native constructor itself names it in a rejection. This
does not establish semantic correctness or autonomous operator invention.
"""

import argparse
import json
from pathlib import Path
import re
import sys

V2 = Path(__file__).resolve().parents[1] / "g3_constructor_v2"
sys.path.insert(0, str(V2))
from native_constructor_bridge import create as create_v2  # noqa: E402


# The exact grammar is independent of any source package or specific field.
# V2 has already normalized generic substitutions to built-in type arguments.
CONFIG_LITERAL = re.compile(r"&pkg\.[A-Za-z_]\w*(?:\[[A-Za-z0-9_, ]+\])?\{\}")


REFINER = r'''
type Repair struct {
    Field string `json:"field"`
    Previous string `json:"previous"`
    New string `json:"new"`
    RejectedBecause string `json:"rejected_because"`
}

func nextPositive(current int64) (int64, bool) {
    if current <= 0 { return 1, true }
    if current < 16 { return 16, true }
    if current < 256 { return 256, true }
    return 0, false
}

func refineNamedField(ptr any, why string) (Repair, bool) {
    p := reflect.ValueOf(ptr)
    if p.Kind()!=reflect.Ptr || p.IsNil() { return Repair{},false }
    v := p.Elem()
    if v.Kind()!=reflect.Struct { return Repair{},false }
    t := v.Type()
    reason := strings.ToLower(why)
    best := -1
    bestLen := 0
    ambiguous := false
    for i:=0;i<t.NumField();i++ {
        f:=t.Field(i)
        value:=v.Field(i)
        if !f.IsExported() || !value.CanSet() { continue }
        switch value.Kind() {
        case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64,
             reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64,
             reflect.Float32, reflect.Float64, reflect.Bool:
        default: continue
        }
        if !strings.Contains(reason, strings.ToLower(f.Name)) {continue}
        n:=len(f.Name)
        if n>bestLen {best=i;bestLen=n;ambiguous=false} else if n==bestLen {ambiguous=true}
    }
    if best<0 || ambiguous {return Repair{},false}
    value:=v.Field(best)
    before:=fmt.Sprint(value.Interface())
    switch value.Kind() {
    case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
        next,ok:=nextPositive(value.Int())
        if !ok || value.OverflowInt(next) {return Repair{},false}
        value.SetInt(next)
    case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64:
        if value.Uint()>256 {return Repair{},false}
        next,ok:=nextPositive(int64(value.Uint()))
        if !ok || value.OverflowUint(uint64(next)) {return Repair{},false}
        value.SetUint(uint64(next))
    case reflect.Float32, reflect.Float64:
        next,ok:=nextPositive(int64(value.Float()))
        if !ok || value.OverflowFloat(float64(next)) {return Repair{},false}
        value.SetFloat(float64(next))
    case reflect.Bool:
        if value.Bool() {return Repair{},false}
        value.SetBool(true)
    default: return Repair{},false
    }
    return Repair{Field:t.Field(best).Name,Previous:before,
        New:fmt.Sprint(value.Interface()),RejectedBecause:why},true
}
'''


def create(manifest: dict, module: str, sha: str, source_dir: Path) -> Path:
    """Generate bounded Go retry code, or keep the V2 run when inapplicable."""
    dest = create_v2(manifest, module, sha, source_dir)
    if not manifest.get("has_error_result"):
        return dest
    call = manifest["call"]
    matches = list(CONFIG_LITERAL.finditer(call))
    if len(matches) != 1:
        return dest

    config_literal = matches[0].group(0)
    constructor_call = call.replace(config_literal, "cfg", 1)
    code = dest.read_text()
    start = code.index("    var object interface{}\n")
    end = code.index("    if object==nil", start)
    loop = f'''    cfg := {config_literal}
    var object interface{{}}
    repairs := []Repair{{}}
    attempts := 0
    for i:=0;i<12;i++ {{
        attempts++
        instance, constructErr := {constructor_call}
        if constructErr==nil {{object=instance;break}}
        repair,ok:=refineNamedField(cfg,constructErr.Error())
        if !ok {{
            fmt.Fprintln(os.Stderr,"UNKNOWN_RUNTIME_HINT_UNMATCHED",constructErr)
            os.Exit(4)
        }}
        repairs=append(repairs,repair)
    }}
    if object==nil {{
        fmt.Fprintln(os.Stderr,"UNKNOWN_RUNTIME_REPAIR_EXHAUSTED")
        os.Exit(5)
    }}
'''
    code = code[:start] + loop + code[end:]
    code = code.replace('    "reflect"\n', '    "reflect"\n    "strings"\n')
    code = code.replace("type Result struct {", REFINER + "\ntype Result struct {")
    code = code.replace('    SpeculativeGeneric bool `json:"speculative_generic"`',
                        '    SpeculativeGeneric bool `json:"speculative_generic"`\n'
                        '    Repairs []Repair `json:"repairs"`\n'
                        '    Attempts int `json:"attempts"`')
    code = code.replace('mathgraph.g3.constructor-native.v2',
                        'mathgraph.g3.constructor-feedback-native.v3')
    code = code.replace('Status:"CONSTRUCTED_NONNIL"',
                        'Status:"CONSTRUCTED_NONNIL_WITH_HINT_REPAIRS"')
    report = '    r:=Result{'
    beginning = code.index(report)
    ending = code.index('\n', beginning)
    original = code[beginning:ending]
    if not original.endswith('}'):
        raise ValueError("UNKNOWN_V2_REPORT_SHAPE")
    code = code[:beginning] + original[:-1] + ',Repairs:repairs,Attempts:attempts}' + code[ending:]
    dest.write_text(code)
    return dest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--source-dir", required=True)
    ap.add_argument("--module", required=True)
    ap.add_argument("--sha", required=True)
    args = ap.parse_args()
    create(json.loads(Path(args.manifest).read_text()), args.module, args.sha, Path(args.source_dir))


if __name__ == "__main__":
    main()
