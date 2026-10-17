#!/usr/bin/env python3
"""Confirm post-outcome timing correction only removed duplicate trial divisions.

The frozen prospective v2 result file is never modified by v2b.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
for split in ('calibration','heldout'):
    original=json.loads((ROOT/f'results_{split}.json').read_text())
    corrected=json.loads((ROOT/f'results_v2b_{split}.json').read_text())
    assert len(original['cases'])==len(corrected['cases'])
    for a,b in zip(original['cases'],corrected['cases']):
        assert a['id']==b['id'] and a['n']==b['n'] and a['factor_hash']==b['factor_hash']
        assert a['siqs']['factor_found']==b['siqs']['factor_found']
        for arm in ('forward_trial','forward_root-sieve','symmetric_trial','symmetric_root-sieve'):
            x=a['arms'][arm];y=b['arms'][arm]
            for k in ('smooth','partial_observed','matched_pairs','retained_relations','factor_first_candidate','factor','relation_stream_sha256','modular_trial_checks'):
                assert x[k]==y[k],(a['id'],arm,k)
    print('TIMING_CORRECTION_INVARIANCE',split,len(original['cases']))
