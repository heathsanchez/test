#!/usr/bin/env python3
"""Independent original-C vs Python arithmetic root selection qualification."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

def run_native(program,a,p):
    proc=subprocess.run([str(program),str(a),str(p)],capture_output=True,text=True,timeout=30,check=True)
    lines=proc.stdout.strip().splitlines()
    if len(lines)!=1 or not lines[0].lstrip('-').isdigit():
        raise AssertionError(('invalid native transcript',proc.stdout,proc.stderr))
    return int(lines[0])

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument('--native',required=True)
    arg.add_argument('--data',default='V7_RESULTS.json')
    arg.add_argument('--out',default='V7_NATIVE_RESULTS.json')
    args=arg.parse_args()
    data=json.loads(Path(args.data).read_text())
    prog=Path(args.native).resolve()
    cases=[]
    for item in data['cases']:
        p=int(item['p_hex'],16)
        c=int(item['source_c_hex'],16)
        a=(-27*pow(c,-1,p))%p
        expected=int(item['original_zsqrtmod_b_hex'],16)
        actual=run_native(prog,a,p)
        assert expected==actual,(item['curve'],expected,actual)
        assert actual*actual%p==a
        cases.append({'name':item['curve'],'exact_match':True,'published':item['original_zsqrtmod_matches_published_b'],'native_b_hex':hex(actual)})
    skipped=data['candidate_876']
    p=int(data['cases'][2]['p_hex'],16)
    c=int('276E46B26A6E09FBA8200CDD418D6DC3738C6B169131927838EC8E71DE4E8548',16)
    original_876=run_native(prog,(-27*pow(c,-1,p))%p,p)
    assert hex(original_876)==skipped['result_b_hex']
    neg=[]
    for item in data['negative_nonresidue_controls']:
        candidate=next(x for x in data['cases'] if int(x['p_hex'],16).bit_length()==item['p_bits'])
        modulus=int(candidate['p_hex'],16)
        result=run_native(prog,item['nonresidue'],modulus)
        assert result==0,('invalid square mutant accepted',item,result)
        neg.append({'bits':item['p_bits'],'returned_zero':True})
    out={
      'status':'PASS_NATIVE_SOURCE_EXACT_ROOT_CHOICE_BOUNDED',
      'source_implementation':'FreeLIP v1.1 mirror commit 00898a4814d2cc1244bf348682be6ed10dda35f0',
      'test':cases,'candidate_876':hex(original_876),
      'negative_controls':neg,
      'expected_published_matches':4,
      'p224_disagreement':True,
      'unique_historical_inference':'UNKNOWN',
      'native_harness_sha256':hashlib.sha256(Path(__file__).with_name('native_freelip_sqrt.c').read_bytes()).hexdigest(),
      'compare_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    assert sum(row['published'] for row in cases)==4
    assert {row['name'] for row in cases if not row['published']}=={'secp224r1'}
    Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'cases':len(cases),'nonresidue_negatives':len(neg),'candidate_876':out['candidate_876']}))
if __name__=='__main__':main()
