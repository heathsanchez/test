"""V14 source-attested, guarded consumer of V12b executable evidence.

Positive event is emitted only after checking producer bytes/receipt.
The inherited V13 runtime represents the event as a synthetic scenario event;
this adapter carries the ACTUAL source verification proof pointer separately.
"""
from __future__ import annotations
from pathlib import Path
from copy import deepcopy
import hashlib, importlib.util, json, os, sys

ROOT=Path(__file__).resolve().parent
V12=Path(os.environ.get('FLASH_V12_SOURCE',ROOT.parent/'flash_genesis_v12'))
V13=Path(os.environ.get('FLASH_V13_SOURCE',ROOT.parent/'flash_v13'))
if not V13.exists():V13=ROOT.parent/'flash_genesis_v13'
sys.path.insert(0,str(V13))
from flash_engine import RecloseEngine,EventRejected
from reference_oracle import FullReference

SOURCE_EXPECTED={
 'learned_objective.py':'eb736c72c3acc5bc152fe811be8d3892d88ac0e1932bb2fb47ef5d562fe49a3f',
 'verify_v12b.py':'6358e8d893aebcb27f3d94861ec86baedf2857b0f0f920241b089d92d65906c9',
 'v12b_results.json':'9b7328e386ff9c47bf9504f8955d267a12dcefbdca345c10d3d52d3e89f1e191',
 'source_receipt.json':'d394d88879f28b78bbe7498d46abfbc42f67c2d59304bbd7a3f73de23428ac1f'}
PROTECTED_SHA='36753698faecf6dce3ef3c786883d85ac810bec841415427b82eccd36d18ba0c'
FIXTURE_SHA='64060c4cbb419ef8ebe295449c19100a8b227ff07c8c12102096092c8bd2cbf9'
RUNS={'v12b':38202495321,'v13':38203812704}

class Gate:
    def __init__(self):
        self.fixture=json.loads((V13/'fixture.json').read_text())
        assert hashlib.sha256((V13/'fixture.json').read_bytes()).hexdigest()==FIXTURE_SHA
        assert hashlib.sha256((ROOT/'protected_domains.py').read_bytes()).hexdigest()==PROTECTED_SHA
        self.engine=RecloseEngine(self.fixture)
        self.reference=FullReference(self.fixture)
        self.program=None
        self.source_evidence=None
        self.archive=[]
        self._event('revoke','verified_v12',{'reason':'initial_consumer_restricted_before_source_attestation'})

    def _event(self,kind,fact,meaning):
        event={'kind':kind,'fact':fact,
               'authority':'synthetic_event' if kind=='promote' else 'synthetic_revoker'}
        changed=self.engine.apply(event)
        ref=self.reference.apply(event)
        assert self.engine.state()==ref
        self.archive.append({'ordinal':len(self.archive),'event':event,'source_note':meaning,
                             'changed_frontiers':changed['changed_frontiers'],
                             'changed_facts':changed['changed_facts'],
                             'engine_chain':self.engine.event_chain})
        return changed

    def independently_attest_producer(self):
        for name,expected in SOURCE_EXPECTED.items():
            observed=hashlib.sha256((V12/name).read_bytes()).hexdigest()
            if observed!=expected:raise EventRejected(('producer_bytes_not_qualified',name,observed))
        r=json.loads((V12/'v12b_results.json').read_text())
        assert r['status']=='PASS_V12B_PROSPECTIVE_FINITE'
        assert (r['valid_families'],r['unsupported_families'])==(6,3)
        assert r['totals']['protected_comparisons']==7914
        assert r['totals']['learned_execution_calls']==r['totals']['stateless_execution_calls']==79332
        source=json.loads((V12/'source_receipt.json').read_text())
        assert source['selector_version']=='unbiased_v2_all_source_qualifying_candidates'
        assert source['warm']['selected']['policy']==source['cold']['selected']['policy']
        assert source['learned_source_sha256']==SOURCE_EXPECTED['learned_objective.py']
        spec=importlib.util.spec_from_file_location('v14_frozen_v12_source_program',V12/'learned_objective.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        assert module.POLICY=={'topology':'both','objective':'sum_weights','bound':'positive_weights','include_first':True}
        self.program=module.developed_optimize
        self.source_evidence={'qualifier_run':RUNS['v12b'],'read_only_source_sha256':SOURCE_EXPECTED['learned_objective.py'],
          'source_receipt_sha256':SOURCE_EXPECTED['source_receipt.json'],
          'retained_evidence_archive':'source bytes, qualified replay and lineage are retained',
          'source_scope':'finite supplied nonnegative modular objective and typed hereditary feasibility interface'}
        return deepcopy(self.source_evidence)

    def promote_after_attestation(self):
        if self.program is None or self.source_evidence is None:
            raise EventRejected('Cannot promote an unqualified executable')
        return self._event('promote','verified_v12',self.source_evidence)

    def simulated_revoke(self):
        return self._event('revoke','verified_v12',{'simulation':'source warrant temporarily withdrawn; no actual GitHub revocation'})

    def _guard(self,world):
        n=world.n
        feas=[bool(world.feasible(m)) for m in range(1<<n)]
        scores=[world.score(m) for m in range(1<<n)]
        calls={'raw_feasibility_reads':1<<n,'raw_score_reads':1<<n}
        if not feas[0]:return False,('empty_infeasible',0),calls
        for mask in range(1<<n):
            if feas[mask]:
                for i in range(n):
                    if (mask>>i&1) and not feas[mask^(1<<i)]:
                        return False,('nonhereditary',mask,mask^(1<<i)),calls
        if any(x<0 for x in world.weights):
            return False,('negative_weight',next(i for i,x in enumerate(world.weights) if x<0)),calls
        for mask,s in enumerate(scores):
            implied=sum(world.weights[i] for i in range(n) if mask>>i&1)
            if implied!=s:return False,('not_modular',mask,implied,s),calls
        return True,None,calls

    def evaluate(self,world):
        guard_ok,reason,calls=self._guard(world)
        doc={'name':world.name,'family':world.family,'declared':world.declared,
            'applicability_checked':guard_ok,'guard_counterexample':reason,**calls}
        if not guard_ok:
            doc.update(status='UNKNOWN_UNSUPPORTED_INTERFACE',called_source=False)
            return doc
        if 'cap_weighted' not in self.engine.active or self.program is None:
            doc.update(status='UNKNOWN_NO_ACTIVE_SOURCE_WARRANT',called_source=False)
            return doc
        observed=0
        def call(mask):
            nonlocal observed
            observed+=1
            return bool(world.feasible(mask))
        got=self.program(world.n,call,world.weights,tuple(range(world.n)))
        doc.update(status='SOURCE_AUTHORIZED_OUTPUT',called_source=True,
                   checked_value=got,source_feasibility_execution_calls=observed,
                   source_warrant_sha256=self.source_evidence['read_only_source_sha256'])
        return doc

    def snapshot(self):
        return {'engine':self.engine.snapshot(),'source_attestation':deepcopy(self.source_evidence),
           'events_archive':deepcopy(self.archive),
           'compiled_source_loaded':self.program is not None}

    @classmethod
    def restore(cls,snapshot):
        self=cls.__new__(cls)
        self.fixture=json.loads((V13/'fixture.json').read_text())
        self.engine=RecloseEngine.restore(self.fixture,snapshot['engine'])
        self.reference=FullReference(self.fixture)
        self.reference.ground=set(self.engine.base)
        self.reference.current=self.reference.rebuild()
        assert self.engine.state()==self.reference.current
        self.archive=deepcopy(snapshot['events_archive'])
        self.source_evidence=None
        self.program=None
        if snapshot['compiled_source_loaded']:
            attest=self.independently_attest_producer()
            assert attest==snapshot['source_attestation']
        else:
            assert snapshot['source_attestation'] is None
        return self
