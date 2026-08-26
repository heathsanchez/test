#!/usr/bin/env bash
set -euxo pipefail
V2=3d7585c21242f29fdaa48ae9a16e16c6afe42238
OUT="$GITHUB_WORKSPACE/v3-final-short1"
rm -rf "$OUT" /tmp/v3s-base /tmp/v3s-lit /tmp/v3s-gen /tmp/arena-v3s
mkdir -p "$OUT"

build_arm() {
  arm="$1"; dst="$2"
  git clone --quiet https://github.com/metalogiclabs/mathgraph-lean-kernel.git "$dst"
  cd "$dst"
  git checkout --quiet "$V2"
  if [ "$arm" != baseline ]; then
    ARM="$arm" python3 - <<'PY'
from pathlib import Path
import os
arm=os.environ['ARM']
p=Path('src/conv.rs')
s=p.read_text()
old='''                    } else {
                        self.unfold_pair(depth, t, t2)
                    }
'''
if arm=='literal':
    cond='''let (a,b)=(sx.len().min(sy.len()), sx.len().max(sy.len()));
                        a == 1 && (b == 3 || b == 4 || b == 6)'''
elif arm=='general':
    cond='''let (a,b)=(sx.len().min(sy.len()), sx.len().max(sy.len()));
                        a == 1 && b >= 3'''
else: raise SystemExit(arm)
new=f'''                    }} else {{
                        {cond};
                        if a == 1 && ''' + ('''(b == 3 || b == 4 || b == 6)''' if arm=='literal' else '''b >= 3''') + ''' {
                            if sx.len() < sy.len() {
                                let v1 = self.unfold_value(depth, t);
                                if !std::ptr::eq(v1, t) { return self.unify::<true>(depth, v1, t2); }
                                let v2 = self.unfold_value(depth, t2);
                                if !std::ptr::eq(v2, t2) { return self.unify::<true>(depth, t, v2); }
                            } else if sy.len() < sx.len() {
                                let v2 = self.unfold_value(depth, t2);
                                if !std::ptr::eq(v2, t2) { return self.unify::<true>(depth, t, v2); }
                                let v1 = self.unfold_value(depth, t);
                                if !std::ptr::eq(v1, t) { return self.unify::<true>(depth, v1, t2); }
                            }
                        }
                        self.unfold_pair(depth, t, t2)
                    }
'''
anchor='''                    } else if rh.is_lt(&lh) {'''
pos=s.index(anchor)
target=s.index(old,pos)
s=s[:target]+s[target:].replace(old,new,1)
p.write_text(s)
PY
  fi
  cargo test --locked
  RUSTFLAGS='-C target-cpu=x86-64' cargo build --release --locked
  cp target/release/sokonanoda "/tmp/v3s-${arm}-bin"
}

build_arm baseline /tmp/v3s-base
build_arm literal /tmp/v3s-lit
build_arm general /tmp/v3s-gen

cat >/tmp/checker-v3s.json <<'EOF'
{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":4,"print_success_message":false}
EOF

git clone --depth 1 https://github.com/leanprover/lean-kernel-arena /tmp/arena-v3s
cd /tmp/arena-v3s
nix develop -c ./lka.py build-test mathlib
M=_build/tests/mathlib.ndjson

# Warm each binary once, then five alternating paired repetitions.
for arm in baseline literal general; do
  "/tmp/v3s-${arm}-bin" /tmp/checker-v3s.json < "$M" >/dev/null
 done
: > "$OUT/timings.tsv"
echo -e 'rep\tarm\tseconds\trc' >> "$OUT/timings.tsv"
run_one() {
  rep="$1"; arm="$2"
  set +e
  t=$(/usr/bin/time -f '%e' "/tmp/v3s-${arm}-bin" /tmp/checker-v3s.json < "$M" >/dev/null 2>"/tmp/t-${rep}-${arm}.txt")
  rc=$?
  set -e
  sec=$(tail -n1 "/tmp/t-${rep}-${arm}.txt")
  echo -e "$rep\t$arm\t$sec\t$rc" | tee -a "$OUT/timings.tsv"
  [ "$rc" -eq 0 ]
}
for rep in 1 2 3 4 5; do
  if [ $((rep%2)) -eq 1 ]; then order='baseline literal general'; else order='general literal baseline'; fi
  for arm in $order; do run_one "$rep" "$arm"; done
 done

python3 - "$OUT/timings.tsv" "$OUT/decision.txt" <<'PY'
import csv,statistics,sys
src,dst=sys.argv[1:]
d={}
for r in csv.DictReader(open(src),delimiter='\t'):
    d.setdefault(r['arm'],[]).append(float(r['seconds']))
med={k:statistics.median(v) for k,v in d.items()}
b=med['baseline']
gain={k:100*(b-v)/b for k,v in med.items() if k!='baseline'}
for k in ('baseline','literal','general'):
    print(k, d[k], 'median', med[k])
for k,v in gain.items(): print('GAIN',k,f'{v:.4f}%')
w=max(gain,key=gain.get)
qualified=gain[w] >= 1.0
with open(dst,'w') as o:
    o.write(f'baseline_median={b:.6f}\n')
    for k in ('literal','general'): o.write(f'{k}_median={med[k]:.6f}\n{k}_gain_pct={gain[k]:.6f}\n')
    o.write(f'winner={w}\nwinner_gain_pct={gain[w]:.6f}\n')
    o.write('V3_SHORT1_DECISION=' + ('PERF_QUALIFIED' if qualified else 'NO_REPRODUCIBLE_GAIN') + '\n')
print(open(dst).read())
if not qualified: raise SystemExit(2)
PY
