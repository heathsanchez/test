#!/usr/bin/env bash
set -euxo pipefail
V2=3d7585c21242f29fdaa48ae9a16e16c6afe42238
OUT="$GITHUB_WORKSPACE/v3-event-signature"
rm -rf "$OUT" /tmp/v3e-src /tmp/arena-v3e
mkdir -p "$OUT"

git clone https://github.com/metalogiclabs/mathgraph-lean-kernel.git /tmp/v3e-src
cd /tmp/v3e-src
git checkout "$V2"

python3 - <<'PY'
from pathlib import Path
p=Path('src/conv.rs')
s=p.read_text()
s=s.replace('use crate::value::{self, ElimView, Env, RigidHead, Spine, UnfoldHead, Value, E, S, V};', '''use crate::value::{self, ElimView, Env, RigidHead, Spine, UnfoldHead, Value, E, S, V};
use std::sync::atomic::{AtomicU64, Ordering};

static V3_TOTAL: AtomicU64 = AtomicU64::new(0);
static V3_PAIR: [AtomicU64; 256] = [const { AtomicU64::new(0) }; 256];
static V3_DEPTH: [AtomicU64; 16] = [const { AtomicU64::new(0) }; 16];
static V3_HINT: [AtomicU64; 6] = [const { AtomicU64::new(0) }; 6];

#[inline]
fn v3_hint_bucket(h: ReducibilityHint) -> usize {
    match h {
        ReducibilityHint::Regular(n) if n <= 8 => 0,
        ReducibilityHint::Regular(n) if n <= 32 => 1,
        ReducibilityHint::Regular(_) => 2,
        ReducibilityHint::Abbrev => 3,
        ReducibilityHint::Opaque => 4,
    }
}

#[inline]
fn record_v3_event(depth: u32, lx: usize, ly: usize, lh: ReducibilityHint, rh: ReducibilityHint) {
    let shorter = lx.min(ly);
    let longer = lx.max(ly);
    let gap = longer - shorter;
    if gap < 2 || longer * 2 < shorter * 3 { return; }
    V3_TOTAL.fetch_add(1, Ordering::Relaxed);
    let si = shorter.min(15);
    let li = longer.min(15);
    V3_PAIR[si * 16 + li].fetch_add(1, Ordering::Relaxed);
    V3_DEPTH[(depth as usize).min(15)].fetch_add(1, Ordering::Relaxed);
    let hb = if lh == rh { v3_hint_bucket(lh) } else { 5 };
    V3_HINT[hb].fetch_add(1, Ordering::Relaxed);
}

pub fn dump_v3_stats() {
    eprintln!("V3STAT total {}", V3_TOTAL.load(Ordering::Relaxed));
    for s in 0..16 { for l in 0..16 {
        let n=V3_PAIR[s*16+l].load(Ordering::Relaxed);
        if n>0 { eprintln!("V3STAT pair {} {} {}",s,l,n); }
    }}
    for d in 0..16 {
        let n=V3_DEPTH[d].load(Ordering::Relaxed);
        if n>0 { eprintln!("V3STAT depth {} {}",d,n); }
    }
    for h in 0..6 {
        let n=V3_HINT[h].load(Ordering::Relaxed);
        if n>0 { eprintln!("V3STAT hint {} {}",h,n); }
    }
}''')
old='''                    } else {
                        self.unfold_pair(depth, t, t2)
                    }
'''
new='''                    } else {
                        record_v3_event(depth, sx.len(), sy.len(), lh, rh);
                        self.unfold_pair(depth, t, t2)
                    }
'''
anchor='''                    } else if rh.is_lt(&lh) {'''
pos=s.index(anchor)
target=s.index(old,pos)
s=s[:target]+s[target:].replace(old,new,1)
p.write_text(s)

p=Path('src/main.rs')
s=p.read_text()
s=s.replace('''    export_file.check_all_declars();
    // Pretty print as necessary''','''    export_file.check_all_declars();
    if std::env::var_os("MG_V3_STATS").is_some() { sokonanoda::conv::dump_v3_stats(); }
    // Pretty print as necessary''')
p.write_text(s)
PY

RUSTFLAGS='-C target-cpu=x86-64' cargo build --release --locked
cp target/release/sokonanoda /tmp/v3e-bin

cat >/tmp/checker-v3e.json <<'EOF'
{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":4,"print_success_message":false}
EOF

git clone --depth 1 https://github.com/leanprover/lean-kernel-arena /tmp/arena-v3e
cd /tmp/arena-v3e
nix develop -c ./lka.py build-test mathlib
M=_build/tests/mathlib.ndjson

# Declaration boundaries, matching the prior localization experiment.
grep -n -E '^\{"(axiom|def|opaque|thm|quot|inductive)"' "$M" > "$OUT/declarations.raw"
python3 - "$OUT/declarations.raw" "$OUT/checkpoints.tsv" <<'PY'
import re,sys
src,dst=sys.argv[1:]
rows=[]; pat=re.compile(r'^(\d+):')
for x in open(src,errors='replace'):
    m=pat.match(x)
    if m: rows.append(int(m.group(1)))
pcts=[1,10,15,20,30,50,75,100]
n=len(rows)
with open(dst,'w') as o:
    o.write('pct\tdecl_index\tline\ttotal_decls\n')
    for pct in pcts:
        i=max(0,min(n-1,(n*pct+99)//100-1))
        o.write(f'{pct}\t{i+1}\t{rows[i]}\t{n}\n')
print('DECLARATIONS',n)
PY
cat "$OUT/checkpoints.tsv"

# One census per cumulative declaration checkpoint. V2 semantics are unchanged;
# instrumentation counts only events that WOULD activate ratio15.
tail -n +2 "$OUT/checkpoints.tsv" | while IFS=$'\t' read -r pct declidx line total; do
  set +o pipefail
  head -n "$line" "$M" | MG_V3_STATS=1 /tmp/v3e-bin /tmp/checker-v3e.json >/tmp/v3e-${pct}.out 2>"$OUT/stats-${pct}.log"
  rc=${PIPESTATUS[1]}
  set -o pipefail
  if [ "$rc" -ne 0 ]; then
    echo "CHECKER_FAILED pct=$pct rc=$rc" >&2
    tail -200 "$OUT/stats-${pct}.log" >&2 || true
    exit "$rc"
  fi
  grep '^V3STAT ' "$OUT/stats-${pct}.log" > "$OUT/v3stat-${pct}.txt"
done

python3 - "$OUT" <<'PY'
import csv,glob,os,re,sys
out=sys.argv[1]
pcts=[1,10,15,20,30,50,75,100]
def read(p):
    z={'total':0,'pair':{},'depth':{},'hint':{}}
    for line in open(f'{out}/v3stat-{p}.txt'):
        a=line.split()
        if a[1]=='total': z['total']=int(a[2])
        elif a[1]=='pair': z['pair'][(int(a[2]),int(a[3]))]=int(a[4])
        elif a[1]=='depth': z['depth'][int(a[2])]=int(a[3])
        elif a[1]=='hint': z['hint'][int(a[2])]=int(a[3])
    return z
cum={p:read(p) for p in pcts}
with open(f'{out}/band-summary.tsv','w') as o:
    o.write('band\ttotal_events\ttop_pair\ttop_pair_share\ttop_depth\ttop_depth_share\ttop_hint\ttop_hint_share\n')
    prev=None
    for p in pcts:
        cur=cum[p]
        if prev is None:
            lo=0; base={'total':0,'pair':{},'depth':{},'hint':{}}
        else:
            lo=prev; base=cum[prev]
        def diff(kind):
            keys=set(cur[kind])|set(base[kind]); return {k:cur[kind].get(k,0)-base[kind].get(k,0) for k in keys}
        total=cur['total']-base['total']; pairs=diff('pair'); depths=diff('depth'); hints=diff('hint')
        top_pair=max(pairs.items(),key=lambda kv:kv[1]) if pairs else (('', ''),0)
        top_depth=max(depths.items(),key=lambda kv:kv[1]) if depths else ('',0)
        top_hint=max(hints.items(),key=lambda kv:kv[1]) if hints else ('',0)
        share=lambda n: (100*n/total if total else 0)
        o.write(f'{lo}-{p}\t{total}\t{top_pair[0]}\t{share(top_pair[1]):.3f}\t{top_depth[0]}\t{share(top_depth[1]):.3f}\t{top_hint[0]}\t{share(top_hint[1]):.3f}\n')
        # Long-form band features for downstream separator synthesis.
        with open(f'{out}/band-{lo}-{p}.tsv','w') as b:
            b.write('feature\tkey\tcount\tshare_pct\n')
            for kind,d in [('pair',pairs),('depth',depths),('hint',hints)]:
                for k,n in sorted(d.items(), key=lambda kv:(-kv[1],str(kv[0]))):
                    b.write(f'{kind}\t{k}\t{n}\t{share(n):.6f}\n')
        prev=p
print(open(f'{out}/band-summary.tsv').read())
# Compare known good (0-20 plus 75-100) against bad (20-30 plus 50-75)
# by feature enrichment, pooling incremental counts.
def band(lo,hi,kind):
    a=cum[hi][kind]; b={} if lo==0 else cum[lo][kind]
    return {k:a.get(k,0)-b.get(k,0) for k in set(a)|set(b)}
def pool(bands,kind):
    r={}
    for lo,hi in bands:
        for k,v in band(lo,hi,kind).items(): r[k]=r.get(k,0)+v
    return r
good=[(0,20),(75,100)]; bad=[(20,30),(50,75)]
with open(f'{out}/enrichment.tsv','w') as o:
    o.write('feature\tkey\tgood_count\tbad_count\tgood_share\tbad_share\tenrichment\n')
    for kind in ('pair','depth','hint'):
        g=pool(good,kind); b=pool(bad,kind); G=sum(g.values()) or 1; B=sum(b.values()) or 1
        rows=[]
        for k in set(g)|set(b):
            gs=g.get(k,0)/G; bs=b.get(k,0)/B
            enr=(gs+1e-12)/(bs+1e-12)
            rows.append((enr,k,g.get(k,0),b.get(k,0),gs,bs))
        for enr,k,gc,bc,gs,bs in sorted(rows,reverse=True):
            o.write(f'{kind}\t{k}\t{gc}\t{bc}\t{gs:.8f}\t{bs:.8f}\t{enr:.5f}\n')
print('TOP ENRICHMENTS')
for line in open(f'{out}/enrichment.tsv').read().splitlines()[:25]: print(line)
PY
