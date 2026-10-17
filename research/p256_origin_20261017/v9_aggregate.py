#!/usr/bin/env python3
"""Fail-closed cross-worker V9 acceptance; no result if one shard missing."""
import hashlib,json,sys
from pathlib import Path
import v9_candidates as v9
HERE=Path(__file__).resolve().parent
EXPECTED='6ae4d488768e622d5ff307ca7bb1af2c2b7d10c0f6935fac2e7107eac1fa5d22'
PUBLISHED_ORDER=v9.PUBLISHED_N

def main():
    rows=json.loads((HERE/'V9_CANDIDATES.json').read_text())
    raw=json.dumps(rows,sort_keys=True,separators=(',',':')).encode()
    assert hashlib.sha256(raw).hexdigest()==EXPECTED
    eligible={x['index'] for x in rows if x['state']=='ELIGIBLE_FOR_POINT_COUNT'}
    shards=[];all_cases=[]
    for s in range(8):
        x=json.loads((HERE/f'V9_SHARD_{s}.json').read_text())
        assert x['status']=='QUALIFIED_BOUNDED_SHARD' and x['full_census'],(s,x['status'])
        assert x['candidate_table_sha256']==EXPECTED
        assert x['shard']==s
        assert len(x['results'])==len(x['eligible_indices'])
        assert set(q['index'] for q in x['results'])==set(x['eligible_indices'])
        assert all(q['index']%8==s for q in x['results'])
        shards.append({'shard':s,'gp_version':x['gp_version'],'counts':x['counts'],'elapsed':x['elapsed_seconds']})
        all_cases.extend(x['results'])
    assert len(all_cases)==len(eligible) and len(set(x['index'] for x in all_cases))==len(eligible)
    assert set(x['index'] for x in all_cases)==eligible
    official=[x for x in all_cases if x['index']==7026]
    assert len(official)==1 and official[0]['status']=='PRIME_ORDER'
    assert int(official[0]['order'])==PUBLISHED_ORDER
    assert official[0]['qualifies_224bit']
    positives=sorted((x for x in all_cases if x['status']=='PRIME_ORDER' and x['qualifies_224bit']),key=lambda x:x['index'])
    previous=[x for x in positives if x['index']<7026]
    primestatus={s:sum(x['status']==s for x in all_cases) for s in ('NOT_PRIME_BY_TORSION_TEST','COMPOSITE_ORDER','PRIME_ORDER')}
    evidence={
      'stage_A':'WARRANTED_EXACT_CONSTRUCTION',
      'stage_B':'WARRANTED_BOUNDED_PARIGP_SEA_SOFTWARE_COUNT' ,
      'published_N_exact':True,'qualified_pre_7026_indices':[x['index'] for x in previous],
      'qualified_pre_7026_count':len(previous),'source_reported_pre_7026_count':3,
      'published_candidate_index':7026,'published_candidate_order':str(PUBLISHED_ORDER),
      'candidate_table_sha256':EXPECTED,'full_census_count':len(all_cases),
      'count_eligible':len(eligible),'field_arithmetic_excluded':7026-len(eligible),
      'shard_provenance':shards,'point_count_verdicts':primestatus,
      'prime_count_including_narrow_or_missing_size':sum(x['status']=='PRIME_ORDER' for x in all_cases),
      'survivors':[{**x,'seed':rows[x['index']-1]['seed'],'c':rows[x['index']-1]['c']} for x in positives],
      'anthropic_report_comparison': 'MATCH_THREE' if len(previous)==3 else 'DISCREPANCY_REQUIRES_REVIEW',
      'historical_selection':'UNKNOWN','base_point_origin':'UNKNOWN',
      'cryptographic_vulnerability':'NOT_CLAIMED','unique_cryptographic_standard_generation_law':'UNKNOWN',
      'agent_advantage':'NOT_TESTED','lean_certificate':'NOT_RUN'
    }
    (HERE/'V9_AGGREGATE.json').write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'stage_A':evidence['stage_A'],'stage_B':evidence['stage_B'],
          'pre_7026_indices':evidence['qualified_pre_7026_indices'],
          'count':evidence['qualified_pre_7026_count'],
          'comparison':evidence['anthropic_report_comparison'],
          'hist_selection':evidence['historical_selection']},indent=2))

if __name__=='__main__':main()
