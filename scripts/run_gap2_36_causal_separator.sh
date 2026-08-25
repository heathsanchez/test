#!/usr/bin/env bash
set -euxo pipefail
V2=3d7585c21242f29fdaa48ae9a16e16c6afe42238
rm -rf /tmp/mg36-src /tmp/mg36-* /tmp/arena36

git clone https://github.com/metalogiclabs/mathgraph-lean-kernel.git /tmp/mg36-src
cd /tmp/mg36-src
git checkout "$V2"
for arm in baseline gap2 only36 not36; do
  git worktree add "/tmp/mg36-$arm" "$V2"
done

python3 - <<'PY'
from pathlib import Path
old='''                    } else {\n                        self.unfold_pair(depth, t, t2)\n                    }\n'''

def repl(cond):
    return f'''                    }} else {{\n                        let lx = sx.len();\n                        let ly = sy.len();\n                        let gap = if lx >= ly {{ lx - ly }} else {{ ly - lx }};\n                        let shorter = lx.min(ly);\n                        let longer = lx.max(ly);\n                        if {cond} {{\n                            if lx <= ly {{\n                                let v1 = self.unfold_value(depth, t);\n                                if !std::ptr::eq(v1, t) {{ return self.unify::<true>(depth, v1, t2); }}\n                                let v2 = self.unfold_value(depth, t2);\n                                if !std::ptr::eq(v2, t2) {{ return self.unify::<true>(depth, t, v2); }}\n                            }} else {{\n                                let v2 = self.unfold_value(depth, t2);\n                                if !std::ptr::eq(v2, t2) {{ return self.unify::<true>(depth, t, v2); }}\n                                let v1 = self.unfold_value(depth, t);\n                                if !std::ptr::eq(v1, t) {{ return self.unify::<true>(depth, v1, t2); }}\n                            }}\n                        }}\n                        self.unfold_pair(depth, t, t2)\n                    }}\n'''

conds={
 'gap2':'gap >= 2',
 'only36':'gap >= 2 && shorter == 3 && longer == 6',
 'not36':'gap >= 2 && !(shorter == 3 && longer == 6)',
}
for arm,cond in conds.items():
    p=Path(f'/tmp/mg36-{arm}/src/conv.rs')
    s=p.read_text()
    anchor='''                    } else if rh.is_lt(&lh) {'''
    pos=s.index(anchor)
    target=s.index(old,pos)
    s=s[:target]+s[target:].replace(old,repl(cond),1)
    p.write_text(s)
PY

for arm in baseline gap2 only36 not36; do
  cd "/tmp/mg36-$arm"
  cargo test --release --locked
  RUSTFLAGS='-C target-cpu=x86-64' cargo build --release --locked
  cp target/release/sokonanoda "/tmp/mg36-bin-$arm"
done

cat >/tmp/checker36.json <<'EOF'
{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":4,"print_success_message":false}
EOF

git clone --depth 1 https://github.com/leanprover/lean-kernel-arena /tmp/arena36
cd /tmp/arena36
nix develop -c ./lka.py build-test mathlib

: > /tmp/gap2-36-times.tsv
measure () {
  local arm=$1 rep=$2
  /usr/bin/time -q -f '%e' -o /tmp/t36.txt "/tmp/mg36-bin-$arm" /tmp/checker36.json < _build/tests/mathlib.ndjson >/tmp/${arm}-${rep}.out 2>/tmp/${arm}-${rep}.err
  printf '%s\t%s\t%s\n' "$arm" "$rep" "$(tail -n 1 /tmp/t36.txt)" >> /tmp/gap2-36-times.tsv
}
orders=(
"baseline gap2 only36 not36"
"not36 only36 gap2 baseline"
"only36 baseline not36 gap2"
)
rep=0
for order in "${orders[@]}"; do
  rep=$((rep+1))
  for arm in $order; do measure "$arm" "$rep"; done
done

python3 - <<'PY' | tee /tmp/gap2-36-decision.txt
import csv, statistics
from collections import defaultdict
r=defaultdict(list)
with open('/tmp/gap2-36-times.tsv') as f:
    for a,rep,x in csv.reader(f,delimiter='\t'): r[a].append(float(x))
arms=['baseline','gap2','only36','not36']
med={a:statistics.median(r[a]) for a in arms}
b=med['baseline']; g=med['gap2']
print('MATHLIB_MEDIANS_SECONDS')
for a in arms:
    print(f'{a:8s} {med[a]:.3f} ratio={med[a]/b:.6f} delta={(med[a]/b-1)*100:+.3f}% reps={r[a]}')
print('ONLY36_VS_GAP2_PCT', (med['only36']/g-1)*100)
print('NOT36_VS_GAP2_PCT', (med['not36']/g-1)*100)
print('ONLY36_VS_NOT36_PCT', (med['only36']/med['not36']-1)*100)
if med['only36'] < b and med['not36'] >= b:
    print('CAUSAL_DECISION=PAIR36_CARRIES_GAIN')
elif med['not36'] < b and med['only36'] >= b:
    print('CAUSAL_DECISION=GAIN_LIVES_OUTSIDE_PAIR36')
elif med['only36'] < med['not36'] and med['only36'] < g:
    print('CAUSAL_DECISION=PAIR36_ENRICHED')
elif med['not36'] < med['only36'] and med['not36'] < g:
    print('CAUSAL_DECISION=PAIR36_NOT_CAUSAL')
else:
    print('CAUSAL_DECISION=NO_CLEAN_SEPARATION')
PY

WINNER=$(python3 - <<'PY'
import csv,statistics
from collections import defaultdict
r=defaultdict(list)
with open('/tmp/gap2-36-times.tsv') as f:
  for a,rep,x in csv.reader(f,delimiter='\t'): r[a].append(float(x))
b=statistics.median(r['baseline'])
cs=[(statistics.median(v),a) for a,v in r.items() if a!='baseline']
v,a=min(cs)
print(a if v <= .99*b else '')
PY
)

: > /tmp/gap2-36-semantic-gate.txt
if [ -n "$WINNER" ]; then
  nix develop -c ./lka.py build-test
  while IFS= read -r f; do
    bstatus=0; wstatus=0
    timeout 120 /tmp/mg36-bin-baseline /tmp/checker36.json < "$f" >/tmp/base36.out 2>/tmp/base36.err || bstatus=$?
    timeout 120 "/tmp/mg36-bin-$WINNER" /tmp/checker36.json < "$f" >/tmp/win36.out 2>/tmp/win36.err || wstatus=$?
    if [ "$bstatus" -ne "$wstatus" ]; then
      printf 'MISMATCH\t%s\tbase=%s\twinner=%s\n' "$f" "$bstatus" "$wstatus" | tee -a /tmp/gap2-36-semantic-gate.txt
      exit 1
    fi
    printf 'MATCH\t%s\tstatus=%s\n' "$f" "$bstatus" >> /tmp/gap2-36-semantic-gate.txt
  done < <(find _build/tests -maxdepth 1 -type f -name '*.ndjson' | sort)
  echo "SEMANTIC_GATE_PASS winner=$WINNER" | tee -a /tmp/gap2-36-semantic-gate.txt
else
  echo 'SEMANTIC_GATE_SKIPPED no >=1% Mathlib winner' > /tmp/gap2-36-semantic-gate.txt
fi

cp /tmp/gap2-36-times.tsv "$GITHUB_WORKSPACE"/
cp /tmp/gap2-36-decision.txt "$GITHUB_WORKSPACE"/
cp /tmp/gap2-36-semantic-gate.txt "$GITHUB_WORKSPACE"/
