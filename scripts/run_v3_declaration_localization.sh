#!/usr/bin/env bash
set -euxo pipefail
V2=3d7585c21242f29fdaa48ae9a16e16c6afe42238
OUT="$GITHUB_WORKSPACE/v3-declaration-localization"
rm -rf "$OUT" /tmp/mgv3-src /tmp/mgv3-baseline /tmp/mgv3-ratio15 /tmp/arena-v3
mkdir -p "$OUT"

git clone https://github.com/metalogiclabs/mathgraph-lean-kernel.git /tmp/mgv3-src
cd /tmp/mgv3-src
git checkout "$V2"
git worktree add /tmp/mgv3-baseline "$V2"
git worktree add /tmp/mgv3-ratio15 "$V2"

# Frozen exploratory ratio15 rule: do not tune this during localization.
python3 - <<'PY'
from pathlib import Path
p=Path('/tmp/mgv3-ratio15/src/conv.rs')
s=p.read_text()
old='''                    } else {\n                        self.unfold_pair(depth, t, t2)\n                    }\n'''
new='''                    } else {\n                        let lx = sx.len();\n                        let ly = sy.len();\n                        let gap = if lx >= ly { lx - ly } else { ly - lx };\n                        let shorter = lx.min(ly);\n                        let longer = lx.max(ly);\n                        if gap >= 2 && (longer * 2 >= shorter * 3) {\n                            if lx <= ly {\n                                let v1 = self.unfold_value(depth, t);\n                                if !std::ptr::eq(v1, t) { return self.unify::<true>(depth, v1, t2); }\n                                let v2 = self.unfold_value(depth, t2);\n                                if !std::ptr::eq(v2, t2) { return self.unify::<true>(depth, t, v2); }\n                            } else {\n                                let v2 = self.unfold_value(depth, t2);\n                                if !std::ptr::eq(v2, t2) { return self.unify::<true>(depth, t, v2); }\n                                let v1 = self.unfold_value(depth, t);\n                                if !std::ptr::eq(v1, t) { return self.unify::<true>(depth, v1, t2); }\n                            }\n                        }\n                        self.unfold_pair(depth, t, t2)\n                    }\n'''
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

# Locate actual exported declaration boundaries. The NDJSON specification makes
# axiom/def/opaque/thm/quot/inductive top-level declaration records.
LC_ALL=C grep -n -E '^\{"(axiom|def|opaque|thm|quot|inductive)"' "$M" > "$OUT/declarations.raw" || true
python3 - "$OUT/declarations.raw" "$OUT/checkpoints.tsv" <<'PY'
import re,sys
src,dst=sys.argv[1:]
rows=[]
pat=re.compile(r'^(\d+):\{"(axiom|def|opaque|thm|quot|inductive)"')
with open(src, errors='replace') as f:
    for line in f:
        m=pat.match(line)
        if m: rows.append((int(m.group(1)),m.group(2)))
if not rows:
    raise SystemExit('NO_DECLARATIONS_FOUND')
pcts=[1,3,5,8,10,15,20,30,50,75,100]
with open(dst,'w') as o:
    o.write('pct\tdecl_index\tline\tkind\ttotal_decls\n')
    n=len(rows)
    for pct in pcts:
        i=max(0,min(n-1,(n*pct+99)//100-1))
        line,kind=rows[i]
        o.write(f'{pct}\t{i+1}\t{line}\t{kind}\t{n}\n')
print('DECLARATIONS',len(rows))
PY
cat "$OUT/checkpoints.tsv"

: > "$OUT/paired-times.tsv"
printf 'pct\trep\tarm\tseconds\tboundary_line\n' >> "$OUT/paired-times.tsv"
measure () {
  local arm=$1 pct=$2 rep=$3 n=$4
  # time only the checker; head is an identical producer for both arms.
  set +o pipefail
  head -n "$n" "$M" | /usr/bin/time -q -f '%e' -o /tmp/v3-time.txt "/tmp/mgv3-bin-$arm" /tmp/checker-v3.json >/tmp/v3-${arm}-${pct}-${rep}.out 2>/tmp/v3-${arm}-${pct}-${rep}.err
  rc=${PIPESTATUS[1]}
  set -o pipefail
  if [ "$rc" -ne 0 ]; then
    echo "CHECKER_FAILED arm=$arm pct=$pct rep=$rep rc=$rc" >&2
    cat /tmp/v3-${arm}-${pct}-${rep}.err >&2 || true
    exit "$rc"
  fi
  printf '%s\t%s\t%s\t%s\t%s\n' "$pct" "$rep" "$arm" "$(tail -n1 /tmp/v3-time.txt)" "$n" >> "$OUT/paired-times.tsv"
}

tail -n +2 "$OUT/checkpoints.tsv" | while IFS=$'\t' read -r pct declidx line kind total; do
  for rep in 1 2 3; do
    if (( rep % 2 == 1 )); then
      measure baseline "$pct" "$rep" "$line"
      measure ratio15 "$pct" "$rep" "$line"
    else
      measure ratio15 "$pct" "$rep" "$line"
      measure baseline "$pct" "$rep" "$line"
    fi
  done
done

python3 - "$OUT/paired-times.tsv" "$OUT/checkpoints.tsv" "$OUT/summary.tsv" "$OUT/decision.txt" <<'PY'
import csv,statistics,sys
from collections import defaultdict
times,ck,summary,decision=sys.argv[1:]
r=defaultdict(lambda:defaultdict(list))
paired=defaultdict(dict)
with open(times) as f:
    for row in csv.DictReader(f,delimiter='\t'):
        pct=int(row['pct']); rep=int(row['rep']); arm=row['arm']; x=float(row['seconds'])
        r[pct][arm].append(x); paired[(pct,rep)][arm]=x
meta={}
with open(ck) as f:
    for row in csv.DictReader(f,delimiter='\t'): meta[int(row['pct'])]=row
rows=[]
prev=None
for pct in sorted(r):
    b=statistics.median(r[pct]['baseline']); g=statistics.median(r[pct]['ratio15'])
    d=(g/b-1)*100
    pd=statistics.median([(paired[(pct,k)]['ratio15']/paired[(pct,k)]['baseline']-1)*100 for k in (1,2,3)])
    if prev is None: inc_b=b; inc_g=g
    else: inc_b=b-prev[1]; inc_g=g-prev[2]
    inc_delta=inc_g-inc_b
    rows.append((pct,int(meta[pct]['decl_index']),int(meta[pct]['line']),meta[pct]['kind'],b,g,d,pd,inc_b,inc_g,inc_delta))
    prev=(pct,b,g)
with open(summary,'w') as o:
    o.write('pct\tdecl_index\tline\tkind\tbaseline_median\tratio15_median\tdelta_pct\tpaired_delta_median_pct\tbaseline_increment\tratio15_increment\tincremental_excess_seconds\n')
    for x in rows:o.write('\t'.join(map(str,x))+'\n')
best=min(rows,key=lambda x:x[7]); worst=max(rows,key=lambda x:x[7])
# Find the first checkpoint at which the cumulative paired effect ceases to be beneficial.
cross=next((x for x in rows if x[7] >= 0),None)
with open(decision,'w') as o:
    o.write('V3_DECLARATION_LOCALIZATION\n')
    o.write(f'best_checkpoint_pct {best[0]} paired_delta_pct {best[7]:.4f} decl_index {best[1]} line {best[2]} kind {best[3]}\n')
    o.write(f'worst_checkpoint_pct {worst[0]} paired_delta_pct {worst[7]:.4f}\n')
    if cross:o.write(f'benefit_crosses_zero_by_pct {cross[0]} decl_index {cross[1]} line {cross[2]} kind {cross[3]}\n')
    else:o.write('benefit_crosses_zero_by_pct NONE\n')
    o.write('RESIDUAL=DECLARATION_REGION_LOCALIZED\n')
print(open(summary).read())
print(open(decision).read())
PY
