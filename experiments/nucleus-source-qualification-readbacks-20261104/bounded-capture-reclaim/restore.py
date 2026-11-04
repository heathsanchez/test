from pathlib import Path
import argparse,hashlib,json,lzma,subprocess,tarfile,tempfile
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();repo=a.repo.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest();base='a2578e77079719ff2064f910bd82fd01d8e120b6'
child=subprocess.Popen(['git','-C',str(repo),'archive',base,'metatron-kernel'],stdout=subprocess.PIPE)
with tarfile.open(fileobj=child.stdout,mode='r|')as archive:archive.extractall(out,filter='data')
assert child.wait()==0
canonical=repo/'experiments/nucleus-source-qualification-readbacks-20261104/projected-function-eta/canonical-source.patch.xz';assert sha(canonical.read_bytes())=='ab59e95f2a1a96b657b764a317ed781bda944392f59819cacb5abdd8ac825978'
raw=lzma.decompress(canonical.read_bytes());assert sha(raw)=='30d563934bca48de43c052e19b0e31f5bdb7d1af16d18d2d6a5d38b4387e0693'
components=[(raw,'30d563934bca48de43c052e19b0e31f5bdb7d1af16d18d2d6a5d38b4387e0693'),((repo/'experiments/nucleus-quotient-result-projection-20261104/quotient-result-projection.patch').read_bytes(),'7fe08412e93652d60bdba0dc3fc499cebb34e7f344fe3d8db254c1cf8775d650'),((repo/'experiments/nucleus-bounded-capture-reclaim-20261104/bounded-capture-reclaim.patch').read_bytes(),'fc0a7dbcaf7df441dabd959ab78060535f0d92636e5a7666f46646d3531270f3')]
for content,expected in components:
 assert sha(content)==expected;subprocess.run(['patch','--batch','--fuzz=0','-p1'],cwd=out,input=content,check=True)
manifest=json.loads((Path(__file__).resolve().parent/'source-manifest.json').read_text());assert len(manifest)==368
assert {str(p.relative_to(out/'metatron-kernel'))for p in(out/'metatron-kernel').rglob('*')if p.is_file()}==set(manifest)
for name,expected in manifest.items():assert sha((out/'metatron-kernel'/name).read_bytes())==expected,name
print(json.dumps(dict(status='VERIFIED_COMPLETE_SOURCE_RECONSTRUCTION',files=len(manifest),base=base)))
