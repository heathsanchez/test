#!/usr/bin/env python3
"""Synthetic precommit gate for gene-level source isolation and readout scoring."""
from __future__ import annotations
import hashlib,importlib.util,json,random,sys,tempfile,zipfile
from pathlib import Path

def import_script(path,name):
 spec=importlib.util.spec_from_file_location(name,str(path))
 m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def run():
 import numpy as np
 p=Path(__file__).resolve().parent
 s=import_script(p/'select.py','sample_selector')
 e=import_script(p/'evaluate.py','sample_evaluator')
 with tempfile.TemporaryDirectory() as dir:
  root=Path(dir);zippath=root/'sample.zip';out=root/'out'
  N=600;M=792
  rng=np.random.default_rng(31)
  genes=[f'YAL{i+1:03d}W' for i in range(N)]
  background=[f'YAL{i+1:03d}W' for i in range(M)]
  original_rows=[]
  header=['GID','Strain','ORF','Name','Label','GWEIGHT']+[f'tsa{i+1000}' for i in range(M)]
  meta=[['AID','','','','','']+[f'ARRY{i+1}X' for i in range(M)],
        ['ORF','','','','','']+background,
        ['Name','','','','','']+['' for _ in range(M)],
        ['Label','','','','','']+[f'ts{i}' for i in range(M)],
        ['EWEIGHT','','','','','']+['1' for _ in range(M)]]
  # Early panel and candidate targets are independent. Missing subset of scores.
  for i,gene in enumerate(genes):
   vals=np.round(rng.normal(0,.025,M),3)
   # Realistic source scores with rare strong context-specific interactions.
   vals[rng.choice(M,size=20,replace=False)]+=rng.choice([-.24,.24],size=20)
   vec=[f'{x:.3f}' for x in vals]
   # Introduce 3% of missingness; test handling without ever reading target candidates in stage 1.
   for j in rng.choice(M,size=23,replace=False):vec[int(j)]=''
   original_rows.append([str(i),'',gene,gene,gene.lower(),'1']+vec)
  txt='\n'.join('\t'.join(line) for line in [header,*meta,*original_rows])+'\n'
  with zipfile.ZipFile(zippath,'w',zipfile.ZIP_DEFLATED) as z:
   z.writestr('Data File S2. Raw genetic interaction datasets: Matrix format/SGA_ExE_clustered.cdt',txt)
  artificial_sha=hashlib.sha256(zippath.read_bytes()).hexdigest()
  s.ARCHIVE_SHA=artificial_sha;e.ARCHIVE_SHA=artificial_sha
  member=s.get_archive(zippath);hdr,idx,arr=s.metadata(zippath,member)
  assert len(idx)==M and len(arr)==M
  prevargv=sys.argv
  try:
   sys.argv=['select.py','--archive',str(zippath),'--out',str(out)]
   s.main()
  finally:sys.argv=prevargv
  seal=json.loads((out/'sealed_predictions.json').read_text())
  assert not set(seal['calibration_query_gene_ids']) & set(seal['target_query_gene_ids'])
  assert all(c['array_gene'] in seal['calibration_query_gene_ids'] for c in seal['selected_candidates'])
  result=e.independent_evaluation(zippath,out/'sealed_predictions.json',out)
  assert result['all_pairs']>=15
  assert result['no_train_test_gene_intersection']
  assert len(result['method_results'])==6
  assert all(v['hits']<=v['observed_count']<=result['all_pairs'] for v in result['method_results'].values())
  # Source-intervention ablation: replace every withheld target candidate cell
  # and every reciprocal calibration->target array cell with an invalid token.
  # The selection MUST be unchanged because neither class of cell is permitted.
  known_idxs=set(c['array_index'] for c in seal['selected_known'])
  target_genes=set(seal['target_query_gene_ids'])
  ablated=[]
  for row in original_rows:
   gene=row[2]
   v=row.copy()
   for j,array_gene in enumerate(background):
    if (gene in target_genes and j not in known_idxs) or (gene not in target_genes and array_gene in target_genes):
     v[j+6]='UNOPENED'
   ablated.append(v)
  altered=root/'no-leak-input.zip'
  txt2='\n'.join('\t'.join(line) for line in [header,*meta,*ablated])+'\n'
  with zipfile.ZipFile(altered,'w',zipfile.ZIP_DEFLATED) as z:
   z.writestr('Data File S2. Raw genetic interaction datasets: Matrix format/SGA_ExE_clustered.cdt',txt2)
  s.ARCHIVE_SHA=hashlib.sha256(altered.read_bytes()).hexdigest()
  prevargv=sys.argv
  try:
   sys.argv=['select.py','--archive',str(altered),'--out',str(root/'ablated_out')]
   s.main()
  finally:sys.argv=prevargv
  ablate_seal=json.loads((root/'ablated_out'/'sealed_predictions.json').read_text())
  for field in ('source_archive_sha256',):
   seal.pop(field);ablate_seal.pop(field)
  assert seal==ablate_seal,'LEAKAGE_ABLATION_CHANGED_SELECTION'
  print('SYNTHETIC_TARGET_AND_RECIPROCAL_WITHDRAWAL_INVARIANT_PASS',flush=True)
  print('SYNTHETIC_GENE_DISJOINT_SELECTOR_EVALUATOR_PASS',flush=True)

if __name__=='__main__':run()