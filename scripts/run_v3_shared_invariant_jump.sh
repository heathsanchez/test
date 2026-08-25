#!/usr/bin/env bash
set -euxo pipefail
V2=3d7585c21242f29fdaa48ae9a16e16c6afe42238
rm -rf /tmp/v3si-src /tmp/v3si-* /tmp/arena-v3si

git clone https://github.com/metalogiclabs/mathgraph-lean-kernel.git /tmp/v3si-src
cd /tmp/v3si-src
git checkout "$V2"
for arm in baseline gap2 ratio15 ratio2 long6 ratio15long6; do
  git worktree add "/tmp/v3si-$arm" "$V2"
done

python3 - <<'PY'
from pathlib import Path
old='''                    } else {\n                        self.unfold_pair(depth, t, t2)\n                    }\n'''

def repl(cond):
    return f'''                    }} else {{\n                        let lx = sx.len();\n                        let ly = sy.len();\n                        let gap = if lx >= ly {{ lx - ly }} else {{ ly - lx }};\n                        let shorter = lx.min(ly);\n                        let longer = lx.max(ly);\n                        if {cond} {{\n                            if lx <= ly {{\n                                let v1 = self.unfold_value(depth, t);\n                                if !std::ptr::eq(v1, t) {{ return self.unify::<true>(depth, v1, t2); }}\n                                let v2 = self.unfold_value(depth, t2);\n                                if !std::ptr::eq(v2, t2) {{ return self.unify::<true>(depth, t, v2); }}\n                            }} else {{\n                                let v2 = self.unfold_value(depth, t2);\n                                if !std::ptr::eq(v2, t2) {{ return self.unify::<true>(depth, t, v2); }}\n                                let v1 = self.unfold_value(depth, t);\n                                if !std::ptr::eq(v1, t) {{ return self.unify::<true>(depth, v1, t2); }}\n                            }}\n                        }}\n                        self.unfold_pair(depth, t, t2)\n                    }}\n'''

# Census-motivated shared invariants. Top observed useful families were
# (3,6), (1,3), (4,6), (2,6), (2,4): all gap>=2, all ratio>=1.5,
# and overwhelmingly longer<=6. Test those structural properties rather
# than any literal pair.
conds={
 'gap2':'gap >= 2',
 'ratio15':'gap >= 2 && (longer * 2 >= shorter * 3)',
 'ratio2':'gap >= 2 && (shorter == 0 || longer >= shorter * 2)',
 'long6':'gap >= 2 && longer <= 6',
 'ratio15long6':'gap >= 2 && longer <= 6 && (longer * 2 >= shorter * 3)',
}
for arm,cond in conds.items():
    p=Path(f'/tmp/v3si-{arm}/src/conv.rs')
    s=p.read_text()
    anchor='''                    } else if rh.is_lt(&lh) {'''
    pos=s.index(anchor)
    target=s.index(old,pos)
    s=s[:target]+s[target:].replace(old,repl(cond),1)
    p.write_text(s)
PY

for arm in baseline gap2 ratio15 ratio2 long6 ratio15long6; do
  cd "/tmp/v3si-$arm"
  cargo test --release --locked
  RUSTFLAGS='-C target-cpu=x86-64' cargo build --release --locked
  cp target/release/sokonanoda "/tmp/v3si-bin-$arm"
done

cat >/tmp/checker-v3si.json <<'EOF'
{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":4,"print_success_message":false}
EOF

git clone --depth 1 https://github.com/leanprover/lean-kernel-arena /tmp/arena-v3si
cd /tmp/arena-v3si
nix develop -c ./lka.py build-test mathlib

: > /tmp/v3-shared-invariant-times.tsv
measure () {
  local arm=$1 rep=$2
  /usr/bin/time -q -f '%e' -o /tmp/tv3si.txt "/tmp/v3si-bin-$arm" /tmp/checker-v3si.json < _build/tests/mathlib.ndjson >/tmp/${arm}-${rep}.out 2>/tmp/${arm}-${rep}.err
  printf '%s\t%s\t%s\n' "$arm" "$rep" "$(tail -n 1 /tmp/tv3si.txt)" >> /tmp/v3-shared-invariant-times.tsv
}
orders=(
"baseline gap2 ratio15 ratio2 long6 ratio15long6"
"ratio15long6 long6 ratio2 ratio15 gap2 baseline"
"ratio2 baseline long6 gap2 ratio15long6 ratio15"
)
rep=0
for order in "${orders[@]}"; do
  rep=$((rep+1))
  for arm in $order; do measure "$arm" "$rep"; done
done

python3 - <<'PY' | tee /tmp/v3-shared-invariant-decision.txt
import csv, statistics
from collections import defaultdict
r=defaultdict(list)
with open('/tmp/v3-shared-invariant-times.tsv') as f:
    for a,rep,x in csv.reader(f,delimiter='\t'): r[a].append(float(x))
arms=['baseline','gap2','ratio15','ratio2','long6','ratio15long6']
med={a:statistics.median(r[a]) for a in arms}
b=med['baseline']; g=med['gap2']
print('MATHLIB_MEDIANS_SECONDS')
for a in arms:
    print(f'{a:13s} {med[a]:.3f} ratio={med[a]/b:.6f} delta={(med[a]/b-1)*100:+.3f}% reps={r[a]}')
win=min((med[a],a) for a in arms if a!='baseline')[1]
print('BEST',win)
print('BEST_VS_BASELINE_PCT',(med[win]/b-1)*100)
print('BEST_VS_GAP2_PCT',(med[win]/g-1)*100)
if med[win] <= 0.98*g:
    print('JUMP_DECISION=MATERIAL_JUMP_OVER_GAP2')
elif med[win] < g:
    print('JUMP_DECISION=SMALL_IMPROVEMENT_OVER_GAP2')
else:
    print('JUMP_DECISION=NO_JUMP_OVER_GAP2')
PY

WINNER=$(python3 - <<'PY'
import csv,statistics
from collections import defaultdict
r=defaultdict(list)
with open('/tmp/v3-shared-invariant-times.tsv') as f:
  for a,rep,x in csv.reader(f,delimiter='\t'): r[a].append(float(x))
med={a:statistics.median(v) for a,v in r.items()}
g=med['gap2']
cs=[(v,a) for a,v in med.items() if a not in ('baseline','gap2')]
v,a=min(cs)
print(a if v <= .98*g else '')
PY
)

: > /tmp/v3-shared-invariant-semantic-gate.txt
if [ -n "$WINNER" ]; then
  nix develop -c ./lka.py build-test
  while IFS= read -r f; do
    bstatus=0; wstatus=0
    timeout 120 /tmp/v3si-bin-baseline /tmp/checker-v3si.json < "$f" >/tmp/base-v3si.out 2>/tmp/base-v3si.err || bstatus=$?
    timeout 120 "/tmp/v3si-bin-$WINNER" /tmp/checker-v3si.json < "$f" >/tmp/win-v3si.out 2>/tmp/win-v3si.err || wstatus=$?
    if [ "$bstatus" -ne "$wstatus" ]; then
      printf 'MISMATCH\t%s\tbase=%s\twinner=%s\n' "$f" "$bstatus" "$wstatus" | tee -a /tmp/v3-shared-invariant-semantic-gate.txt
      exit 1
    fi
    printf 'MATCH\t%s\tstatus=%s\n' "$f" "$bstatus" >> /tmp/v3-shared-invariant-semantic-gate.txt
  done < <(find _build/tests -type f -name '*.ndjson' | sort)
  echo "RECURSIVE_SEMANTIC_GATE_PASS winner=$WINNER" | tee -a /tmp/v3-shared-invariant-semantic-gate.txt
else
  echo 'RECURSIVE_SEMANTIC_GATE_SKIPPED no >=2% jump over gap2' > /tmp/v3-shared-invariant-semantic-gate.txt
fi

cp /tmp/v3-shared-invariant-times.tsv "$GITHUB_WORKSPACE"/
cp /tmp/v3-shared-invariant-decision.txt "$GITHUB_WORKSPACE"/
cp /tmp/v3-shared-invariant-semantic-gate.txt "$GITHUB_WORKSPACE"/
