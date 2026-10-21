import io, json, keyword, subprocess, tokenize
from collections import Counter
from pathlib import Path

OUT = Path('artifacts/v54')
OUT.mkdir(parents=True, exist_ok=True)
DJ = Path('/tmp/v54_django')
RQ = Path('/tmp/v54_requests')
RH = Path('/tmp/v54_rich')

OLD_GENERATORS = ['IDENTITY','REVERSE_WINDOW','ROTATE_LEFT','ROTATE_RIGHT','SWAP_ADJACENT']
DESTS = sorted(set([s for s in tokenize.EXACT_TOKEN_TYPES if 1 <= len(s) <= 2] + keyword.kwlist))


def sh(cmd, cwd, timeout=40):
    try:
        p = subprocess.run(cmd, cwd=cwd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        return p.returncode == 0, p.stdout[-2500:]
    except subprocess.TimeoutExpired as e:
        x = e.stdout or ''
        if isinstance(x, bytes): x = x.decode(errors='replace')
        return False, (x + '\nTIMEOUT')[-2500:]


def reset(repo):
    subprocess.run('git reset --hard -q HEAD && git clean -fdxq', cwd=repo, shell=True, check=True)


def tokens(path):
    return list(tokenize.generate_tokens(io.StringIO(path.read_text()).readline))


def sites(path, value, line_no=None):
    out=[]
    for t in tokens(path):
        if t.type in (tokenize.OP, tokenize.NAME) and t.string == value and (line_no is None or t.start[0] == line_no):
            out.append((t.start[0], t.start[1], t.end[1], t.string))
    return out


def mutate(path, site, dst):
    row,c0,c1,_ = site
    ls = path.read_text().splitlines(True)
    old = ls[row-1]
    ls[row-1] = old[:c0] + dst + old[c1:]
    path.write_text(''.join(ls))
    return old.strip()


def test_dj_trunc():
    return sh('python tests/runtests.py backends.test_utils.TestUtils.test_truncate_name --verbosity 0', DJ, 40)[0]

def test_dj_page():
    return sh('python tests/runtests.py pagination.tests.PaginationTests.test_orphans_value_larger_than_per_page_value --verbosity 0', DJ, 40)[0]

def test_rq():
    return sh('timeout 7s pytest -q tests/test_utils.py -k test_iter_slices', RQ, 12)[0]

def test_rich():
    return sh('pytest -q tests/test_highlighter.py::test_highlight_json_string_only tests/test_highlighter.py::test_highlight_json_empty_string_only', RH, 40)[0]


def unique_breaking_site(repo, path, src, bad, test):
    reset(repo); assert test()
    bads=[]
    for s in sites(path, src):
        reset(repo); line=mutate(path,s,bad); ok=test()
        if not ok: bads.append((s,line))
    reset(repo)
    return bads


def emission_survivors(repo, path, site, broken_token, test):
    survivors=[]
    for d in DESTS:
        if d == broken_token: continue
        reset(repo)
        good = tuple(site[:3]) + (site[3],)
        mutate(path, good, broken_token)
        cur=[s for s in sites(path, broken_token, site[0]) if s[1] == site[1]]
        if len(cur) != 1: continue
        try:
            mutate(path, cur[0], d)
        except Exception:
            continue
        if test(): survivors.append(d)
    reset(repo)
    return sorted(set(survivors))


def line_first_word(line):
    xs=[t.string for t in tokenize.generate_tokens(io.StringIO(line+'\n').readline) if t.type == tokenize.NAME]
    return xs[0] if xs else None

# ---------- Phase A: construct genuinely closure-expanding O1 ----------
trunc = DJ/'django/db/backends/utils.py'
page = DJ/'django/core/paginator.py'
rich = RH/'rich/highlighter.py'

b1=unique_breaking_site(DJ,trunc,'<=','<',test_dj_trunc)
b2=unique_breaking_site(DJ,page,'<=','<',test_dj_page)
assert len(b1)==1 and len(b2)==1
s1,l1=b1[0]; s2,l2=b2[0]
r1=emission_survivors(DJ,trunc,s1,'<',test_dj_trunc)
r2=emission_survivors(DJ,page,s2,'<',test_dj_page)
common=sorted(set(r1)&set(r2))
O1_DST=common[0] if len(common)==1 else None
O1={'kind':'TOKEN_REWRITE','src':'<','dst':O1_DST} if O1_DST else None
old_closure_obstruction_O1=bool(O1 and Counter(['<']) != Counter([O1_DST]))

reset(RH); assert test_rich()
rh_bads=[]
for s in sites(rich,'<'):
    reset(RH); line=mutate(rich,s,'<=')
    if not test_rich(): rh_bads.append((s,line))
reset(RH)
assert len(rh_bads)==1
harm_line=rh_bads[0][1]
help_first={line_first_word(l1),line_first_word(l2)}
harm_first=line_first_word(harm_line)
scope_word=next(iter(help_first)) if len(help_first)==1 and next(iter(help_first)) != harm_first else None

# ---------- Phase B target: two simultaneous missing operators ----------
rq_path=RQ/'src/requests/utils.py'
reset(RQ); assert test_rq()
rq_break=unique_breaking_site(RQ,rq_path,'<=','<',test_rq)
assert len(rq_break)==1
rq_le_site,rq_line=rq_break[0]
line_no=rq_le_site[0]
or_sites=sites(rq_path,'or',line_no)
assert len(or_sites)>=1
rq_or_site=or_sites[0]

def make_double_broken():
    reset(RQ)
    mutate(rq_path, rq_le_site, '<')
    cur_or=[s for s in sites(rq_path,'or',line_no) if s[1] == rq_or_site[1]]
    if len(cur_or)!=1: raise RuntimeError('lost OR site')
    mutate(rq_path,cur_or[0],'and')

# Frozen one-new-generator discovery from A0. Tokenize the actual double-broken
# state so character-width changes cannot invalidate stored coordinates.
def one_rewrite_discovery():
    make_double_broken()
    line=rq_path.read_text().splitlines()[line_no-1]
    ts=[t for t in tokenize.generate_tokens(io.StringIO(line+'\n').readline) if t.type in (tokenize.NAME,tokenize.OP)]
    survivors=[]
    for t in ts:
        if t.string in {':','(',')','.',','}: continue
        for d in DESTS:
            if d == t.string: continue
            make_double_broken()
            ls=rq_path.read_text().splitlines(True); current=ls[line_no-1]
            c0,c1=t.start[1],t.end[1]
            if c1 > len(current) or current[c0:c1] != t.string: continue
            ls[line_no-1]=current[:c0]+d+current[c1:]
            rq_path.write_text(''.join(ls))
            if test_rq(): survivors.append({'src':t.string,'dst':d,'col':c0})
    make_double_broken()
    return survivors

cold_survivors=one_rewrite_discovery()

# Warm A1: lawful closure reuse of O1. Re-tokenize the current state and require
# a unique source token on the target line instead of using a stale column.
make_double_broken()
warm_line=rq_path.read_text().splitlines()[line_no-1]
if O1 and scope_word and line_first_word(warm_line)==scope_word:
    cur=sites(rq_path,'<',line_no)
    assert len(cur)==1
    mutate(rq_path,cur[0],O1['dst'])
assert not test_rq(), 'O1 alone should expose residual rather than solve target'

# Search exactly one NEW rewrite after O1 has been reused.
def discover_after_O1():
    base_text=rq_path.read_text()
    line=base_text.splitlines()[line_no-1]
    ts=[t for t in tokenize.generate_tokens(io.StringIO(line+'\n').readline) if t.type in (tokenize.NAME,tokenize.OP)]
    survivors=[]
    for t in ts:
        if t.string in {':','(',')','.',','}: continue
        for d in DESTS:
            if d==t.string: continue
            rq_path.write_text(base_text)
            ls=rq_path.read_text().splitlines(True); current=ls[line_no-1]
            c0,c1=t.start[1],t.end[1]
            if current[c0:c1] != t.string: continue
            ls[line_no-1]=current[:c0]+d+current[c1:]
            rq_path.write_text(''.join(ls))
            if test_rq(): survivors.append({'src':t.string,'dst':d,'col':c0})
    rq_path.write_text(base_text)
    return survivors

warm_survivors=discover_after_O1()
unique_pairs=sorted(set((x['src'],x['dst']) for x in warm_survivors))
O2={'kind':'TOKEN_REWRITE','src':unique_pairs[0][0],'dst':unique_pairs[0][1]} if len(unique_pairs)==1 else None
old_A1_obstruction_O2=bool(O2 and O2['src'] in {'and','or'} and O2['dst'] in {'and','or'} and O2['src']!=O2['dst'])

# Causal final execution with O1 then O2.
make_double_broken(); cold=test_rq()
cur=sites(rq_path,'<',line_no)
if O1 and len(cur)==1: mutate(rq_path,cur[0],O1['dst'])
mid=test_rq()
if O2:
    cur2=sites(rq_path,O2['src'],line_no)
    if len(cur2)==1: mutate(rq_path,cur2[0],O2['dst'])
warm=test_rq()

# Ablate O1 but keep O2 present.
make_double_broken()
if O2:
    cur2=sites(rq_path,O2['src'],line_no)
    if len(cur2)==1: mutate(rq_path,cur2[0],O2['dst'])
ablated_O1=test_rq()

R={
 'protocol':'V54_TWO_GENERATION_COMPOUNDING_20260814',
 'old_generators':OLD_GENERATORS,
 'constructor_destinations':len(DESTS),
 'O1':{'repair_survivors_1':r1,'repair_survivors_2':r2,'common':common,'operator':O1,'old_closure_obstruction':old_closure_obstruction_O1,'scope_word':scope_word,'harm_first_word':harm_first},
 'O2_target':{'double_broken_line':rq_line,'cold_one_rewrite_survivors':cold_survivors,'after_O1_one_rewrite_survivors':warm_survivors,'unique_pairs':unique_pairs,'operator':O2,'A1_obstruction':old_A1_obstruction_O2},
 'causal':{'cold':cold,'after_O1_only':mid,'after_O1_O2':warm,'O1_ablated_O2_present':ablated_O1},
}
R['gates']={
 'O1_constructed':O1 is not None,
 'O1_outside_old_closure':old_closure_obstruction_O1,
 'O1_scope_learned_not_global':scope_word=='if' and harm_first!='if',
 'O2_not_discoverable_under_A0_budget':len(cold_survivors)==0,
 'O2_discoverable_after_O1':O2 is not None,
 'O2_is_new_operator':old_A1_obstruction_O2,
 'O1_alone_not_enough':mid is False,
 'O1_plus_O2_solves':warm is True,
 'ablating_O1_removes_final_capability':ablated_O1 is False,
}
R['verdict']='PASS_V54_TWO_GENERATION_COMPOUNDING' if all(R['gates'].values()) else 'FAIL_V54_TWO_GENERATION_COMPOUNDING'
R['claim_boundary']='This combines genuine old-closure-expanding O1 construction with a later source-distinct target whose O2 is outside the fixed one-new-rewrite discovery horizon before O1 reuse and inside it afterward. Both operators are constructed inside a supplied generic token-emission meta-substrate; this is not invention outside all meta-languages.'
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2))
print(json.dumps(R,indent=2))
if R['verdict'].startswith('FAIL'): raise SystemExit(1)
