#!/usr/bin/env python3
from pathlib import Path

# 1. Preserve the structured panic event but ALSO call Rust's original panic hook,
# so native stderr remains independently observable.
p = Path('trace/src/main.rs')
s = p.read_text()
old = '''fn main() {
    std::panic::set_hook(Box::new(|info| {
        if let Some(loc) = info.location() {
            eprintln!("[MGTRACE] kind=panic site={}:{}:{}", loc.file(), loc.line(), loc.column());
        } else {
            eprintln!("[MGTRACE] kind=panic site=unknown");
        }
    }));
    let mut args = std::env::args();'''
new = '''fn main() {
    let mg_prev_hook = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        if let Some(loc) = info.location() {
            eprintln!("[MGTRACE] kind=panic site={}:{}:{}", loc.file(), loc.line(), loc.column());
        } else {
            eprintln!("[MGTRACE] kind=panic site=unknown");
        }
        mg_prev_hook(info);
    }));
    let mut args = std::env::args();'''
if old not in s:
    raise SystemExit('trace panic hook anchor not found')
p.write_text(s.replace(old, new, 1))

# 2. Tighten the V4 native-boundary gate: null locations are invalid.
p = Path('scripts/run_developmental_checker_repair_game.py')
s = p.read_text()
old = "summary['native_panic_locations']=sorted(set(r['native_panic_location'] for r in rows))\n"
new = "native_locations={r['native_panic_location'] for r in rows if r['native_panic_location'] is not None}\nsummary['native_panic_locations']=sorted(native_locations)\nsummary['native_panic_missing_count']=sum(r['native_panic_location'] is None for r in rows)\n"
if old not in s:
    raise SystemExit('native location summary anchor not found')
s = s.replace(old, new, 1)
old = "if len(summary['native_panic_locations']) != 1:\n    raise SystemExit(f\"common native boundary gate failed: {summary['native_panic_locations']}\")\n"
new = "if summary['native_panic_missing_count'] != 0 or len(summary['native_panic_locations']) != 1:\n    raise SystemExit(f\"common native boundary gate failed: missing={summary['native_panic_missing_count']} locations={summary['native_panic_locations']}\")\n"
if old not in s:
    raise SystemExit('native location gate anchor not found')
s = s.replace(old, new, 1)
s = s.replace("'status':'LIVE_COMMON_BOUNDARY_REPAIR_GAME_V4'", "'status':'LIVE_COMMON_BOUNDARY_REPAIR_GAME_V4B_NATIVE_VALIDATED'", 1)
p.write_text(s)

print('applied V4B chained native panic hook and non-null boundary gate')
