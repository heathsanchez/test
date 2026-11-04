"""Engineering control only: a temporarily missing live basis must not warrant."""
import importlib.util,json,os
from pathlib import Path
import pytest

def test_pending_source_requalification_does_not_admit_or_abort(tmp_path):
    here=Path(__file__).resolve().parent
    path=here/os.environ.get('UDM_TEST_PROFILE','pilot_v3_posthoc_repair.py')
    spec=importlib.util.spec_from_file_location('restoration_profile',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    rows=json.loads((m.WORK/'pilot_run_v3/rows.json').read_text())
    row=next(r for r in rows if r['arm']=='D' and r['split']=='train' and not r['witnesses'])
    graph=m.Graph(tmp_path/'state')
    # Model only the already selected historical policy during a fresh-source
    # support shortfall. No native result, source change or capability is invented.
    sig=[['V100_FAMILY','BIN_OP'],['UNCHANGED_BASE']]
    m.selected=lambda rows:[sig]
    class PriorBaseline:
        def verify(self,*args):return row['baseline']
    graph.add(row,PriorBaseline())
    assert graph.current==[]
    assert graph.machine.active_capabilities()==[]
