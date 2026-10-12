#!/usr/bin/env python3
"""Reproducible local wall time: exact same frozen input stream, separate engines."""
import json, random, statistics, time
from pathlib import Path
from flash_engine import RecloseEngine
from reference_oracle import FullReference
ROOT=Path(__file__).parent
f=json.loads((ROOT/'fixture.json').read_text())
rng=random.Random(20261012)
stream=[]
for i in range(16000):
    kind=rng.choice(('promote','revoke'))
    stream.append({'kind':kind,'fact':rng.choice(f['allowed_events']['promote']),
     'authority':'synthetic_event' if kind=='promote' else 'synthetic_revoker'})
records={'incremental':[],'batch':[]}
for rep in range(8):
    trial=('incremental','batch') if rep%2==0 else ('batch','incremental')
    states={}
    for mode in trial:
        cls=RecloseEngine if mode=='incremental' else FullReference
        t=time.perf_counter()
        x=cls(f)
        for event in stream:
            x.apply(event)
        records[mode].append(time.perf_counter()-t)
        states[mode]=x.state() if mode=='incremental' else x.current
    assert states['incremental']==states['batch'],('final_semantics_regression',rep)
result={'status':'PASS_BOUNDED_LOCAL_WALL_COMPARISON',
        'fixture':'flash_v13_20261012',
        'event_count':len(stream),'repetitions':8,
        'times_seconds':{k:[round(t,6) for t in v] for k,v in records.items()},
        'medians_seconds':{k:round(statistics.median(v),6) for k,v in records.items()},
        'speed_ratio_batch_over_incremental':round(statistics.median(records['batch'])/statistics.median(records['incremental']),5),
        'limitations':'Same Python interpreter and frozen synthetic fixture; not a hardware benchmark, throughput guarantee, or adversarial optimized batch competitor. Source acquisition and formal qualification costs excluded.'}
(ROOT/'benchmark_results.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,indent=2))
