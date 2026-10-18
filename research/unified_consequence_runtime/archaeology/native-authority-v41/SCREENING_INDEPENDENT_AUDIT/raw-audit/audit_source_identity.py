"""Offline audit: read retained source and Git bytes, execute no retained code.

No subprocess, Git command, network call, import of source-under-audit, extraction,
or write outside this audit directory is used. Git objects are decoded as data.
"""
import ast
import base64
import configparser
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import sys
import tomllib
import zlib

# Use only the generic retained dependency, under this audit interpreter.
# Do not launch the controller interpreter or import any controller/project code.
sys.path.insert(0,'/tmp/udm-v4-acceptance-venv/lib/python3.12/site-packages')
import packaging
from packaging.requirements import Requirement, InvalidRequirement

ROOT = Path('/workspace/qualification/native-authority-v41-screening-audit')
META = ROOT/'metadata-preaudit'
RAW = ROOT/'raw-audit'
SEALED = Path('/workspace/qualification/native-authority-v41-screening-sealed')
COMMIT = 'bd46699ea9933794a1c3fee161039c24a630bf4b'
CODE = META/'source-binding/gate-files'/COMMIT/'research/unified_consequence_runtime'
CHECKS = []
INPUTS = {}

def sha(b): return hashlib.sha256(b).hexdigest()
def canonical(v): return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)
def fp(v): return sha(canonical(v).encode())
def oid(kind,b): return hashlib.sha1(kind.encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()
def check(name,condition,detail=None):
    CHECKS.append({'check':name,'passed':bool(condition),**({'detail':detail} if detail is not None else {})})
    if not condition: raise AssertionError(name)
def read(p):
    p=Path(p);b=p.read_bytes();INPUTS[str(p)]={'sha256':sha(b),'bytes':len(b)};return b
def js(p): return json.loads(read(p))
def u32(b,i): return struct.unpack_from('>I',b,i)[0]

class Objects:
    """Read SHA-1 Git pack v2/3 and idx v2; validate every resolved object ID."""
    def __init__(self,git):
        self.git=git;self.locations={};self.packs={};self.cache={};self.offset_cache={};self.pack_records=[]
        for idx in sorted((git/'objects/pack').glob('*.idx')):
            b=read(idx);check('idx_v2:'+str(idx),b[:8]==b'\xfftOc\0\0\0\2')
            check('idx_checksum:'+str(idx),hashlib.sha1(b[:-20]).digest()==b[-20:])
            n=u32(b,8+255*4);start=8+256*4;names=[b[start+20*i:start+20*(i+1)].hex() for i in range(n)]
            offsets_start=start+n*20+n*4;large_start=offsets_start+n*4
            pack=idx.with_suffix('.pack');data=read(pack)
            check('pack_header:'+str(pack),data[:4]==b'PACK' and u32(data,4) in (2,3) and u32(data,8)==n)
            check('pack_checksum:'+str(pack),hashlib.sha1(data[:-20]).digest()==data[-20:]==b[-40:-20])
            check('pack_name:'+str(pack),pack.stem=='pack-'+data[-20:].hex())
            self.packs[str(pack)]=data
            for i,name in enumerate(names):
                pos=u32(b,offsets_start+i*4)
                if pos&0x80000000:pos=struct.unpack_from('>Q',b,large_start+(pos&0x7fffffff)*8)[0]
                check('unique_object:'+name,name not in self.locations)
                self.locations[name]=(str(pack),pos)
            self.pack_records.append({'pack':str(pack),'sha256':sha(data),'objects':n,'pack_sha1':data[-20:].hex()})
        for directory in (git/'objects').iterdir():
            if re.fullmatch('[0-9a-f]{2}',directory.name) and directory.is_dir():
                for p in directory.iterdir():
                    if re.fullmatch('[0-9a-f]{38}',p.name):self.locations[directory.name+p.name]=p
    def get(self,name):
        if name in self.cache:return self.cache[name]
        loc=self.locations[name]
        if isinstance(loc,Path):
            raw=zlib.decompress(read(loc));header,body=raw.split(b'\0',1);kind,size=header.decode().split()
            check('loose_object_size:'+name,len(body)==int(size));answer=(kind,body)
        else:answer=self.at(*loc)
        check('object_sha1:'+name,oid(*answer)==name)
        self.cache[name]=answer;return answer
    def at(self,pack,offset):
        key=(pack,offset)
        if key in self.offset_cache:return self.offset_cache[key]
        b=self.packs[pack];pos=offset;c=b[pos];pos+=1;typ=(c>>4)&7;size=c&15;shift=4
        while c&128:
            c=b[pos];pos+=1;size|=(c&127)<<shift;shift+=7
        base=None
        if typ==6:
            c=b[pos];pos+=1;distance=c&127
            while c&128:
                c=b[pos];pos+=1;distance=((distance+1)<<7)+(c&127)
            base=self.at(pack,offset-distance)
        elif typ==7:
            name=b[pos:pos+20].hex();pos+=20;base=self.get(name)
        d=zlib.decompressobj();body=d.decompress(b[pos:]);check('packed_object_size:'+pack+':'+str(offset),d.eof and len(body)==size)
        if base is not None:
            q=0
            def varint():
                nonlocal q
                value=0;shift=0
                while True:
                    c=body[q];q+=1;value|=(c&127)<<shift
                    if not c&128:return value
                    shift+=7
            source_size=varint();target_size=varint();check('delta_base_size',source_size==len(base[1]));parts=[]
            while q<len(body):
                cmd=body[q];q+=1
                if cmd&128:
                    start=count=0
                    for bit in range(4):
                        if cmd&(1<<bit):start|=body[q]<<(8*bit);q+=1
                    for bit in range(3):
                        if cmd&(1<<(4+bit)):count|=body[q]<<(8*bit);q+=1
                    count=count or 0x10000;piece=base[1][start:start+count];check('delta_copy_bound',len(piece)==count);parts.append(piece)
                else:
                    check('delta_nonzero_insert',cmd!=0);parts.append(body[q:q+cmd]);q+=cmd
            answer=(base[0],b''.join(parts));check('delta_target_size',len(answer[1])==target_size)
        else:
            check('supported_pack_type',typ in (1,2,3,4));answer=({1:'commit',2:'tree',3:'blob',4:'tag'}[typ],body)
        self.offset_cache[key]=answer;return answer
    def tree(self,name,prefix=''):
        kind,b=self.get(name);check('tree_object:'+name,kind=='tree');out=[];pos=0
        while pos<len(b):
            end=b.index(b'\0',pos);mode,leaf=b[pos:end].split(b' ',1);child=b[end+1:end+21].hex();pos=end+21
            leaf=leaf.decode('utf-8');path=prefix+leaf
            check('canonical_tree_path:'+path,bool(path) and '\\' not in path and '..' not in PurePosixPath(path).parts and PurePosixPath(path).as_posix()==path)
            if mode==b'40000':out.extend(self.tree(child,path+'/'))
            else:out.append({'path':path,'mode':mode.decode(),'blob':child})
        return out

def parse_index(p):
    b=read(p);check('index_header:'+str(p),b[:4]==b'DIRC' and u32(b,4) in (2,3));check('index_checksum:'+str(p),hashlib.sha1(b[:-20]).digest()==b[-20:]);pos=12;rows=[]
    for i in range(u32(b,8)):
        start=pos;mode=u32(b,pos+24);name=b[pos+40:pos+60].hex();flags=struct.unpack_from('>H',b,pos+60)[0];pos+=62
        if flags&0x4000:pos+=2
        end=b.index(b'\0',pos);path=b[pos:end].decode();pos=start+((end+1-start+7)//8)*8
        rows.append({'path':path,'mode':format(mode,'o'),'blob':name})
    return rows

def fs_tree(root,gitlinks):
    rows=[]
    def walk(directory,prefix=''):
        entries=[]
        for p in directory.iterdir():
            if p.name=='.git' and directory==root:continue
            st=p.lstat();name=prefix+p.name
            if name in gitlinks:
                row=gitlinks[name]
                check('unmaterialized_gitlink_empty_directory:'+name,stat.S_ISDIR(st.st_mode) and not list(p.iterdir()))
                rows.append({**row,'sha256':None})
                entries.append((p.name,b'160000 '+os.fsencode(p.name)+b'\0'+bytes.fromhex(row['blob'])))
            elif stat.S_ISDIR(st.st_mode):
                tree=walk(p,name+'/');entries.append((p.name+'/',b'40000 '+os.fsencode(p.name)+b'\0'+bytes.fromhex(tree)))
            elif stat.S_ISREG(st.st_mode) or stat.S_ISLNK(st.st_mode):
                symlink=stat.S_ISLNK(st.st_mode);raw=os.fsencode(os.readlink(p)) if symlink else read(p)
                mode='120000' if symlink else ('100755' if st.st_mode&0o111 else '100644');blob=oid('blob',raw)
                rows.append({'path':name,'mode':mode,'blob':blob,'sha256':sha(raw)})
                entries.append((p.name,mode.encode()+b' '+os.fsencode(p.name)+b'\0'+bytes.fromhex(blob)))
            else:raise AssertionError('unsupported_filesystem_kind:'+name)
        return oid('tree',b''.join(value for _,value in sorted(entries,key=lambda x:os.fsencode(x[0]))))
    tree=walk(root);return tree,rows

def code_bindings():
    names=['decisive_native_verify.py','native_environment_v3.py','native_environment_v41.py','native_environment_selection_v3.py','native_environment_selection_v4.py','native_environment_selection_v41.py']
    result=[]
    for n in names:
        p=CODE/n;raw=read(p);matches=[]
        for q in META.glob('git-gate-*-pool.json'):
            d=json.loads(q.read_text())
            if d.get('argv',[])[-1]==COMMIT+':research/unified_consequence_runtime/'+n:
                check('retained_committed_code_bytes:'+n,base64.b64decode(d['stdout_base64'])==raw and d['returncode']==0);matches.append(q.name)
        check('one_code_binding:'+n,len(matches)==1)
        result.append({'name':n,'sha256':sha(raw),'git_blob_sha1':oid('blob',raw),'binding':matches[0]})
    # AST/literal source inspection only; no retained source is imported or evaluated.
    verify=ast.parse(read(CODE/'decisive_native_verify.py'))
    snap=next(n for n in verify.body if isinstance(n,ast.FunctionDef) and n.name=='_snapshot')
    text=ast.get_source_segment(read(CODE/'decisive_native_verify.py').decode(),snap)
    check('snapshot_exact_refusal_branch',"mode not in ('100644', '100755') or kind != 'blob'" in text and "raise ValueError('only regular tracked files supported; no symlinks or submodules')" in text)
    env=read(CODE/'native_environment_v3.py').decode()
    check('provision_snapshot_before_identity_archive_selection',env.index('identity,files,manifest=_snapshot(source,base)')<env.index('(root/\'metadata-source.tar.gz\')')<env.index('chosen=selection.select_profile(files,catalog)'))
    check('provision_exception_mapping',"return save('UNKNOWN_SOURCE_ENVIRONMENT',type(error).__name__+': '+str(error))" in env)
    v41=read(CODE/'native_environment_selection_v41.py').decode()
    check('v41_only_tox_literal_include_dispatch',"path == 'tox.ini'" in v41 and 'target = _include_target(line)' in v41 and "return _bind(_ADD, _namespace, result=result)(value, path, field, extra, python_versions)" in v41)
    return result

def build_constraints(files,index):
    """Independent limited interpreter for the three observed early refusal paths.

    This audits the complete retained constraint record on these inputs. It does
    not implement unobserved success/compatibility/native paths.
    """
    result={'schema':'UDM_NATIVE_ENVIRONMENT_CONSTRAINTS_V41','status':'UNKNOWN','metadata_sha256':{},'source_sha256':fp({n:sha(b) for n,b in sorted(files.items())}),'python_specifiers':[],'declared_python':[],'python_implementations':[],'requirements':[],'plugin_requirements':[],'evidence':[],'reasons':[]}
    def evidence(path,field,value):result['metadata_sha256'][path]=sha(files[path]);result['evidence'].append({'path':path,'field':field,'value':value})
    def req(value,path,field):
        r=Requirement(value);row={'requirement':str(r),'path':path,'field':field,'extra':''}
        if row not in result['requirements']:result['requirements'].append(row)
    if 'pyproject.toml' in files:
        data=tomllib.loads(files['pyproject.toml'].decode());project=data.get('project',{});build=data.get('build-system',{})
        check('observed_toml_static:'+str(index),not set(project.get('dynamic',[]))&{'requires-python','dependencies','optional-dependencies','classifiers'})
        if 'requires-python' in project:result['python_specifiers'].append(project['requires-python']);evidence('pyproject.toml','project.requires-python',project['requires-python'])
        if 'classifiers' in project:evidence('pyproject.toml','project.classifiers',project['classifiers'])
        for field,values in [('build-system.requires',build.get('requires',[])),('project.dependencies',project.get('dependencies',[]))]:
            for value in values:req(value,'pyproject.toml',field)
            if values:evidence('pyproject.toml',field,values)
        check('no_observed_test_extras:'+str(index),not any(k in ('test','tests','testing') for k in project.get('optional-dependencies',{})))
        for group,values in sorted(data.get('dependency-groups',{}).items()):
            if group in ('test','tests','testing'):
                check('observed_group_literal:'+str(index),all(isinstance(v,str) for v in values))
                for value in values:req(value,'pyproject.toml','dependency-groups.'+group)
                evidence('pyproject.toml','dependency-groups.'+group,values)
    branch={}
    if 'setup.py' in files:
        tree=ast.parse(files['setup.py'],filename='setup.py')
        dynamic_names={'exec','eval','compile','globals','locals','vars','getattr','setattr','delattr','__import__','__builtins__','__dict__','__getattribute__','__globals__','_getframe','currentframe','f_globals','f_locals'}
        dynamic=[n for n in ast.walk(tree) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load) and n.id in dynamic_names or isinstance(n,ast.Attribute) and n.attr in dynamic_names or isinstance(n,ast.ImportFrom) and n.module in ('builtins','__builtin__') and any(v.name in dynamic_names|{'*'} for v in n.names)]
        if dynamic:
            n=dynamic[0];result['reasons']=[{'reason':'UNKNOWN_DYNAMIC_METADATA','detail':'dynamic execution or namespace reflection in setup metadata scope'}]
            branch={'path':'setup.py','line':n.lineno,'node':type(n).__name__,'name':getattr(n,'id',getattr(n,'attr',None))}
            return result,branch
        # Babel uses direct literal environment-bearing setup keyword values.
        setup_calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and (isinstance(n.func,ast.Name) and n.func.id=='setup' or isinstance(n.func,ast.Attribute) and n.func.attr=='setup')]
        check('one_static_setup_call:'+str(index),len(setup_calls)==1)
        values={kw.arg:ast.literal_eval(kw.value) for kw in setup_calls[0].keywords if kw.arg in {'python_requires','classifiers','install_requires','tests_require','extras_require'}}
        if 'python_requires' in values:result['python_specifiers'].append(values['python_requires']);evidence('setup.py','setup.python_requires',values['python_requires'])
        if 'classifiers' in values:evidence('setup.py','setup.classifiers',values['classifiers'])
        for key in ('install_requires','tests_require'):
            for value in values.get(key,[]):req(value,'setup.py','setup.'+key)
            if key in values:evidence('setup.py','setup.'+key,values[key])
        check('no_setup_testing_extras:'+str(index),not any(k in ('test','tests','testing') for k in values.get('extras_require',{})))
    if 'setup.cfg' in files:
        parser=configparser.ConfigParser(interpolation=None);parser.read_string(files['setup.cfg'].decode())
        check('no_earlier_setup_cfg_fields:'+str(index),not any(parser.has_option('options',k) for k in ('python_requires','install_requires','tests_require','setup_requires')) and not parser.has_option('metadata','classifiers') and not parser.has_section('options.extras_require'))
    parser=configparser.ConfigParser(interpolation=None);parser.read_string(files['tox.ini'].decode())
    for key in ('envlist','env_list'):
        if parser.has_option('tox',key):evidence('tox.ini','tox.'+key,parser.get('tox',key))
    for value in parser.get('testenv','deps').splitlines():
        value=value.strip()
        if not value or value.startswith('#') or re.fullmatch(r'\{env:[A-Z_]+:\}',value):continue
        try:req(value,'tox.ini','testenv.deps')
        except InvalidRequirement as error:
            result['reasons']=[{'reason':'UNKNOWN_REQUIREMENT_GRAMMAR','detail':str(error)}]
            branch={'path':'tox.ini','field':'testenv.deps','literal':value,'line':next(i for i,line in enumerate(files['tox.ini'].decode().splitlines(),1) if line.strip()==value),'literal_include':value.startswith(('-r ','--requirement '))}
            return result,branch
    raise AssertionError('expected_early_refusal_not_reached:'+str(index))

def main():
    code=code_bindings();pool=js(META/'committed/FROZEN_POOL.json')['pool'];catalog=js(META/'source-binding/research/unified_consequence_runtime/archaeology/native-authority-v41/ENVIRONMENT_CATALOG.json');cases=[]
    check('generic_packaging_version',packaging.__version__=='26.0')
    for i,spec in enumerate(pool):
        root=SEALED/f'case-{i:03d}';sr=root/'source-environment';source=sr/'metadata-source';git=source/'.git';case=js(root/'SCREENING_CASE.json');setup=js(sr/'admission-v3.json')
        check('case_setup_exact:'+str(i),case['setup']==setup)
        check('no_git_alternates:'+str(i),not (git/'objects/info/alternates').exists() and not (git/'objects/info/http-alternates').exists())
        check('local_git_object_directory:'+str(i),(git/'objects').is_dir() and not (git/'objects').is_symlink() and (git/'objects').resolve()==git/'objects')
        objects=Objects(git);base=spec['base_commit'];head=spec['head_commit'];kind,commit=objects.get(base)
        check('base_commit_type:'+str(i),kind=='commit');tree=commit.splitlines()[0].decode().removeprefix('tree ');rows=objects.tree(tree)
        index=parse_index(git/'index');check('index_exact_base_tree:'+str(i),index==sorted(rows,key=lambda r:r['path'].encode()))
        check('detached_head_base:'+str(i),read(git/'HEAD').decode().strip()==base)
        check('shallow_base_only:'+str(i),read(git/'shallow').decode().splitlines()==[base])
        fetch=read(git/'FETCH_HEAD').decode();check('fetch_head_exact_base:'+str(i),fetch.split('\t',1)[0]==base and spec['repo'] in fetch)
        gitlinks={r['path']:r for r in rows if r['mode']=='160000'}
        fstree,fsrows=fs_tree(source,gitlinks);check('filesystem_tree_equals_commit_using_index_gitlinks:'+str(i),fstree==tree)
        fsmap={r['path']:r for r in fsrows};check('filesystem_paths_exact:'+str(i),set(fsmap)=={r['path'] for r in rows})
        files={};manifest=[];unsupported=[]
        for r in rows:
            if r['mode']=='160000':
                unsupported.append(r)
                check('gitlink_index_and_empty_materialization:'+str(i)+':'+r['path'],{k:fsmap[r['path']][k] for k in ('path','mode','blob')}==r)
                continue
            kind,raw=objects.get(r['blob']);check('tree_child_blob:'+str(i)+':'+r['path'],kind=='blob');check('filesystem_object_exact:'+str(i)+':'+r['path'],{k:fsmap[r['path']][k] for k in ('path','mode','blob')}==r and sha(raw)==fsmap[r['path']]['sha256'])
            if r['mode'] not in ('100644','100755'):unsupported.append(r)
            files[r['path']]=raw;manifest.append({**r,'sha256':sha(raw)})
        # All object identities are verified from bytes, including objects not tree-reachable.
        for name in list(objects.locations):objects.get(name)
        commit_objects=[name for name,(kind,body) in objects.cache.items() if kind=='commit']
        check('only_base_commit_materialized:'+str(i),commit_objects==[base])
        check('protected_head_absent_from_objects:'+str(i),head not in objects.locations)
        check('no_native_materialization:'+str(i),not (sr/'native').exists() and setup['setup'] is None and setup['runtime'] is None)
        identity={'git_tree':tree,'tracked_tree_sha256':fp(manifest),'file_count':len(files)}
        detail={'index':i,'repository':spec['repo'],'base_commit':base,'base_commit_object_sha1':oid('commit',commit),'base_tree':tree,'filesystem_tree_with_index_gitlinks':fstree,'tracked_entries':len(rows),'mode_counts':{m:sum(r['mode']==m for r in rows) for m in sorted({r['mode'] for r in rows})},'index_sha256':sha(read(git/'index')),'git_objects':len(objects.locations),'commit_objects':commit_objects,'protected_head_object_present':False,'all_git_objects_hash_validated':True,'worktree_exact_base_bytes_modes_paths_with_unmaterialized_gitlinks':True,'packs':objects.pack_records,'unsupported_entries':unsupported,'source_identity':identity if not gitlinks else None,'retained_status':setup['status'],'retained_reason':setup['reason']}
        if unsupported:
            expected='ValueError: only regular tracked files supported; no symlinks or submodules'
            check('exact_mode_refusal:'+str(i),setup['status']=='UNKNOWN_SOURCE_ENVIRONMENT' and setup['reason']==expected and setup['selection'] is None and setup['source_metadata_identity'] is None and not (sr/'selection.json').exists() and not (sr/'metadata-source.tar.gz').exists())
            detail['reproduction']={'branch':'decisive_native_verify._snapshot unsupported tracked mode','first_refused_path':unsupported[0]['path'],'expected_status':'UNKNOWN_SOURCE_ENVIRONMENT','expected_reason':expected,'exact_match':True}
        else:
            check('complete_retained_source_identity:'+str(i),identity==setup['source_metadata_identity'])
            actual=js(sr/'selection.json');constraints,branch=build_constraints(files,i)
            check('exact_static_constraints:'+str(i),constraints==actual['constraints'])
            reason=constraints['reasons'][0]['reason']
            expected={'schema':'UDM_NATIVE_ENVIRONMENT_SELECTION_V41','status':'UNKNOWN','constraints':constraints,'catalog_sha256':fp(catalog),'selector_sha256':sha(read(CODE/'native_environment_selection_v41.py')),'packaging_version':packaging.__version__,'candidates':[{'id':p['id'],'status':'UNKNOWN','reason':reason,'reasons':constraints['reasons']} for p in catalog['profiles']],'selected_profile':None,'reason':reason}
            check('exact_static_selection:'+str(i),actual==expected and setup['selection']==actual)
            check('exact_environment_refusal:'+str(i),setup['status']=='UNKNOWN_ENVIRONMENT_SELECTION' and setup['reason']==reason)
            detail['reproduction']={'branch':branch,'expected_status':'UNKNOWN_ENVIRONMENT_SELECTION','expected_reason':reason,'exact_constraint_record_match':True,'exact_selection_record_match':True,'exact_match':True}
        cases.append(detail)
    dependencies={name:{'path':str(Path(module.__file__).resolve()),'sha256':sha(read(Path(module.__file__).resolve()))} for name,module in sorted(sys.modules.items()) if name=='packaging' or name.startswith('packaging.')}
    result={'schema':'UDM_V41_PURE_FILESYSTEM_SOURCE_IDENTITY_STATIC_REFUSAL_AUDIT','status':'PASS','auditor_source_sha256':sha(Path(__file__).read_bytes()),'authority_code':code,'generic_packaging_dependency':{'version':packaging.__version__,'modules':dependencies},'cases':cases,'checks':CHECKS,'check_count':len(CHECKS),'check_count_note':'Includes mechanical per-object, per-delta-copy and per-file consistency assertions; this is not a count of independent scientific controls.','all_checks_passed':all(c['passed'] for c in CHECKS),'inputs':INPUTS,'boundary':{'git_commands':0,'network_calls':0,'native_calls':0,'retained_code_executed':False,'target_source_executed':False,'original_selector_executed':False,'writes':'this audit directory only','git_objects_inspected':True,'protected_head_materialized':False},'limitations':['Static reproduction implements the complete observed early-refusal paths, not unobserved successful admission/native behavior.','The four mode refusals first encounter symlinks (120000). Wcwidth additionally has a later unmaterialized gitlink (160000); its tree reconstruction uses the validated base-tree/index gitlink object ID and separately verifies an empty filesystem directory, rather than claiming submodule source-byte materialization.','SHA-1 object identity, pack/index checksums, base-only object materialization and worktree equality verify retained consistency; they do not establish authenticity of a remote repository independently of the retained transport/authority evidence.','Generic packaging 26.0 Requirement parsing is executed only to independently reproduce the retained grammar-error text; original project, controller and selector code is never imported or executed.']}
    (RAW/'SOURCE_IDENTITY_AUDIT.json').write_text(canonical(result)+'\n')
    print(canonical({'status':result['status'],'cases':len(cases),'checks':len(CHECKS),'public_refusals':[{'index':r['index'],'repository':r['repository'],'status':r['retained_status'],'reason':r['retained_reason'],'exact_match':r['reproduction']['exact_match']} for r in cases]}))

if __name__=='__main__':main()
