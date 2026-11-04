from pathlib import Path
import argparse,hashlib,lzma,subprocess,tarfile,tempfile,json
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
here=Path(__file__).resolve().parent;v=json.loads((here/'verified-readback.json').read_text())
archive=here/'canonical-source.patch.xz';raw=archive.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='ab59e95f2a1a96b657b764a317ed781bda944392f59819cacb5abdd8ac825978'
patch=lzma.decompress(raw);assert hashlib.sha256(patch).hexdigest()==v['canonical_patch_sha']
manifest_bytes=(here/'source-manifest.json').read_bytes();assert hashlib.sha256(manifest_bytes).hexdigest()==v['source_manifest_sha']
manifest=json.loads(manifest_bytes);a.out.mkdir(parents=True,exist_ok=False)
with tempfile.TemporaryDirectory()as tmp:
 tmp=Path(tmp);base=tmp/'base.tar';delta=tmp/'source.patch';delta.write_bytes(patch)
 with base.open('wb')as stream:subprocess.run(['git','-C',str(a.repo),'archive',v['source_base'],'metatron-kernel'],stdout=stream,check=True)
 with tarfile.open(base)as t:t.extractall(a.out,filter='data')
 subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(delta)],cwd=a.out,check=True)
source=a.out/'metatron-kernel'
assert {str(p.relative_to(source))for p in source.rglob('*')if p.is_file()}==set(manifest)
for n,sha in manifest.items():assert hashlib.sha256((source/n).read_bytes()).hexdigest()==sha,n
print(json.dumps(dict(status='SOURCE_RECONSTRUCTED',files=len(manifest),qualified_binary=v['binary_sha'])))
