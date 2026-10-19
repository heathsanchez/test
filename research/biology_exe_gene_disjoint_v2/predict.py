#!/usr/bin/env python3
"""ExE prospective gene-disjoint blind *selector*. Never reads target x candidate outcomes.

All effect thresholds, grouping, models and controls frozen in protocol.md.
"""
from __future__ import annotations
import argparse, collections, csv, hashlib, io, json, re, shutil, urllib.request, zipfile
from decimal import Decimal
from pathlib import Path
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.neighbors import NearestNeighbors

SEED=20261019
SOURCE='https://thecellmap.org/costanzo2016/data_files/Raw%20genetic%20interaction%20datasets%3A%20Matrix%20format.zip'
ARCHIVE_SHA='53c69b7dc6e54aeff54afddfa84a24741b9e09c2fdc6bfd9fcbf0b73939ec30f'
MEMBER_SUFFIX='/SGA_ExE_clustered.cdt'
ORF=re.compile(r'^Y[A-P][LR][0-9]{3}[CW](?:-[A-Z])?$', re.IGNORECASE)
KNOWN=8; CANDIDATES=128; K=31; MAX_PAIRS=100; MIN_PAIRS=15
EQ=Decimal('0.08'); DISTINCT=Decimal('0.16')
METHODS=('contrast_mixture','knn_point','knn_uncertainty_ucb','ridge_point','global_variance','random')

def fail(msg): raise RuntimeError('UNKNOWN_FAIL_CLOSED: '+str(msg))
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(path,x):
 path.parent.mkdir(parents=True,exist_ok=True)
 raw=(json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
 path.write_bytes(raw)
 return hashlib.sha256(raw).hexdigest()
def get_archive(path):
 if not path.exists():
  path.parent.mkdir(parents=True,exist_ok=True)
  req=urllib.request.Request(SOURCE,headers={'User-Agent':'yeast-exe-gene-disjoint-prospective-v2/1.0'})
  with urllib.request.urlopen(req,timeout=180) as r,path.open('wb') as out:shutil.copyfileobj(r,out)
 d=digest(path)
 if d!=ARCHIVE_SHA:fail('original source identity '+d)
 with zipfile.ZipFile(path) as z:
  matches=[n for n in z.namelist() if n.endswith(MEMBER_SUFFIX)]
  if len(matches)!=1:fail('matrix name not unique '+str(matches))
 return matches[0]
def metadata(archive,member):
 with zipfile.ZipFile(archive) as z:
  with z.open(member) as f:
   lines=[f.readline().decode('utf-8-sig').rstrip('\r\n').split('\t') for _ in range(6)]
 hdr,meta=lines[0],lines[1:]
 if len(hdr)<100 or 'ORF' not in hdr:fail('invalid CDT header')
 score_idx=[i for i,c in enumerate(hdr) if c.lower().startswith('tsa')]
 if len(score_idx)<136:fail('not ExE TSA matrix: '+str(len(score_idx)))
 if any(len(x)!=len(hdr) for x in meta):fail('metadata width mismatch')
 orfmeta=[x for x in meta if x and x[0]=='ORF']
 if len(orfmeta)!=1:fail('no unique array ORF metadata')
 arrorf=[orfmeta[0][i].strip().upper() for i in score_idx]
 if sum(bool(ORF.fullmatch(v)) for v in arrorf)/len(arrorf)<.98:fail('unreliable array ORF identities')
 return hdr,score_idx,arrorf

def parse_rows(archive,member,orf_col):
 # ROW IDENTITIES ONLY; numeric ExE scores never converted/read in first pass.
 genes=[]
 with zipfile.ZipFile(archive) as z:
  with z.open(member) as f:
   reader=csv.reader(io.TextIOWrapper(f,'utf-8-sig',newline=''),delimiter='\t')
   for _ in range(6):next(reader)
   for row in reader:
    if len(row)<=orf_col:fail('ragged source row')
    genes.append(row[orf_col].strip().upper())
 return genes

def read_permitted_rows(archive,member,score_idx,cal_indices,target_indices,known_cols=None,allowed_cal_cols=None):
 # Caller may NEVER request target values unless known_cols is an explicitly
 # frozen eight-column panel. This function does not retain the other strings.
 cal_set=set(cal_indices);tar_set=set(target_indices);cal={}; target={};t_raw={}
 if known_cols is not None and len(known_cols)!=KNOWN:fail('unfrozen target panel')
 with zipfile.ZipFile(archive) as z:
  with z.open(member) as f:
   reader=csv.reader(io.TextIOWrapper(f,'utf-8-sig',newline=''),delimiter='\t')
   for _ in range(6):next(reader)
   for rid,row in enumerate(reader):
    if rid in cal_set:
     if allowed_cal_cols is None:fail('all-column calibration reads forbidden')
     vec=np.full(len(score_idx),np.nan,dtype=np.float64)
     # Even calibration rows may contain reciprocal readouts against held-out
     # target genes. NEVER numerically interpret those source cells.
     for i in allowed_cal_cols:
      raw=row[score_idx[i]]
      try:vec[i]=float(raw)
      except (ValueError,TypeError):pass
     cal[rid]=vec
    elif known_cols is not None and rid in tar_set:
     vals=[row[score_idx[i]] for i in known_cols]
     target[rid]=np.array([float(v) if v not in ('','NA','NaN','nan') else np.nan for v in vals],dtype=np.float64)
     t_raw[rid]=vals
 if set(cal)!=cal_set or (known_cols is not None and set(target)!=tar_set):fail('row mapping incomplete')
 return cal,target,t_raw

def knn_model(xcal,ycal,xt):
 neighbors=NearestNeighbors(n_neighbors=K,metric='euclidean').fit(xcal)
 dist,idx=neighbors.kneighbors(xt)
 weights=1/(dist+.05);weights=weights/weights.sum(axis=1,keepdims=True)
 ys=ycal[idx]
 present=np.isfinite(ys)
 raww=weights[:,:,None]*present
 sums=raww.sum(axis=1)
 means=np.divide(np.nansum(np.where(present,ys,0)*weights[:,:,None],axis=1),sums,out=np.full_like(sums,np.nan),where=sums>0)
 deviations=np.where(present,ys-means[:,None,:],0)
 var=np.divide(np.nansum(raww*deviations**2,axis=1),sums,out=np.full_like(sums,np.nan),where=sums>0)
 return means,np.maximum(var,0),ys,weights

def mix_pair_prob(ya,yb,wa,wb):
 # Pairwise empirical intervention contrast. No hidden future scores.
 finite_a=np.isfinite(ya);finite_b=np.isfinite(yb)
 valid=finite_a[:,None,:] & finite_b[None,:,:]
 sep=np.abs(np.where(finite_a,ya,0)[:,None,:]-np.where(finite_b,yb,0)[None,:,:]) >= float(DISTINCT)
 weights=wa[:,None,None]*wb[None,:,None]
 denom=np.sum(weights*valid,axis=(0,1))
 numerator=np.sum(weights*(valid & sep),axis=(0,1))
 return np.divide(numerator,denom,out=np.full_like(denom,np.nan),where=denom>0)

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--archive',type=Path,default=Path('data/yeast_exe_v2/source.zip'))
 parser.add_argument('--out',type=Path,default=Path('out/yeast_exe_v2'))
 args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
 member=get_archive(args.archive)
 hdr,score_cols,col_genes=metadata(args.archive,member)
 all_gene=parse_rows(args.archive,member,hdr.index('ORF'))
 valid={g for g in all_gene if ORF.fullmatch(g)}
 if len(valid)<300:fail('not enough query gene ids '+str(len(valid)))
 rng=np.random.default_rng(SEED)
 unique_genes=np.array(sorted(valid),dtype=object)
 perm=rng.permutation(len(unique_genes))
 split=int(len(perm)*.70)
 cal_genes=set(str(x) for x in unique_genes[perm[:split]])
 target_genes=set(str(x) for x in unique_genes[perm[split:]])
 assert not cal_genes & target_genes
 cal_rows=[i for i,g in enumerate(all_gene) if g in cal_genes]
 tar_rows=[i for i,g in enumerate(all_gene) if g in target_genes]
 if len(cal_rows)<100 or len(tar_rows)<40:fail('small row partitions')
 allowed_cal_cols=[j for j,g in enumerate(col_genes) if g in cal_genes]
 cal_values,_,_=read_permitted_rows(args.archive,member,score_cols,cal_rows,[],allowed_cal_cols=allowed_cal_cols)
 # Coverage over calibration genes only. Repeated query alleles don't leak into target.
 c=np.stack([cal_values[i] for i in cal_rows])
 cov=np.isfinite(c).mean(axis=0)
 representative={}
 for idx,g in enumerate(col_genes):
  if g not in cal_genes:continue
  if g not in representative or (cov[idx],-idx)>(cov[representative[g]],-representative[g]):representative[g]=idx
 rank=sorted((g for g,ix in representative.items() if cov[ix]>=.40),key=lambda g:(-cov[representative[g]],g))
 if len(rank)<KNOWN+CANDIDATES:fail('insufficient distinct accessible contexts '+str(len(rank)))
 pool=rank[:min(320,len(rank))]
 chosen=rng.permutation(len(pool))[:KNOWN+CANDIDATES]
 allcols=np.array([representative[pool[int(ix)]] for ix in chosen],dtype=int)
 known_cols=allcols[:KNOWN];candidate_cols=allcols[KNOWN:]
 if len(set(col_genes[x] for x in allcols))!=KNOWN+CANDIDATES:fail('array allele gene duplicate')
 if not set(col_genes[x] for x in allcols)<=cal_genes:fail('reciprocal target gene array leak')
 _,target_panel,target_raw=read_permitted_rows(args.archive,member,score_cols,[],tar_rows,known_cols)
 # One allele per gene, first qualifying native source row; never inspect target outcomes.
 def representatives(rows,panel):
  unique={}
  for i in rows:
   g=all_gene[i]
   if g not in unique and np.isfinite(panel[i]).all():unique[g]=i
  return list(unique.values())
 x_cal={i:cal_values[i][known_cols] for i in cal_rows}
 cal_reps=representatives(cal_rows,x_cal)
 tar_reps=representatives(tar_rows,target_panel)
 if len(cal_reps)<100 or len(tar_reps)<40:fail('insufficient complete 8-background profiles')
 Xcal=np.array([x_cal[i] for i in cal_reps]);Ycal=np.array([cal_values[i][candidate_cols] for i in cal_reps])
 Xtar=np.array([target_panel[i] for i in tar_reps])
 if not np.isfinite(Xcal).all() or not np.isfinite(Xtar).all():fail('incomplete known panel unexpectedly')
 if len(Xcal)<=K:fail('fewer calibration mutants than neighbors')
 means,var,neighbor_targets,neighbor_weights=knn_model(Xcal,Ycal,Xtar)
 ridge=np.full_like(means,np.nan)
 for ci in range(CANDIDATES):
  fin=np.isfinite(Ycal[:,ci])
  if fin.sum()>=100:
   ridge[:,ci]=Ridge(alpha=5.).fit(Xcal[fin],Ycal[fin,ci]).predict(Xtar)
 coverage=np.isfinite(Ycal).mean(axis=0)
 margvar=np.nanvar(Ycal,axis=0)
 order=rng.permutation(len(tar_reps))
 unused=set(int(x) for x in order)
 pairs=[]
 for a in order:
  a=int(a)
  if a not in unused:continue
  unused.remove(a)
  options=[]
  for b in sorted(unused):
   diffs=[abs(Decimal(target_raw[tar_reps[a]][n])-Decimal(target_raw[tar_reps[b]][n])) for n in range(KNOWN)]
   g=max(diffs)
   if g<=EQ:options.append((g,b))
  if not options:continue
  b=min(options,key=lambda x:(x[0],x[1]))[1]
  unused.remove(b); pairs.append((a,b))
  if len(pairs)>=MAX_PAIRS:break
 if len(pairs)<MIN_PAIRS:fail('insufficient panel-equivalent disjoint pairs '+str(len(pairs)))
 attempts=[]
 for ii,(a,b) in enumerate(pairs):
  point=np.abs(means[a]-means[b]);rgap=np.abs(ridge[a]-ridge[b])
  uncertainty=np.sqrt(var[a]+var[b]);ucb=point+1.96*uncertainty
  mixture=mix_pair_prob(neighbor_targets[a],neighbor_targets[b],neighbor_weights[a],neighbor_weights[b])
  scores={'contrast_mixture':mixture*coverage,'knn_point':point*coverage,
          'knn_uncertainty_ucb':ucb*coverage,'ridge_point':rgap*coverage,
          'global_variance':margvar*coverage}
  choices={}
  for method,v in scores.items():
   if not np.isfinite(v).any():fail('no finite score for '+method)
   j=int(np.nanargmax(v)); choices[method]={'array_index':int(candidate_cols[j]),'array_gene':col_genes[candidate_cols[j]],'predicted_rank_score':float(v[j])}
  j=int(rng.integers(CANDIDATES))
  choices['random']={'array_index':int(candidate_cols[j]),'array_gene':col_genes[candidate_cols[j]],'predicted_rank_score':None}
  panelgap=max(abs(Decimal(target_raw[tar_reps[a]][n])-Decimal(target_raw[tar_reps[b]][n])) for n in range(KNOWN))
  attempts.append({'index':ii,'query_row_a':int(tar_reps[a]),'query_row_b':int(tar_reps[b]),
                   'gene_a':all_gene[tar_reps[a]],'gene_b':all_gene[tar_reps[b]],
                   'known_panel_gap_decimal':str(panelgap),'choices':choices})
 result={'experiment':'gene-disjoint-yeast-exe-v2','source_archive_sha256':ARCHIVE_SHA,'member':member,
   'matrix_sha256':None, # evaluator independently fills it, no score needed for method selection
   'seed':SEED,'known':KNOWN,'candidates':CANDIDATES,'eq_decimal':str(EQ),'different_decimal':str(DISTINCT),
   'calibration_gene_count':len(cal_genes),'target_gene_count':len(target_genes),
   'calibration_query_gene_ids':sorted(cal_genes),'target_query_gene_ids':sorted(target_genes),
   'selected_known': [{'array_index':int(j),'array_gene':col_genes[j]} for j in known_cols],
   'selected_candidates':[{'array_index':int(j),'array_gene':col_genes[j]} for j in candidate_cols],
   'calibration_representative_rows':cal_reps,'target_representative_rows':tar_reps,
   'training_complete_8_context_genes':len(cal_reps),'target_complete_8_context_genes':len(tar_reps),
   'n_pairs':len(pairs),'calibration_candidate_coverage_min':float(min(coverage)),'methods':METHODS,
   'attempts':attempts,'status':'PREDICTIONS_SEALED_NOT_SCORED'}
 file=args.out/'sealed_predictions.json';sha=save(file,result)
 print('GENE_DISJOINT_EXE_PREOUTCOME_SHA256='+sha,flush=True)
 print('GENE_DISJOINT_EXE_PREOUTCOME_SHAPE='+json.dumps({k:v for k,v in result.items() if k in ('calibration_gene_count','target_gene_count','training_complete_8_context_genes','target_complete_8_context_genes','n_pairs','calibration_candidate_coverage_min','methods')},sort_keys=True),flush=True)

if __name__=='__main__':main()