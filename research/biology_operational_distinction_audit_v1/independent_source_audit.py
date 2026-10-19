#!/usr/bin/env python3
"""Independent SOURCE-EXACT audit of biology V1a.

Deliberately does NOT call, import, modify, or execute experiment.py.
Uses standard-library TSV/ZIP parsing and separately obtained original archive.
Validates the original sealed predictions and observed 100-pair outcomes on native
matrix cells and inspects allele IDs, reciprocal measurements and missingness.
The audit is retrospective: not a new scientific prospective holdout.
"""
import argparse
from collections import Counter, defaultdict
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import numpy as np
from pathlib import Path
import re
import urllib.request
import zipfile

ARCHIVE_URL = ('https://thecellmap.org/costanzo2016/data_files/'
               'Raw%20genetic%20interaction%20datasets%3A%20Matrix%20format.zip')
EXPECTED_ARCHIVE_SHA = '53c69b7dc6e54aeff54afddfa84a24741b9e09c2fdc6bfd9fcbf0b73939ec30f'
EXPECTED_NXN_SHA = '10e82acc42fe66416111cfecd7b62040c284664741df15bd2c3d95f7f410bd9c'
EXPECTED_PRED_SHA = 'e9e4ef40bf963ee5d356a7baf6dca7ce511804ce99286f682beda253a963eceb'
ORF = re.compile(r'Y[A-P][LR]\d{3}[CW](?:-[A-Z])?$', re.I)
METHODS = ('warrant_lcb', 'knn_point', 'ridge_point', 'global_variance', 'random')


def hashpath(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for piece in iter(lambda: f.read(1 << 20), b''):
            h.update(piece)
    return h.hexdigest()


def get_archive(dest):
    if not dest.exists():
        req = urllib.request.Request(ARCHIVE_URL, headers={'User-Agent':'biology-independent-source-audit/1.0'})
        with urllib.request.urlopen(req, timeout=180) as response, dest.open('wb') as f:
            import shutil
            shutil.copyfileobj(response, f)
    assert hashpath(dest) == EXPECTED_ARCHIVE_SHA, 'WRONG ORIGINAL ARCHIVE'
    return dest


def parse_float(s):
    try: return float(s)
    except (TypeError, ValueError): return float('nan')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--receipts', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--archive', type=Path)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    archive = args.archive or (args.out / 'raw_original.zip')
    get_archive(archive)
    b=(args.receipts/'sealed_predictions.json').read_bytes()
    assert hashlib.sha256(b).hexdigest() == EXPECTED_PRED_SHA, 'PREDICTION RECEIPT MUTATED'
    seals=json.loads(b)
    report=json.loads((args.receipts/'outcome_report.json').read_bytes())
    orig_prov=json.loads((args.receipts/'provenance.json').read_bytes())
    assert report['predictions_sha256'] == EXPECTED_PRED_SHA
    assert orig_prov['cdt_sha256'] == EXPECTED_NXN_SHA
    assert len(seals['attempts']) == len(report['each_pair']) == 100
    with zipfile.ZipFile(archive) as z:
        matrix_names=[n for n in z.namelist() if n.endswith('.cdt')]
        found=[n for n in matrix_names if n.endswith('/SGA_NxN_clustered.cdt')]
        assert len(found) == 1, f'Native NxN identities ambiguous: {found}'
        with z.open(found[0]) as f:
            # Independently hash the source bytes before interpreting them.
            h=hashlib.sha256()
            with (args.out/'original_NxN.cdt').open('wb') as raw:
                for chunk in iter(lambda: f.read(1024*1024), b''):
                    h.update(chunk);raw.write(chunk)
        assert h.hexdigest() == EXPECTED_NXN_SHA, 'CDT SOURCE HASH WRONG'
    paths=(args.out/'original_NxN.cdt')
    attempts=seals['attempts']
    index_to_methods=defaultdict(list)
    target_rows=set()
    requested_cols=set(seals['known_array_indices'])|set(seals['candidate_array_indices'])
    for a in attempts:
        for ix in (a['target_row_a'],a['target_row_b']): target_rows.add(ix)
        for m in METHODS:
            index_to_methods[a['choices'][m]['candidate_array_index']].append((a['pair_index'],m))
    known_cols=list(seals['known_array_indices']);candidate_cols=list(seals['candidate_array_indices'])
    chosen_cols=sorted(requested_cols)
    localcols={j:i for i,j in enumerate(chosen_cols)}
    rows=[]; ids=[]; source_rows={}
    with paths.open('r',newline='',encoding='utf-8-sig') as f:
        reader=csv.reader(f,delimiter='\t')
        hdr=next(reader)
        metas=[next(reader) for _ in range(5)]
        values=[j for j,c in enumerate(hdr) if c.lower().startswith('dma')]
        assert len(values) == 3892 and len(hdr) > len(values)
        assert all(j>=0 and j<len(values) for j in chosen_cols)
        assert 'ORF' in hdr
        orf_idx=hdr.index('ORF')
        # Column indices in receipts are offsets into selected DMA columns, not raw TSV.
        origcols=[values[j] for j in chosen_cols]
        for row_index, fields in enumerate(reader):
            if not fields or not fields[orf_idx]: continue
            ids.append(fields[orf_idx]);
            rows.append([parse_float(fields[k]) for k in origcols])
            if row_index in target_rows:
                source_rows[row_index]=[fields[k] for k in origcols]
    assert len(rows) == 3608 and len(ids)==3608
    assert len(chosen_cols) == 136
    assert len(set(ids)) > 3400
    assert all(attempts[i]['query_a']==ids[a['target_row_a']] and attempts[i]['query_b']==ids[a['target_row_b']] for i,a in enumerate(attempts))
    # Re-evaluate each target in *three* number semantics:
    # (1) published decimal strings as exact base-10 values; (2) IEEE float64;
    # (3) numpy float32 matching ORIGINAL V1a implementation.
    # Decimals are the interpretation authority for literal threshold comparisons.
    np32=np.asarray(rows,dtype=np.float32)
    def decimal_gap(a,b,col):
        i=localcols[col]
        try:
            return abs(Decimal(source_rows[a][i])-Decimal(source_rows[b][i]))
        except (InvalidOperation,TypeError): return None
    truth_by_pair={entry['pair_index']:entry for entry in report['each_pair']}
    raw_hit=Counter(); raw_present=Counter(); disagreements=[]; new_oracle_count=0
    legacy_oracle_count=0; exact_decimal_hit=Counter(); exact_decimal_oracle_count=0
    boundary_differences=[]
    for attempt in attempts:
        pi=attempt['pair_index']
        a,b=attempt['target_row_a'],attempt['target_row_b']
        observed_max=max(abs(rows[a][localcols[j]]-rows[b][localcols[j]]) for j in known_cols)
        if abs(observed_max-attempt['observed_panel_max_gap'])>1e-5:
            disagreements.append(f'Panel mismatch pair {pi}')
        if observed_max>0.08000001:
            disagreements.append(f'Panel not equivalent {pi}')
        sep=0;seplegacy=0;sepdecimal=0
        for j in candidate_cols:
            z=abs(rows[a][localcols[j]]-rows[b][localcols[j]])
            legacy=float(abs(np32[a,localcols[j]]-np32[b,localcols[j]]))
            exact=decimal_gap(a,b,j)
            if z == z and z >=0.16:sep+=1
            if legacy == legacy and legacy >=0.16:seplegacy+=1
            if exact is not None and exact >=Decimal('0.16'):sepdecimal+=1
        new_oracle_count+=int(bool(sep))
        legacy_oracle_count+=int(bool(seplegacy))
        exact_decimal_oracle_count+=int(bool(sepdecimal))
        if bool(seplegacy)!=truth_by_pair[pi]['potentially_distinguishable']:
            disagreements.append(f'Legacy float32 oracle count mismatch pair {pi}')
        if bool(seplegacy)!=bool(sepdecimal):
            boundary_differences.append({'pair':pi,'method':'oracle_any_128',
                'legacy':bool(seplegacy),'literal_source_decimal':bool(sepdecimal)})
        for method in METHODS:
            col=attempt['choices'][method]['candidate_array_index']
            val=abs(rows[a][localcols[col]]-rows[b][localcols[col]])
            orig=truth_by_pair[pi]['observations'][method]
            legacy=float(abs(np32[a,localcols[col]]-np32[b,localcols[col]]))
            exact=decimal_gap(a,b,col)
            finite=(val == val and abs(val)!=float('inf'))
            hit=bool(finite and legacy >=.16)
            literal_hit=bool(exact is not None and exact >=Decimal('0.16'))
            raw_present[method]+=int(finite)
            raw_hit[method]+=int(hit)
            exact_decimal_hit[method]+=int(literal_hit)
            if literal_hit!=hit:
                boundary_differences.append({'pair':pi,'method':method,'original_float32_gap':legacy,
                    'literal_decimal_gap':str(exact),'original_hit':hit,'literal_source_hit':literal_hit})
            if finite != orig['measured'] or hit != orig['distinction_detected'] or (finite and abs(legacy-orig['actual_abs_epsilon_gap']) > 1e-6):
                disagreements.append(f'Native FLOAT32 gap mismatch {pi}:{method}, computed={legacy}, receipt={orig}')
    assert not disagreements, f'SOURCE_OUTCOME_DISCREPANCIES: {disagreements[:10]}'
    assert legacy_oracle_count == report['pairs_with_any_measured_separator_in_128_candidates']
    # Metadata: infer the source column ORF row only if nearly all values match
    # canonical yeast systematic gene names; otherwise explicitly UNKNOWN.
    array_orf_summaries=[]
    for meta_index, meta in enumerate(metas):
        mapped=[meta[j] if j<len(meta) else '' for j in values]
        match=sum(bool(ORF.fullmatch(x)) for x in mapped)
        array_orf_summaries.append({'metadata_line':meta_index+2,'orf_format_count':match,'first_header_values':meta[:6],
                                    'sample_array_values':[mapped[i] for i in candidate_cols[:5]]})
    best=max(range(len(metas)),key=lambda i:array_orf_summaries[i]['orf_format_count'])
    conf=array_orf_summaries[best]['orf_format_count']/len(values)
    arr_gene=None
    if conf>0.9:
        arr_gene={i:metas[best][values[i]] for i in range(len(values))}
    query_counts=Counter(ids)
    dup_queries={k:v for k,v in query_counts.items() if v>1}
    # Check exact original train/target split (random generator matches stable seed;
    # only used here to audit duplication/reciprocal sources, not predictions).
    rng=np.random.default_rng(20261019)
    perm=rng.permutation(len(ids)); cut=int(len(ids)*.75)
    cal_ids=set(ids[int(j)] for j in perm[:cut]); target_ids=set(ids[int(j)] for j in perm[cut:])
    cross_split_orfs=sorted(cal_ids & target_ids)
    reverse_possible=0;reverse_pairs=[]
    if arr_gene is not None:
        selected_context_genes=set(arr_gene[j] for j in requested_cols)
        for attempt in attempts:
            pairgenes={attempt['query_a'],attempt['query_b']}
            represented=pairgenes & selected_context_genes
            if represented:
                reverse_possible+=1
                reverse_pairs.append({'pair_index':attempt['pair_index'], 'represented_target_orfs':sorted(represented)})
    diagnostics={
        'status':'WARRANTED_SOURCE_EXACT_REPLAY_WITH_SOURCE_PRECISION_SENSITIVITY',
        'scope':'Independent original raw TSV extraction and 100-pair outcome replay, not new biological prospectivity',
        'original_archive_sha256':hashpath(archive),
        'cdt_sha256':h.hexdigest(),
        'matrix_members':matrix_names,
        'matrix_shape': [len(rows),len(values)],
        'original_predictions_sha256':EXPECTED_PRED_SHA,
        'pair_count':len(attempts),
        'hit_counts':dict(raw_hit),
        'observed_counts':dict(raw_present),
        'measured_panel_equivalent_but_expanded_separator_original_float32':legacy_oracle_count,
        'measured_panel_equivalent_but_expanded_separator_source_decimal':exact_decimal_oracle_count,
        'measured_panel_equivalent_but_expanded_separator_float64':new_oracle_count,
        'method_hits_original_float32':dict(raw_hit),
        'method_hits_source_decimal':dict(exact_decimal_hit),
        'source_threshold_precision_discrepancies':boundary_differences,
        'distinct_query_orfs':len(query_counts),
        'duplicate_query_orfs_count':len(dup_queries),
        'duplicate_orf_sample':list(dup_queries.items())[:20],
        'cross_calibration_target_shared_orfs_count':len(cross_split_orfs),
        'cross_calibration_target_shared_orfs_example':cross_split_orfs[:20],
        'array_orf_metadata_confidence_fraction':conf,
        'array_orf_metadata_line':best+2 if conf>.9 else None,
        'array_orf_metadata_candidates':array_orf_summaries,
        'target_pairs_with_gene_represented_in_selected_array_columns':reverse_possible if arr_gene else None,
        'target_pairs_possible_reciprocal_proxy':reverse_pairs[:30],
        'source_has_pvalue_column':any(c.lower().replace('-','').startswith('pval') for c in hdr),
        'limitation':'A 1.96*sqrt(2)*RMSE point penalty is not a calibrated 95% lower confidence bound for pair differences',
        'meaning':'Difference of two epsilon scores is not necessarily significant genetic interaction (requires native p-values and error accounting)'
    }
    result=args.out/'source_audit.json'
    result.write_text(json.dumps(diagnostics,indent=2,sort_keys=True)+'\n')
    # 85MB input is public and by hash; keep compact derived receipts only.
    paths.unlink()
    if args.archive is None:archive.unlink()
    print('SOURCE_EXACT_INDEPENDENT_AUDIT='+json.dumps({k:v for k,v in diagnostics.items() if k not in ('array_orf_metadata_candidates','target_pairs_possible_reciprocal_proxy')},sort_keys=True),flush=True)
    print('BIOLOGY_V1A_SOURCE_AUDIT_PASS',flush=True)

if __name__=='__main__':main()