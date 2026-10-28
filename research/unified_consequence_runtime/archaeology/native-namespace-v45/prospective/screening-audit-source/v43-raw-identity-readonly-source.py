"""Offline supplied-case identity checks; never launch a target interpreter.

The old generic Git decoder and filesystem runtime checks are reused from exact
retained sources. Only scm_snapshot uses Git, for three read-only metadata calls
whose default ordering is part of the builder wire format. No entrypoint runs on
import. Caller must retain results privately: source bytes may be protected.
"""
import base64
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from types import FunctionType

DEPENDENCIES = {
    '/workspace/qualification/native-authority-v42-screening-audit/source-identity/audit_source_identity.py':
        'a5cc8a89b51f7737322d92cbd5ca80f36572530f2a11fe2e13d8768dc99bed84',
    '/workspace/qualification/native-authority-v42-screening-audit/runtime-identity/audit_runtime_filesystem.py':
        'ab967175109c620f88a5be39111b3a9709751e6f7c83ca07a825b0699c5f1c73',
}
CONTROL_ROOT = Path('/workspace/udm-v54')
CONTROL_PINS = {
    'native_source_v42.py':'f16d4a05a6d3fccde048921559ab130872806afc84757ec8da95d7c2193c8b98',
    'native_admission_v42.py':'96671d481728559ea0b7f751d2a7774dd92fef6c5677b24fdd6a81a21b90e92f',
    'native_admission_v2.py':'4056cb0fd40af3badbe41225919e660d560cac7bb2fda25580399e865778977e',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def fp(value):
    return sha(canonical(value).encode())


def _load(path, name):
    path = Path(path)
    if path.is_symlink() or sha(path.read_bytes()) != DEPENDENCIES[str(path)]:
        raise ValueError('offline audit dependency differs: '+str(path))
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _decoder():
    return _load(next(iter(DEPENDENCIES)), '_v43_original_raw_git_decoder')


def _runtime_helper():
    return _load(list(DEPENDENCIES)[1], '_v43_original_runtime_filesystem_auditor')


def _control():
    for name, expected in CONTROL_PINS.items():
        path=CONTROL_ROOT/'research/unified_consequence_runtime'/name
        if path.is_symlink() or sha(path.read_bytes())!=expected:
            raise ValueError('qualified static source algorithm differs: '+name)
    if str(CONTROL_ROOT) not in sys.path:
        sys.path.insert(0,str(CONTROL_ROOT))
    from research.unified_consequence_runtime import native_source_v42 as source
    from research.unified_consequence_runtime import native_admission_v42 as admission
    source._guard()
    admission.assert_source_identity()
    return source, admission


def check_file(row):
    path = Path(row['path'])
    return (path.is_absolute() and path.is_file() and sha(path.read_bytes()) == row['sha256'])


def raw_snapshot(repo, commit, *, filesystem=False):
    """Decode retained raw SHA-1 Git objects, typed links, index and worktree."""
    repo = Path(repo)
    if not repo.is_absolute() or repo.resolve() != repo:
        raise ValueError('canonical retained source path required')
    git = repo/'.git'
    if not git.is_dir() or git.is_symlink():
        raise ValueError('ordinary retained Git directory required')
    if any((git/'objects/info'/n).exists() for n in ('alternates','http-alternates')):
        raise ValueError('external object alternate refused')
    if not re.fullmatch('[0-9a-f]{40}',commit):
        raise ValueError('exact retained commit required')
    mod = _decoder()
    objects = mod.Objects(git)
    kind, body = objects.get(commit)
    mod.check('source_commit_type',kind == 'commit')
    tree = body.splitlines()[0].decode().removeprefix('tree ')
    rows = sorted(objects.tree(tree),key=lambda r:r['path'])
    source, _ = _control()
    raw_files = {}; files = {}; mapping = {}
    for row in rows:
        name = source._name(row['path'])
        if name in mapping:
            raise ValueError('duplicate immutable source entry')
        if row['mode'] == '160000':
            entry = dict(row,sha256=None)
        else:
            kind, raw = objects.get(row['blob'])
            mod.check('source_blob_type:'+name,kind == 'blob')
            if row['mode'] not in ('100644','100755','120000'):
                raise ValueError('unsupported immutable source mode')
            entry = dict(row,sha256=sha(raw));raw_files[name] = raw
            if row['mode'] == '120000':
                entry['target'] = raw.decode('utf-8')
            else:
                files[name] = raw
        mapping[name] = entry
    directories = source._directories(mapping)
    for name, row in mapping.items():
        if row['mode'] == '120000':
            target = source._resolve_link(name,mapping,directories)
            row.update(resolved_path=target,content_sha256=sha(files[target]))
            files[name] = files[target]
    manifest = list(mapping.values());files=dict(sorted(files.items()))
    source._validate(files,manifest)
    identity={'git_tree':tree,'tracked_tree_sha256':fp(manifest),'file_count':len(files)}
    # Close all retained object representations, not only reachable blobs.
    for name in list(objects.locations):
        objects.get(name)
    for name, location in objects.duplicates:
        if isinstance(location,Path):
            import zlib
            raw=zlib.decompress(mod.read(location));header,raw=raw.split(b'\0',1)
            kind,size=header.decode().split();mod.check('duplicate_object_size',len(raw)==int(size));answer=(kind,raw)
        else:
            answer=objects.at(*location)
        mod.check('duplicate_object_exact:'+name,answer==objects.get(name) and mod.oid(*answer)==name)
    if filesystem:
        mod.check('source_detached_head',mod.read(git/'HEAD').decode().strip()==commit)
        mod.check('source_index_exact',mod.parse_index(git/'index')==rows)
        actual_tree, actual_rows = mod.fs_tree(repo,{r['path']:r for r in rows if r['mode']=='160000'})
        mod.check('source_filesystem_tree_exact',actual_tree==tree)
        mod.check('source_filesystem_paths_exact',{r['path'] for r in actual_rows}==set(mapping))
    return {'identity':identity,'files':files,'manifest':manifest,'raw_files':raw_files,
        'checks':mod.CHECKS,'inputs':mod.INPUTS,'object_ids':sorted(objects.locations),
        'commit':commit,'repo_path':str(repo),'coverage_complete':True}


def derive_authority(before, after, base, augmented, binding, repository):
    """Original static assertion/config algorithm over independently decoded bytes."""
    _, admission = _control()
    config=admission.configuration(after['files'])
    old={r['path']:r for r in before['manifest']};new={r['path']:r for r in after['manifest']}
    for name in old.keys()|new.keys():
        if old.get(name)==new.get(name):
            continue
        if (name not in new or new[name]['mode'] not in ('100644','100755')
                or name in old and old[name]['mode'] not in ('100644','100755')
                or not admission._test_scope(name,config)):
            raise ValueError('typed non-test source delta: source overlay may change canonical author Python tests only')
    original = admission._original_derive
    def snapshot(repo, commit):
        row = before if commit == base else after if commit == augmented else None
        if row is None:
            raise ValueError('unbound static source commit')
        return row['identity'],row['files'],row['manifest']
    namespace = dict(original.__globals__,_snapshot=snapshot)
    rebound = FunctionType(original.__code__,namespace,original.__name__,original.__defaults__,original.__closure__)
    return rebound('/OFFLINE_DECODED_ONLY',base,augmented,binding,repository=repository)


def scm_snapshot(repo, base, base_identity):
    """Exact builder metadata wire shape, read-only and no lazy fetch."""
    repo=Path(repo)
    if list((repo/'.git/objects/pack').glob('*.promisor')):
        raise ValueError('offline SCM refuses lazy-fetch object storage')
    config=repo/'.git/config'
    if config.is_file() and re.search(r'(?im)^\s*(?:promisor\s*=\s*(?:true|yes|1)|partialclone\s*=)',config.read_text()):
        raise ValueError('offline SCM refuses partial-clone transport')
    env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_TERMINAL_PROMPT='0')
    def git(*args):
        proc=subprocess.run(['git','--no-replace-objects','-C',str(repo),*args],env=env,capture_output=True,timeout=60)
        if proc.returncode:
            raise ValueError('offline SCM metadata unavailable: '+repr(args))
        return proc.stdout
    ancestors_raw=git('rev-list',base);ancestors=ancestors_raw.decode().splitlines()
    decoded=raw_snapshot(repo,base)
    if decoded['identity']!=base_identity:
        raise ValueError('offline SCM base identity differs')
    if not ancestors or ancestors[0] != base or len(set(ancestors))!=len(ancestors):
        raise ValueError('invalid base ancestry')
    mod=_decoder();objects=mod.Objects(repo/'.git')
    for name in ancestors:
        if objects.get(name)[0]!='commit':
            raise ValueError('SCM ancestor is not a decoded commit')
    tags=[];selected=[]
    for line in git('for-each-ref','--format=%(objectname)%09%(refname)','refs/tags').decode().splitlines():
        name,ref=line.split('\t');target=git('rev-parse',ref+'^{}').decode().strip()
        if (not re.fullmatch(r'refs/tags/[A-Za-z0-9_+./()-]+',ref) or '..' in ref or '//' in ref
                or ref.endswith(('/','.')) or any(p.startswith('.') or p.endswith('.lock') for p in ref.split('/'))):
            raise ValueError('unsafe tag metadata')
        objects.get(name);objects.get(target)
        row={'ref':ref,'tag_object':name,'target':target};tags.append(row)
        if target in ancestors:
            selected.append(row)
    receipts={}
    for filename in ('source-boundaries.json','scm-provenance.json'):
        p=repo.parent/filename
        if not p.exists():
            continue
        if p.is_symlink() or p.resolve()!=p:
            raise ValueError('unsafe original SCM receipt')
        raw=p.read_bytes();receipt=json.loads(raw);metadata=receipt.get('scm_metadata',{}) if filename=='source-boundaries.json' else receipt
        if filename=='source-boundaries.json' and (receipt.get('base_commit')!=base or receipt.get('base_identity')!=base_identity):
            raise ValueError('original SCM base receipt differs')
        if (metadata.get('backend')!='hatch-vcs' or metadata.get('base_ancestry_only') is not True
                or metadata.get('tracked_source_preserved') is not True or metadata.get('ancestor_tags')!=selected
                or metadata.get('ancestor_commits_sha256')!=sha(ancestors_raw)):
            raise ValueError('original SCM metadata differs')
        receipts[filename]=sha(raw)
    return {'scope':'OBSERVED_LOCAL_BASE_REACHABLE_SCM; REMOTE_AUTHENTICITY_NOT_INFERRED_FROM_HASHES',
        'ancestor_commits':ancestors,'all_observed_tags':tags,'ancestor_tags':selected,
        'original_receipts_sha256':receipts}


def audit_source(contract, authority, certificate, case_dir, *, include_scm=False):
    if not isinstance(contract,dict) or not isinstance(authority,dict):
        return {'status':'UNKNOWN_NO_PREPARED_SOURCE','coverage_complete':False,'checks':[],
            'limitations':['No prepared native contract/authority supplied; metadata-refusal source must be checked separately with raw_snapshot.']}
    before=raw_snapshot(contract['repo_path'],authority['baseline_commit'])
    after=raw_snapshot(contract['repo_path'],contract['commit'],filesystem=True)
    checks=[*before['checks'],*after['checks']]
    def check(name,value):
        checks.append({'check':name,'passed':bool(value)})
        if not value:
            raise ValueError(name)
    check('contract_augmented_source_identity',all(contract.get(k)==v for k,v in after['identity'].items()))
    check('authority_source_identity',authority.get('source')==after['identity'] and authority.get('baseline_source')==before['identity'])
    derived=derive_authority(before,after,authority['baseline_commit'],contract['commit'],contract['protocol_binding'],contract['repository'])
    check('complete_original_static_suite_authority',derived==authority)
    boundary_path=Path(contract['repo_path']).parent/'source-boundaries.json'
    boundaries=None;transports=[]
    if boundary_path.is_file():
        boundaries=json.loads(boundary_path.read_bytes())
        for key, expected in [('base_identity',before['identity']),('augmented_identity',after['identity']),('base_manifest',before['manifest']),('augmented_manifest',after['manifest'])]:
            check('source_boundary_'+key,boundaries.get(key)==expected)
        check('source_boundary_commits',boundaries.get('base_commit')==authority['baseline_commit'] and boundaries.get('augmented_commit')==contract['commit'])
        for row in boundaries.get('author_tests',[]):
            raw=after['files'][row['path']];p=Path(row['transport_json']);encoded=p.read_bytes();transport=json.loads(encoded)
            check('original_author_test_transport:'+row['path'],base64.b64decode(transport['content'].encode('ascii').translate(None,b' \t\r\n\v\f'),validate=True)==raw and transport['sha']==row['git_blob'] and sha(raw)==row['sha256'] and len(raw)==row['bytes'] and sha(encoded)==row['transport_sha256'])
            transports.append({'record':row,'transport':transport,'transport_sha256':sha(encoded)})
    result={'status':'PASS_OFFLINE_SOURCE_IDENTITY','coverage_complete':True,'checks':checks,
        'files':after['files'],'manifest':after['manifest'],'base_files':before['files'],
        'base_manifest':before['manifest'],'identity':after['identity'],'base_identity':before['identity'],
        'object_ids':after['object_ids'],'rederived_authority':derived,'source_boundaries':boundaries,
        'author_test_transports':transports,'inputs':{**before['inputs'],**after['inputs']},
        'limitations':['Raw local identity does not independently authenticate a remote. Parent must bind transport records to the frozen PR head metadata and exact requests.','SCM Git metadata reads are deferred unless include_scm=True; no target interpreter/backend/test is executed.']}
    if include_scm:
        result['scm']=scm_snapshot(contract['repo_path'],authority['baseline_commit'],before['identity'])
    return result


def audit_runtime(contract, policy, authority, *, certificate=None, case_dir=None, environment=None, plugins=None):
    """Hash installed executable/stdlib/distribution/plugin bytes without imports."""
    if environment is None and isinstance(certificate,dict):
        environment=certificate.get('environment');plugins=certificate.get('plugins') if plugins is None else plugins
    root=Path(contract.get('repo_path','/NONEXISTENT')).parent
    if environment is None and (root/'environment.json').is_file():
        environment=json.loads((root/'environment.json').read_bytes())
    if plugins is None and (root/'plugin-identity.json').is_file():
        plugins=json.loads((root/'plugin-identity.json').read_bytes())
    if not isinstance(environment,dict) or not isinstance(plugins,list):
        return {'status':'UNKNOWN_NO_RETAINED_RUNTIME_IDENTITY','coverage_complete':False,'checks':[],
            'limitations':['A retained environment and complete plugin identity list are required; no target interpreter was queried.']}
    mod=_runtime_helper();checks=[]
    def check(name,value):
        checks.append({'check':name,'passed':bool(value)})
        if not value:
            raise ValueError(name)
    interpreter=Path(contract['interpreter'])
    check('environment_contract_fingerprint',fp(environment)==contract['environment_sha256'])
    check('environment_executable_path',environment['executable']==str(interpreter))
    check('environment_executable_bytes',sha(interpreter.read_bytes())==environment['executable_sha256']==environment['runtime_identity']['executable_sha256'])
    check('pytest_policy_version',environment['pytest_version']==policy['pytest_version'])
    check('pytest_import_bytes',check_file(environment['pytest_import']))
    stdlib,diagnostics=mod.source_walk(environment['runtime_import_roots'])
    check('complete_qualified_stdlib_fingerprint',fp(stdlib)==environment['runtime_identity']['stdlib_manifest_sha256'])
    version=environment['runtime_identity']['version_info'];venv=interpreter.absolute().parent.parent
    site=venv/'lib'/('python'+'.'.join(map(str,version[:2])))/'site-packages'
    rows=[];ownership={};installed={}
    distributions=sorted(importlib.metadata.distributions(path=[str(site)]),key=lambda d:(d.metadata['Name'] or '').lower())
    for dist in distributions:
        name=dist.metadata['Name'];files=[];owned=set()
        for entry in sorted(dist.files or [],key=str):
            path=Path(dist.locate_file(entry))
            if path.is_file():
                files.append([str(entry),sha(path.read_bytes())]);owned.add(str(path.resolve()))
        rows.append([name,dist.version,files]);ownership[mod.canonical_name(name or '')]=owned;installed[mod.canonical_name(name or '')]=dist.version
    check('complete_distribution_count',len(rows)==environment['distribution_count'])
    check('complete_distribution_file_fingerprint',fp(rows)==environment['distributions_sha256'])
    expected={r['module']:r for r in policy['plugins']}
    check('complete_licensed_plugin_inventory',{r['module'] for r in plugins}==set(expected) and len(plugins)==len(expected))
    for row in plugins:
        license=expected[row['module']];name=mod.canonical_name(license['distribution'])
        check('plugin_license:'+row['module'],all(row.get(k)==v for k,v in license.items()))
        check('plugin_bytes:'+row['module'],check_file(row))
        check('plugin_distribution_version:'+row['module'],installed.get(name)==license['version'])
        check('plugin_distribution_ownership:'+row['module'],str(Path(row['path']).resolve()) in ownership.get(name,set()))
        builtins,_=mod.builtin_plugin_names(site)
        module='_pytest.'+row['module'] if row['module'] in builtins else row['module']
        relative=Path(*module.split('.'))
        candidates=[p.resolve() for p in (site/(str(relative)+'.py'),site/relative/'__init__.py') if p.is_file()]
        check('plugin_static_module_path:'+row['module'],len(candidates)==1 and candidates[0]==Path(row['path']).resolve())
    check('pytest_distribution_ownership',str(Path(environment['pytest_import']['path']).resolve()) in ownership.get('pytest',set()))
    return {'status':'PASS_OFFLINE_RUNTIME_BYTE_IDENTITY','coverage_complete':True,'checks':checks,
        'environment':environment,'plugins':plugins,'stdlib_files':stdlib,'distribution_files':rows,
        'walk_diagnostics':diagnostics,'limitations':['Implementation/version/base_prefix/sysconfig-root provenance are retained executable claims, internally bound but not independently queried by this offline audit.','Stdlib coverage is the original suffix-filtered walk excluding site-packages/dist-packages. Distribution rows follow installed RECORD metadata and do not establish ownership of unlisted files.','Static plugin bytes/ownership checks do not execute import resolution or establish plugin behavior.']}
