"""Finite native meta-choice through original Pareto/MSI/MDA mechanisms.

The native caller independently reconstructs receipt profiles. This adapter
checks that reconstruction, retains a callable policy in the one Metatron log,
and never turns UNKNOWN or finite search failure into grammar inadequacy.
No native verifier or external authority is invented by numeric profile binding.
"""
from __future__ import annotations

from dataclasses import asdict
import inspect
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from .developmental_machine import canonical, digest
from .consequence_selection import native_selectors, SOURCE_PINS
from .developmental_choice import choose_verified_profiles, profile_binding, SOURCE_PIN

EVIDENCE_SCHEMA = 'UDM_NATIVE_META_PROFILE_EVIDENCE_V1'
POLICY_KIND = 'native_meta_policy'
EVENT_KIND = 'native_meta_mda_event'
DOMAIN = 'udm-native-meta-choice-v1'


def _live(machine, ids):
    live = set(machine.mt.live_ids(machine.log)) & machine.flash_live_ids()
    if any(key not in live for key in ids):
        raise PermissionError('native meta-policy causal evidence withdrawn or absent')


def _sources(repos):
    # Cached Python modules do not excuse checking original source bytes again.
    for pin in SOURCE_PINS.values():
        raw = subprocess.check_output(['git', '--no-replace-objects', '-C', str(repos/pin['repo']),
            'show', pin['commit']+':'+pin['path']], stderr=subprocess.PIPE)
        if digest(raw) != pin['sha256']:
            raise ValueError('native meta-choice original source changed')
    return native_selectors(str(repos))


def _checker_source(checker):
    if (not inspect.isfunction(checker) or checker.__qualname__ != checker.__name__ or
            not checker.__name__.isidentifier() or checker.__module__ == '__main__'):
        raise ValueError('independent checker must be a top-level importable function')
    module = importlib.import_module(checker.__module__)
    path = inspect.getsourcefile(checker)
    if not path or getattr(module,checker.__name__,None) is not checker:
        raise ValueError('independent checker source or import identity unavailable')
    path = Path(path).resolve()
    if not getattr(module,'__file__',None) or Path(module.__file__).resolve() != path:
        raise ValueError('independent checker imported from a different source')
    return {'path':str(path),'sha256':digest(path.read_bytes()),
            'module':checker.__module__,'name':checker.__name__}


def _objects(machine, evidence_ids, declared=()):
    nodes = {node.id:node for node in machine.log}
    keys = set(declared)
    for key in evidence_ids:
        for field in ('receipt','report','bundle'):
            value = nodes[key].payload.get(field)
            if isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value): keys.add(value)
    for key in keys: machine.get(key)
    return sorted(keys)


def _compile_policy(native, candidates, futures, profiles, binding, selected):
    core = native['core']
    state = core.DevelopmentState(tuple(futures),language=tuple(candidates),policy=candidates[0])
    residual = core.AcquisitionResidual('native bounded future acquisition',tuple(candidates),
        candidates[0],binding['scope']['budget'],cold_success=False)
    repair = core.UpdatePolicy(selected)
    certified = core.certify_repair(state,residual,repair,
        lambda *_: any(profiles[candidates[0]][future][0] for future in futures) and
            all(profiles[selected][future][0] == 0 for future in futures),
        attachment=digest(canonical(binding).encode()))
    after,lineage = core.compile_repair(state,certified)
    if after.policy != selected or after.language != state.language:
        raise ValueError('original MSI compilation changed the declared language')
    return certified,lineage


def _checked(machine, candidates, futures, profiles, evidence_ids, checker):
    if not isinstance(evidence_ids, tuple) or not evidence_ids or len(set(evidence_ids)) != len(evidence_ids):
        raise ValueError('nonempty unique evidence ID tuple required')
    _live(machine, evidence_ids)
    before = _checker_source(checker)
    result = checker(machine, candidates, futures, evidence_ids)
    if _checker_source(checker) != before:
        raise ValueError('independent checker source changed during verification')
    if not isinstance(result, dict) or set(result) != {'schema','profiles','evidence_ids','scope'}:
        raise ValueError('structured independently reconstructed profiles required')
    if (result['schema'] != EVIDENCE_SCHEMA or result['profiles'] != profiles or
            result['evidence_ids'] != list(evidence_ids)):
        raise ValueError('independent native profile/evidence reconstruction mismatch')
    scope = result['scope']
    if not isinstance(scope, dict):
        raise ValueError('native profile scope missing')
    for key in ('protocol_binding','candidate_catalog_sha256','source_binding'):
        if not isinstance(scope.get(key), str) or not re.fullmatch('[0-9a-f]{64}', scope[key]):
            raise ValueError('native profile scope digest missing: '+key)
    if type(scope.get('budget')) is not int or scope['budget'] < 1:
        raise ValueError('frozen positive native acquisition budget required')
    binding = profile_binding(candidates, futures, profiles,
        scope={**scope, 'evidence_ids':list(evidence_ids), 'independent_checker':before,
               'evidence_objects':_objects(machine,evidence_ids,scope.get('receipt_objects',()))})
    for candidate in candidates:
        for future in futures:
            vector = profiles[candidate][future]
            if (len(vector) != 2 or type(vector[0]) is not int or vector[0] not in (0,1) or
                    type(vector[1]) is not int or vector[1] < 0):
                raise ValueError('native profiles require [failure_or_unknown, charged_native_calls]')
    _live(machine, evidence_ids)
    return binding


def choose_meta_decision(machine, candidates, futures, profiles, evidence_ids, *, independent_check, source_repo=None):
    """Choose a finite verified policy; receipt authority stays in the caller.

    The checker must reconstruct all declared profiles from actual independent
    native receipts and exact source/protocol/catalogue identities. A Boolean or
    caller-supplied score is insufficient. No syntactic-equivalence tie breaker.
    """
    started = time.perf_counter()
    try:
        repos = Path(source_repo or os.environ.get('UDM_SOURCE_REPOS','/workspace/repos')).resolve()
        result = {'status':'UNKNOWN_EVIDENCE', 'policy_id':None, 'selected':None,
            'candidates':list(candidates), 'futures':list(futures), 'grammar_extension_licensed':False,
            'expressivity':'UNKNOWN', 'formal_python_refinement':'UNKNOWN', 'external_enforcement':'UNKNOWN'}
        try:
            binding = _checked(machine,candidates,futures,profiles,evidence_ids,independent_check)
            native = _sources(repos)
            choice = choose_verified_profiles(repos/'test', candidates, futures, profiles, evidence_binding=binding)
        except (ValueError,KeyError,PermissionError,OSError,TypeError,subprocess.SubprocessError) as error:
            return {**result,'reason':str(error)}
        result.update(choice=choice)
        if choice['status'] != 'AUTHORIZED_REPAIR':
            return {**result,'status':choice['status'],'reason':choice.get('reason')}
        selected = choice['selected']
        if (not any(profiles[candidates[0]][future][0] for future in futures) or
                any(profiles[selected][future][0] for future in futures)):
            return {**result,'status':'UNKNOWN_OBSTRUCTION',
                    'reason':'no verified failed cold acquisition resolved on every declared future'}
        vectors = [sum((profiles[candidate][future] for future in futures),[]) for candidate in candidates]
        basis = native['minimal_basis'](vectors,[f'{future}:{kind}' for future in futures for kind in ('failure','calls')])
        mda = native['mda']
        checked,lineage = _compile_policy(native,candidates,futures,profiles,binding,selected)
        program = {'schema':'UDM_NATIVE_META_POLICY_V1','op':'SELECT_EXISTING_NATIVE_OPERATION',
            'candidate':selected,'candidates':list(candidates),'futures':list(futures),
            'scope':binding['scope'],'profiles':profiles,'evidence_ids':list(evidence_ids)}
        program_id = machine.put(program)
        binding_id = machine.put(binding)
        sources = {'selection':SOURCE_PIN,'msi_mda':SOURCE_PINS}
        adapter_sha = digest(Path(__file__).read_bytes())
        policy_nodes = []

        class Store:
            def state(self):
                live = set(machine.mt.live_ids(machine.log)) & machine.flash_live_ids()
                caps = {key:{'id':key,'evidence_only':True} for key in evidence_ids if key in live}
                for node in machine.log:
                    if node.kind == POLICY_KIND and node.id in live:
                        record = node.payload['mda_record']; caps[record['id']] = record
                return {'capabilities':caps}
            def append(self,event):
                payload = {'event':event,'binding':binding_id}
                kind = EVENT_KIND
                if event['type'] == 'admit':
                    kind = POLICY_KIND
                    payload.update(program=program_id,mda_record=event['record'],sources=sources,
                        adapter_sha256=adapter_sha,msi_lineage=machine.put(asdict(lineage)),
                        observation_basis=basis)
                node = machine.append(kind,payload,evidence_ids); machine.flush()
                if kind == POLICY_KIND: policy_nodes.append(node)
                return node

        class Adapter:
            name = DOMAIN
            verifier_id = 'source-bound-independent-native-meta:'+digest(canonical(binding).encode())
            contract = mda.IRContract('FrozenNativeMetaObligation','ExistingNativePolicyAST','IndependentNativeProfile',
                'Select existing executable operation; language unchanged','Complete declared native profile carrier',
                'Source-bound independent native receipts and original MSI policy certificate')
            def assess(self,current,obligation):
                admitted = any(rec.get('repair',{}).get('payload') == program_id for rec in current['capabilities'].values())
                return mda.Evidence('verified' if admitted else 'unknown',mda.assessment_claim(current,obligation),
                    self.verifier_id,{'binding':binding_id,'program':program_id},
                    residual=None if admitted else {'kind':'AcquisitionResidual','binding':binding_id},scope=self.name)
            def propose(self,*_):
                yield mda.Repair('policy','native-existing-operation-policy',program_id,self.name,evidence_ids)
            def verify(self,current,obligation,proposal):
                fresh = _checked(machine,candidates,futures,profiles,evidence_ids,independent_check)
                if fresh != binding: raise ValueError('native profile authority changed before admission')
                return mda.Evidence('verified',proposal.id,self.verifier_id,
                    {'binding':binding_id,'program':program_id,'msi_attachment':checked.attachment},scope=self.name)
            def attach(self,*_):
                return {'program':program_id,'binding':binding_id,'transition':'DEVELOPMENTAL_POLICY_IMPROVEMENT'}

        run = mda.Developer(Store(),Adapter()).run(mda.Obligation(DOMAIN,{'binding':binding_id},budget=1,kind='policy'))
        transition = 'DEVELOPMENTAL_POLICY_IMPROVEMENT' if policy_nodes else 'ACTIVATION'
        if not policy_nodes:
            live = set(machine.mt.live_ids(machine.log)) & machine.flash_live_ids()
            policy_nodes = [node.id for node in machine.log if node.kind == POLICY_KIND and node.id in live
                and node.payload['program'] == program_id and node.payload['binding'] == binding_id]
        if run.verdict != 'verified' or len(policy_nodes) != 1:
            return {**result,'status':'UNKNOWN_CHOICE' if len(policy_nodes)>1 else 'UNKNOWN_EVIDENCE','mda':asdict(run)}
        invoke_meta_policy(machine,policy_nodes[0],protocol_binding=binding['scope']['protocol_binding'],
            candidate_catalog_sha256=binding['scope']['candidate_catalog_sha256'])
        return {**result,'status':'WARRANTED_BOUNDED_POLICY_SELECTION','selected':selected,
            'policy_id':policy_nodes[0],'program':program_id,'binding':binding_id,'mda':asdict(run),
            'observation_basis':basis,'transition':transition}
    finally:
        machine.costs.append({'phase':'native_meta_decision','seconds':time.perf_counter()-started,
            'native_calls_included_in_profiles':True,
            'observation_basis_scope':'finite declared profile distinctions only'})


def invoke_meta_policy(machine, policy_id, *, protocol_binding, candidate_catalog_sha256):
    """Replay offline receipt authority, then return a scoped policy choice.

    This never reruns native tests. The independently source-bound checker must
    traverse its raw evidence; caller still enforces native task applicability.
    """
    nodes = {node.id:node for node in machine.log}
    node = nodes[policy_id]
    if node.kind != POLICY_KIND:
        raise ValueError('not an admitted native meta-policy')
    _live(machine,(policy_id,*node.premises))
    payload = node.payload
    if (payload['adapter_sha256'] != digest(Path(__file__).read_bytes()) or
            payload['sources'] != {'selection':SOURCE_PIN,'msi_mda':SOURCE_PINS}):
        raise ValueError('native meta-policy implementation/source changed')
    program, binding = machine.get(payload['program']), machine.get(payload['binding'])
    checker = binding['scope']['independent_checker']
    if digest(Path(checker['path']).read_bytes()) != checker['sha256']:
        raise ValueError('independent native checker source changed')
    check_function = getattr(importlib.import_module(checker['module']),checker['name'])
    if _checker_source(check_function) != checker:
        raise ValueError('independent native checker import binding changed')
    if (program['schema'] != 'UDM_NATIVE_META_POLICY_V1' or program['op'] != 'SELECT_EXISTING_NATIVE_OPERATION' or
            program['scope'] != binding['scope'] or
            program['scope']['protocol_binding'] != protocol_binding or
            program['scope']['candidate_catalog_sha256'] != candidate_catalog_sha256 or
            tuple(program['evidence_ids']) != tuple(node.premises) or
            tuple(binding['scope']['evidence_ids']) != tuple(node.premises) or
            payload['mda_record']['repair']['payload'] != payload['program'] or
            tuple(payload['mda_record']['repair']['dependencies']) != tuple(node.premises)):
        raise ValueError('native meta-policy scope, program or causal lineage mismatch')
    fresh_binding = _checked(machine,tuple(program['candidates']),tuple(program['futures']),
        program['profiles'],tuple(node.premises),check_function)
    if fresh_binding != binding:
        raise ValueError('offline native receipt reconstruction differs from retained policy')
    repos = Path(os.environ.get('UDM_SOURCE_REPOS','/workspace/repos')).resolve()
    native = _sources(repos)
    record = payload['mda_record']
    expected_repair = native['mda'].Repair('policy','native-existing-operation-policy',
        payload['program'],DOMAIN,tuple(node.premises))
    verifier_id = 'source-bound-independent-native-meta:'+digest(canonical(binding).encode())
    certificate = {'binding':payload['binding'],'program':payload['program'],
        'msi_attachment':digest(canonical(binding).encode())}
    if (payload['event'].get('type') != 'admit' or payload['event'].get('record') != record or
            record.get('id') != native['mda'].admission_id(expected_repair,verifier_id) or
            record.get('status') != 'verified' or record.get('level') != 'K1' or
            canonical(record.get('repair')) != canonical(asdict(expected_repair)) or
            record['evidence'].get('verdict') != 'verified' or
            record['evidence'].get('claim') != expected_repair.id or
            record['evidence'].get('verifier') != verifier_id or
            record['evidence'].get('scope') != DOMAIN or
            record['evidence'].get('certificate') != certificate or
            record.get('attachment') != {'program':payload['program'],'binding':payload['binding'],
                'transition':'DEVELOPMENTAL_POLICY_IMPROVEMENT'}):
        raise ValueError('native meta-policy MDA admission certificate mismatch')
    choice = choose_verified_profiles(repos/'test',tuple(program['candidates']),tuple(program['futures']),
        program['profiles'],evidence_binding=binding)
    if choice.get('selected') != program['candidate'] or choice['status'] != 'AUTHORIZED_REPAIR':
        raise ValueError('retained policy differs from original verified choice')
    objects = _objects(machine,node.premises,binding['scope'].get('receipt_objects',()))
    if objects != binding['scope']['evidence_objects']:
        raise ValueError('native profile evidence object carrier changed')
    _,lineage = _compile_policy(native,program['candidates'],program['futures'],program['profiles'],
        binding,program['candidate'])
    vectors = [sum((program['profiles'][candidate][future] for future in program['futures']),[])
        for candidate in program['candidates']]
    basis = native['minimal_basis'](vectors,[f'{future}:{kind}' for future in program['futures']
        for kind in ('failure','calls')])
    if (canonical(machine.get(payload['msi_lineage'])) != canonical(asdict(lineage)) or
            payload['observation_basis'] != basis):
        raise ValueError('native meta-policy retained MSI lineage or observation basis changed')
    _live(machine,(policy_id,*node.premises))
    return program['candidate']
