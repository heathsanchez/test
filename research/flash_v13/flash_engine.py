"""FLASH V13: finite, incremental proof-supported consequence closure.

This is generic over a frozen synthetic graph. Verified SOURCE facts are inputs,
not inferred by this engine. It does not prove cross-domain dependency edges.
"""
from __future__ import annotations
import hashlib, json
from collections import defaultdict, deque
from copy import deepcopy


def wire_json(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)


def digest(value):
    return hashlib.sha256(wire_json(value).encode()).hexdigest()


class EventRejected(ValueError):
    pass


class RecloseEngine:
    def __init__(self, fixture):
        self.fixture=deepcopy(fixture)
        self.fixture_digest=digest(fixture)
        self._compile()
        self.base=set(fixture['base_facts'])
        self.active=set()
        self.supports={}
        self.frontiers={}
        self.event_count=0
        self.event_chain=digest({'genesis':'FLASH_V13','fixture':self.fixture_digest})
        self.metrics={'fact_dirty_visits':0,'rule_evaluations':0,'frontier_evaluations':0,
                      'events':0,'noops':0,'reclosure_passes':0}
        self._recompute(set(self.symbols),force_frontiers=True)

    def _compile(self):
        f=self.fixture
        assert f['version']=='flash-v13-20261012'
        assert len({r['id'] for r in f['rules']})==len(f['rules'])
        assert len({q['id'] for q in f['frontiers']})==len(f['frontiers'])
        assert len(f['events'])<2000
        self.rules=tuple(f['rules'])
        self.rules_by_conclusion=defaultdict(list)
        self.descendants=defaultdict(set)
        self.watchers=defaultdict(set)
        self.symbols=set(f['base_facts'])
        for kind,facts in f['allowed_events'].items():
            assert kind in ('promote','revoke')
            self.symbols.update(facts)
        for r in self.rules:
            assert r['when'] and r['then'] not in r['when']
            assert len(r['when'])==len(set(r['when']))
            self.rules_by_conclusion[r['then']].append(r)
            self.symbols.add(r['then'])
            self.symbols.update(r['when'])
            for parent in r['when']:
                self.descendants[parent].add(r['then'])
        self.frontier_specs={q['id']:q for q in f['frontiers']}
        for fr in f['frontiers']:
            assert fr['budget']>=0
            assert len({o['id'] for o in fr['options']})==len(fr['options'])
            for opt in fr['options']:
                assert opt['cost']>=0
                for symbol in opt['when']+opt['unless']:
                    self.watchers[symbol].add(fr['id'])
                    self.symbols.add(symbol)

    def _cone(self, changed):
        dirty=set(changed)
        queue=deque(sorted(changed))
        while queue:
            parent=queue.popleft()
            for target in sorted(self.descendants.get(parent,())):
                if target not in dirty:
                    dirty.add(target);queue.append(target)
        return dirty

    def _frontier_state(self, fid):
        spec=self.frontier_specs[fid]
        candidates=[]
        for o in spec['options']:
            missing=sorted(set(o['when'])-self.active)
            forbidden=sorted(set(o['unless']) & self.active)
            over_budget=o['cost']>spec['budget']
            eligible=not missing and not forbidden and not over_budget
            candidates.append({'id':o['id'],'cost':o['cost'],'eligible':eligible,
                'missing':missing,'forbidden':forbidden,'over_budget':over_budget})
        viable=sorted((o for o in candidates if o['eligible']),key=lambda o:(o['cost'],o['id']))
        selected=viable[0] if viable else None
        return {'status':'SELECTED' if selected else 'UNKNOWN',
            'selected':selected['id'] if selected else None,
            'selected_cost':selected['cost'] if selected else None,
            'candidates':sorted(candidates,key=lambda o:o['id'])}

    def _recompute(self,dirty,force_frontiers=False):
        if not dirty and not force_frontiers:
            return {'dirty_facts':0,'rule_checks':0,'changed_facts':[],
                    'changed_supports':[],'checked_frontiers':[],'changed_frontiers':[],
                    'fixed_point':True}
        # Read only the affected dependency cone. No full graph/snapshot copy.
        before_active=self.active
        before_supports={fact:self.supports.get(fact) for fact in dirty}
        working=(self.active-dirty)|(self.base & dirty)
        rules=[rule for rule in self.rules if rule['then'] in dirty]
        checks=0;passes=0
        for _ in range(len(self.symbols)+1):
            passes+=1
            newly=set()
            for rule in rules:
                checks+=1
                if all(parent in working for parent in rule['when']):
                    newly.add(rule['then'])
            delta=newly-working
            if not delta:break
            working|=delta
        else:
            raise RuntimeError('Nonconvergent or oversized consequence closure')
        changed=before_active.symmetric_difference(working)
        self.active=working
        new_supports={}
        for fact in dirty:
            if fact not in working:
                self.supports.pop(fact,None)
                continue
            valid=[]
            if fact in self.base:valid.append('BASE:'+fact)
            for rule in self.rules_by_conclusion.get(fact,()):
                if all(parent in working for parent in rule['when']):
                    valid.append('RULE:'+rule['id'])
            assert valid,(fact,'no surviving proof support')
            new_supports[fact]=sorted(set(valid))
            self.supports[fact]=new_supports[fact]
        changed_supports=sorted(fact for fact in dirty
                                if before_supports.get(fact)!=new_supports.get(fact))
        touched=set(self.frontier_specs) if force_frontiers else set()
        if not force_frontiers:
            for fact in changed:
                touched.update(self.watchers.get(fact,()))
        changed_frontiers=[]
        for fid in sorted(touched):
            before=self.frontiers.get(fid)
            after=self._frontier_state(fid)
            self.frontiers[fid]=after
            if before!=after:changed_frontiers.append(fid)
        self.metrics['fact_dirty_visits']+=len(dirty)
        self.metrics['rule_evaluations']+=checks
        self.metrics['frontier_evaluations']+=len(touched)
        self.metrics['reclosure_passes']+=passes
        assert len(self.supports)==len(self.active)
        return {'dirty_facts':len(dirty),'rule_checks':checks,
            'changed_facts':sorted(changed),
            'changed_supports':changed_supports,
            'checked_frontiers':sorted(touched),
            'changed_frontiers':changed_frontiers,
            'fixed_point':True}

    def apply(self,event):
        # A forged, untyped, or scope-mismatched event must fail BEFORE mutation.
        assert isinstance(event,dict)
        kind=event.get('kind');fact=event.get('fact');authority=event.get('authority')
        if kind not in ('promote','revoke') or fact not in self.fixture['allowed_events'].get(kind,()):
            raise EventRejected(('unsupported_event',kind,fact))
        required_authority='synthetic_event' if kind=='promote' else 'synthetic_revoker'
        if authority!=required_authority:
            raise EventRejected(('incorrect_authority',authority,kind))
        if kind=='promote':
            new=fact not in self.base
            if new:self.base.add(fact)
        else:
            new=fact in self.base
            if new:self.base.remove(fact)
        update=self._recompute(self._cone({fact}) if new else set())
        self.event_chain=digest({'prior':self.event_chain,'event':event,'ordinal':self.event_count})
        self.event_count+=1
        self.metrics['events']+=1
        if not new:self.metrics['noops']+=1
        update['event_index']=self.event_count-1
        update['event']=deepcopy(event)
        update['noop']=not new
        return update

    def state(self):
        return {'active':sorted(self.active),'base':sorted(self.base),
            'supports':{x:self.supports[x] for x in sorted(self.supports)},
            'frontiers':{x:self.frontiers[x] for x in sorted(self.frontiers)}}

    def snapshot(self):
        data={'version':1,'fixture_sha256':self.fixture_digest,'event_count':self.event_count,
            'event_chain_sha256':self.event_chain,'state':self.state(),'metrics':deepcopy(self.metrics)}
        data['sha256']=digest(data)
        return data

    @classmethod
    def restore(cls,fixture,snapshot):
        data=deepcopy(snapshot)
        given=data.pop('sha256',None)
        if digest(data)!=given:
            raise EventRejected('snapshot checksum invalid; full signed source authority required')
        self=cls.__new__(cls)
        self.fixture=deepcopy(fixture)
        self.fixture_digest=digest(fixture)
        if self.fixture_digest!=data['fixture_sha256'] or data['version']!=1:
            raise EventRejected('snapshot interface or fixture mismatch')
        self._compile()
        state=data['state']
        self.base=set(state['base'])
        self.active=set(state['active'])
        self.supports=deepcopy(state['supports'])
        self.frontiers=deepcopy(state['frontiers'])
        self.event_count=data['event_count']
        self.event_chain=data['event_chain_sha256']
        self.metrics=deepcopy(data['metrics'])
        assert self.base<=self.symbols and self.active<=self.symbols
        assert set(self.supports)==self.active
        assert set(self.frontiers)==set(self.frontier_specs)
        # This is checksum-bound *integrity*, NOT independent source authenticity.
        # Independent reference recomputation in verifier checks correctness.
        return self
