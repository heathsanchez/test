#!/usr/bin/env python3
"""Compact auditable witness: 22 rejection-gap lattices + 20 schedules."""
import json,hashlib
from pathlib import Path
p=Path(__file__).parent
r=json.loads((p/'V13_RESULTS.json').read_text())
assert r['frozen_protocol']=='3563c99349d7fee713425ead832c18f2ee0ab8a9'
cert={'name':'V13 complete source FreeLIP 11x26 bounded non-origin certificate',
 'protocol':r['frozen_protocol'],'source':r['source'],
 'params':r['parameters'],
 'invariants':r['invariants'],
 'rejection_gap_witnesses':[],
 'schedule_witnesses':[],
 'claim':'ZERO_SOURCE_P256_Gx_MATCHES_FOR_ALL_MOD_2^107_FREE_LIP_11x26_STATES_AND_INTERNAL_REJECTIONS'}
for g in r['rejection_gap_certificates']:
    cert['rejection_gap_witnesses'].append({
      'd':g['gap'],'unimodular_transform':g['unimodular_transform'],
      'reduced_basis':g['reduced_basis'],'nodes':g['nodes'],'leaves':g['leaves'],
      'pairs':g['rejected_state_pair_witnesses']})
for a in r['one_rejection_schedules']:
    cert['schedule_witnesses'].append({
      'orientation':a['orientation'],'skip_before_call':a['skip_before_call'],
      'observations':a['observations'],
      'unimodular_transform':a['unimodular_transform'],
      'reduced_basis':a['reduced_basis'],
      'nodes':a['nodes'],'sphere_leaves':a['sphere_leaves'],
      'box_state_count':a['box_state_count'],
      'box_firststates':sorted(z['earliest_observed_state'] for z in a['all_states']),
      'full_matches':a['full_Gx_matches'],
      'source_valid_matches':a['valid_rejection_Gx_matches']})
out=p/'V13_CERTIFICATE.json'
out.write_text(json.dumps(cert,indent=2,sort_keys=True)+'\n')
print(out.name,out.stat().st_size,'bytes; all',len(cert['rejection_gap_witnesses'])+len(cert['schedule_witnesses']),'proof cases')
