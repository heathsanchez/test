#!/usr/bin/env bash
set -euxo pipefail
V2=3d7585c21242f29fdaa48ae9a16e16c6afe42238
OUT="$GITHUB_WORKSPACE/v3-hint-separator"
rm -rf "$OUT" /tmp/v3h-* /tmp/arena-v3h
mkdir -p "$OUT"

git clone https://github.com/metalogiclabs/mathgraph-lean-kernel.git /tmp/v3h-src
cd /tmp/v3h-src
git checkout "$V2"
for arm in baseline all regular regle8 reg9to32 reggt32 nonregular; do
  git worktree add "/tmp/v3h-$arm" "$V2"
done

python3 - <<'PY'
from pathlib import Path
arms={
'all':'true',
'regular':'matches!((lh, rh), (crate::env::ReducibilityHint::Regular(a), crate::env::ReducibilityHint::Regular(b)) if a == b)',
'regle8':'matches!((lh, rh), (crate::env::ReducibilityHint::Regular(a), crate::env::ReducibilityHint::Regular(b)) if a == b && a <= 8)',
'reg9to32':'matches!((lh, rh), (crate::env::ReducibilityHint::Regular(a), crate::env::ReducibilityHint::Regular(b)) if a == b && a >= 9 && a <= 32)',
'reggt32':'matches!((lh, rh), (crate::env::ReducibilityHint::Regular(a), crate::env::ReducibilityHint::Regular(b)) if a == b && a > 32)',
'nonregular':'matches!((lh, rh), (crate::env::ReducibilityHint::Abbrev, crate::env::ReducibilityHint::Abbrev) | (crate::env::ReducibilityHint::Opaque, crate::env::ReducibilityHint::Opaque))',
}
old='''                    } else {\n                        self.unfold_pair(depth, t, t2)\n                    }\n'''
anchor='''                    } else if rh.is_lt(&lh) {'''
for arm,gate in arms.items():
    p=Path(f'/tmp/v3h-{arm}/src/conv.rs')
    s=p.read_text()
    pos=s.index(anchor)
    target=s.index(old,pos)
    new=f'''                    }} else {{\n                        let lx = sx.len();\n                        let ly = sy.len();\n                        let gap = if lx >= ly {{ lx - ly }} else {{ ly - lx }};\n                        let shorter = lx.min(ly);\n                        let longer = lx.max(ly);\n                        let class_gate = {gate};\n                        if class_gate && gap >= 2 && (longer * 2 >= shorter * 3) {{\n                            if lx <= ly {{\n                                let v1 = self.unfold_value(depth, t);\n                                if !std::ptr::eq(v1, t) {{ return self.unify::<true>(depth, v1, t2); }}\n                                let v2 = self.unfold_value(depth, t2);\n                                if !std::ptr::eq(v2, t2) {{ return self.unify::<true>(depth, t, v2); }}\n                            }} else {{\n                                let v2 = self.unfold_value(depth, t2);\n                                if !std::ptr::eq(v2, t2) {{ return self.unify::<true>(depth, t, v2); }}\n                                let v1 = self.unfold_value(depth, t);\n                                if !std::ptr::eq(v1, t) {{ return self.unify::<true>(depth, v1, t2); }}\n                            }}\n                        }}\n                        self.unfold_pair(depth, t, t2)\n                    }}\n'''
    s=s[:target]+s[target:].replace(old,new,1)
    p.write_text(s)
PY

for arm in baseline all regular regle8 reg9to32 reggt32 nonregular; do
  cd "/tmp/v3h-$arm"
  RUSTFLAGS='-C target-cpu=x86-64' cargo build --release --locked
  cp target/release/sokonanoda "/tmp/v3h-bin-$arm"
done

cat >/tmp/checker-v3h.json <<'EOF'
{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":4,"print_success_message":false}
EOF

git clone --depth 1 https://github.com/leanprover/lean-kernel-arena /tmp/arena-v3h
cd /tmp/arena-v3h
nix develop -c ./lka.py build-test mathlib
M=_build/tests/mathlib.ndjson

printf 'rep\tarm\tseconds\n' > "$OUT/times.tsv"
arms=(baseline all regular regle8 reg9to32 reggt32 nonregular)
measure () {
  local arm=$1 rep=$2
  /usr/bin/time -q -f '%e' -o /tmp/v3h-time.txt "/tmp/v3h-bin-$arm" /tmp/checker-v3h.json < "$M" >/tmp/v3h-$arm-$rep.out 2>/tmp/v3h-$arm-$rep.err
  printf '%s\t%s\t%s\n' "$rep" "$arm" "$(tail -n1 /tmp/v3h-time.txt)" >> "$OUT/times.tsv"
}
for rep in 1 2 3; do
  if (( rep % 2 == 1 )); then order=(baseline all regular regle8 reg9to32 reggt32 nonregular); else order=(nonregular reggt32 reg9to32 regle8 regular all baseline); fi
  for arm in "${order[@]}"; do measure "$arm" "$rep"; done
done

python3 - "$OUT/times.tsv" "$OUT/summary.tsv" "$OUT/decision.txt" <<'PY'
import csv,statistics,sys
times,summary,decision=sys.argv[1:]
d={}
with open(times) as f:
    for r in csv.DictReader(f,delimiter='\t'): d.setdefault(r['arm'],[]).append(float(r['seconds']))
med={k:statistics.median(v) for k,v in d.items()}
b=med['baseline']
rows=sorted(((k,v,(v/b-1)*100) for k,v in med.items()),key=lambda x:x[2])
with open(summary,'w') as o:
    o.write('arm\tmedian_seconds\tdelta_vs_baseline_pct\n')
    for r in rows:o.write(f'{r[0]}\t{r[1]}\t{r[2]}\n')
best=rows[0]
with open(decision,'w') as o:
    o.write('V3_HINT_SEPARATOR\n')
    o.write(f'best_arm {best[0]} median {best[1]:.4f} delta_pct {best[2]:.4f}\n')
    if best[0] != 'baseline' and best[2] <= -1.0:o.write('RESIDUAL=STRUCTURAL_HINT_CLASS_CANDIDATE\n')
    else:o.write('RESIDUAL=NO_STABLE_HINT_SEPARATOR\n')
print(open(summary).read()); print(open(decision).read())
PY

# If a structural arm beats baseline by >=1%, preserve semantic evidence on recursive Arena corpus.
WIN=$(awk -F'\t' 'NR>1 && $1!="baseline" && $3<=-1 {print $1; exit}' "$OUT/summary.tsv" || true)
if [ -n "$WIN" ]; then
  nix develop -c ./lka.py build-test all
  python3 - "$WIN" "$OUT/semantic.tsv" <<'PY'
import pathlib,subprocess,sys
win,out=sys.argv[1:]
root=pathlib.Path('_build/tests')
files=sorted(root.rglob('*.ndjson'))
config='/tmp/checker-v3h.json'; base='/tmp/v3h-bin-baseline'; cand=f'/tmp/v3h-bin-{win}'
with open(out,'w') as o:
    o.write('file\tbaseline_rc\tcandidate_rc\n')
    for p in files:
        with p.open('rb') as f: br=subprocess.run([base,config],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
        with p.open('rb') as f: cr=subprocess.run([cand,config],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
        o.write(f'{p}\t{br}\t{cr}\n')
        if br!=cr: raise SystemExit(f'SEMANTIC_MISMATCH {p} {br} {cr}')
print('RECURSIVE_SEMANTIC_GATE_PASS',win,len(files))
PY
fi
