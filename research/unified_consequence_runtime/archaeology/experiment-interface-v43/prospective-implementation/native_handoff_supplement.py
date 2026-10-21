"""Local diagnostic infrastructure; no prospective source or native oracle double."""
from pathlib import Path
import copy
import hashlib
import json
import os
import sys
import time
from unittest.mock import patch

from research.unified_consequence_runtime import native_environment_v43 as environment
from research.unified_consequence_runtime import qualify_native_frontier_v43 as controller
from research.unified_consequence_runtime import native_execution_v43 as worker
from research.unified_consequence_runtime import native_build_v43 as build
from research.unified_consequence_runtime.developmental_machine_v43 import Machine
from research.unified_consequence_runtime.native_runtime_v43 import NativeRuntimeV43
from research.unified_consequence_runtime.native_v43_test_support import make_project, MODERN_PYTHON


def reporting_controls(destination):
 """Exercise refusal/cost/manifest wiring; no native result is supplied."""
 destination.mkdir(parents=True,exist_ok=False)
 machine=Machine(Path(os.environ.get('UDM_COMPONENTS','/workspace/components')),
  destination/'machine-state',destination/'evaluator',destination/'unused-config.json')
 refused={'schema':'UDM_SOURCE_ENVIRONMENT_ADMISSION_V42','status':'UNKNOWN_ORIGINAL_FIXTURE_REFUSAL',
  'reason':'original diagnostic refusal','source':{'diagnostic_only':True}}
 result=environment._attach_interface(machine,refused,destination/'unused-build-output')
 assert result==dict(refused,schema='UDM_SOURCE_ENVIRONMENT_ADMISSION_V43')
 assert refused['schema']=='UDM_SOURCE_ENVIRONMENT_ADMISSION_V42'
 snapshot=worker.build_snapshot()
 spec={'repo':'fixture/reporting-wiring-only'}
 report={'schema':'UDM_ADMISSION_ONLY_CASE_V43','repository':spec['repo'],
  'spec_sha256':worker.fingerprint(spec),'status':'UNKNOWN_ORIGINAL_FIXTURE_REFUSAL','eligible':False,
  'screening_mode':'ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH','total_wall_seconds':0,
  'controller_attempts':{'native_calls':0,'collection_calls':0},'accounting_complete':True,
  'build_attempts':{'before':copy.deepcopy(snapshot),'after':copy.deepcopy(snapshot)}}
 case=destination/'SCREENING_CASE.json';case.write_text(controller.canonical(report)+'\n')
 envelope=controller.screening_envelope(report,case)
 assert envelope['costs']=={'native_calls':0,'collection_calls':0}
 assert envelope['build_costs']['build_calls']==envelope['build_costs']['verification_attempts']==0
 synthetic=copy.deepcopy(report)
 synthetic['build_attempts']['after']['builder_attempts']['build_calls']+=2
 synthetic['build_attempts']['after']['builder_attempts']['build_seconds']+=1.25
 synthetic['build_attempts']['after']['verification_attempts']+=3
 delta=controller._screening_build_costs(synthetic)
 assert (delta['build_calls'],delta['build_seconds'],delta['verification_attempts'])==(2,1.25,3)
 records={}
 def bound(name,value):
  descriptor=controller._write_record(destination/name,value)
  records[descriptor['sha256']]=value
  return descriptor
 gate={'diagnostic_only':True}
 value={'environment_gate':gate,'interface_gate':gate,'interface_archive_audit':gate,'requested_roles':0}
 value['prequery']=bound('PREQUERY.json',{'state':'PREQUERY_COMMITTED_BEFORE_QUERIES'})
 value['pool']=bound('POOL.json',{'pool':[spec]})
 authority=bound('AUTHORITY.json',{'schema':controller.AUTHORITY_SCHEMA,'operation':'screen'})
 meter=bound('METER.json',{'schema':'UDM_ORDERED_SCREENING_METER_V43','authority_sha256':authority['sha256'],
  'source_commit':'0'*40,'pending':None,'accounting_complete':True,'cases':[{'index':0,
  'spec_sha256':worker.fingerprint(spec),'accounting_complete':True,'report':envelope['sealed_report']}]})
 audit=bound('AUDIT.json',{'status':'PASS_ADMISSION_ONLY_SCREENING_AUDIT','pool_sha256':value['pool']['sha256'],
  'reports_sha256':worker.fingerprint([envelope]),'eligibility_rule':'PASS_NATIVE_OR_FAIL_NATIVE_IDENTICAL',
  'all_screened_cases_and_costs_retained':True})
 manifest={'schema':'UDM_ADMISSION_ONLY_SCREENING_V43','pool_sha256':value['pool']['sha256'],
  'prequery_sha256':value['prequery']['sha256'],'environment_gate':gate,'interface_gate':gate,
  'interface_archive_audit':gate,'independent_screener':True,'search_or_policy_outcomes_accessed':False,
  'learner_future_source_accessed':False,'reports':[envelope],'independent_audit':audit,
  'screening_authority':authority,'screening_meter':meter}
 value['screening']=bound('MANIFEST.json',manifest)
 metadata=destination/'METADATA.json';metadata.write_text(controller.canonical({'selected':[]})+'\n')
 value['metadata_sha256']=controller.digest(metadata.read_bytes())
 source=Path(controller.__file__).read_bytes()
 def check_source(command):
  assert command[-1]=='0'*40+':research/unified_consequence_runtime/qualify_native_frontier_v43.py'
  return source
 # These doubles exercise only bound-file/committed-source transport. This
 # requested-zero diagnostic is never a prospective authority or native oracle.
 with patch.object(controller,'_bound_json',lambda record:records[record['sha256']]), \
      patch.object(controller,'_committed_record',lambda *args,**kwargs:None), \
      patch.object(controller,'METADATA',metadata), \
      patch.object(controller.subprocess,'check_output',check_source):
  assert controller.require_screening_manifest(value)==manifest
  invalid=copy.deepcopy(envelope['build_costs']);invalid['build_calls']=-1
  try:controller._validate_screening_build_costs(invalid)
  except ValueError:pass
  else:raise AssertionError('negative build accounting accepted')
 result={'schema':'UDM_V43_REPORTING_WIRING_CONTROLS_V1','status':'PASS_WIRING_ONLY',
  'native_oracle_doubles':False,'requested_zero_manifest_is_diagnostic_only':True,
  'controls':['original-refusal-preserved','native-cost-shape-preserved','separate-build-delta',
              'strict-manifest-acceptance','exact-controller-source-guard','negative-delta-rejected']}
 (destination/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 return result


if len(sys.argv)==3 and sys.argv[1]=='--reporting-only':
 print(json.dumps(reporting_controls(Path(sys.argv[2])),sort_keys=True))
 raise SystemExit(0)

out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
repo=Path(environment.__file__).resolve().parents[2]
names=('native_environment_v43.py','qualify_native_frontier_v43.py','native_runtime_v43.py',
       'native_materialization_v43.py','native_build_v43.py','native_execution_v43.py')
snapshots={name:hashlib.sha256((repo/'research/unified_consequence_runtime'/name).read_bytes()).hexdigest() for name in names}
for name in names:(out/name).write_bytes((repo/'research/unified_consequence_runtime'/name).read_bytes())
report={'schema':'UDM_V43_REAL_ENVIRONMENT_HANDOFF_SUPPLEMENT_V1','status':'UNKNOWN',
 'scope':'Fixed local original Hatch VCS fixture infrastructure; prepared-context handoff, not a claim of original network provisioning or prospective science.',
 'verdicts':{f'G{i}':'UNKNOWN' for i in range(2,7)},'source_sha256':snapshots,
 'native_before':worker.attempt_snapshot(),'build_before':build.attempt_snapshot()}
started=time.monotonic()
try:
 report['reporting_controls']=reporting_controls(out/'reporting-controls')
 actual_environment=worker.environment_identity(str(MODERN_PYTHON))
 alpha=make_project(out/'alpha','handoff_alpha',actual_environment,expected=0)
 beta=make_project(out/'beta','handoff_beta',actual_environment,expected=1)
 machine=Machine(Path(os.environ.get('UDM_COMPONENTS','/workspace/components')),out/'machine-state',out/'evaluator',out/'unused-config.json')
 contexts={}
 for label,case in (('alpha',alpha),('beta',beta)):
  old_contract=dict(case.contract,schema=environment.previous.execution.SCHEMA);old_contract.pop('generated_build')
  old_policy=dict(case.policy,schema=environment.previous.execution.POLICY_SCHEMA)
  prepared={'status':'PREPARED','contract':old_contract,'authority':case.authority,'policy':old_policy,
   'source_boundaries':{'base_commit':case.base,'augmented_commit':case.augmented},
   'fixture_setup_origin':'Actual immutable source/suite/environment context; no original transport result is asserted.'}
  environment.record_admission_request(machine,{'repo':case.contract['repository'],'base_commit':case.base,
   'head_commit':case.augmented},case.contract['protocol_binding'])
  (out/(label+'-prepared-input.json')).write_text(json.dumps(prepared,sort_keys=True)+'\n')
  warm=environment._attach_interface(machine,prepared,out/(label+'-interface'))
  assert warm['status']=='PREPARED' and warm['contract']['generated_build'] is not None
  certificate=worker.collect(warm['contract'],warm['authority'],out/(label+'-collection'),policy=warm['policy'])
  runtime=NativeRuntimeV43(machine,warm['contract'],warm['authority'],certificate,warm['policy'],
   out/(label+'-native'),materialization_capability=warm['materialization_capability'])
  probe=controller.native_probe(machine,runtime,{'replacements':[]},'real-handoff-'+label)
  expected='PASS_NATIVE' if label=='alpha' else 'FAIL_NATIVE'
  assert probe['receipt']['status']==expected
  assert probe['receipt']['junit']['tests']==2
  prefix=(warm['materialization_binding']['capability_id'],warm['materialization_binding']['consequence_id'])
  assert tuple(probe['producer']['dependencies'])==prefix
  event=next(node for node in machine.log if node.id==probe['evidence'])
  assert tuple(event.premises)==(runtime.source,runtime.authority,*prefix)
  actual=controller.checked_record(machine.get(probe['record']),machine)
  cache={worker.fingerprint(machine.get(probe['record'])):actual}
  assert controller.checked_record(machine.get(probe['record']),machine,cache=cache)==actual
  contexts[label]={'setup':warm,'certificate':certificate,'runtime':runtime,'probe':probe,'cache':cache}
  (out/(label+'-warm-context.json')).write_text(json.dumps({'setup':warm,'certificate':certificate,'probe':probe},sort_keys=True)+'\n')
 assert contexts['alpha']['setup']['materialization_capability']==contexts['beta']['setup']['materialization_capability']
 beta_context=contexts['beta'];warm=beta_context['setup'];runtime=beta_context['runtime']
 corrected=controller.native_probe(machine,runtime,beta.candidate(),'real-handoff-fixed-beta')
 assert corrected['receipt']['status']=='PASS_NATIVE'
 cold=beta_context['probe'];order=[worker.fingerprint(cold['candidate']),worker.fingerprint(corrected['candidate'])]
 episode={'within_budget':True,'budget':2,'attempts':[cold['record'],corrected['record']],'winner':order[1]}
 assert controller._check_episode(machine,episode,order,2,contract=warm['contract'],dependencies=())
 reports=[{'repository':case.contract['repository'],'spec_sha256':worker.fingerprint({'repo':case.contract['repository']}),
  'status':contexts[label]['probe']['receipt']['status'],'eligible':True,
  'screening_mode':'ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH'} for label,case in (('alpha',alpha),('beta',beta))]
 selected=controller.select_screened_roles([{'repo':case.contract['repository']} for case in (alpha,beta)],reports,2)
 assert len(selected)==2
 witness=warm['materialization_binding']['consequence_id']
 machine.append('revoke',{'target':witness,'reason':'exact invocation witness handoff qualification'})
 machine.flush()
 before_native=worker.attempt_snapshot();before_build=build.attempt_snapshot()
 denied=[]
 for label,operation in (
  ('cached-profile',lambda:controller.checked_record(machine.get(cold['record']),machine,cache=beta_context['cache'])),
  ('uncached-profile',lambda:controller.checked_record(machine.get(cold['record']),machine)),
  ('new-native-probe',lambda:controller.native_probe(machine,runtime,beta.candidate(),'withdrawn'))):
  try:operation()
  except PermissionError:denied.append(label)
  else:raise AssertionError('withdrawn witness accepted '+label)
 arm={'schema':controller.AGENT_SCHEMA,'candidate_budget':8,'total_acquisition_native_calls':512,
  'total_acquisition_wall_seconds':3600,'protocol_binding':warm['contract']['protocol_binding'],
  'contract':warm['contract'],'authority':warm['authority'],'certificate':beta_context['certificate'],'policy':warm['policy'],
  'machine_context':controller._machine_context(machine),'common_acquisition_costs':[],
  'common_acquisition_wall_seconds':0,'meter_path':str(out/'ARM_METER.json'),
  'candidate_catalog':[{'id':worker.fingerprint(beta.candidate()),'candidate':beta.candidate()}]}
 try:controller._execute_agent_candidate(arm,beta.candidate(),out/'withdrawn-agent-native')
 except PermissionError:denied.append('actual-agent-worker-path')
 else:raise AssertionError('withdrawn witness reached agent native worker')
 assert worker.attempt_snapshot()==before_native and build.attempt_snapshot()==before_build
 unrelated=controller.native_probe(machine,contexts['alpha']['runtime'],{'replacements':[]},'unrelated-live-alpha')
 assert unrelated['receipt']['status']=='PASS_NATIVE'
 assert set(machine.mt.live_ids(machine.log))==machine.flash_live_ids()
 report.update(status='PASS_BOUNDED_REAL_NATIVE_ENVIRONMENT_HANDOFF',original_statuses={
  label:context['probe']['receipt']['status'] for label,context in contexts.items()},selected=selected,
  denied_before_any_producer=denied,exact_revoked_witness=witness,
  shared_generic_instrument=warm['materialization_capability'],unrelated_native_status=unrelated['receipt']['status'],
  closure_agrees=True,machine_costs=machine.costs)
finally:
 report.update(seconds=time.monotonic()-started,native_after=worker.attempt_snapshot(),build_after=build.attempt_snapshot())
 report['source_unchanged']=all(hashlib.sha256((repo/'research/unified_consequence_runtime'/name).read_bytes()).hexdigest()==sha for name,sha in snapshots.items())
 if not report['source_unchanged']:report['status']='UNKNOWN_SOURCE_CHANGED_DURING_HANDOFF'
 (out/'RESULT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({key:report[key] for key in ('status','seconds','source_unchanged')},sort_keys=True))
