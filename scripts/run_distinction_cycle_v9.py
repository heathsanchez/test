#!/usr/bin/env python3
from pathlib import Path
from itertools import combinations
import json, os, re, shutil, subprocess

root = Path.cwd()
out = root / 'results/distinction-cycle-v9'
out.mkdir(parents=True, exist_ok=True)
TRACE = root / 'trace'
ARENA = root / 'arena-tests'
CFG = '{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":1}\n'

FAMILIES = ['INFER_APP', 'PROJECTION', 'IOTA', 'UNFOLD']
# Frozen before outcome inspection: first case per family is development, second is source-distinct protected evaluation.
SELECTED = {
    'INFER_APP': ['good/tutorial/016_levelParams.ndjson', 'good/tutorial/037_andType.ndjson'],
    'PROJECTION': ['good/perf/grind-ring-5.ndjson', 'good/tutorial/084_PSigma.snd.ndjson'],
    'IOTA': ['good/perf/grind-ring-5.ndjson', 'good/undecidability/alg-conv-trans-acc-right.ndjson'],
    'UNFOLD': ['good/perf/grind-ring-5.ndjson', 'good/undecidability/alg-conv-trans-acc-right.ndjson'],
}
BINARY_ORDER = FAMILIES[:]

# Frozen generic candidate distinctions over the terminal structured event.
CANDIDATES = [
    ('site=infer.proj', lambda e: e.get('site') == 'infer.proj'),
    ('site=conv.recursor', lambda e: e.get('site') == 'conv.recursor'),
    ('site=conv.unfold_pair', lambda e: e.get('site') == 'conv.unfold_pair'),
    ('site=infer.app_arg', lambda e: e.get('site') == 'infer.app_arg'),
    ('kind=projection', lambda e: e.get('kind') == 'projection'),
    ('kind=iota', lambda e: e.get('kind') in ('iota', 'iota_result')),
    ('kind=unfold', lambda e: e.get('kind') in ('unfold', 'unfold_result')),
    ('kind=infer_fail', lambda e: e.get('site') == 'infer.app_arg' and e.get('ok') == 'false'),
]

def run(bin_path, case):
    cfg = bin_path.parent.parent.parent / 'config.json'
    with case.open('rb') as f:
        cp = subprocess.run([str(bin_path), str(cfg)], stdin=f, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return cp.returncode, cp.stderr.decode('utf-8', 'replace')

def status(rc):
    return 'accept' if rc == 0 else ('decline' if rc == 2 else 'reject')

def parse_events(err):
    xs = []
    for line in err.splitlines():
        if not line.startswith('[MGTRACE] '):
            continue
        d = {}
        for tok in line[10:].split():
            if '=' in tok:
                k, v = tok.split('=', 1)
                d[k] = v
        xs.append(d)
    return xs

def terminal_semantic_event(ev):
    for e in reversed(ev):
        k = e.get('kind')
        s = e.get('site', '')
        if k == 'panic':
            continue
        if s == 'infer.proj' or k == 'projection': return e
        if s == 'conv.recursor' or k in ('iota', 'iota_result'): return e
        if s == 'conv.unfold_pair' or k in ('unfold', 'unfold_result'): return e
        if s == 'infer.app_arg' and e.get('ok') == 'false': return e
    return {}

def inject(src, fam):
    if fam == 'INFER_APP':
        p = src / 'src/infer.rs'; s = p.read_text()
        pat = re.compile(r'(?m)^(\s*)assert!\(mg_ok, "app arg def_eq failed"\);')
        m = pat.search(s)
        if not m: raise RuntimeError('anchor missing INFER_APP')
        i = m.group(1)
        s = pat.sub(i + 'panic!("MGFAULT_INFER_APP");\n' + i + 'assert!(mg_ok, "app arg def_eq failed");', s, count=1)
        p.write_text(s); return
    if fam == 'PROJECTION':
        p = src / 'src/infer.rs'; s = p.read_text()
        anchor = '        eprintln!("[MGTRACE] kind=projection site=infer.proj depth={}", depth);'
        repl = anchor + '\n        panic!("MGFAULT_PROJECTION");'
    elif fam == 'IOTA':
        p = src / 'src/conv.rs'; s = p.read_text()
        anchor = '                eprintln!("[MGTRACE] kind=iota site=conv.recursor depth={} heads_match={}", depth, heads_match);'
        repl = anchor + '\n                panic!("MGFAULT_IOTA");'
    elif fam == 'UNFOLD':
        p = src / 'src/conv.rs'; s = p.read_text()
        anchor = '                        eprintln!("[MGTRACE] kind=unfold site=conv.unfold_pair depth={}", depth);'
        repl = anchor + '\n                        panic!("MGFAULT_UNFOLD");'
    else:
        raise ValueError(fam)
    if anchor not in s: raise RuntimeError(f'anchor missing {fam}')
    p.write_text(s.replace(anchor, repl, 1))

def sig(event, subset):
    return tuple(bool(CANDIDATES[i][1](event)) for i in subset)

def partition_purity(rows, subset):
    cells = {}
    for r in rows:
        cells.setdefault(sig(r['terminal_event'], subset), []).append(r['family'])
    good = sum(max(v.count(x) for x in set(v)) for v in cells.values())
    return good / len(rows), cells

def choose_minimal(rows):
    # Exact minimal separator. Tie-break lexicographically by frozen candidate order.
    for k in range(len(CANDIDATES) + 1):
        for subset in combinations(range(len(CANDIDATES)), k):
            purity, cells = partition_purity(rows, subset)
            if purity == 1.0:
                return tuple(subset), cells
    raise RuntimeError('no separating distinction subset')

def mapping(rows, subset):
    m = {}
    for r in rows:
        key = sig(r['terminal_event'], subset)
        if key in m and m[key] != r['family']:
            raise RuntimeError('non-pure mapping')
        m[key] = r['family']
    return m

trace_bin = TRACE / 'target/release/sokonanoda'
(trace_bin.parent.parent.parent / 'config.json').write_text(CFG)

# Build one faulty checker per mechanism once, then collect paired source-distinct episodes.
fault_bins = {}
for fam in FAMILIES:
    work = root / f'fault-v9-{fam.lower()}'
    if work.exists(): shutil.rmtree(work)
    shutil.copytree(TRACE, work, ignore=shutil.ignore_patterns('target'))
    inject(work, fam)
    (work / 'config.json').write_text(CFG)
    subprocess.run(['cargo', 'build', '--release'], cwd=work, check=True, env={**os.environ, 'RUSTFLAGS':'-C target-cpu=native'})
    fault_bins[fam] = work / 'target/release/sokonanoda'

rows = []
for fam in FAMILIES:
    for split_idx, rel in enumerate(SELECTED[fam]):
        case = ARENA / rel
        br, _ = run(trace_bin, case)
        fr, err = run(fault_bins[fam], case)
        if status(br) != 'accept' or status(fr) != 'reject':
            raise SystemExit(f'discriminator failed {fam} {rel}: {status(br)}->{status(fr)}')
        ev = parse_events(err)
        term = terminal_semantic_event(ev)
        if not term:
            raise SystemExit(f'no terminal semantic event {fam} {rel}')
        rows.append({
            'family': fam,
            'case': rel,
            'split': 'train' if split_idx == 0 else 'heldout',
            'event_count': len(ev),
            'terminal_event': term,
            'events_tail': ev[-12:],
        })

train = [r for r in rows if r['split'] == 'train']
heldout = [r for r in rows if r['split'] == 'heldout']
coarse_purity, _ = partition_purity(train, ())
full_subset = tuple(range(len(CANDIDATES)))
full_purity, _ = partition_purity(train, full_subset)
selected, selected_cells = choose_minimal(train)
selected_purity, _ = partition_purity(train, selected)
train_map = mapping(train, selected)

# Backward deletion is the quotient test: every retained distinction must be load-bearing.
ablations = []
for i in selected:
    sub = tuple(x for x in selected if x != i)
    purity, cells = partition_purity(train, sub)
    ablations.append({
        'removed': CANDIDATES[i][0],
        'remaining': [CANDIDATES[j][0] for j in sub],
        'train_purity': purity,
        'cell_count': len(cells),
    })

# Protected source-distinct evaluation.
heldout_rows = []
for r in heldout:
    key = sig(r['terminal_event'], selected)
    pred = train_map.get(key)
    full_key = sig(r['terminal_event'], full_subset)
    # Full-structure route is the direct recognized terminal mechanism.
    direct = None
    s = r['terminal_event'].get('site',''); k = r['terminal_event'].get('kind','')
    if s == 'infer.proj' or k == 'projection': direct = 'PROJECTION'
    elif s == 'conv.recursor' or k in ('iota','iota_result'): direct = 'IOTA'
    elif s == 'conv.unfold_pair' or k in ('unfold','unfold_result'): direct = 'UNFOLD'
    elif s == 'infer.app_arg': direct = 'INFER_APP'

    def calls_for(first):
        order = ([first] + [x for x in BINARY_ORDER if x != first]) if first in FAMILIES else BINARY_ORDER
        attempts = []
        for cand in order:
            checker = trace_bin if cand == r['family'] else fault_bins[r['family']]
            rc, _ = run(checker, ARENA / r['case'])
            attempts.append({'candidate': cand, 'verdict': status(rc)})
            if status(rc) == 'accept': break
        return len(attempts), attempts

    b_calls, b_attempts = calls_for(None)
    q_calls, q_attempts = calls_for(pred)
    f_calls, f_attempts = calls_for(direct)
    heldout_rows.append({
        **r,
        'selected_signature': list(key),
        'full_signature': list(full_key),
        'predicted_family': pred,
        'direct_full_route': direct,
        'selected_correct': pred == r['family'],
        'quotient_matches_full_route': pred == direct,
        'binary_calls': b_calls,
        'quotient_calls': q_calls,
        'full_calls': f_calls,
        'binary_attempts': b_attempts,
        'quotient_attempts': q_attempts,
        'full_attempts': f_attempts,
    })

heldout_accuracy = sum(r['selected_correct'] for r in heldout_rows) / len(heldout_rows)
route_equivalence = sum(r['quotient_matches_full_route'] for r in heldout_rows) / len(heldout_rows)
mean_binary = sum(r['binary_calls'] for r in heldout_rows) / len(heldout_rows)
mean_quotient = sum(r['quotient_calls'] for r in heldout_rows) / len(heldout_rows)
mean_full = sum(r['full_calls'] for r in heldout_rows) / len(heldout_rows)
raw_events = sum(r['event_count'] for r in heldout_rows)
selected_bits = len(selected) * len(heldout_rows)

summary = {
    'status': 'DISTINCTION_CYCLE_V9',
    'precommit': {
        'hypothesis': 'split until consequence is predictable, then quotient until no predictive distinction is wasted',
        'train_per_family': 1,
        'heldout_per_family': 1,
        'candidate_distinctions': [x[0] for x in CANDIDATES],
        'selection_rule': 'smallest candidate subset with 1.0 training partition purity; frozen-order tie break',
        'admission_gates': [
            'coarse representation is not perfectly predictive',
            'selected representation reaches 1.0 training purity',
            'every retained distinction is deletion-load-bearing',
            'heldout source-distinct prediction accuracy is 1.0',
            'quotient route agrees with full terminal-semantic route on heldout',
            'quotient repair benefit matches full route',
        ],
    },
    'coarse_train_purity': coarse_purity,
    'full_candidate_train_purity': full_purity,
    'selected_train_purity': selected_purity,
    'selected_distinctions': [CANDIDATES[i][0] for i in selected],
    'selected_count': len(selected),
    'selected_cells': {str(k): v for k, v in selected_cells.items()},
    'deletion_ablations': ablations,
    'heldout_accuracy': heldout_accuracy,
    'heldout_route_equivalence_to_full': route_equivalence,
    'mean_binary_verifier_calls': mean_binary,
    'mean_quotient_verifier_calls': mean_quotient,
    'mean_full_verifier_calls': mean_full,
    'binary_vs_quotient_factor': mean_binary / mean_quotient if mean_quotient else None,
    'heldout_raw_trace_events': raw_events,
    'heldout_selected_bits': selected_bits,
    'raw_events_per_selected_bit': raw_events / selected_bits if selected_bits else None,
    'rows': heldout_rows,
}
summary['gates'] = {
    'G0_coarse_not_sufficient': coarse_purity < 1.0,
    'G1_selected_predictive': selected_purity == 1.0,
    'G2_deletion_minimal': all(a['train_purity'] < 1.0 for a in ablations),
    'G3_heldout_transfer': heldout_accuracy == 1.0,
    'G4_quotient_preserves_full_route': route_equivalence == 1.0,
    'G5_quotient_preserves_full_repair_cost': mean_quotient == mean_full,
    'G6_quotient_beats_binary': mean_quotient < mean_binary,
}
summary['pass'] = all(summary['gates'].values())
out.joinpath('summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True))
print(json.dumps(summary, indent=2, sort_keys=True))
if not summary['pass']:
    raise SystemExit('distinction cycle V9 gate failed')
