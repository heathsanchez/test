#!/usr/bin/env python3
"""Independent read-only audit of V3c Costanzo 2021 holdout, without importing
prepare.py, predict.py, or evaluate.py. Post-hoc evidence audit, NOT a new blind test.

Authority = official source workbook hashed to fixed digest, fixed 3 GitHub artifacts,
and source-authored exact native columns. Difference != universal functional equality.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from pathlib import Path
import shutil
from urllib.request import Request, urlopen

from openpyxl import load_workbook
import numpy as np

SOURCE_URL = 'https://zenodo.org/records/4560674/files/Costanzo_et_al_Data_File_3_Raw_interaction_dataset.xlsx?download=1'
SOURCE_NAME = 'Costanzo_et_al_Data_File_3_Raw_interaction_dataset.xlsx'
EXPECTED_SOURCE_SHA = 'b4e242087e554df1adc648aefb890144d397a1eb303a55509a90ae08e912c488'
EXPECTED_SOURCE_MD5 = 'f81a8123a8113b795a00e8e154fa072d'
EXPECTED = {
    'allowed': '4cc011240f682d1a0ea5b0f842ee8a8136c5beab2e1a678a613cbeabe1e667ea',
    'sealed': 'e3c87932914c48e86904aab8c2842ab791b14b485bb100c2544aebc423428031',
    'report': 'e380314b5a1cd4580dc270e1d7f34b70d0e7e65d65d6069b5483033502b3c000',
    'receipts': '72359773328a8f09ff69d651b28d8577ac1d16312eb379065524e163aaae3b43',
}
KNOWN_HEADER = {
    0: 'query_orf', 1: 'array_orf', 2: 'Condition',
    12: 'mean_reference_epsilon',
    15: 'rep1_differential_epsilon',
    16: 'rep2_differential_epsilon',
    17: 'mean_differential_epsilon',
    19: 'differential_p_value',
}
D = Decimal


def hashfile(path: Path, algo='sha256') -> str:
    h = hashlib.new(algo)
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def read_json_exact(p: Path, expected: str):
    raw = p.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected, f'RECEIPT_IDENTITY_FAILED: {p.name}'
    return json.loads(raw)


def dec(x):
    if x is None or x == '' or isinstance(x, bool): return None
    try:
        q = D(str(x))
        return q if q.is_finite() else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def condition(x):
    s = ''.join(c for c in str(x or '').casefold() if c.isalnum())
    # Explicit source metadata typo authority; no numeric/outcome matching heuristic.
    return {'boretzeomib': 'bortezomib', 'concanmycina': 'concanamycina'}.get(s, s)


def classified(z):
    # Independent primitive classification with exact (decimal-from-source) comparisons.
    e, p, rep1, rep2, _ref = z
    if e is None or p is None: return (None, None)
    good = p < D('0.05') and abs(e) > D('0.08')
    rigorous = (p < D('0.005') and abs(e) > D('0.08') and rep1 is not None
                and rep2 is not None and rep1*rep2 > 0 and e*rep1 > 0 and e*rep2 > 0)
    return (bool(good), bool(rigorous))


def bh_flags(pvals, alpha=D('0.05')):
    """Exploratory Benjamini–Hochberg sensitivity. Missing tests count at p=1."""
    indexed = sorted((D('1') if p is None else p, i) for i,p in enumerate(pvals))
    largest = 0
    n = len(indexed)
    for rank, (p,i) in enumerate(indexed,1):
        if p <= alpha*D(rank)/D(n): largest = rank
    yes = [False]*n
    for p,i in indexed[:largest]: yes[i] = True
    return yes


def cluster_bootstrap(diff, qs, n=4000):
    groups = sorted(set(qs)); assert len(groups) >= 4
    clusters = {q:[int(v) for v,z in zip(diff,qs) if z == q] for q in groups}
    rng = np.random.default_rng(20261020)
    r = []
    for _ in range(n):
        sampled = rng.choice(groups,len(groups),replace=True)
        vals = [d for q in sampled for d in clusters[q]]
        r.append(sum(vals)/len(vals))
    return [round(float(x),8) for x in np.quantile(r,[.025,.975])]


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--allowed',type=Path,required=True)
    a.add_argument('--sealed',type=Path,required=True)
    a.add_argument('--report',type=Path,required=True)
    a.add_argument('--receipts',type=Path,required=True)
    a.add_argument('--out',type=Path,required=True)
    a.add_argument('--source',type=Path)
    args = a.parse_args(); args.out.mkdir(parents=True,exist_ok=True)
    allowed = read_json_exact(args.allowed, EXPECTED['allowed'])
    sealed = read_json_exact(args.sealed, EXPECTED['sealed'])
    report = read_json_exact(args.report, EXPECTED['report'])
    recorded = read_json_exact(args.receipts, EXPECTED['receipts'])
    assert sealed['allowed_sha256'] == EXPECTED['allowed']
    assert report['sealed_prediction_sha256'] == EXPECTED['sealed']
    assert report['allowed_sha256'] == EXPECTED['allowed']
    assert sealed['source_sha256'] == allowed['source_sha256'] == EXPECTED_SOURCE_SHA
    assert sealed['protocol'] == allowed['protocol'] == '2021_environment_v3'
    assert len(allowed['target']) == len(sealed['decisions']) == len(recorded) == 200
    methods = sealed['methods']
    assert methods == ['contrast_exploration','knn_hit','knn_effect','logistic_hit',
                       'random_forest_hit','global_prevalence','random']
    assert len(allowed['known_conditions']) == 4 and len(allowed['candidate_conditions']) == 10
    assert not set(allowed['known_conditions']) & set(allowed['candidate_conditions'])
    assert not set(allowed['candidate_conditions']) - set(sealed['candidates'])
    assert all(set(t)== {'id','q','a','x'} for t in allowed['target'])
    assert all(len(t['x'])==5 for t in allowed['target'])
    assert len({(t['q'],t['a']) for t in allowed['target']})==200, 'DUPLICATE_TARGET_GENE_PAIR'
    train_genes={g for t in allowed['training'] for g in [t['q'],t['a']]}
    test_genes={g for t in allowed['target'] for g in [t['q'],t['a']]}
    assert not train_genes & test_genes, 'GENE_ORF_LEAKAGE'
    assert len(test_genes)==159 and len(train_genes)==779
    target_keys = {t['id'] for t in allowed['target']}
    assert len(target_keys)==200
    assert [t['id'] for t in allowed['target']] == [t['id'] for t in sealed['decisions']] == [r['id'] for r in recorded]
    for row in sealed['decisions']:
        assert set(row['choices']) == set(methods)
        assert set(row['choices'].values()) <= set(allowed['candidate_conditions'])
    source = args.source or args.out/SOURCE_NAME
    if not source.exists():
        request = Request(SOURCE_URL,headers={'User-Agent':'Independent-Environmental-GI-Audit/1.0'})
        with urlopen(request,timeout=480) as src, source.open('wb') as dst: shutil.copyfileobj(src,dst)
    assert hashfile(source) == EXPECTED_SOURCE_SHA, 'ORIGINAL_SOURCE_SHA_MISMATCH'
    assert hashfile(source,'md5') == EXPECTED_SOURCE_MD5, 'ORIGINAL_SOURCE_MD5_MISMATCH'
    # This reader independently performs native source identity checking; not the V3 evaluator.
    wb=load_workbook(source,read_only=True,data_only=True)
    sheet=wb['Diagnostic array_complete']; reader=sheet.iter_rows(values_only=True)
    head=next(reader)
    assert len(head)==25 and all(head[i]==field for i,field in KNOWN_HEADER.items())
    contexts=set(allowed['known_conditions']+allowed['candidate_conditions'])
    rows=defaultdict(list)
    native_read=0
    for vals in reader:
        q=str(vals[0] or '').strip().upper()
        r=str(vals[1] or '').strip().upper()
        key=q+'|'+r
        if key not in target_keys: continue
        ctx=condition(vals[2])
        if ctx not in contexts: continue
        native_read+=1
        val=(dec(vals[17]),dec(vals[19]),dec(vals[15]),dec(vals[16]),dec(vals[12]))
        rows[(key,ctx)].append(val)
    wb.close()
    assert native_read > 1700, f'ABNORMAL_SOURCE_MATCHES {native_read}'

    per_method={m:Counter() for m in methods}
    successful={m:[] for m in methods}; strict_success={m:[] for m in methods}
    q_list=[]; all_pvals=[]; by_method_pvals={m:[] for m in methods}
    by_method_effect={m:[] for m in methods}; by_method_strict={m:[] for m in methods}
    oracle=0; strict_oracle=0; source_exact_records=0
    cell_claim_supports={}
    candidate_cell_index={}
    for t,pred,trace in zip(allowed['target'],sealed['decisions'],recorded):
        key=t['id'];q=t['q'];q_list.append(q)
        assert pred['id']==key==trace['id'] and trace['q']==q
        assert key.split('|')[0].split('_')[0].upper()==q
        assert key.split('|')[1].split('_')[0].upper()==t['a']
        known=[]
        for ctx in allowed['known_conditions']:
            matched=rows.get((key,ctx),[])
            assert len(matched)==1,'KNOWN_CELL_MISSING_OR_DUPLICATE: '+key+' '+ctx
            known.append(matched[0]); assert classified(matched[0])[0] is False
        for i,z in enumerate(known):
            assert z[0] is not None and abs(float(z[0])-t['x'][i]) < 1e-9, 'KNOWN_FEATURE_CHANGED'
        assert all(z[4] is not None for z in known)
        ref=sum(z[4] for z in known)/D(4)
        assert abs(float(ref)-t['x'][4]) < 1e-9,'REFERENCE_FEATURE_CHANGED'
        actual={}; candidates=[]; anyhit=False; anystrict=False
        for ctx in allowed['candidate_conditions']:
            matched=rows.get((key,ctx),[])
            z=matched[0] if len(matched)==1 else (None,None,None,None,None)
            actual[ctx]=z
            h,st=classified(z)
            anyhit |= h is True; anystrict |= st is True
            candidate_cell_index[(key,ctx)]=len(all_pvals)
            all_pvals.append(z[1])
            candidates.append((ctx,z))
        assert trace['oracle_some_candidate']==anyhit and trace['oracle_strict_some_candidate']==anystrict
        oracle+=int(anyhit);strict_oracle+=int(anystrict)
        for method in methods:
            ctx=pred['choices'][method]
            obs=trace['chosen'][method];z=actual[ctx]
            main,strict=classified(z)
            assert ctx==obs['condition']
            assert main is obs['hit'] and strict is obs['strict_hit'], 'CLASSIFICATION_MISMATCH '+key+method
            assert (main is not None) == obs['measured'], 'MISSINGNESS_MISMATCH'
            for j,label in enumerate(['source_effect','source_p']):
                assert (z[j] is None) == (obs[label] is None), 'EFFECT_P_PRESENT_MISMATCH'
                if z[j] is not None:assert D(obs[label]) == z[j], 'SOURCE_NUMERIC_DISCREPANCY'
            assert all((obs['signed_replicates'][j] is None if z[j+2] is None else D(obs['signed_replicates'][j])==z[j+2]) for j in range(2))
            per_method[method]['attempts']+=1
            per_method[method]['observed']+=int(main is not None)
            per_method[method]['missing']+=int(main is None)
            per_method[method]['success']+=int(main is True)
            per_method[method]['strict_success']+=int(strict is True)
            successful[method].append(int(main is True));strict_success[method].append(int(strict is True))
            by_method_pvals[method].append(z[1]);by_method_effect[method].append(z[0]);by_method_strict[method].append(strict)
            if main is True:
                cell_claim_supports[(key,ctx)]={f'source:{EXPECTED_SOURCE_SHA}',f'cell:{key}:{ctx}',f'policy:primary-v3'}
            source_exact_records+=1
    assert oracle==report['oracle_measurable_targets']==14
    assert strict_oracle==report['oracle_strict_targets']==5
    assert len(all_pvals)==2000
    for method in methods:
        for k in ['attempts','observed','missing','success','strict_success']:
            assert per_method[method][k]==report['methods'][method][k], f'COUNTER_MISMATCH {method}:{k}'
    differences=[a-b for a,b in zip(successful['contrast_exploration'],successful['knn_hit'])]
    assert abs(sum(differences)/200-report['primary_method_difference'])<1e-12
    assert cluster_bootstrap(differences,q_list)==report['query_cluster_bootstrap_95']
    assert len(set(q_list))==8
    # Post-hoc sensitivity: BH selected-only (200/method) and whole known test universe
    # (200*10 = 2000). These DO NOT certify familywise error or independence.
    bh_all=bh_flags(all_pvals)
    bh_method={}
    for method in methods:
        chosen_flags=bh_flags(by_method_pvals[method])
        bh_method[method]={
            'BH_q0.05_selected_Ps_only':sum(chosen_flags),
            'BH_selected_Ps_and_effect_gt_0p08':sum(f and e is not None and abs(e)>D('0.08') for f,e in zip(chosen_flags,by_method_effect[method])),
            'BH_selected_Ps_effect_and_replicate_strict':sum(f and e is not None and abs(e)>D('0.08') and bool(st) for f,e,st in zip(chosen_flags,by_method_effect[method],by_method_strict[method])),
        }
    # Whole 200x10 family: exploratory, source-native p-value sensitivity, preserving
    # the exact pre-outcome target/context roster, including missing as p=1.
    # Neither BH under arbitrary dependence nor the source study's broader screening
    # multiplicity is promised by this restricted post-hoc family.
    assert len(candidate_cell_index)==2000
    full_BH={}; full_bonf={}; family_size=len(all_pvals)
    cutoff=D('0.05')/D(family_size)
    for method in methods:
        bhs=[];bons=[];assays=[]
        for t,d in zip(allowed['target'],sealed['decisions']):
            k=(t['id'],d['choices'][method]);i=candidate_cell_index[k]
            val=all_pvals[i];eff=by_method_effect[method][len(bhs)]
            is_effect=eff is not None and abs(eff)>D('0.08')
            bhs.append(bool(bh_all[i] and is_effect))
            bons.append(bool(val is not None and val<=cutoff and is_effect))
            assays.append({'target':k[0],'context':k[1], 'bh':bhs[-1], 'bonferroni':bons[-1]})
        full_BH[method]=sum(bhs)
        full_bonf[method]=sum(bons)
    # Negative control for incorrect scope: same smallest valid p can fail a
    # study-wide Bonferroni with ~363k tests. No family choice changed afterward.
    study_wide_nominal_cutoff=str(D('0.05')/D('363201'))
    # Source-backed narrowed biology claim supports: revocation is modeled as a separate
    # *post-hoc* finite CLC/FLASH test, not formal verification of the entire calculus.
    claim_keys=sorted(cell_claim_supports)
    assert len(claim_keys)>=3
    strict_detected=[]
    for t,trace in zip(allowed['target'],recorded):
        if trace['chosen']['contrast_exploration']['strict_hit'] is True:
            strict_detected.append((t['id'],trace['chosen']['contrast_exploration']['condition']))
    assert len(strict_detected)==1
    chosen=strict_detected[0];token=f'cell:{chosen[0]}:{chosen[1]}'
    live=set().union(*cell_claim_supports.values())
    before={k for k,v in cell_claim_supports.items() if v <= live}
    live_after=live-{token}
    after={k for k,v in cell_claim_supports.items() if v <= live_after}
    assert before-after=={chosen} and chosen not in after
    assert after == before - {chosen}
    # An actual dependency-cone reclosure is tested at the *consumer* level.
    # Withdraw one original measured cell (P/effect/replicate authority) from a
    # copied evaluation view. Preserve attempt IDs and choices. Recount only
    # claims whose exact source cell is no longer admissible. A result goes to
    # UNKNOWN, not a negative biological claim; denominator stays as attempted.
    # The chosen positive cell is used AFTER the holdout was opened, so this is
    # a diagnostic of revocation semantics, NOT a prospective study.
    cell_dependencies={m:[(t['id'],d['choices'][m]) for t,d in zip(allowed['target'],sealed['decisions'])] for m in methods}
    original_evidence_hits={m:sum(successful[m]) for m in methods}
    original_evidence_strict={m:sum(strict_success[m]) for m in methods}
    reclosed_hits={};reclosed_strict={};reclosed_unknown={}; affected_methods=[]
    for m in methods:
        indices=[i for i,k in enumerate(cell_dependencies[m]) if k==chosen]
        assert len(indices)<=1, 'DUPLICATED SELECTED CELL IN SAME METHOD'
        was=[successful[m][i] for i in indices];was_strict=[strict_success[m][i] for i in indices]
        reclosed_hits[m]=original_evidence_hits[m]-sum(was)
        reclosed_strict[m]=original_evidence_strict[m]-sum(was_strict)
        reclosed_unknown[m]=per_method[m]['missing']+len(indices)
        assert reclosed_hits[m]>=0 and reclosed_strict[m]>=0
        if indices:affected_methods.append(m)
        else:
            assert reclosed_hits[m]==original_evidence_hits[m]
            assert reclosed_strict[m]==original_evidence_strict[m]
            assert reclosed_unknown[m]==per_method[m]['missing']
    assert set(affected_methods)=={'contrast_exploration','knn_hit'}
    assert reclosed_hits['contrast_exploration']==2 and reclosed_hits['knn_hit']==1
    assert reclosed_strict['contrast_exploration']==0 and reclosed_strict['knn_hit']==0
    # After restoring the SAME original cell witness, all consumers recover
    # exactly; detached claims not on the dependency cone never changed.
    restored_hits={m:reclosed_hits[m]+sum(successful[m][i] for i,k in enumerate(cell_dependencies[m]) if k==chosen) for m in methods}
    restored_strict={m:reclosed_strict[m]+sum(strict_success[m][i] for i,k in enumerate(cell_dependencies[m]) if k==chosen) for m in methods}
    assert restored_hits==original_evidence_hits and restored_strict==original_evidence_strict
    # Entire source authority removed: all biological source-dependent warrant collapses to UNKNOWN.
    without_source=live-{f'source:{EXPECTED_SOURCE_SHA}'}
    assert not {k for k,v in cell_claim_supports.items() if v<=without_source}
    # No positive EQ is issued from absence of a selected separator; UNKNOWN remains UNKNOWN.
    semantics={'DIST':len(before),'UNKNOWN_on_cell_withdrawal':len(before-after),
               'unchanged_other_claims':len(after),'after_global_source_withdrawal':0,
               'selected_source_cell':{'target':chosen[0],'condition':chosen[1], 'evidence_token':token},
               'affected_methods':affected_methods, 'reclosed_counts':reclosed_hits,
               'reclosed_strict_counts':reclosed_strict,'reclosed_unknown_counts':reclosed_unknown,
               'restored_counts_exact':restored_hits==original_evidence_hits and restored_strict==original_evidence_strict}
    result={
        'status':'PASS_INDEPENDENT_NATIVE_2021_SOURCE_AUDIT_POSTHOC',
        'original_workbook_sha256':EXPECTED_SOURCE_SHA,
        'original_workbook_md5':EXPECTED_SOURCE_MD5,
        'immutable_artifact_hashes':EXPECTED,
        'source_matched_rows_for_protected_targets':native_read,
        'gene_disjoint_train_count':len(train_genes),
        'gene_disjoint_target_count':len(test_genes),
        'target_pair_count':len(allowed['target']),
        'query_gene_count':len(set(q_list)),
        'query_gene_counts':dict(Counter(q_list)),
        'method_native_counts':{m:dict(v) for m,v in per_method.items()},
        'oracle_primary':oracle,'oracle_strict':strict_oracle,
        'primary_minus_knn':sum(differences)/200,
        'primary_bootstrap_cluster_95':report['query_cluster_bootstrap_95'],
        'bh_selected_per_method_DIAGNOSTIC_NOT_PRECOMMITTED':bh_method,
        'bh_2000_candidate_pvalues_DIAGNOSTIC_NOT_PRECOMMITTED':sum(bh_all),
        'bh_whole_2000_family_selected_effect_events_DIAGNOSTIC':full_BH,
        'bonferroni_whole_2000_family_selected_effect_events_DIAGNOSTIC':full_bonf,
        'bonferroni_2000_alpha_0p05_p_cutoff':str(cutoff),
        'bonferroni_entire_study_363201_nominal_cutoff_NOT_APPLIED':study_wide_nominal_cutoff,
        'finite_lineage_authority_withdrawal':semantics,
        'strict_primary_hits_query_gene_count':len({t['q'] for t,r in zip(allowed['target'],recorded) if r['chosen']['contrast_exploration']['strict_hit']}),
        'v3_claim':'SOURCE_BOUND_RESULTS_ONLY; method superiority NOT WARRANTED',
        'limitations':['Cell event labels are source-authored P values, not independent lab reanalysis',
                       'BH exploratory under dependence; NOT confirmed FDR control',
                       'Original selection uses 8 query genes; genotype pairs not independent study replicates',
                       'Whole 2000-family significance is a post-hoc restricted family and not original study-wide multiplicity',
                       'Finite CLC/Flash revocation model is a scoped audit, not a Lean proof or novel biology']
    }
    out=args.out/'independent_source_audit.json'
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    if args.source is None:source.unlink()
    print('BIOLOGY_2021_INDEPENDENT_AUDIT_RESULT='+json.dumps(result,sort_keys=True),flush=True)
    print('BIOLOGY_2021_NATIVE_REPLAY_AND_DEPENDENCY_WITHDRAWAL_PASS',flush=True)

if __name__ == '__main__':main()