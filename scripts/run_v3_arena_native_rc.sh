#!/usr/bin/env bash
set -euxo pipefail

V2=3d7585c21242f29fdaa48ae9a16e16c6afe42238
ARENA_REV=0dfcffe02c183311ac9168dcab9cde9b36959a95
PUBLIC_BASELINE_INSTR=823456774492
OUT="$GITHUB_WORKSPACE/v3-arena-native-rc"
rm -rf "$OUT" /tmp/mgv3rc-src /tmp/mgv3rc-baseline /tmp/mgv3rc-v3 /tmp/arena-v3rc
mkdir -p "$OUT"

# Arena's headline metric is retired instructions. Refuse to substitute wall time.
if ! perf stat -x, -e instructions:u -- true 2>"$OUT/perf-probe.csv"; then
  echo 'V3_ARENA_RC_DECISION=INFRA_NO_VPMU' | tee "$OUT/decision.txt"
  cat "$OUT/perf-probe.csv"
  exit 3
fi
if grep -qiE 'not supported|not counted|permission|no permission' "$OUT/perf-probe.csv"; then
  echo 'V3_ARENA_RC_DECISION=INFRA_NO_VPMU' | tee "$OUT/decision.txt"
  cat "$OUT/perf-probe.csv"
  exit 3
fi

echo 'PMU_OK=1' | tee "$OUT/decision.txt"

# Exact public MathGraph source baseline.
git clone --quiet https://github.com/metalogiclabs/mathgraph-lean-kernel.git /tmp/mgv3rc-src
cd /tmp/mgv3rc-src
git checkout --quiet "$V2"
git worktree add /tmp/mgv3rc-baseline "$V2"
git worktree add /tmp/mgv3rc-v3 "$V2"

# Frozen V3 intervention: only equal-hint Unfold/Unfold fallback at spine pairs (1,3),(1,4),(1,6).
python3 - <<'PY'
from pathlib import Path
p=Path('/tmp/mgv3rc-v3/src/conv.rs')
s=p.read_text()
old='''                    } else {\n                        self.unfold_pair(depth, t, t2)\n                    }\n'''
new='''                    } else {\n                        let lx = sx.len();\n                        let ly = sy.len();\n                        let a = lx.min(ly);\n                        let b = lx.max(ly);\n                        if a == 1 && (b == 3 || b == 4 || b == 6) {\n                            if lx < ly {\n                                let v1 = self.unfold_value(depth, t);\n                                if !std::ptr::eq(v1, t) { return self.unify::<true>(depth, v1, t2); }\n                                let v2 = self.unfold_value(depth, t2);\n                                if !std::ptr::eq(v2, t2) { return self.unify::<true>(depth, t, v2); }\n                            } else if ly < lx {\n                                let v2 = self.unfold_value(depth, t2);\n                                if !std::ptr::eq(v2, t2) { return self.unify::<true>(depth, t, v2); }\n                                let v1 = self.unfold_value(depth, t);\n                                if !std::ptr::eq(v1, t) { return self.unify::<true>(depth, v1, t2); }\n                            }\n                        }\n                        self.unfold_pair(depth, t, t2)\n                    }\n'''
anchor='''                    } else if rh.is_lt(&lh) {'''
pos=s.index(anchor)
target=s.index(old,pos)
s=s[:target]+s[target:].replace(old,new,1)
p.write_text(s)
assert s.count('a == 1 && (b == 3 || b == 4 || b == 6)') == 1
PY

# Arena's exact public checker config and PGO recipe from results.json.
cat >/tmp/mgv3rc-config.json <<'EOF'
{
  "use_stdin": true,
  "nat_extension": true,
  "string_extension": true,
  "unpermitted_axiom_hard_error": false,
  "unsafe_permit_all_axioms": true,
  "num_threads": 4
}
EOF

# Pin the exact Arena revision represented by the supplied results.json.
git clone --quiet https://github.com/leanprover/lean-kernel-arena /tmp/arena-v3rc
cd /tmp/arena-v3rc
git checkout --quiet "$ARENA_REV"
nix develop -c ./lka.py build-test init-prelude mathlib

for arm in baseline v3; do
  cd "/tmp/mgv3rc-$arm"
  rm -rf pgo target/release/sokonanoda
  RUSTFLAGS="-C target-cpu=native -Cprofile-generate=$PWD/pgo" cargo build --release
  target/release/sokonanoda /tmp/mgv3rc-config.json < /tmp/arena-v3rc/_build/tests/init-prelude.ndjson >/dev/null
  llvm-profdata merge -o "$PWD/pgo/merged.profdata" "$PWD/pgo"
  RUSTFLAGS="-C target-cpu=native -Cprofile-use=$PWD/pgo/merged.profdata" cargo build --release
  cp target/release/sokonanoda "/tmp/mgv3rc-bin-$arm"
done

# Sanity correctness on init-prelude before expensive measurement.
for arm in baseline v3; do
  /tmp/mgv3rc-bin-$arm /tmp/mgv3rc-config.json < /tmp/arena-v3rc/_build/tests/init-prelude.ndjson >/dev/null
 done

measure() {
  local arm="$1" rep="$2" out="$OUT/${arm}-rep${rep}.perf.csv"
  perf stat -x, -e instructions:u -o "$out" -- \
    /tmp/mgv3rc-bin-$arm /tmp/mgv3rc-config.json < /tmp/arena-v3rc/_build/tests/mathlib.ndjson >/dev/null
  awk -F, '$3 ~ /instructions/ {gsub(/ /,"",$1); print $1; exit}' "$out"
}

: > "$OUT/instructions.tsv"
# Paired alternating order to reduce drift; Arena itself uses one count, we retain three for RC confidence.
for rep in 1 2 3; do
  if (( rep % 2 == 1 )); then order='baseline v3'; else order='v3 baseline'; fi
  for arm in $order; do
    instr=$(measure "$arm" "$rep")
    [[ "$instr" =~ ^[0-9]+$ ]]
    printf '%s\t%s\t%s\n' "$rep" "$arm" "$instr" | tee -a "$OUT/instructions.tsv"
  done
done

python3 - "$OUT" "$PUBLIC_BASELINE_INSTR" <<'PY'
import csv, pathlib, statistics, sys
out=pathlib.Path(sys.argv[1]); public=int(sys.argv[2])
vals={'baseline':[],'v3':[]}
for line in (out/'instructions.tsv').read_text().splitlines():
    rep,arm,n=line.split('\t'); vals[arm].append(int(n))
mb=int(statistics.median(vals['baseline']))
mv=int(statistics.median(vals['v3']))
gain=(mb-mv)/mb*100
public_delta=(mb-public)/public*100
arena_seconds=mv/6_000_000_000
text=(
 f'public_v2_instructions={public}\n'
 f'local_v2_median_instructions={mb}\n'
 f'v3_median_instructions={mv}\n'
 f'v3_gain_percent={gain:.6f}\n'
 f'v3_arena_seconds_at_6Gips={arena_seconds:.6f}\n'
 f'v3_arena_minutes_at_6Gips={arena_seconds/60:.6f}\n'
 f'local_v2_vs_public_percent={public_delta:.6f}\n'
)
(out/'summary.txt').write_text(text)
print(text,end='')
with (out/'summary.csv').open('w',newline='') as f:
    w=csv.writer(f); w.writerow(['arm','median_instructions']); w.writerow(['baseline',mb]); w.writerow(['v3',mv])
if gain <= 0:
    print('V3_ARENA_RC_DECISION=NO_INSTRUCTION_GAIN')
    sys.exit(2)
print('V3_ARENA_RC_DECISION=INSTRUCTION_GAIN')
PY

echo 'V3_ARENA_RC_DECISION=QUALIFIED_MEASUREMENT' | tee -a "$OUT/decision.txt"
