#!/usr/bin/env python3
"""Independent direct-integer implementation of 1997 FreeLIP source semantics.
V14 preregistered on the isolated branch before native source execution.
No general historical ECDSA / NSA origin claim is authorized by this test.
"""
from __future__ import annotations
import hashlib,json,subprocess,sys,platform,time
from pathlib import Path

M=(1<<107)-1
A=pow(3,121,M)
U=1<<26
BOUND=M-(U-1)
P=int('FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF',16)
SEEDS=[20000,20420,7157891,1234567,871696354]
HERE=Path(__file__).resolve().parent

def py_stream(seed, count):
    assert seed>0
    state=seed%M
    values=[];rej=0
    while len(values)<count:
        state=state*A%M
        if state>=BOUND:
            rej+=1
            continue
        values.append(state%U)
    return values,rej

def point_from_limbs(limbs):
    n=0
    for x in limbs:
        assert 0<=x<U
        n=n*U+x
    return n%P

def native_exe(exe,seed,mode):
    p=subprocess.run([str(exe),str(seed),mode],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=25)
    if p.stderr.strip():
        raise AssertionError(f'legacy native warning/error: {p.stderr[:450]}')
    tokens=p.stdout.split()
    assert len(tokens)==(1 if mode=='point' else 20), (seed,mode,tokens)
    return [int(x) for x in tokens]

def main():
    exe=(HERE/'native_freelip').resolve() if len(sys.argv)<2 else Path(sys.argv[1]).resolve()
    if not exe.is_file():raise SystemExit('UNKNOWN_ENVIRONMENT: native 1997 binary not found')
    tests=[]
    for seed in SEEDS:
        words,rej=py_stream(seed,20)
        got_words=native_exe(exe,seed,'words')
        assert words==got_words, (seed,words[:4],got_words[:4])
        result,_=py_stream(seed,11)
        expected=point_from_limbs(result)
        got_point=native_exe(exe,seed,'point')[0]
        assert got_point==expected, (seed,got_point,expected)
        assert 0<=got_point<P
        # Fix one bit at the first returned limb, leaving the rest unmodified.
        mut=result[:]; mut[0]^=1
        assert point_from_limbs(mut)!=expected
        # A distinct seed changes the full source point within this frozen domain.
        other,_=py_stream(seed+1,11)
        assert point_from_limbs(other)!=expected
        tests.append({'seed':seed,'native_and_independent_20_words_match':True,
           'native_point_equals_python_11_limb_sampler':True,
           'original_source_p256_sample_dec':str(got_point),
           'source_accepted_words11':result,
           'python_extra_rejections_first20':rej,
           'two_mutation_guards_pass':True})
    local={'status':'WARRANTED_BOUNDED_NATIVE_SOURCE_26BIT_SAMPLER_FIDELITY',
        'source_authority':'1997 mirrored FreeLIP v1.1 exact commit 00898a4814d2cc1244bf348682be6ed10dda35f0',
        'frozen_protocol_commit':'8d8dc687b2c0e7cf94c9aaab44cccd4ba8f7f951',
        'source_abi':'32bit C -DSINGLE_MUL (NBITS=26)',
        'test_seed_count':len(tests),'tested_words':100,'tested_direct_points':5,
        'tests':tests,'separate_mode_reseed':True,
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'c_wrapper_sha256':hashlib.sha256((HERE/'v14_native.c').read_bytes()).hexdigest(),
        'historical_NSA_1997_source':'UNKNOWN',
        'this_is_not_general_semantic_equivalence_proof':True,
        'v13_exclusion_logic_unchanged':True,
        'security_implications':'NONE'}
    out=HERE/'V14_RESULTS.json';out.write_text(json.dumps(local,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':local['status'],'verified_seeds':len(tests),
        'native_words':local['tested_words'],'native_points':5,
        'native_point_samples':[t['original_source_p256_sample_dec'] for t in tests],
        'unknown_historical_generator':True},indent=2))
if __name__=='__main__':main()
