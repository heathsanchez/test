"""Close a supplied-run offline dossier into the canonical screening audit.

No target execution or source reads. A PASS refers to retained screening evidence
only. It does not make UNKNOWN cases eligible and cannot establish G2–G6.
"""
import argparse
import datetime
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dossier',type=Path,required=True)
    parser.add_argument('--dossier-sha256',required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    spec=importlib.util.spec_from_file_location('_frozen_v43_screening_auditor',HERE/'audit_retained_v44.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for name,expected in json.loads((HERE/'AUDITOR_FREEZE.json').read_text())['source_files_sha256'].items():
        module.require(module.sha(Path(name).read_bytes())==expected,'frozen auditor/dependency changed')
    raw=args.dossier.read_bytes();module.require(module.sha(raw)==args.dossier_sha256,'dossier pin differs')
    value=json.loads(raw);module.require_closed_dossier(value)
    actor=Path(value['attestation']['path']);module.require(module.sha(actor.read_bytes())==value['attestation']['sha256'],'actor attestation changed')
    actor=json.loads(actor.read_bytes())
    for key,expected in [('independent_screener',True),('search_or_policy_outcomes_accessed',False),('learner_future_source_accessed',False)]:
        module.require(actor.get(key) is expected,'original screener exposure attestation missing')
    module.require(len(value['reports'])==len(value['cases']) and all('raw_identity' in c['identity'] or not c['eligible'] for c in value['cases']),
        'complete fixed pool raw/native context audit missing')
    module.require(value['reports_sha256']==module.fp(value['reports']),'sealed reports fingerprint differs')
    result={'schema':'UDM_V44_INDEPENDENT_ADMISSION_ONLY_SCREENING_AUDIT_V1',
        'status':'PASS_ADMISSION_ONLY_SCREENING_AUDIT','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'auditor':'/root/integrate_bootstrap_runtime','source_commit':value['source_commit'],
        'pool_sha256':value['pool_sha256'],'reports_sha256':value['reports_sha256'],
        'reports':value['reports'],'eligibility_rule':'PASS_NATIVE_OR_FAIL_NATIVE_IDENTICAL',
        'all_screened_cases_and_costs_retained':True,'independent_screener':True,
        'search_or_policy_outcomes_accessed':False,'learner_future_source_accessed':False,
        'exposure_scope':'Original independent screening role only, supported by exact actor attestation and controller evidence. Auditor source/native diagnostics remain sealed before learner role release.',
        'scientific_scope':'Metadata/admission-only; all authentic PASS/FAIL admissions equally eligible; all UNKNOWN/refusals retained; no replacement, repairs, native retries, candidate or policy search.',
        'counts':{'screened_cases':len(value['reports']),'eligible_cases':sum(row['eligible'] for row in value['reports'])},
        'costs':value['costs'],'dossier':{'path':str(args.dossier.absolute()),'sha256':args.dossier_sha256},
        'authority':value['authority'],'controller':value['controller'],'attestation':value['attestation'],
        'all_checks_closed':True,'checks':value['checks'],'limitations':value['limitations'],
        'scientific_verdicts':{'G'+str(i):'UNKNOWN' for i in range(2,7)}}
    with args.out.open('x') as output:output.write(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(module.canonical({'status':result['status'],'path':str(args.out.absolute()),'sha256':module.sha(args.out.read_bytes())}))


if __name__=='__main__':main()
