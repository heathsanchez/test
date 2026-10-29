"""Source-free tests for amended transport; original metadata stays immutable."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest

HERE=Path(__file__).resolve().parent


def module():
    path=HERE/'audit_retained_request_v1.py'
    assert path.is_file(), 'versioned screening auditor missing'
    spec=importlib.util.spec_from_file_location('request_v1_screening_audit',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def strings(code):
    for item in code.co_consts:
        if hasattr(item,'co_consts'):yield from strings(item)
        elif isinstance(item,str):yield item


def test_existing_metadata_and_new_authority_paths_are_separate():
    m=module();fn=m.prepare_amended_main_binding()
    literals=set(strings(fn.__code__))
    for name in ('FROZEN_POOL.json','PREQUERY_EXECUTION.json','METADATA_CURATION.json'):
        assert str(m.ORIGINAL_RECORDS/name) in literals
        assert name not in literals
    assert 'SCREENING_AUTHORITY.json' in literals
    assert 'FRONTIER_PROTOCOL.json' in literals
    assert 'UDM_NATIVE_CLI_AUTHORITY_V45' in literals
    assert 'research/unified_consequence_runtime/native_execution_v45.py' in literals


def test_original_metadata_and_native_algorithms_are_reused():
    m=module()
    assert m.audit_native.__code__ is m.original.audit_native.__code__
    assert m.audit_partial_packets.__code__ is m.original.audit_partial_packets.__code__
    assert m.derive_authority.__code__ is m.original.derive_authority.__code__
    assert m.select_compiler_profile.__code__ is m.original.select_compiler_profile.__code__
    assert m.HERE==m.original.HERE


@pytest.mark.parametrize('change',('none','old-module','request-path','authority-path','runtime-path','extra-argument'))
def test_actual_new_controller_command_has_exact_source_and_authority(change):
    m=module();args=SimpleNamespace(requests=Path('/synthetic/requests'),records=Path('/synthetic/new-records'),
        compiler_runtimes=Path('/synthetic/runtime-paths.json'),authority_sha256='a'*64)
    argv=['/synthetic/controller/bin/python','-B','-m',m.MODULE,
          '--screen-spec','/synthetic/requests/request-000.json','--authority','/synthetic/new-records/SCREENING_AUTHORITY.json',
          '--authority-sha256','a'*64,'--runtimes','/synthetic/runtime-paths.json','--out','/synthetic/screening/case-000']
    if change=='old-module':argv[3]='research.unified_consequence_runtime.qualify_native_frontier_v45'
    elif change=='request-path':argv[5]='/synthetic/requests/request-001.json'
    elif change=='authority-path':argv[7]='/synthetic/old-records/SCREENING_AUTHORITY.json'
    elif change=='runtime-path':argv[11]='/synthetic/stale-runtime.json'
    elif change=='extra-argument':argv+=['--catalog-spec','unannounced.json']
    controller={'cases':[{'index':0,'command':argv}]}
    if change=='none':m.validate_controller_commands(controller,args)
    else:
        with pytest.raises(ValueError):m.validate_controller_commands(controller,args)


def test_original_exposure_record_is_reconstructed_not_loaded_from_old_missing_file():
    m=module()
    assert m.original.audit_metadata.__code__ is not m.audit_metadata.__code__
    assert 'PRIOR_EXPOSURE.json' not in set(strings(m.audit_metadata.__code__))
    assert m.ORIGINAL_PREQUERY_COMMIT=='b25f18c7fd2cfc3bb1b01dd668535b49254c0604'
    assert m.ORIGINAL_SCREENING_COMMIT=='d557e509315ed884c26c74ed4a26f5dc51788f3c'


def test_new_auditor_retains_every_original_cli_binding():
    m=module();argv=[]
    for name in ('repo','records','requests','sealed','controller-manifest','attestation','out',
                 'compiler-runtimes','outer-budget-receipt'):
        argv+=['--'+name,'/synthetic/'+name]
    for name in ('authority-sha256','controller-manifest-sha256','attestation-sha256','source-commit',
                 'prequery-commit','outer-budget-sha256'):
        argv+=['--'+name,'held-'+name]
    args=m.parse_settings(argv)
    assert args.requests==Path('/synthetic/requests')
    assert args.source_commit=='held-source-commit'
    assert args.authority_sha256=='held-authority-sha256'
    assert args.controller_manifest==Path('/synthetic/controller-manifest')
    assert args.attestation_sha256=='held-attestation-sha256'


@pytest.mark.parametrize('change',('none','wrong-actor','wrong-source','renewed-prior','bad-clock','over-budget'))
def test_outer_budget_cannot_replay_actor_authority_or_renew_original_time(tmp_path,change):
    m=module();controller={'wall_seconds':1.0}
    manifest=tmp_path/'controller.PARSER_FIXTURE.json';manifest.write_text(json.dumps(controller))
    actor=tmp_path/'actor.PARSER_FIXTURE.json';actor.write_text(json.dumps({'actor_identity':'/fixture/independent'}))
    args=SimpleNamespace(source_commit='b'*40,prequery_commit=m.ORIGINAL_PREQUERY_COMMIT,
        authority_sha256='a'*64,records=Path('/synthetic/new-records'),controller_manifest=manifest,
        controller_manifest_sha256=m.sha(manifest.read_bytes()),attestation=actor,
        attestation_sha256=m.sha(actor.read_bytes()))
    value={'schema':'UDM_REQUEST_ACTIVATION_V1_SCREENING_OUTER_BUDGET',
      'status':'COMPLETED_WITHIN_ORIGINAL_SCREENING_BUDGET','scope':'OUTER_TRANSPORT_COMPLETION_AND_COST_ONLY',
      'qualified':True,'returncode':0,'timed_out':False,'process_completed':True,
      'nested_intervals_not_additive':True,'raw_native_outcomes_accessed':False,'retry_or_pool_substitution':False,
      'source_commit':args.source_commit,'prequery_commit':args.prequery_commit,'authority_sha256':args.authority_sha256,
      'records_path':str(args.records),'actor_identity':'/fixture/independent',
      'total_budget_seconds':7200.0,'prior_charged_outer_wall_seconds':25.756850843,
      'declared_remaining_seconds':7174.243149157,'new_outer_wall_seconds':2.0,
      'combined_outer_wall_seconds':27.756850843,
      'original_completion_artifacts':{'ORDERED_PROCESS_COSTS.json':{'path':str(manifest),'sha256':args.controller_manifest_sha256},
          'SCREENING_ACTOR_ATTESTATION.json':{'path':str(actor),'sha256':args.attestation_sha256}},
      'prior_outer':{'path':'/workspace/qualification/native-namespace-v45-prospective-20261028T2335Z/ORDERED_DRIVER_OUTER_COSTS.json',
          'sha256':'6e0104a9c1cb91078a189b349694496038f9ae21003ec883e13decc4bd7b95d1',
          'observed_outer_wall_seconds':25.756850842999484,'charged_outer_wall_seconds':25.756850843},
      'versioned_transport_sha256':m.sha((HERE/'ordered_screening_request_v1.py').read_bytes()),
      'command':['/synthetic/python','-B',str(HERE/'ordered_screening_request_v1.py'),'--child'],
      'outer_process_clock':{'clock':'CLOCK_BOOTTIME','clock_ticks_per_second':100,
          'process_start_ticks':10000,'process_start_lower_bound_seconds':100.0},
      'finished_clock_boottime_seconds':102.0}
    if change=='wrong-actor':value['actor_identity']='/fixture/other'
    elif change=='wrong-source':value['source_commit']='c'*40
    elif change=='renewed-prior':value['prior_charged_outer_wall_seconds']=0.
    elif change=='bad-clock':value['outer_process_clock']['process_start_lower_bound_seconds']=99.
    elif change=='over-budget':value['new_outer_wall_seconds']=7200.;value['combined_outer_wall_seconds']=7225.756850843
    if change=='none':
        assert m.validate_outer_budget(m.old.Audit(),value,controller,args)['status']=='PASS_UNRENEWED_ORIGINAL_SCREENING_OUTER_BUDGET'
    else:
        with pytest.raises(ValueError):m.validate_outer_budget(m.old.Audit(),value,controller,args)


@pytest.mark.parametrize('equals',(False,True))
def test_original_argument_forwarding_accepts_every_standard_new_flag_form(equals):
    m=module();old=['--repo','/synthetic/repo','--source-commit','held-source']
    if equals:new=['--outer-budget-receipt=/synthetic/budget.json','--outer-budget-sha256='+'a'*64]
    else:new=['--outer-budget-receipt','/synthetic/budget.json','--outer-budget-sha256','a'*64]
    assert m.forward_original_arguments(old+new)==old


def test_help_is_source_free_and_lists_the_complete_new_contract(capsys):
    m=module()
    with pytest.raises(SystemExit) as stopped:m.parse_settings(['--help'])
    assert stopped.value.code==0
    assert '--outer-budget-receipt' in capsys.readouterr().out
