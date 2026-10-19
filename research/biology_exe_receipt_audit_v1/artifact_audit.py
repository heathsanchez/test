#!/usr/bin/env python3
"""Independent read-only receipt audit; never imports selector, evaluator or uses raw ExE outcomes."""
from __future__ import annotations
import collections,decimal,hashlib,json,random,sys,zipfile
from pathlib import Path
ARCHIVE_SHA='ab9314cfa9d3f7b0906ce21b398c156e8feb8253db6a96f0be0a64e7e4bbf205'
PRE_SHA='d34095f4cf51a0c8b0088471e8b36bd7fdff1d42839795cfadc3792cab432f1b'
METHODS=('contrast_mixture','knn_point','knn_uncertainty_ucb','ridge_point','global_variance','random')

def audit(zip_path):
 raw=zip_path.read_bytes()
 assert hashlib.sha256(raw).hexdigest()==ARCHIVE_SHA,'Original GitHub artifact ZIP hash changed'
 with zipfile.ZipFile(zip_path) as z:
  assert sorted(z.namelist())==['outcome_report.json','sealed_predictions.json']
  seal_bytes=z.read('sealed_predictions.json')
  assert hashlib.sha256(seal_bytes).hexdigest()==PRE_SHA,'Original preoutcome seal changed'
  seal=json.loads(seal_bytes); report=json.loads(z.read('outcome_report.json'))
  assert report['sealed_predictions_sha256']==PRE_SHA
  assert report['archive_sha256']=='53c69b7dc6e54aeff54afddfa84a24741b9e09c2fdc6bfd9fcbf0b73939ec30f'
  assert report['source_matrix_sha256']=='6ac9ad373846836ae3ac9800ca3843358ffe98d442ae66c17cea2bd66fe98180'
  assert len(seal['attempts'])==len(report['pair_results'])==47
  train=set(seal['calibration_query_gene_ids']);target=set(seal['target_query_gene_ids']);assert not train & target
  selected=seal['selected_known']+seal['selected_candidates']
  assert len(selected)==136
  assert len(set(c['array_gene'] for c in selected))==136
  assert all(c['array_gene'] in train and c['array_gene'] not in target for c in selected)
  allowed=set(c['array_index'] for c in seal['selected_candidates'])
  seen=set();totals=collections.Counter();obs=collections.Counter();oracle=0
  pair_methods=[]
  for old,new in zip(seal['attempts'],report['pair_results']):
   assert old['index']==new['pair_index']
   assert old['gene_a']==new['gene_a'] and old['gene_b']==new['gene_b']
   assert old['gene_a'] != old['gene_b']
   for k in (old['gene_a'],old['gene_b']):
    assert k in target and k not in seen
    seen.add(k)
   assert decimal.Decimal(old['known_panel_gap_decimal'])<=decimal.Decimal('0.08')
   oracle+=int(new['retrospective_any_possible'])
   item={}
   for m in METHODS:
    choice=old['choices'][m];record=new['observations'][m]
    assert choice['array_index'] in allowed
    assert choice['array_gene']==record['array_gene']
    assert record['array_index']==choice['array_index']
    gap=decimal.Decimal(record['actual_gap_decimal']) if record['observed'] else None
    if gap is not None:
     assert gap.is_finite()
     assert bool(gap>=decimal.Decimal('0.16'))==record['hit']
    else:assert not record['hit']
    obs[m]+=int(record['observed']);totals[m]+=int(record['hit']);item[m]=bool(record['hit'])
   pair_methods.append(item)
  assert oracle==report['pairs_with_any_measured_separator']==46
  assert totals==collections.Counter({m:report['method_results'][m]['hits'] for m in METHODS})
  for m in METHODS:
   assert obs[m]==report['method_results'][m]['observed_count']
  def contingency(m1,m2):
   n11=sum(k[m1] and k[m2] for k in pair_methods)
   n10=sum(k[m1] and not k[m2] for k in pair_methods)
   n01=sum(k[m2] and not k[m1] for k in pair_methods)
   n00=len(pair_methods)-n11-n10-n01
   return dict(both=n11,only_first=n10,only_second=n01,neither=n00)
  chosen_agreement={m:sum(a['choices']['contrast_mixture']['array_index']==a['choices'][m]['array_index'] for a in seal['attempts']) for m in METHODS if m!='contrast_mixture'}
  sensitivity={}
  for t in ('0.12','0.16','0.20','0.24'):
   threshold=decimal.Decimal(t)
   sensitivity[t]={m:sum(decimal.Decimal(r['observations'][m]['actual_gap_decimal']) >=threshold for r in report['pair_results'] if r['observations'][m]['observed']) for m in METHODS}
  result={'audit_status':'PASS_SOURCE_IDENTITY_SEAL_AND_REPORT_COUNTERS','verified_zip_sha256':ARCHIVE_SHA,
          'verified_preoutcome_sha256':PRE_SHA,'target_genes_used':len(seen),
          'n_calibration_genes':len(train),'n_target_genes':len(target),
          'strict_no_shared_gene_or_array':True,'n_pairs':len(pair_methods),
          'real_counts':dict(totals),'present_counts':dict(obs),'oracle_pair_count':oracle,
          'pair_contingency_mixture_vs_knn_point':contingency('contrast_mixture','knn_point'),
          'pair_contingency_mixture_vs_global_variance':contingency('contrast_mixture','global_variance'),
          'method_same_selected_array_as_mixture':chosen_agreement,
          'posthoc_threshold_sensitivity_NOT_PRECOMMITTED':sensitivity,
          'limitations':['cannot independently reparse actual source raw bytes from this artifact alone',
                         'the experiment represents source-extracted genetic epsilon scores, not p-value-qualified individual biological interactions',
                         'pair bootstrap ignores shared calibration/model context and experimental batch dependence']}
  return result
if __name__=='__main__':
 r=audit(Path(sys.argv[1]))
 dest=Path(sys.argv[2]) if len(sys.argv)>2 else None
 if dest:
  dest.parent.mkdir(parents=True,exist_ok=True)
  dest.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
 print('EXE_INDEPENDENT_ARTIFACT_REPLAY='+json.dumps(r,sort_keys=True))