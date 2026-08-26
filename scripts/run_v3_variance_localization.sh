#!/usr/bin/env bash
set -euxo pipefail
V2=3d7585c21242f29fdaa48ae9a16e16c6afe42238
OUT="$GITHUB_WORKSPACE/v3-variance"
mkdir -p "$OUT"
rm -rf /tmp/mgv3-src /tmp/mgv3-baseline /tmp/mgv3-ratio15 /tmp/arena-v3

git clone https://github.com/metalogiclabs/mathgraph-lean-kernel.git /tmp/mgv3-src
cd /tmp/mgv3-src
git checkout "$V2"
git worktree add /tmp/mgv3-baseline "$V2"
git worktree add /tmp/mgv3-ratio15 "$V2"

python3 - <<'PY'
from pathlib import Path
p=Path('/tmp/mgv3-ratio15/src/conv.rs')
s=p.read_text()
old='''                    } else {\n                        self.unfold_pair(depth, t, t2)\n                    }\n'''
new='''                    } else {\n                        let lx = sx.len();\n                        let ly = sy.len();\n                        let gap = if lx >= ly { lx - ly } else { ly - lx };\n                        let shorter = lx.min(ly);\n                        let longer = lx.max(ly);\n                        if gap >= 2 && (longer * 2 >= shorter * 3) {\n                            if lx <= ly {\n                                let v1 = self.unfold_value(depth, t);\n                                if !std::ptr::eq(v1, t) {\n                                    return self.unify::<true>(depth, v1, t2);\n                                }\n                                let v2 = self.unfold_value(depth, t2);\n                                if !std::ptr::eq(v2, t2) {\n                                    return self.unify::<true>(depth, t, v2);\n                                }\n                            } else {\n                                let v2 = self.unfold_value(depth, t2);\n                                if !std::ptr::eq(v2, t2) {\n                                    return self.unify::<true>(depth, t, v2);\n                                }\n                                let v1 = self.unfold_value(depth, t);\n                                if !std::ptr::eq(v1, t) {\n                                    return self.unify::<true>(depth, v1, t2);\n                                }\n                            }\n                        }\n                        self.unfold_pair(depth, t, t2)\n                    }\n'''
anchor='''                    } else if rh.is_lt(&lh) {'''
pos=s.index(anchor)
target=s.index(old,pos)
s=s[:target]+s[target:].replace(old,new,1)
p.write_text(s)
PY

for arm in baseline ratio15; do
  cd "/tmp/mgv3-$arm"
  cargo test --release --locked
  RUSTFLAGS='-C target-cpu=x86-64' cargo build --release --locked
  cp target/release/sokonanoda "/tmp/mgv3-bin-$arm"
done

cat >/tmp/checker-v3.json <<'EOF'
{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":4,"print_success_message":false}
EOF

git clone --depth 1 https://github.com/leanprover/lean-kernel-arena /tmp/arena-v3
cd /tmp/arena-v3
nix develop -c ./lka.py build-test mathlib
M=_build/tests/mathlib.ndjson
LINES=$(wc -l < "$M")
echo -e "total_lines\t$LINES" > "$OUT/meta.tsv"

# Prefixes preserve declaration history while localizing where cumulative cost diverges.
for pct in 10 25 50 75 100; do
  n=$(( LINES * pct / 100 ))
  head -n "$n" "$M" > "/tmp/mathlib-p${pct}.ndjson"
done

: > "$OUT/prefix-pairs.tsv"
measure () {
  local arm=$1 pct=$2 rep=$3
  local file="/tmp/mathlib-p${pct}.ndjson"
  /usr/bin/time -q -f '%e' -o /tmp/v3-time.txt "/tmp/mgv3-bin-$arm" /tmp/checker-v3.json < "$file" >/dev/null 2>"/tmp/${arm}-p${pct}-r${rep}.err" || true
  printf '%s\t%s\t%s\t%s\n' "$pct" "$rep" "$arm" "$(tail -n1 /tmp/v3-time.txt)" >> "$OUT/prefix-pairs.tsv"
}

for pct in 10 25 50 75 100; do
  for rep in 1 2 3; do
    if (( rep % 2 == 1 )); then
      measure baseline "$pct" "$rep"; measure ratio15 "$pct" "$rep"
    else
      measure ratio15 "$pct" "$rep"; measure baseline "$pct" "$rep"
    fi
  done
done

python3 - "$OUT/prefix-pairs.tsv" > "$OUT/prefix-summary.tsv" <<'PY'
import csv,statistics,sys
from collections import defaultdict
r=defaultdict(lambda:defaultdict(list))
with open(sys.argv[1]) as f:
    for pct,rep,arm,t in csv.reader(f,delimiter='\t'):
        r[int(pct)][arm].append(float(t))
print('pct\tbaseline_median\tratio15_median\tdelta_pct\tpaired_delta_median_pct')
for pct in sorted(r):
    b=r[pct]['baseline']; g=r[pct]['ratio15']
    bm=statistics.median(b); gm=statistics.median(g)
    paired=[(gg/bb-1)*100 for bb,gg in zip(b,g)]
    print(f'{pct}\t{bm:.4f}\t{gm:.4f}\t{(gm/bm-1)*100:.4f}\t{statistics.median(paired):.4f}')
PY

# Full-run hardware counters: compare retired work, not just wall clock.
: > "$OUT/perf-stat.txt"
for arm in baseline ratio15; do
  echo "=== $arm ===" >> "$OUT/perf-stat.txt"
  perf stat -x $'\t' -e task-clock,cycles,instructions,branches,branch-misses,cache-references,cache-misses \
    "/tmp/mgv3-bin-$arm" /tmp/checker-v3.json < "$M" >/dev/null 2>> "$OUT/perf-stat.txt" || true
done

python3 - "$OUT/prefix-summary.tsv" "$OUT/perf-stat.txt" > "$OUT/decision.txt" <<'PY'
import csv,sys
rows=list(csv.DictReader(open(sys.argv[1]),delimiter='\t'))
full=next(x for x in rows if x['pct']=='100')
d=float(full['paired_delta_median_pct'])
print('V3_VARIANCE_LOCALIZATION')
print('full_paired_delta_median_pct',d)
print('prefix_curve')
for x in rows: print(x['pct'],x['paired_delta_median_pct'])
if abs(d) < 0.5:
    print('RESIDUAL=WHOLE_RUN_GAIN_COLLAPSES_UNDER_PAIRED_REPETITION')
elif d <= -1.0:
    print('RESIDUAL=REPRODUCIBLE_FULL_RUN_GAIN_REQUIRES_PREFIX_LOCALIZATION')
else:
    print('RESIDUAL=REPRODUCIBLE_REGRESSION_OR_RUNNER_EFFECT')
print('See perf-stat.txt to distinguish retired-work change from wall-clock noise.')
PY

cat "$OUT/prefix-summary.tsv"
cat "$OUT/decision.txt"
