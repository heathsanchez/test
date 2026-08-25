#!/usr/bin/env bash
set -euxo pipefail
V2=3d7585c21242f29fdaa48ae9a16e16c6afe42238
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
nix develop -c ./lka.py build-test

: > /tmp/v3-semantic-gate.txt
count=0
while IFS= read -r f; do
  count=$((count+1))
  bstatus=0; rstatus=0
  timeout 180 /tmp/mgv3-bin-baseline /tmp/checker-v3.json < "$f" >/tmp/v3-base.out 2>/tmp/v3-base.err || bstatus=$?
  timeout 180 /tmp/mgv3-bin-ratio15 /tmp/checker-v3.json < "$f" >/tmp/v3-ratio15.out 2>/tmp/v3-ratio15.err || rstatus=$?
  if [ "$bstatus" -ne "$rstatus" ]; then
    printf 'MISMATCH\t%s\tbase=%s\tratio15=%s\n' "$f" "$bstatus" "$rstatus" | tee -a /tmp/v3-semantic-gate.txt
    cp /tmp/v3-semantic-gate.txt "$GITHUB_WORKSPACE"/
    exit 1
  fi
  printf 'MATCH\t%s\tstatus=%s\n' "$f" "$bstatus" >> /tmp/v3-semantic-gate.txt
done < <(find _build/tests -type f -name '*.ndjson' | sort)
echo "RECURSIVE_SEMANTIC_GATE_PASS tests=$count candidate=ratio15" | tee -a /tmp/v3-semantic-gate.txt

: > /tmp/v3-times.tsv
measure () {
  local arm=$1 rep=$2
  /usr/bin/time -q -f '%e' -o /tmp/v3-time.txt "/tmp/mgv3-bin-$arm" /tmp/checker-v3.json < _build/tests/mathlib.ndjson >/tmp/v3-${arm}-${rep}.out 2>/tmp/v3-${arm}-${rep}.err
  printf '%s\t%s\t%s\n' "$arm" "$rep" "$(tail -n 1 /tmp/v3-time.txt)" >> /tmp/v3-times.tsv
}
for rep in 1 2 3 4 5; do
  if (( rep % 2 == 1 )); then
    measure baseline "$rep"; measure ratio15 "$rep"
  else
    measure ratio15 "$rep"; measure baseline "$rep"
  fi
done

python3 - <<'PY' | tee /tmp/v3-decision.txt
import csv, statistics
from collections import defaultdict
r=defaultdict(list)
with open('/tmp/v3-times.tsv') as f:
    for arm,rep,x in csv.reader(f, delimiter='\t'):
        r[arm].append(float(x))
b=statistics.median(r['baseline']); g=statistics.median(r['ratio15'])
delta=(g/b-1)*100
print('V3_RATIO15_MATHLIB_QUALIFICATION')
print('baseline', b, r['baseline'])
print('ratio15', g, r['ratio15'])
print('delta_pct', delta)
if g <= 0.99*b:
    print('V3_PR_DECISION=QUALIFIED_RATIO15')
else:
    print('V3_PR_DECISION=PERF_NOT_REPRODUCED')
    raise SystemExit(1)
PY

cp /tmp/v3-semantic-gate.txt "$GITHUB_WORKSPACE"/
cp /tmp/v3-times.tsv "$GITHUB_WORKSPACE"/
cp /tmp/v3-decision.txt "$GITHUB_WORKSPACE"/
