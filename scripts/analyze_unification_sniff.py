from pathlib import Path
import json, re, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'results/unification-obligation-v1')
kind_names = ['Rigid','Unfold','Lam','Pi','Sort','NatLit','StrLit','Thunk']

def parse_sniff(path):
    c = {}
    pairs = []
    for line in path.read_text(errors='replace').splitlines():
        if line.startswith('MG_UNIFY_SNIFF '):
            k,v = line.split(' ',1)[1].split('=',1)
            c[k] = int(v)
        elif line.startswith('MG_UNIFY_PAIR '):
            _,_,i,j,n = line.split()
            pairs.append((int(n), int(i), int(j)))
    return c, pairs

def parse_summary(path):
    for line in path.read_text(errors='replace').splitlines():
        if line.startswith('summary:'):
            return int(line.split(':',1)[1].strip().split()[0])
    return 0

def parse_annotate(path):
    rows=[]
    rx=re.compile(r'^\s*([0-9,]+)\s+\(([0-9.]+)%\)\s+(.*)$')
    for line in path.read_text(errors='replace').splitlines():
        m=rx.match(line)
        if m:
            rows.append({'instructions':int(m.group(1).replace(',','')),'percent':float(m.group(2)),'symbol':m.group(3).strip()})
    return rows

work=[]
for sniff in sorted(root.glob('sniff.*.stderr')):
    tag=sniff.stem.split('.',1)[1]
    cg=root/f'callgrind.{tag}.out'
    ann_self=root/f'annotate-self.{tag}.txt'
    ann_inc=root/f'annotate-inclusive.{tag}.txt'
    counters,pairs=parse_sniff(sniff)
    total=parse_summary(cg) if cg.exists() else 0
    self_rows=parse_annotate(ann_self) if ann_self.exists() else []
    inc_rows=parse_annotate(ann_inc) if ann_inc.exists() else []
    def find(rows, needle):
        xs=[r for r in rows if needle in r['symbol']]
        return max(xs,key=lambda r:r['instructions']) if xs else None
    no_cache_self=find(self_rows,'unify_no_cache')
    direct_inc=find(inc_rows,'sniff_direct_route')
    cold_inc=find(inc_rows,'sniff_cold_route')
    nat_inc=find(inc_rows,'sniff_nat_route')
    enter=max(1,counters.get('unify_enter',0)); nc=max(1,counters.get('no_cache_enter',0))
    cacheable=counters.get('cacheable',0)
    cache_hits=counters.get('uf_hit',0)+counters.get('neg_hit',0)+counters.get('neg_probe_hit',0)
    pair_top=[]
    for n,i,j in sorted(pairs, reverse=True)[:12]:
        pair_top.append({'left':kind_names[i],'right':kind_names[j],'count':n,'fraction_no_cache':n/nc})
    rec={
        'workload':tag,'total_instructions':total,'counters':counters,
        'shares':{
            'ptr_equal_of_unify':counters.get('ptr_eq',0)/enter,
            'force_left_changed_of_unify':counters.get('force_left_changed',0)/enter,
            'force_right_changed_of_unify':counters.get('force_right_changed',0)/enter,
            'cacheable_of_post_ptr':cacheable/max(1,cacheable+counters.get('noncacheable',0)),
            'cache_hit_of_cacheable':cache_hits/max(1,cacheable),
            'nat_decided_of_no_cache':counters.get('nat_decided',0)/nc,
            'direct_true_of_no_cache':counters.get('direct_true',0)/nc,
            'cold_enter_of_no_cache':counters.get('cold_enter',0)/nc,
        },
        'profile':{
            'unify_no_cache_self':no_cache_self,
            'nat_route_inclusive':nat_inc,
            'direct_route_inclusive':direct_inc,
            'cold_route_inclusive':cold_inc,
        },
        'top_pairs':pair_top,
    }
    # Sniff-test verdicts: these are discovery thresholds, not admission thresholds.
    tests={}
    tests['S1_hot_self'] = bool(no_cache_self and no_cache_self['percent'] >= 3.0)
    tests['S2_cold_dominant'] = rec['shares']['cold_enter_of_no_cache'] >= 0.25
    tests['S3_cache_headroom'] = cacheable >= 1000 and rec['shares']['cache_hit_of_cacheable'] < 0.35
    tests['S4_force_headroom'] = max(rec['shares']['force_left_changed_of_unify'],rec['shares']['force_right_changed_of_unify']) >= 0.05
    tests['S5_pair_concentration'] = bool(pair_top and pair_top[0]['fraction_no_cache'] >= 0.20)
    tests['S6_route_mass'] = any(r and r['percent'] >= 3.0 for r in (nat_inc,direct_inc,cold_inc))
    rec['sniff_tests']=tests
    work.append(rec)

# Cross-workload tests.
for rec in work:
    rec['sniff_tests']['S7_source_distinct_recurrence'] = False
for i,a in enumerate(work):
    for b in work[i+1:]:
        amap={(p['left'],p['right']) for p in a['top_pairs'][:5] if p['fraction_no_cache']>=0.05}
        bmap={(p['left'],p['right']) for p in b['top_pairs'][:5] if p['fraction_no_cache']>=0.05}
        if amap & bmap:
            a['sniff_tests']['S7_source_distinct_recurrence']=True
            b['sniff_tests']['S7_source_distinct_recurrence']=True

# Rank candidate abstraction changes by actual inclusive route mass when available.
candidates=[]
for r in work:
    for name,key in [('NAT_SPECIALIZE','nat_route_inclusive'),('DIRECT_SPECIALIZE','direct_route_inclusive'),('COLD_REWRITE','cold_route_inclusive')]:
        row=r['profile'][key]
        if row:
            candidates.append({'workload':r['workload'],'candidate':name,'inclusive_percent':row['percent'],'instructions':row['instructions']})
    row=r['profile']['unify_no_cache_self']
    if row:
        candidates.append({'workload':r['workload'],'candidate':'NO_CACHE_DISPATCH_OVERHEAD','inclusive_percent':row['percent'],'instructions':row['instructions']})
candidates.sort(key=lambda x:x['inclusive_percent'],reverse=True)

# Rewrite license: high route mass + concentrated semantic phenotype OR high mass recurring across workloads.
rewrite=[]
for r in work:
    pm=max([x['percent'] for x in r['profile'].values() if x] or [0.0])
    concentrated=r['sniff_tests']['S5_pair_concentration']
    recurring=r['sniff_tests']['S7_source_distinct_recurrence']
    if pm>=5.0 and (concentrated or recurring):
        rewrite.append({'workload':r['workload'],'max_profile_percent':pm,'pair_concentrated':concentrated,'source_distinct_recurrence':recurring})

out={'workloads':work,'ranked_candidates':candidates[:20],'rewrite_signals':rewrite}
(root/'unification_sniff_report.json').write_text(json.dumps(out,indent=2,sort_keys=True))
print(json.dumps({'ranked_candidates':candidates[:10],'rewrite_signals':rewrite,'workload_sniff_tests':{r['workload']:r['sniff_tests'] for r in work}},indent=2))
