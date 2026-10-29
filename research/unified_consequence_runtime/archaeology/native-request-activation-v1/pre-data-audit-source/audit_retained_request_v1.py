"""Pre-data-amended independent screening audit, preserving original verifiers.

Original V45 native/typed-source/metadata/build/namespace algorithms are reused.
Only metadata origin, controller module and external remaining-budget bindings
change. No original historical file or query is invented by this transport.
"""
from __future__ import annotations
import argparse
from decimal import Decimal
import hashlib
import importlib.util
import inspect
import json
import math
from pathlib import Path
import sys
from types import CodeType,FunctionType,SimpleNamespace

PREP=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_request_metadata_reconstruction',PREP/'predata_metadata.py')
metadata_reconstruction=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=metadata_reconstruction
_spec.loader.exec_module(metadata_reconstruction)
original=metadata_reconstruction.original_auditor()
for _name,_value in vars(original).items():
    if not _name.startswith('__'):globals().setdefault(_name,_value)
for _name,_value in vars(original).items():
    if isinstance(_value,FunctionType) and _value.__globals__ is vars(original):
        _bound=FunctionType(_value.__code__,globals(),_name,_value.__defaults__,_value.__closure__)
        _bound.__kwdefaults__=_value.__kwdefaults__;globals()[_name]=_bound

ORIGINAL_RECORDS=Path('/workspace/udm-v54/research/unified_consequence_runtime/archaeology/native-namespace-v45/prospective')
ORIGINAL_PREQUERY_COMMIT='b25f18c7fd2cfc3bb1b01dd668535b49254c0604'
ORIGINAL_SCREENING_COMMIT='d557e509315ed884c26c74ed4a26f5dc51788f3c'
MODULE='research.unified_consequence_runtime.qualify_native_frontier_request_v1'
_ARGS=None
_CONTEXT_PROTOCOL=None
_COMPILE_EVENTS=[]
_NAMESPACE_CASES=[]
_METADATA_RECONSTRUCTION=None
_BUDGET_AUDIT=None
_original_source_index_hook=_audit_original_source_index
_original_require_closed=require_closed_dossier


def verify_freeze():
    original.verify_freeze()
    value=json.loads((PREP/'AUDITOR_FREEZE.json').read_text())
    for name,digest in value['source_files_sha256'].items():
        require(sha(Path(name).read_bytes())==digest,'frozen amendment auditor dependency differs: '+name)


def audit_metadata(plan,pre,metadata,pool):
    global _METADATA_RECONSTRUCTION
    require(_ARGS.prequery_commit==ORIGINAL_PREQUERY_COMMIT,
            'original pre-query commit must remain the independently observed original A')
    _METADATA_RECONSTRUCTION=metadata_reconstruction.inspect_original(
        _ARGS.repo,ORIGINAL_RECORDS,ORIGINAL_PREQUERY_COMMIT,ORIGINAL_SCREENING_COMMIT)
    for name,value in (('PREQUERY.json',plan),('PREQUERY_EXECUTION.json',pre),
                       ('METADATA_CURATION.json',metadata),('FROZEN_POOL.json',pool)):
        require(value==json.loads((ORIGINAL_RECORDS/name).read_bytes()),
                'amendment replayed another historical metadata object: '+name)
    return dict(_METADATA_RECONSTRUCTION['metadata_summary'],
        exposure_semantic_fingerprint=_METADATA_RECONSTRUCTION['exposure_reconstruction']['semantic_fingerprint'],
        original_prequery_commit=ORIGINAL_PREQUERY_COMMIT,original_screening_commit=ORIGINAL_SCREENING_COMMIT,
        exposure_record_is_new_reconstruction=True)


def validate_controller_commands(controller,args):
    for index,row in enumerate(controller['cases']):
        argv=row['command']
        require(row['index']==index and len(argv)==14 and isinstance(argv[0],str)
            and Path(argv[0]).is_absolute() and argv[1:5]==['-B','-m',MODULE,'--screen-spec']
            and argv[5]==str(args.requests/('request-'+format(index,'03d')+'.json'))
            and argv[6:10]==['--authority',str(args.records/'SCREENING_AUTHORITY.json'),
                           '--authority-sha256',args.authority_sha256]
            and argv[10:13]==['--runtimes',str(args.compiler_runtimes),'--out'],
            'actual screening argv does not bind the declared new controller/source/authority/runtime')


def validate_outer_budget(a,value,controller,args):
    require(value.get('schema')=='UDM_REQUEST_ACTIVATION_V1_SCREENING_OUTER_BUDGET'
        and value.get('status')=='COMPLETED_WITHIN_ORIGINAL_SCREENING_BUDGET'
        and value.get('scope')=='OUTER_TRANSPORT_COMPLETION_AND_COST_ONLY'
        and value.get('qualified') is True and value.get('returncode')==0
        and type(value.get('returncode')) is int and value.get('timed_out') is False
        and value.get('process_completed') is True and value.get('nested_intervals_not_additive') is True
        and value.get('raw_native_outcomes_accessed') is False and value.get('retry_or_pool_substitution') is False,
        'external remaining-screening-budget interval is incomplete or over budget')
    require(value['source_commit']==args.source_commit and value['prequery_commit']==args.prequery_commit
        and value['authority_sha256']==args.authority_sha256 and value['records_path']==str(args.records),
        'external budget receipt has another source/protocol authority')
    require(value['total_budget_seconds']==7200 and value['prior_charged_outer_wall_seconds']==25.756850843
        and value['declared_remaining_seconds']==7174.243149157,
        'original 7200-second total or charged prior interval was renewed')
    seconds=value['new_outer_wall_seconds']
    require(type(seconds) in (int,float) and math.isfinite(seconds) and seconds>=0
        and seconds>=controller['wall_seconds'],'external whole-outer screening cost is invalid or omits child time')
    combined=Decimal('25.756850843')+Decimal(str(seconds))
    require(combined<=Decimal('7200') and value['combined_outer_wall_seconds']==float(combined),
        'external combined interval does not charge original and new measured outer costs')
    artifacts=value['original_completion_artifacts']
    require(artifacts['ORDERED_PROCESS_COSTS.json']=={'path':str(args.controller_manifest),
                  'sha256':args.controller_manifest_sha256}
        and artifacts['SCREENING_ACTOR_ATTESTATION.json']=={'path':str(args.attestation),
                  'sha256':args.attestation_sha256},'external budget receipt has stale completion artifacts')
    actor=a.bound({'path':str(args.attestation),'sha256':args.attestation_sha256})
    require(value.get('actor_identity')==actor['actor_identity'],
            'external budget receipt has another independent screening actor')
    prior=value['prior_outer']
    require(prior['path']=='/workspace/qualification/native-namespace-v45-prospective-20261028T2335Z/ORDERED_DRIVER_OUTER_COSTS.json'
        and prior['sha256']=='6e0104a9c1cb91078a189b349694496038f9ae21003ec883e13decc4bd7b95d1',
        'original outer-cost raw evidence identity differs')
    old=a.bound({'path':prior['path'],'sha256':prior['sha256']})
    require(old['outer_wall_seconds']==prior['observed_outer_wall_seconds']
        and prior['charged_outer_wall_seconds']==25.756850843
        and Decimal('0')<=Decimal('25.756850843')-Decimal(str(old['outer_wall_seconds']))<Decimal('0.000000001'),
        'original raw observed cost was not conservatively charged')
    transport=PREP/'ordered_screening_request_v1.py'
    require(value['versioned_transport_sha256']==sha(transport.read_bytes())
        and value['command'][1:]==['-B',str(transport),'--child'],
        'external budget source/child command differs from frozen original transport')
    clock=value['outer_process_clock']
    require(clock['clock']=='CLOCK_BOOTTIME' and type(clock['clock_ticks_per_second']) is int
        and clock['clock_ticks_per_second']>0 and type(clock['process_start_ticks']) is int
        and clock['process_start_ticks']>=0,'external process-birth clock identity differs')
    lower=float(Decimal(clock['process_start_ticks'])/clock['clock_ticks_per_second'])
    require(lower==clock['process_start_lower_bound_seconds']
        and seconds==float(Decimal(str(value['finished_clock_boottime_seconds']))-Decimal(str(lower))),
        'external whole-outer clock does not include the declared process-birth bound')
    return {'status':'PASS_UNRENEWED_ORIGINAL_SCREENING_OUTER_BUDGET','prior_outer_seconds':25.756850843,
        'new_outer_seconds':seconds,'combined_outer_seconds':float(combined),
        'controller_wall_seconds':controller['wall_seconds'],'nested_intervals_not_additive':True,
        'complete_lifecycle_cost':'UNKNOWN; engineering/model/final-receipt costs are not granted by this receipt.'}


def _audit_original_source_index(a,controller,path):
    global _BUDGET_AUDIT
    validate_controller_commands(controller,_ARGS)
    value=a.bound({'path':str(_ARGS.outer_budget_receipt),'sha256':_ARGS.outer_budget_sha256})
    _BUDGET_AUDIT=validate_outer_budget(a,value,controller,_ARGS)
    return _original_source_index_hook(a,controller,path)


def _replace_paths(code):
    mapping={name:str(ORIGINAL_RECORDS/name) for name in
             ('METADATA_CURATION.json','FROZEN_POOL.json','PREQUERY_EXECUTION.json')}
    return code.replace(co_consts=tuple(_replace_paths(v) if isinstance(v,CodeType)
        else mapping.get(v,v) if isinstance(v,str) else v for v in code.co_consts))


def prepare_amended_main_binding():
    base=prepare_main_binding()
    namespace=dict(base.__globals__)
    namespace.update(audit_metadata=audit_metadata,verify_freeze=verify_freeze,
                     _audit_original_source_index=_audit_original_source_index)
    result=FunctionType(_replace_paths(base.__code__),namespace,'main',base.__defaults__,base.__closure__)
    result.__kwdefaults__=base.__kwdefaults__;return result


def require_closed_dossier(value):
    _original_require_closed(value)
    require(value.get('original_metadata_reconstruction',{}).get('status')==
          'PASS_ORIGINAL_COMMITTED_METADATA_AND_RECONSTRUCTED_EXPOSURE_ONLY',
          'original metadata reconstruction is unclosed')
    require(value.get('external_screening_budget',{}).get('status')==
          'PASS_UNRENEWED_ORIGINAL_SCREENING_OUTER_BUDGET','external original screening budget is unclosed')


def parse_settings(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('repo','records','requests','sealed','controller-manifest','attestation','out',
                 'compiler-runtimes','outer-budget-receipt'):
        parser.add_argument('--'+name,type=Path,required=True)
    for name in ('authority-sha256','controller-manifest-sha256','attestation-sha256','source-commit',
                 'prequery-commit','outer-budget-sha256'):
        parser.add_argument('--'+name,required=True)
    return parser.parse_args(argv)


def forward_original_arguments(argv):
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--outer-budget-receipt',required=True)
    parser.add_argument('--outer-budget-sha256',required=True)
    _,remaining=parser.parse_known_args(argv)
    return remaining


def main():
    global _ARGS,_CONTEXT_PROTOCOL
    _ARGS=parse_settings()
    require(_ARGS.records==_ARGS.repo/'research/unified_consequence_runtime/archaeology/native-request-activation-v1/prospective',
            'amendment requires the new source-bound protocol/authority record root')
    _CONTEXT_PROTOCOL=json.loads((_ARGS.records/'FRONTIER_PROTOCOL.json').read_text())
    verify_freeze();sys.path.insert(0,str(_ARGS.repo.resolve()))
    from research.unified_consequence_runtime.qualify_experiment_interface_v43 import index_interval
    before=None
    try:
        with index_interval(_ARGS.repo,_ARGS.out.with_name(_ARGS.out.name+'.ROOT_INDEX_INTERVAL')):
            from research.unified_consequence_runtime import qualify_native_frontier_request_v1 as controller
            controller.require_environment_gate(_CONTEXT_PROTOCOL)
            base=prepare_amended_main_binding()
            # The new arguments are consumed here; the original complete audit
            # parser and evidence algorithms remain otherwise byte-exact.
            old_argv=sys.argv[:]
            sys.argv[:]=[old_argv[0],*forward_original_arguments(old_argv[1:])]
            try:base()
            finally:sys.argv[:]=old_argv
    except Exception as error:
        path=_ARGS.out/'RETAINED_CHECKS.json'
        if path.is_file():
            value=json.loads(path.read_bytes());value['status']='UNKNOWN_RETAINED_SCREENING_BINDINGS'
            value.setdefault('checks',[]).append({'check':'amended_audit_root_interval','pass':False,
                                                  'detail':type(error).__name__+': '+str(error)})
            path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
        raise
    path=_ARGS.out/'RETAINED_CHECKS.json';value=json.loads(path.read_bytes())
    value.update(schema='UDM_REQUEST_ACTIVATION_V1_OFFLINE_RETAINED_SCREENING_DOSSIER',
        original_metadata_reconstruction=_METADATA_RECONSTRUCTION,external_screening_budget=_BUDGET_AUDIT,
        declaration_compilations=_COMPILE_EVENTS,namespace_cases=_NAMESPACE_CASES,
        namespace_authority_closed=all(v['status'] in ('REFUSED_NO_CERTIFICATE',
            'PASS_INDEPENDENT_ORIGINAL_DECLARATION_BINDING') for v in _NAMESPACE_CASES),
        independent_compile_seconds=sum(v['seconds'] for v in _COMPILE_EVENTS),
        independent_compile_calls=len(_COMPILE_EVENTS),independent_compilation_test_execution=False)
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
