"""Original V104 retained constructor programs over the existing Machine.

The low-level selector/builder grammar is supplied. Only original source-distinct
native improvement and original MDL/support/hash retention choose its executable
subset. Output candidates still require independent native qualification. This
is neither primitive-language invention nor new external authority.
"""
from __future__ import annotations

import ast
from collections import defaultdict
import copy
from dataclasses import asdict
import hashlib
import inspect
import marshal
from pathlib import Path
import re
import subprocess
import time

from .developmental_machine import Capability, canonical, digest
from .decisive_native_frontier import AUTHORITY
from .decisive_native import checked_native_receipt
from . import decisive_native_verify as verifier

SOURCE_PIN={'repository':'heathsanchez/triskelion',
    'commit':'426c54f7c774560e0fabe7213c5ef333b1327c71',
    'path':'experiments/METALOGIC_V104_GENERIC_CONSTRUCTOR_SYNTHESIS.py',
    'sha256':'d00301852efd278be8ac22b848e0c9e56ced7c574980753b2ebc2ef0a3b7cce9'}
OPERATION='v104.ast_constructor'
VERIFICATION_KIND='decisive_v104_constructor_verification'


def _original(source_repo):
    raw=subprocess.check_output(['git','--no-replace-objects','-C',str(source_repo),'show',
        SOURCE_PIN['commit']+':'+SOURCE_PIN['path']],stderr=subprocess.PIPE)
    if digest(raw)!=SOURCE_PIN['sha256']:raise ValueError('original V104 source pin mismatch')
    tree=ast.parse(raw)
    assignments={'SEED','SELECTORS','BUILDERS','PROGRAM_CAP','MIN_SUPPORT'}
    functions={'h','nodes_for_selector','build_expr','program_candidates'}
    definitions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in functions
        or isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in assignments for t in node.targets)]
    namespace={'ast':ast,'copy':copy,'hashlib':hashlib}
    exec(compile(ast.Module(body=definitions,type_ignores=[]),SOURCE_PIN['path'],'exec'),namespace)
    main=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='main')
    start=next(i for i,node in enumerate(main.body) if isinstance(node,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='retained' for t in node.targets))
    # EXACT original assignment, MDL/support/hash block, and null-control assignments.
    retention=main.body[start:start+5]
    if (len(retention)!=5 or not isinstance(retention[1],ast.If)
            or not all(isinstance(n,ast.Assign) for n in retention[2:])):
        raise ValueError('original V104 retention/null source shape changed')
    return namespace,retention


def _signature(value, native):
    if not isinstance(value,(list,tuple)) or len(value)!=2:
        raise ValueError('constructor signature must be selector/builder pair')
    if any(not isinstance(x,(list,tuple)) for x in value):raise ValueError('invalid signature components')
    signature=(tuple(value[0]),tuple(value[1]))
    if not any(canonical(signature)==canonical((selector,builder))
        for selector in native['SELECTORS'] for builder in native['BUILDERS']):
        raise ValueError('constructor signature outside original grammar')
    return signature


def generate_candidates(source_repo, source, *, allowed=None, cap=64):
    """Run original allowed filtering BEFORE original slot enumeration and cap."""
    if type(cap) is not int or not 0<cap<=320:raise ValueError('positive frozen V104 cap<=320 required')
    if not isinstance(source,str):raise ValueError('original constructor consumes source text')
    native,_=_original(source_repo)
    permitted=None if allowed is None else {_signature(value,native) for value in allowed}
    return native['program_candidates'](source,allowed=permitted,cap=cap)


def original_retention(source_repo, supported_program_sources):
    """Execute unchanged original retention/null statements on checked support."""
    native,statements=_original(source_repo);support=defaultdict(set)
    for signature,source in supported_program_sources:
        if not isinstance(source,str) or not source:raise ValueError('exact source task identity required')
        support[_signature(signature,native)].add(source)
    native['support']=support
    exec(compile(ast.Module(body=statements,type_ignores=[]),SOURCE_PIN['path'],'exec'),native)
    return {'signatures':[[list(s),list(b)] for s,b in native['retained']],
        'null_signatures':[[list(s),list(b)] for s,b in native['null']],
        'support':{repr(sig):sorted(values) for sig,values in support.items()},
        'source_minimum':native['MIN_SUPPORT']}


def _live(machine, ids):
    live=set(machine.mt.live_ids(machine.log))&machine.flash_live_ids()
    if any(key not in live for key in ids):raise PermissionError('constructor causal support withdrawn or missing')


def _checker(checker):
    if (not inspect.isfunction(checker) or checker.__closure__ or '<' in checker.__qualname__
            or checker.__defaults__ or checker.__kwdefaults__):
        raise ValueError('independent constructor checker must be an inspectable top-level function')
    path=inspect.getsourcefile(checker)
    if not path:raise ValueError('independent constructor checker source unavailable')
    source=Path(path).resolve()
    return {'path':str(source),'sha256':digest(source.read_bytes()),'module':checker.__module__,
        'qualname':checker.__qualname__,'code_sha256':digest(marshal.dumps(checker.__code__))}


def _scope(protocol_binding):
    return {'protocol_binding':protocol_binding,'input_type':'PythonSourceText','output_type':'ExecutablePythonCandidates',
        'constructor_language':'original supplied V104 selector/builder AST grammar',
        'retention':'original support>=2 / shortest repr / strongest support / frozen hash top2',
        'authority_ceiling':AUTHORITY,'authorization':'LOCAL_RESEARCH_EXECUTION_ONLY'}


def _checked_supports(machine, supports, protocol_binding, source_repo, independent_check):
    if not isinstance(protocol_binding,str) or not re.fullmatch('[0-9a-f]{64}',protocol_binding):
        raise ValueError('exact constructor protocol required')
    if not isinstance(supports,(list,tuple)) or not supports:raise ValueError('nonempty native support list required')
    native,_=_original(source_repo);checker=_checker(independent_check)
    nodes={node.id:node for node in machine.log};pairs=[];proofs=[];evidence=[]
    for item in supports:
        if not isinstance(item,dict) or set(item)!={'context','record','signature','evidence'}:
            raise ValueError('exact source-context/native-record/signature/evidence support required')
        _live(machine,(item['evidence'],))
        event=nodes[item['evidence']]
        if event.kind!='decisive_native_probe' or event.payload.get('receipt')!=item['record']:
            raise ValueError('native constructor support event has wrong receipt lineage')
        raw_context=machine.get(item['context'])
        context=independent_check(machine,item['context'])
        if not isinstance(context,dict) or canonical(context)!=canonical(raw_context):
            raise ValueError('independent constructor context must be exactly reconstructed')
        contract=context['contract']
        if contract['protocol_binding']!=protocol_binding:raise ValueError('constructor support from another protocol')
        record=machine.get(item['record']);baseline=machine.get(context['baseline_record'])
        if record['contract']!=contract or baseline['contract']!=contract or baseline['candidate']!={'replacements':[]}:
            raise ValueError('constructor source/baseline receipt scope mismatch')
        if (record.get('native_suite_authority')!=context.get('native_suite_authority')
                or baseline.get('native_suite_authority')!=context.get('native_suite_authority')):
            raise ValueError('constructor native protected assertion authority mismatch')
        actual=checked_native_receipt(record,machine);old=checked_native_receipt(baseline,machine)
        if (actual.get('status') not in ('PASS_NATIVE','FAIL_NATIVE') or old.get('status')!='FAIL_NATIVE'
                or actual['junit']['tests']!=old['junit']['tests']
                or actual['junit']['failures']>=old['junit']['failures']):
            raise ValueError('constructor needs independently verified native improvement')
        signature=_signature(item['signature'],native)
        replacements=record['candidate']['replacements']
        if len(replacements)!=1:raise ValueError('original V104 produces exactly one source replacement')
        replacement=replacements[0];name=replacement['path']
        identity,files,_=verifier._snapshot(contract['repo_path'],contract['commit'])
        if any(contract[key]!=value for key,value in identity.items()):raise ValueError('constructor source changed')
        verifier._candidate(record['candidate'],files,allow_declared_addopts=record.get('native_suite_authority') is not None)
        row=next((row for row in context['catalog'] if row['id']==verifier.fingerprint(record['candidate'])
            and row['candidate']==record['candidate']),None)
        if row is None or canonical((row['selector'],row['builder']))!=canonical(signature):
            raise ValueError('verified patch does not have original signature provenance')
        cap=context['catalog_spec']['cap']
        programs=generate_candidates(source_repo,files[name].decode(),allowed=[signature],cap=cap)
        if not any(canonical((selector,builder))==canonical(signature) and text==replacement['replacement']
            for selector,builder,text in programs):
            raise ValueError('native patch was not emitted by the original constructor program')
        # Different repository task identities supply different native support; no
        # claim of scientific independence of arbitrary forks follows from this.
        source=contract['repository'];pairs.append((signature,source));evidence.append(item['evidence'])
        proofs.append({'repository':source,'source_commit':contract['commit'],'record':item['record'],
            'baseline_record':context['baseline_record'],'signature':item['signature'],
            'before_failures':old['junit']['failures'],'after_failures':actual['junit']['failures']})
    if _checker(independent_check)!=checker:raise ValueError('constructor checker changed during evidence verification')
    if len(set(evidence))!=len(evidence):raise ValueError('duplicate constructor support event')
    _live(machine,tuple(evidence))
    return original_retention(source_repo,pairs),proofs,checker,tuple(evidence)


def _once(machine,kind,payload,premises=()):
    for node in machine.log:
        if node.kind==kind and node.payload==payload and tuple(node.premises)==tuple(premises):return node.id
    return machine.append(kind,payload,premises)


def retain_constructor(machine,supports,*,protocol_binding,source_repo,independent_check,dependencies=(),supersedes=None):
    started=time.perf_counter()
    try:
        selected,proofs,checker,evidence=_checked_supports(machine,supports,protocol_binding,source_repo,independent_check)
        dependencies=tuple(dependencies);_live(machine,dependencies)
        if len(set(dependencies))!=len(dependencies):raise ValueError('duplicate constructor dependencies')
        if not selected['signatures']:
            return {'status':'UNKNOWN_CONSTRUCTOR_SUPPORT','constructor_id':None,
                'reason':'original source-distinct minimum support/retention requirements not met','retention':selected}
        source={**SOURCE_PIN,'adapter_sha256':digest(Path(__file__).read_bytes()),'independent_checker':checker}
        scope=_scope(protocol_binding)
        if supersedes is not None:
            old=machine.descriptor(supersedes)
            if old.operation!=OPERATION or old.source!=source or old.scope!=scope or supersedes in machine.mt.live_ids(machine.log):
                raise ValueError('constructor restoration requires withdrawn exact original constructor')
            previous=machine.get(old.observation)['supports']
            if set(item['evidence'] for item in previous)&set(evidence) or set(item['record'] for item in previous)&set(item['record'] for item in supports):
                raise ValueError('constructor restoration requires fresh native source evidence lineage')
        # Independently reconstruct once more before admission; this is receipt
        # verification, not a claim that native acquisition was executed twice.
        repeated=_checked_supports(machine,supports,protocol_binding,source_repo,independent_check)
        if canonical(repeated[:3])!=canonical((selected,proofs,checker)):
            raise ValueError('constructor evidence changed before admission')
        authority=_once(machine,'execution_authority_ceiling',AUTHORITY)
        source_id=_once(machine,'source_constructor',{'family':'original-V104-retained-constructor','source':source},(authority,))
        _live(machine,(authority,source_id))
        generation=1+sum(node.kind=='executable_capability' and node.payload.get('operation')==OPERATION
            and node.payload.get('scope')==scope for node in machine.log)
        program=machine.put({'schema':'UDM_ORIGINAL_V104_CONSTRUCTOR_V1','signatures':selected['signatures'],
            'null_signatures':selected['null_signatures'],'source':SOURCE_PIN})
        observation=machine.put({'supports':supports,'proofs':proofs,'retention':selected})
        payload={'family':'original-V104-retained-constructor','program':program,'observation':observation,
            'generation':generation,'supersedes':supersedes,'external_dependencies':list(dependencies)}
        support=machine.append('source_support',payload,(source_id,authority,*evidence,*dependencies))
        verified=machine.append(VERIFICATION_KIND,{'program':program,'observation':observation,'source':source},(support,))
        cap=Capability(OPERATION,source,scope,observation,program,generation,
            (support,*evidence,*dependencies),(verified,),'CONSTRUCTOR_ACQUISITION',supersedes)
        key=machine.append('executable_capability',asdict(cap),(support,verified,*evidence,*dependencies))
        machine.flush()
        return {'status':'WARRANTED_BOUNDED_CONSTRUCTOR','constructor_id':key,
            'signatures':selected['signatures'],'null_signatures':selected['null_signatures'],'retention':selected,
            'verification_boundary':'original supplied constructor subset; future candidate outputs need native verification'}
    except (ValueError,KeyError,PermissionError,OSError,TypeError,subprocess.SubprocessError) as error:
        return {'status':'UNKNOWN_CONSTRUCTOR_EVIDENCE','constructor_id':None,'reason':str(error)}
    finally:
        machine.costs.append({'phase':'original_v104_constructor_retention','seconds':time.perf_counter()-started,
            'native_calls':0,'receipt_verification_and_pure_original_retention':True})


def invoke_constructor(machine,constructor_id,*,protocol_binding,source_repo,independent_check):
    """Reload, recheck lineage and expose executable original constructor programs."""
    started=time.perf_counter()
    try:
        return _invoke_constructor(machine,constructor_id,protocol_binding=protocol_binding,
            source_repo=source_repo,independent_check=independent_check)
    finally:
        machine.costs.append({'phase':'original_v104_constructor_invocation','seconds':time.perf_counter()-started,
            'native_calls':0,'receipt_verification_and_original_program_reload':True})


def _invoke_constructor(machine,constructor_id,*,protocol_binding,source_repo,independent_check):
    cap=machine.descriptor(constructor_id)
    _live(machine,(constructor_id,*cap.dependencies,*cap.evidence))
    if (cap.operation!=OPERATION or cap.transition!='CONSTRUCTOR_ACQUISITION'
            or cap.source!={**SOURCE_PIN,'adapter_sha256':digest(Path(__file__).read_bytes()),'independent_checker':_checker(independent_check)}
            or cap.scope!=_scope(protocol_binding) or len(cap.evidence)!=1 or not cap.dependencies):
        raise ValueError('wrong constructor source, protocol, class or verifier')
    observation=machine.get(cap.observation);program=machine.get(cap.program)
    selected,proofs,checker,evidence=_checked_supports(machine,observation['supports'],protocol_binding,source_repo,independent_check)
    if observation!={'supports':observation['supports'],'proofs':proofs,'retention':selected} or program!={
            'schema':'UDM_ORIGINAL_V104_CONSTRUCTOR_V1','signatures':selected['signatures'],
            'null_signatures':selected['null_signatures'],'source':SOURCE_PIN} or not selected['signatures']:
        raise ValueError('retained constructor executable bytes or native support changed')
    nodes={node.id:node for node in machine.log};support=nodes[cap.dependencies[0]];verified=nodes[cap.evidence[0]]
    external=tuple(cap.dependencies[1+len(evidence):])
    if (tuple(cap.dependencies[1:1+len(evidence)])!=evidence or support.kind!='source_support'
            or support.payload!={'family':'original-V104-retained-constructor','program':cap.program,'observation':cap.observation,
                'generation':cap.generation,'supersedes':cap.supersedes,'external_dependencies':list(external)}
            or len(support.premises)!=2+len(evidence)+len(external)
            or tuple(support.premises[2:])!=(*evidence,*external)
            or nodes[support.premises[0]].kind!='source_constructor'
            or nodes[support.premises[0]].payload!={'family':'original-V104-retained-constructor','source':cap.source}
            or nodes[support.premises[1]].kind!='execution_authority_ceiling'
            or nodes[support.premises[1]].payload!=AUTHORITY
            or tuple(nodes[support.premises[0]].premises)!=(support.premises[1],)
            or verified.kind!=VERIFICATION_KIND or tuple(verified.premises)!=(support.id,)
            or verified.payload!={'program':cap.program,'observation':cap.observation,'source':cap.source}
            or tuple(nodes[constructor_id].premises)!=(support.id,verified.id,*evidence,*external)):
        raise ValueError('constructor causal lineage or independent verification changed')
    _live(machine,(constructor_id,*cap.dependencies,*cap.evidence))
    return {'status':'WARRANTED_BOUNDED_CONSTRUCTOR','constructor_id':constructor_id,
        'signatures':selected['signatures'],'null_signatures':selected['null_signatures'],'generation':cap.generation}
