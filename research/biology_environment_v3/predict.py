#!/usr/bin/env python3
"""Frozen exploration-first context discovery. ONLY reads allowlisted JSON, not raw workbook.
Methods human-authored, not an autonomously acquired observation language.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

SEED=20261020
K=31
METHODS=['contrast_exploration','knn_hit','knn_effect','logistic_hit','random_forest_hit','global_prevalence','random']


def save_json(p,d):
 b=(json.dumps(d,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 return hashlib.sha256(b).hexdigest()


def rank_contexts(allowed):
 train=allowed['training'];target=allowed['target'];contexts=allowed['candidate_conditions'];m=len(contexts)
 X=np.asarray([z['x'] for z in train],dtype=np.float64)
 Xt=np.asarray([z['x'] for z in target],dtype=np.float64)
 if not np.isfinite(X).all() or not np.isfinite(Xt).all():raise ValueError('Nonfinite source feature')
 Y=np.asarray([[np.nan if x is None else float(x) for x in z['y']] for z in train])
 E=np.asarray([[np.nan if x is None else float(x) for x in z['effect']] for z in train])
 if X.shape[1]!=5 or Y.shape[1]!=m or m!=10 or len(X)<1000 or len(Xt)<40:raise ValueError('Native shape not qualified')
 # Shared conditioning on exact same input information for every method.
 scaler=StandardScaler().fit(X)
 xx=scaler.transform(X);xt=scaler.transform(Xt)
 neighbors=NearestNeighbors(n_neighbors=K,metric='euclidean').fit(xx)
 ds,ind=neighbors.kneighbors(xt)
 w=1/(ds+0.05)
 succ=Y[ind];valid=np.isfinite(succ)
 wp=np.where(valid,w[:,:,None],0)
 den=wp.sum(axis=1)
 pknn=np.divide(np.nansum(succ*wp,axis=1),den,out=np.full((len(xt),m),np.nan),where=den>0)
 effects=E[ind];good=np.isfinite(effects);we=np.where(good,w[:,:,None],0)
 pe=np.divide(np.nansum(effects*we,axis=1),we.sum(axis=1),out=np.full((len(xt),m),np.nan),where=we.sum(axis=1)>0)
 prior=np.nanmean(Y,axis=0)
 if not np.isfinite(prior).all() or np.any(np.isfinite(Y).sum(axis=0)<100):raise ValueError('NOT_ENOUGH_TRAINING_LABELS_BY_CONTEXT')
 # Human-authored candidate exploration policy; NOT a confidence/warrant certificate.
 contrast=0.50*pknn + 0.25*np.sqrt(np.clip(pknn*(1-pknn),0,1)) + 0.25*prior[None,:]
 logp=np.full_like(pknn,np.nan)
 forest=np.full_like(pknn,np.nan)
 for i in range(m):
  finite=np.isfinite(Y[:,i]);yv=Y[finite,i].astype(int)
  if yv.min()==yv.max():
   logp[:,i]=forest[:,i]=float(yv[0]);continue
  lr=LogisticRegression(C=1.0,max_iter=500,random_state=SEED)
  lr.fit(xx[finite],yv)
  logp[:,i]=lr.predict_proba(xt)[:,1]
  rf=RandomForestClassifier(n_estimators=100,min_samples_leaf=12,max_features='sqrt',n_jobs=2,random_state=SEED+i)
  rf.fit(xx[finite],yv)
  forest[:,i]=rf.predict_proba(xt)[:,list(rf.classes_).index(1)]
 scores={'contrast_exploration':contrast,'knn_hit':pknn,'knn_effect':np.abs(pe),
         'logistic_hit':logp,'random_forest_hit':forest,
         'global_prevalence':np.tile(prior,(len(xt),1))}
 # Explicit missing rankings get minus infinity, no selective removal of target cases.
 for name,ss in scores.items():
  if ss.shape!=(len(xt),m):raise AssertionError('method rank shape')
  if np.any(np.isfinite(ss).sum(axis=1)==0):raise RuntimeError('METHOD_INAPPLICABLE '+name)
 chosen={name:np.nanargmax(ss,axis=1).tolist() for name,ss in scores.items()}
 chosen['random']=[int(np.random.default_rng(SEED+int(hashlib.sha256(z['id'].encode()).hexdigest()[:8],16)).integers(0,m)) for z in target]
 return [{'id':t['id'],'q':t['q'],'a':t['a'],
          'choices':{name:contexts[chosen[name][i]] for name in METHODS}}
         for i,t in enumerate(target)]


def main():
 p=argparse.ArgumentParser();p.add_argument('--allowed',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 args=p.parse_args();blob=args.allowed.read_bytes();a=json.loads(blob)
 if a['protocol']!='2021_environment_v3' or a['separation']['no_overlap']!=True:raise ValueError('invalid authority')
 if set(z['q'] for z in a['target']) & set(z['q'] for z in a['training']):raise ValueError('query gene leakage')
 if set(y for z in a['target'] for y in (z['q'],z['a'])) & set(y for z in a['training'] for y in (z['q'],z['a'])):
  raise ValueError('gene leakage')
 if any(set(z)-{'id','q','a','x'} for z in a['target']):raise ValueError('target source contains unauthorized outcomes')
 selections=rank_contexts(a)
 receipt={'protocol':'2021_environment_v3','allowed_sha256':hashlib.sha256(blob).hexdigest(),
 'source_sha256':a['source_sha256'],'known':a['known_conditions'],
 'candidates':a['candidate_conditions'],'methods':METHODS,'n_targets':len(selections),
 'selection':'single held-out environmental condition per target genotype',
 'decisions':selections,'no_outcomes_accessed':True}
 h=save_json(args.out/'sealed_predictions.json',receipt)
 print('ENVIRONMENT_2021_PREOUTCOME_SEAL_SHA256='+h,flush=True)
 print('ENVIRONMENT_2021_PREOUTCOME_SHAPE='+json.dumps({'targets':len(selections),'methods':METHODS,'source_digest':a['source_sha256']},sort_keys=True),flush=True)

if __name__=='__main__':main()
