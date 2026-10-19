#!/usr/bin/env python3
"""Independent source-native evaluator: Python stdlib + Decimal; NEVER imports select.py.

Called only AFTER first runner step exits with persisted SHA256 sealed predictions.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,random,re,zipfile
from collections import Counter
from decimal import Decimal,InvalidOperation
from pathlib import Path

ARCHIVE_SHA='53c69b7dc6e54aeff54afddfa84a24741b9e09c2fdc6bfd9fcbf0b73939ec30f'
MEMBER_SUFFIX='/SGA_ExE_clustered.cdt'
METHODS=('contrast_mixture','knn_point','knn_uncertainty_ucb','ridge_point','global_variance','random')

def sha(b):return hashlib.sha256(b).hexdigest()
def dec(s):
 try:
  x=Decimal(s)
  return x if x.is_finite() else None
 except(InvalidOperation,TypeError):return None

def parse_source(archive):
 src=archive.read_bytes()
 assert sha(src)==ARCHIVE_SHA,'BAD_SOURCE_ARCHIVE'
 with zipfile.ZipFile(io.BytesIO(src)) as z:
  names=[n for n in z.namelist() if n.endswith(MEMBER_SUFFIX)]
  assert len(names)==1,'INVALID_SOURCE_MEMBER'
  b=z.read(names[0])
 matrix_hash=sha(b)
 reader=csv.reader(io.StringIO(b.decode('utf-8-sig'),newline=''),delimiter='\t')
 header=next(reader); metadata=[next(reader) for _ in range(5)]
 score_idx=[i for i,c in enumerate(header) if c.lower().startswith('tsa')]
 assert len(score_idx)==792,'SOURCE_SCHEMA_DRIFT'
 assert len([m for m in metadata if m[0]=='ORF'])==1
 m=[m for m in metadata if m[0]=='ORF'][0]
 cols=[m[i].strip().upper() for i in score_idx]
 row_genes=[];rows=[]
 for fields in reader:
  assert len(fields)==len(header),'SOURCE_RAGGED'
  row_genes.append(fields[header.index('ORF')].strip().upper())
  rows.append(fields)
 return matrix_hash,score_idx,cols,row_genes,rows

def independent_evaluation(archive,seal_path,out):
 before=seal_path.read_bytes(); predicted_hash=sha(before); seal=json.loads(before)
 assert seal['status']=='PREDICTIONS_SEALED_NOT_SCORED'
 assert seal['source_archive_sha256']==ARCHIVE_SHA
 assert len(seal['selected_known'])==8 and len(seal['selected_candidates'])==128
 assert tuple(seal['methods'])==METHODS
 assert seal['n_pairs']==len(seal['attempts'])
 mhash,indices,genes,query,source_rows=parse_source(archive)
 assert len(set(seal['calibration_query_gene_ids']) & set(seal['target_query_gene_ids']))==0,'TRAIN_TEST_GENE_LEAK'
 assert not set(seal['target_query_gene_ids']) & set(x['array_gene'] for x in seal['selected_known']+seal['selected_candidates']),'RECIPROCAL_TARGET_LEAK'
 assert len(set(x['array_gene'] for x in seal['selected_known']+seal['selected_candidates']))==136,'DUPLICATE_ARRAY_GENE'
 assert set(x['array_gene'] for x in seal['selected_known']+seal['selected_candidates'])<=set(seal['calibration_query_gene_ids']),'ARRAY_NOT_CALIBRATION_GENE'
 for c in seal['selected_known']+seal['selected_candidates']:
  assert genes[c['array_index']]==c['array_gene'],'WRONG_COLUMN_ORF'
 known=[x['array_index'] for x in seal['selected_known']]
 candidate=[x['array_index'] for x in seal['selected_candidates']]
 assert len(set(candidate))==128
 query_seen=[]; any_hits=0; records=[]; successes={m:0 for m in METHODS}; present={m:0 for m in METHODS}
 threshold=Decimal('0.16');eq=Decimal('0.08')
 for k,a in enumerate(seal['attempts']):
  assert a['index']==k
  ai,bi=a['query_row_a'],a['query_row_b']
  assert 0<=ai<len(source_rows) and 0<=bi<len(source_rows)
  assert query[ai]==a['gene_a'] and query[bi]==a['gene_b']
  assert a['gene_a']!=a['gene_b']
  assert a['gene_a'] in seal['target_query_gene_ids'] and a['gene_b'] in seal['target_query_gene_ids']
  query_seen.extend([a['gene_a'],a['gene_b']])
  def gap(idx):
   x=dec(source_rows[ai][indices[idx]])
   y=dec(source_rows[bi][indices[idx]])
   return None if x is None or y is None else abs(x-y)
  panel=[gap(j) for j in known]
  assert all(g is not None for g in panel),'KNOWN_PANEL_MISSING'
  assert max(panel)<=eq,'NOT_PANEL_EQUIVALENT'
  assert str(max(panel))==a['known_panel_gap_decimal'],'WRONG_PANEL_GAP'
  # Oracle is strictly a retrospective diagnostic; read only after sealed predictions.
  candidate_gaps=[gap(j) for j in candidate]
  positive=sum(g is not None and g>=threshold for g in candidate_gaps)
  any_hits+=int(positive>0)
  chosen={}
  for method in METHODS:
   c=a['choices'][method]
   assert c['array_index'] in candidate and genes[c['array_index']]==c['array_gene'],'UNDECLARED_METHOD_COLUMN'
   g=gap(c['array_index']); observed=g is not None; hit=observed and g>=threshold
   successes[method]+=int(hit);present[method]+=int(observed)
   chosen[method]={'array_gene':c['array_gene'],'array_index':c['array_index'],
                   'observed':observed,'hit':bool(hit),'actual_gap_decimal':str(g) if observed else None}
  records.append({'pair_index':k,'gene_a':a['gene_a'],'gene_b':a['gene_b'],
                  'available_candidates':sum(x is not None for x in candidate_gaps),
                  'retrospective_any_possible':bool(positive),'observations':chosen})
 assert len(query_seen)==len(set(query_seen)),'SAME_GENE_REUSED_ACROSS_PAIRS'
 assert len(records)>=15
 n=len(records); outcomes={m:[int(r['observations'][m]['hit']) for r in records] for m in METHODS}
 rng=random.Random(20261019+17); boots=[]
 diff=[a-b for a,b in zip(outcomes['contrast_mixture'],outcomes['knn_point'])]
 for _ in range(2000):
  boots.append(sum(diff[rng.randrange(n)] for __ in range(n))/n)
 boots.sort(); lower,upper=boots[50],boots[1950]
 advantage=sum(diff)/n
 result={'status':'REAL_EXE_RETROSPECTIVE_HOLDOUT_EVALUATED','source_member':seal['member'],
   'source_matrix_sha256':mhash,'archive_sha256':ARCHIVE_SHA,'sealed_predictions_sha256':predicted_hash,
   'no_train_test_gene_intersection':True,'no_target_gene_in_selected_arrays':True,
   'one_target_allele_per_gene_and_pair':True,'all_pairs':n,
   'method_results':{m:{'hits':successes[m],'all_attempt_rate':successes[m]/n,
                        'observed_count':present[m],'missing_count':n-present[m],
                        'observed_only_precision':successes[m]/present[m] if present[m] else None} for m in METHODS},
   'pairs_with_any_measured_separator':any_hits,
   'primary_exploration_minus_matched_knn_point':advantage,
   'paired_descriptive_bootstrap_95_interval':[lower,upper],
   'principal_comparison_status':'POSITIVE_BOUNDED' if lower>0 else 'NEGATIVE_BOUNDED' if upper<0 else 'NO_CONCLUSIVE_ADVANTAGE',
   'not_claimed':['novel biological law','measured p-values or significance','genuinely new wet lab perturbations',
                  'gene-level independence outside known ORF aliases','fully calibrated Bayesian probabilities',
                  'independent experimental replication','independent genotype beyond allele grouping'],
   'pair_results':records}
 out.mkdir(parents=True,exist_ok=True)
 p=out/'outcome_report.json';p.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
 print('SOURCE_NATIVE_DECIMAL_EXE_RESULT='+json.dumps({k:v for k,v in result.items() if k!='pair_results'},sort_keys=True),flush=True)
 print('EXE_GENE_DISJOINT_EVALUATION_PASS',flush=True)
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--sealed',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();independent_evaluation(a.archive,a.sealed,a.out)
if __name__=='__main__':main()