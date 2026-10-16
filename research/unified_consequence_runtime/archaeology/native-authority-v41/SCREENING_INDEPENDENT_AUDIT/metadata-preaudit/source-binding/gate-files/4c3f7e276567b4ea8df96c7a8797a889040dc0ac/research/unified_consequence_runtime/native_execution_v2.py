"""Versioned native collection authority; original verifiers remain immutable.

Certificates are independently reconstructed from original source at use time.
Original tests and explicitly licensed plugins remain trusted Python execution;
this finite authority check is not a hostile-process sandbox or a Python proof.
"""
from __future__ import annotations
import base64
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time

from . import decisive_native_verify as original
from . import native_admission_v2 as admission

SCHEMA='UDM_GENERIC_NATIVE_PYTEST_V2'
CERTIFICATE_SCHEMA='UDM_NATIVE_ADMISSION_CERTIFICATE_V2'
POLICY_SCHEMA='UDM_NATIVE_EXECUTION_POLICY_V2'
ADMISSION_REVISION='2.1'
canonical=original.canonical
fingerprint=original.fingerprint
sha256=original.sha256
_LOADED_SOURCE_SHA256=sha256(Path(__file__).read_bytes())


def _runner_hash():
    if sha256(Path(__file__).read_bytes())!=_LOADED_SOURCE_SHA256:
        raise ValueError('UNKNOWN_VERIFIER_SOURCE_MUTATION')
    return _LOADED_SOURCE_SHA256

_PLUGINS=r'''
import importlib.util,importlib.metadata as md,json,pathlib,hashlib,sys
from _pytest.config import builtin_plugins
out=[]
for row in json.loads(sys.argv[1]):
    module='_pytest.'+row['module'] if row['module'] in builtin_plugins else row['module']
    spec=importlib.util.find_spec(module)
    if spec is None or spec.origin is None:raise RuntimeError('licensed plugin unavailable')
    path=pathlib.Path(spec.origin).resolve();dist=md.distribution(row['distribution'])
    if dist.version!=row['version']:raise RuntimeError('licensed plugin version differs')
    if path not in {pathlib.Path(dist.locate_file(p)).resolve() for p in dist.files or []}:
        raise RuntimeError('plugin import outside independent distribution')
    out.append(dict(row,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
print(json.dumps(out,sort_keys=True))
'''

_BOOTSTRAP=r'''
import hashlib,json,pathlib,sys,struct,types,inspect
world=pathlib.Path(sys.argv[1]).resolve();mode=sys.argv[2]
output=pathlib.Path(sys.argv[3]);junit=sys.argv[4]
expected=json.loads(sys.argv[5]);roots=set(json.loads(sys.argv[6]));plugins=json.loads(sys.argv[7])
import pytest
location=pathlib.Path(pytest.__file__).resolve()
verified={'path':str(location),'sha256':hashlib.sha256(location.read_bytes()).hexdigest()}
if verified!=expected:raise RuntimeError('independent pytest import differs')
sys.path[:0]=[str(world/'src'),str(world)]
from _pytest.config import default_plugins
default_modules={'_pytest.'+name for name in default_plugins}|{'_pytest.config'}
licensed={str(pathlib.Path(row['path']).resolve()) for row in plugins}
def plugin_identity(plugin):
    module=plugin if isinstance(plugin,types.ModuleType) else inspect.getmodule(plugin) or inspect.getmodule(type(plugin))
    filename=getattr(module,'__file__',None)
    if not filename:return None
    path=pathlib.Path(filename).resolve();module_name=getattr(module,'__name__','')
    if path.is_relative_to(world):relative=str(path.relative_to(world));kind='source'
    elif str(path) in licensed:relative=str(path);kind='licensed'
    elif module_name in default_modules:relative=str(path);kind='pytest-core'
    else:return None
    return {'module':module_name,'path':relative,'kind':kind,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def code_hash(obj):
    obj=getattr(obj,'__func__',obj)
    while hasattr(obj,'__wrapped__'):obj=obj.__wrapped__
    code=getattr(obj,'__code__',None)
    def value(v):
        if isinstance(v,types.CodeType):return ['code',clean(v)]
        if isinstance(v,tuple):return ['tuple',[value(x) for x in v]]
        if isinstance(v,frozenset):return ['frozenset',sorted([value(x) for x in v],key=lambda x:json.dumps(x,sort_keys=True))]
        if isinstance(v,bytes):return ['bytes',v.hex()]
        if isinstance(v,float):return ['float',struct.pack('!d',v).hex()]
        if isinstance(v,complex):return ['complex',value(v.real),value(v.imag)]
        if v is Ellipsis:return ['ellipsis']
        if v is None or type(v) in (str,int,bool):return [type(v).__name__,v]
        raise TypeError('unsupported native code constant')
    def clean(c):
        name=c.co_filename
        try:name=str(pathlib.Path(name).resolve().relative_to(world))
        except ValueError:pass
        return [c.co_argcount,c.co_posonlyargcount,c.co_kwonlyargcount,c.co_nlocals,c.co_stacksize,c.co_flags,
            c.co_code.hex(),value(c.co_consts),c.co_names,c.co_varnames,c.co_freevars,c.co_cellvars,
            name,c.co_name,c.co_qualname,c.co_firstlineno,c.co_linetable.hex(),c.co_exceptiontable.hex()]
    return hashlib.sha256(json.dumps(clean(code),sort_keys=True,separators=(',',':')).encode()).hexdigest() if code else None
class Monitor:
    def __init__(self):
        self.items=[];self.deselected=[];self.reports=[];self.selected=[];self.collection_errors=[];self.changed=[]
        self.plugin_manifest=[];self.plugin_violations=[]
    def pytest_plugin_registered(self,plugin,plugin_name,manager):
        if plugin is self:return
        identity=plugin_identity(plugin)
        if identity is None:self.plugin_violations.append(str(plugin_name))
        else:self.plugin_manifest.append(identity)
    def pytest_configure(self,config):self.manager=config.pluginmanager
    def pytest_itemcollected(self,item):
        path=pathlib.Path(item.path).resolve()
        try:relative=str(path.relative_to(world))
        except ValueError:relative='EXTERNAL:'+str(path)
        self.items.append({'nodeid':item.nodeid,'path':relative,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'code_sha256':code_hash(getattr(item,'obj',None))})
    def pytest_collection_finish(self,session):self.selected=[i.nodeid for i in session.items]
    def pytest_deselected(self,items):self.deselected.extend(i.nodeid for i in items)
    def pytest_collectreport(self,report):
        if report.failed or report.skipped:self.collection_errors.append({'nodeid':report.nodeid,'outcome':report.outcome})
    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_call(self,item):
        previous=next((r for r in self.items if r['nodeid']==item.nodeid),None)
        if previous is None or previous['code_sha256']!=code_hash(getattr(item,'obj',None)):self.changed.append(item.nodeid)
    def pytest_runtest_logreport(self,report):
        strict_xpass=(report.failed and isinstance(report.longrepr,str)
            and report.longrepr.startswith('[XPASS(strict)]'))
        self.reports.append({'nodeid':report.nodeid,'when':report.when,'outcome':report.outcome,
            'wasxfail':repr(report.wasxfail) if hasattr(report,'wasxfail') else
                ('[XPASS(strict)]' if strict_xpass else '')})
monitor=Monitor();args=['-q','-p','no:cacheprovider','--junitxml='+junit]
for row in plugins:args+=['-p',row['module']]
if mode=='collect':args+=['--collect-only']
code=pytest.main(args,plugins=[monitor])
imports=[];external=[]
for name,module in tuple(sys.modules.items()):
    location=getattr(module,'__file__',None)
    if not location:continue
    path=pathlib.Path(location).resolve()
    if not path.is_file():continue
    if path.is_relative_to(world):imports.append({'path':str(path.relative_to(world)),
        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    elif name.split('.')[0] in roots:external.append({'module':name,'path':str(path)})
data={'mode':mode,'exit_code':int(code),'collected_test_nodes':[r['nodeid'] for r in monitor.items],
 'selected_test_nodes':monitor.selected,'deselected_test_nodes':monitor.deselected,'test_items':monitor.items,
 'reports':monitor.reports,'collection_errors':monitor.collection_errors,'changed_test_code':monitor.changed,
 'import_manifest':sorted(imports,key=lambda r:r['path']),'external_project_imports':external,'pytest_import':verified,
 'plugin_manifest':sorted(monitor.plugin_manifest,key=lambda r:(r['module'],r['path'])),'plugin_violations':monitor.plugin_violations}
output.write_text(json.dumps(data,sort_keys=True));raise SystemExit(code)
'''


def _context(contract,authority,policy):
    required={'schema','repository','repo_path','commit','git_tree','tracked_tree_sha256','file_count',
        'interpreter','environment_sha256','protocol_binding','horizon_seconds'}
    if not isinstance(contract,dict) or set(contract)!=required or contract['schema']!=SCHEMA:
        raise ValueError('wrong versioned native contract')
    if not isinstance(policy,dict) or set(policy)!={'schema','collection_seconds','execution_seconds','pytest_version','plugins'}:
        raise ValueError('wrong external native policy')
    if policy['schema']!=POLICY_SCHEMA or any(type(policy[k]) is not int or not 1<=policy[k]<=600
            for k in ('collection_seconds','execution_seconds')) or contract['horizon_seconds']!=policy['execution_seconds']:
        raise ValueError('wrong independent native horizon')
    if not isinstance(policy['plugins'],list) or any(not isinstance(row,dict) or set(row)!={'module','distribution','version'}
        or any(not isinstance(v,str) or not re.fullmatch(r'[A-Za-z0-9_.+-]+',v) for v in row.values()) for row in policy['plugins']):
        raise ValueError('wrong independently licensed plugin list')
    if len({row['module'] for row in policy['plugins']})!=len(policy['plugins']):raise ValueError('duplicate licensed plugin')
    identity,files,manifest=original._snapshot(contract['repo_path'],contract['commit'])
    if any(contract[k]!=v for k,v in identity.items()):raise ValueError('wrong original source identity')
    admission.validate_suite_contract(contract,authority)
    licensed={row['module'] for row in policy['plugins']}
    if not set(authority['configuration']['plugin_requirements'])<=licensed:raise ValueError('missing independent plugin license')
    environment=original.environment_identity(contract['interpreter'])
    if fingerprint(environment)!=contract['environment_sha256'] or environment['pytest_version']!=policy['pytest_version']:
        raise ValueError('wrong executable environment or pytest identity')
    result=subprocess.run([contract['interpreter'],'-I','-B','-c',_PLUGINS,canonical(policy['plugins'])],
        env=original._env('/nonexistent'),capture_output=True,text=True,timeout=60)
    if result.returncode:raise ValueError('plugin authority unavailable: '+result.stderr[-600:])
    return files,manifest,environment,json.loads(result.stdout)


def _roots(files):
    roots=set()
    for name in files:
        p=Path(name);parts=p.parts
        if p.suffix!='.py':continue
        if len(parts)>=3 and parts[0]=='src':roots.add(parts[1])
        elif len(parts)>=2 and parts[0] not in ('src','tests','test','docs','bench','examples') and not parts[0].startswith('.'):roots.add(parts[0])
        elif len(parts)==1 and p.name not in ('conftest.py','setup.py') and not p.name.startswith('test_'):roots.add(p.stem)
    return sorted(roots)


def _run(contract,files,manifest,environment,plugins,out,mode,seconds,candidate):
    _runner_hash()
    out=Path(out).absolute()
    repo=Path(contract['repo_path']).absolute()
    if out.resolve()!=out or out==repo or out.is_relative_to(repo) or out.exists():
        raise ValueError('new canonical native evidence directory outside source required')
    out.mkdir(parents=True);started=time.monotonic();expected=dict(files)
    with tempfile.TemporaryDirectory(prefix='udm-native-v2-') as folder:
        temporary=Path(folder);world=temporary/'world';world.mkdir()
        for name,raw in files.items():
            if name.endswith(('.pyc','.pyo')):expected.pop(name,None);continue
            p=world/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        for row in manifest:
            if row['path'] in expected:(world/row['path']).chmod(int(row['mode'],8)&0o777)
        for row in candidate['replacements']:
            raw=row['replacement'].encode();(world/row['path']).write_bytes(raw);expected[row['path']]=raw
        script=temporary/'trusted-runner.py';script.write_text(_BOOTSTRAP)
        report=temporary/'report.json';junit=temporary/'native.xml'
        args=[contract['interpreter'],'-I','-B',str(script),str(world),mode,str(report),str(junit),
            canonical(environment['pytest_import']),canonical(_roots(files)),canonical(plugins)]
        timeout=False
        with (out/'stdout.log').open('wb') as stdout,(out/'stderr.log').open('wb') as stderr:
            process=subprocess.Popen(args,cwd=world,env=original._env(temporary),stdout=stdout,stderr=stderr,start_new_session=True)
            try:process.wait(timeout=seconds)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait();timeout=True
        raw=report.read_bytes() if report.exists() else b'{}';(out/'report.json').write_bytes(raw)
        data=json.loads(raw);data['process_exit_code']=process.returncode;data['timeout']=timeout
        mutations=[name for name,raw in expected.items() if not (world/name).is_file()
            or (world/name).resolve()!=world/name or (world/name).read_bytes()!=raw]
        data['source_mutations']=mutations
        data['unexpected_imports']=[row for row in data.get('import_manifest',[]) if row['path'] not in expected
            or row['sha256']!=sha256(expected[row['path']])]
        if junit.exists():(out/'native.xml').write_bytes(junit.read_bytes())
    data['costs']={'collection_calls':int(mode=='collect'),'native_calls':int(mode=='run'),
        'seconds':time.monotonic()-started,'horizon_seconds':seconds}
    _runner_hash()
    (out/'tracked-source-manifest.json').write_text(canonical(manifest)+'\n')
    (out/'checked-report.json').write_text(canonical(data)+'\n')
    packet={name:base64.b64encode((out/name).read_bytes()).decode() for name in
        ('stdout.log','stderr.log','report.json','checked-report.json','tracked-source-manifest.json','native.xml') if (out/name).is_file()}
    return data,packet


def _collection(data,authority,files):
    if data.get('timeout'):raise ValueError('UNKNOWN_COLLECTION_TIMEOUT')
    if data.get('process_exit_code')!=0 or data.get('exit_code')!=0 or data.get('collection_errors'):
        raise ValueError('UNKNOWN_COLLECTION_ERROR')
    if data.get('source_mutations') or data.get('unexpected_imports') or data.get('external_project_imports') or data.get('plugin_violations'):
        raise ValueError('UNKNOWN_SOURCE_OR_IMPORT_IDENTITY')
    nodes=data.get('collected_test_nodes',[])
    selected=data.get('selected_test_nodes',[])
    if (not nodes or len(set(nodes))!=len(nodes) or len(set(selected))!=len(selected)
            or set(selected)!=set(nodes) or data.get('deselected_test_nodes')):
        raise ValueError('UNKNOWN_EXACT_COLLECTION_OR_DESELECTION')
    if any(row['path'] not in files or row['sha256']!=sha256(files[row['path']]) for row in data['test_items']):
        raise ValueError('UNKNOWN_NATIVE_TEST_IDENTITY')
    for prefix in authority['required_test_nodes']:
        if not any(node==prefix or node.startswith(prefix+'[') or node.startswith(prefix+'::') for node in nodes):
            raise ValueError('UNKNOWN_MISSING_PROTECTED_ASSERTION: '+prefix)
    keys=('collected_test_nodes','selected_test_nodes','deselected_test_nodes','test_items','import_manifest','external_project_imports','pytest_import','plugin_manifest','plugin_violations')
    return {key:data[key] for key in keys}


def _binding(contract,authority,policy,environment,plugins):
    return {'schema':CERTIFICATE_SCHEMA,'admission_revision':ADMISSION_REVISION,
        'contract_sha256':fingerprint(contract),'authority_sha256':fingerprint(authority),
        'policy_sha256':fingerprint(policy),'runner_sha256':_runner_hash(),
        'environment':environment,'plugins':plugins}


def collect(contract,authority,output_dir,*,policy):
    started=time.monotonic();files,manifest,environment,plugins=_context(contract,authority,policy)
    data,packet=_run(contract,files,manifest,environment,plugins,output_dir,'collect',policy['collection_seconds'],{'replacements':[]})
    result={**_binding(contract,authority,policy,environment,plugins),'status':'ADMITTED_NATIVE_COLLECTION',
        'collection':_collection(data,authority,files),'packet':packet,
        'packet_sha256':{key:sha256(base64.b64decode(value)) for key,value in packet.items()},'costs':dict(data['costs'])}
    result['costs']['total_seconds']=time.monotonic()-started
    (Path(output_dir)/'admission-certificate.json').write_text(canonical(result)+'\n');return result


def validate_certificate(contract,authority,certificate,*,policy,output_dir=None):
    files,manifest,environment,plugins=_context(contract,authority,policy)
    binding=_binding(contract,authority,policy,environment,plugins)
    if not isinstance(certificate,dict) or set(certificate)!=set(binding)|{'status','collection','packet','packet_sha256','costs'}:
        raise ValueError('wrong native admission certificate fields')
    if any(certificate[k]!=v for k,v in binding.items()) or certificate['status']!='ADMITTED_NATIVE_COLLECTION':
        raise ValueError('native certificate source/environment/policy replay')
    try:
        packet={key:base64.b64decode(value,validate=True) for key,value in certificate['packet'].items()}
        if set(packet)!={'stdout.log','stderr.log','report.json','checked-report.json','tracked-source-manifest.json','native.xml'}:
            raise ValueError('unexpected or missing certificate packet file')
        if certificate['packet_sha256']!={key:sha256(value) for key,value in packet.items()}:
            raise ValueError('certificate packet bytes changed')
        checked=json.loads(packet['checked-report.json'])
        costs=certificate['costs']
        if (set(costs)!={'collection_calls','native_calls','seconds','horizon_seconds','total_seconds'}
                or {key:costs[key] for key in ('collection_calls','native_calls','seconds','horizon_seconds')}!=checked['costs']
                or costs['collection_calls']!=1 or costs['native_calls']!=0 or costs['horizon_seconds']!=policy['collection_seconds']
                or any(not isinstance(costs[key],(int,float)) or not math.isfinite(costs[key]) or costs[key]<0 for key in ('seconds','total_seconds'))
                or costs['total_seconds']<costs['seconds'] or checked.get('mode')!='collect'):
            raise ValueError('certificate collection cost or invocation claims differ')
        if _collection(checked,authority,files)!=certificate['collection']:
            raise ValueError('certificate raw collection differs')
        raw=json.loads(packet['report.json'])
        controller={'process_exit_code','timeout','source_mutations','unexpected_imports','costs'}
        if raw!={k:v for k,v in checked.items() if k not in controller}:raise ValueError('checked collection differs from producer')
        if json.loads(packet['tracked-source-manifest.json'])!=manifest:raise ValueError('certificate source manifest differs')
    except (KeyError,TypeError,json.JSONDecodeError) as error:raise ValueError('missing native collection evidence') from error
    path=Path(output_dir) if output_dir is not None else Path(tempfile.mkdtemp(prefix='udm-v2-independent-'))/'recollection'
    data,independent=_run(contract,files,manifest,environment,plugins,path,'collect',policy['collection_seconds'],{'replacements':[]})
    if _collection(data,authority,files)!=certificate['collection']:
        raise ValueError('independent original collection rejects certificate')
    return dict(certificate,independent_recollection={'output':str(path),'costs':data['costs']})


def _status(data,counts,original_collection):
    status='UNKNOWN_NATIVE_ERROR'
    if data['timeout']:status='UNKNOWN_TIMEOUT'
    elif data.get('source_mutations') or data.get('unexpected_imports') or data.get('external_project_imports') or data.get('changed_test_code') or data.get('plugin_violations'):
        status='UNKNOWN_SOURCE_OR_IMPORT_IDENTITY'
    elif (data.get('collected_test_nodes')!=original_collection['collected_test_nodes']
            or data.get('selected_test_nodes')!=original_collection['selected_test_nodes']
            or data.get('plugin_manifest')!=original_collection['plugin_manifest']
            or data.get('test_items')!=original_collection['test_items'] or data.get('deselected_test_nodes') or data.get('collection_errors')):
        status='UNKNOWN_EXACT_COLLECTION'
    else:
        reports=data.get('reports',[]);nodes=original_collection['selected_test_nodes']
        if any(not isinstance(r,dict) or set(r)!={'nodeid','when','outcome','wasxfail'}
                or r['when'] not in ('setup','call','teardown')
                or r['outcome'] not in ('passed','failed','skipped') or not isinstance(r['wasxfail'],str)
                for r in reports):return 'UNKNOWN_REQUIRED_ASSERTION_EXECUTION'
        calls=[r for r in reports if r['when']=='call'];setups=[r for r in reports if r['when']=='setup'];ends=[r for r in reports if r['when']=='teardown']
        if (any(r['wasxfail'] or r['outcome']=='skipped' for r in reports) or counts['skipped']):status='UNKNOWN_SKIPPED_OR_XFAIL'
        elif (any(r['outcome']!='passed' for r in setups+ends) or [r['nodeid'] for r in calls]!=nodes
                or [r['nodeid'] for r in setups]!=nodes or [r['nodeid'] for r in ends]!=nodes
                or counts['tests']!=len(nodes) or counts['errors']
                or counts['passed']!=sum(r['outcome']=='passed' for r in calls)
                or counts['failures']!=sum(r['outcome']=='failed' for r in calls)):
            status='UNKNOWN_REQUIRED_ASSERTION_EXECUTION'
        elif counts['failures'] and data.get('process_exit_code')==1:status='FAIL_NATIVE'
        elif counts['passed']==len(nodes) and data.get('process_exit_code')==0:status='PASS_NATIVE'
    return status


def verify(contract,candidate,output_dir,*,authority,admission_certificate,policy):
    started=time.monotonic();out=Path(output_dir).absolute()
    checked=validate_certificate(contract,authority,admission_certificate,policy=policy,output_dir=out/'independent-collection')
    files,manifest,environment,plugins=_context(contract,authority,policy)
    admission.validate_candidate(candidate,files)
    data,packet=_run(contract,files,manifest,environment,plugins,out/'execution','run',policy['execution_seconds'],candidate)
    counts=original._junit(out/'execution/native.xml')
    status=_status(data,counts,checked['collection'])
    receipt={'schema':SCHEMA,'admission_revision':ADMISSION_REVISION,
        'status':status,'source':{k:contract[k] for k in ('git_tree','tracked_tree_sha256','file_count')},
        'repository':contract['repository'],'commit':contract['commit'],'protocol_binding':contract['protocol_binding'],
        'contract_sha256':fingerprint(contract),'candidate_sha256':fingerprint(candidate),'authority_sha256':fingerprint(authority),
        'certificate_sha256':fingerprint(admission_certificate),'policy_sha256':fingerprint(policy),
        'runner_sha256':_runner_hash(),'environment':environment,'plugins':plugins,
        'junit':counts,'execution':data,'packet':packet,'independent_collection':checked['independent_recollection'],
        'packet_sha256':{key:sha256(base64.b64decode(value)) for key,value in packet.items()},
        'costs':{'native_calls':1,'collection_calls':1,'native_seconds':data['costs']['seconds'],
            'total_seconds':time.monotonic()-started},'external_enforcement':'UNKNOWN_NONBYPASSABILITY',
        'scope':'Exact original collected suite, no skips/xfails/deselection; trusted original tests and licensed plugins'}
    (out/'receipt.json').write_text(canonical(receipt)+'\n');return receipt


def validate_receipt(contract,candidate,authority,certificate,receipt,*,policy,output_dir=None,independent=True):
    """Check a retained packet; independently re-execute untrusted submissions.

    ``independent=False`` is only structural validation for the existing trusted
    controller's own two native runs. It never turns caller-supplied evidence
    into independently warranted native evidence.
    """
    files,manifest,environment,plugins=_context(contract,authority,policy)
    admission.validate_candidate(candidate,files)
    expected={'schema':SCHEMA,'admission_revision':ADMISSION_REVISION,
        'source':{k:contract[k] for k in ('git_tree','tracked_tree_sha256','file_count')},
        'repository':contract['repository'],'commit':contract['commit'],'protocol_binding':contract['protocol_binding'],
        'contract_sha256':fingerprint(contract),'candidate_sha256':fingerprint(candidate),'authority_sha256':fingerprint(authority),
        'certificate_sha256':fingerprint(certificate),'policy_sha256':fingerprint(policy),'runner_sha256':_runner_hash(),
        'environment':environment,'plugins':plugins,'external_enforcement':'UNKNOWN_NONBYPASSABILITY',
        'scope':'Exact original collected suite, no skips/xfails/deselection; trusted original tests and licensed plugins'}
    if (not isinstance(receipt,dict) or set(receipt)!=set(expected)|{'status','junit','execution','packet',
            'packet_sha256','independent_collection','costs'} or any(receipt.get(k)!=v for k,v in expected.items())):
        raise ValueError('native receipt source, candidate, authority or schema differs')
    binding=_binding(contract,authority,policy,environment,plugins)
    if any(certificate.get(k)!=v for k,v in binding.items()):raise ValueError('receipt uses stale native certificate')
    try:
        packet={key:base64.b64decode(value,validate=True) for key,value in receipt['packet'].items()}
        required={'stdout.log','stderr.log','report.json','checked-report.json','tracked-source-manifest.json'}
        if not required<=set(packet) or set(packet)-required-{'native.xml'}:
            raise ValueError('missing or unexpected native receipt packet')
        if receipt['packet_sha256']!={key:sha256(value) for key,value in packet.items()}:
            raise ValueError('native receipt packet bytes changed')
        data=json.loads(packet['checked-report.json']);raw=json.loads(packet['report.json'])
        controller={'process_exit_code','timeout','source_mutations','unexpected_imports','costs'}
        if data!=receipt['execution'] or raw!={k:v for k,v in data.items() if k not in controller}:
            raise ValueError('native receipt raw execution differs')
        expected_files=dict(files)
        for row in candidate['replacements']:expected_files[row['path']]=row['replacement'].encode()
        unexpected=[row for row in data.get('import_manifest',[]) if row['path'] not in expected_files
            or row['sha256']!=sha256(expected_files[row['path']])]
        if data.get('unexpected_imports')!=unexpected:raise ValueError('native receipt import claims differ from executable bytes')
        if json.loads(packet['tracked-source-manifest.json'])!=manifest:raise ValueError('native receipt source manifest differs')
        with tempfile.TemporaryDirectory(prefix='udm-native-receipt-') as folder:
            path=Path(folder)/'native.xml'
            if 'native.xml' in packet:path.write_bytes(packet['native.xml'])
            counts=original._junit(path)
        if counts!=receipt['junit'] or _status(data,counts,certificate['collection'])!=receipt['status']:
            raise ValueError('native receipt status or original assertion outcome differs')
        costs=receipt['costs'];native=data['costs'];collection=receipt['independent_collection']['costs']
        if (set(costs)!={'native_calls','collection_calls','native_seconds','total_seconds'}
                or costs['native_calls']!=1 or costs['collection_calls']!=1
                or native['native_calls']!=1 or native['collection_calls']!=0 or native['horizon_seconds']!=policy['execution_seconds']
                or collection['native_calls']!=0 or collection['collection_calls']!=1 or collection['horizon_seconds']!=policy['collection_seconds']
                or costs['native_seconds']!=native['seconds'] or data.get('mode')!='run'
                or any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in
                       (native['seconds'],collection['seconds'],costs['total_seconds']))
                or costs['total_seconds']<native['seconds']+collection['seconds']):
            raise ValueError('native receipt costs or actual invocation claims differ')
    except (KeyError,TypeError,json.JSONDecodeError) as error:raise ValueError('missing native receipt evidence') from error
    if independent:
        path=Path(output_dir) if output_dir is not None else Path(tempfile.mkdtemp(prefix='udm-receipt-recheck-'))/'execution'
        fresh=verify(contract,candidate,path,authority=authority,admission_certificate=certificate,policy=policy)
        if (fresh['status']!=receipt['status'] or fresh['junit']!=counts
                or {k:v for k,v in fresh['execution'].items() if k!='costs'}!={k:v for k,v in data.items() if k!='costs'}):
            raise ValueError('independent native re-execution rejects receipt')
        return dict(receipt,independent_reexecution={'output':str(path),'costs':fresh['costs']})
    return receipt
