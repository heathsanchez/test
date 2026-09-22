#!/usr/bin/env python3
"""Compatibility launcher for the post-radius-5 transport residual.

The exact-state radius<=5 connector family is certified exhausted on the current
transport-slack cohort.  Existing Actions runs still invoke this path, so this
launcher preserves that CLI while routing the newly justified next mechanism:
the six-context exact-depth-6 Proof Atlas fiber search.
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path


def snapshot_rows(path):
    snap=json.loads(Path(path).read_text()); data=snap.get('data',snap); out={}
    for row in data['items']:
        cid=row.get('problemId') or row.get('challengeId')
        if cid: out[str(cid)]=row
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--acc-root',required=True)
    ap.add_argument('--atlas',required=True)
    ap.add_argument('--snapshot-ac',required=True)
    ap.add_argument('--snapshot-stable',required=True)
    ap.add_argument('--target-ids-file',required=True)
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--connector-depth',type=int,default=5)
    ap.add_argument('--node-cap',type=int,default=250000)
    a=ap.parse_args()
    if a.connector_depth != 5:
        raise RuntimeError('compatibility launcher applies only after certified radius-5 exhaustion')

    ac=snapshot_rows(a.snapshot_ac); stable=snapshot_rows(a.snapshot_stable)
    ids_raw=json.loads(Path(a.target_ids_file).read_text())
    ids=[str(x.get('challenge_id')) if isinstance(x,dict) else str(x) for x in ids_raw]
    rows=[]
    for cid in ids:
        sid='sac-'+cid[3:]
        ar=ac.get(cid,{}); sr=stable.get(sid,{})
        ab=ar.get('currentBestLength'); sb=sr.get('currentBestLength')
        if ar.get('status')!='solved' or sr.get('status')!='solved' or not isinstance(ab,int) or not isinstance(sb,int):
            continue
        slack=sb-ab-2
        if slack<=0: continue
        rows.append({'challenge_id':cid,'stable_challenge_id':sid,'ac_best':ab,'stable_best':sb,
                     'transport_slack':slack,'source_bound_exclusive':max(ab,sb-2),
                     'ac_kTeams':ar.get('kTeams'),'stable_kTeams':sr.get('kTeams')})
    if not rows:
        raise RuntimeError('no positive transport-slack rows survived fresh freeze')

    with tempfile.TemporaryDirectory() as td:
        rows_path=Path(td)/'rows.json'; rows_path.write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
        cmd=[sys.executable,str(Path(__file__).with_name('transport_atlas_fiber_depth6_v1.py')),
             '--acc-root',a.acc_root,'--atlas',a.atlas,'--rows',str(rows_path),
             '--target-ids-file',a.target_ids_file,'--out-dir',a.out_dir,'--depth','6']
        print('TRANSPORT_PHASE_CHANGE',json.dumps({'from':'exact-radius<=5','to':'six-context-fiber-exact-depth6','targets':len(rows)},sort_keys=True))
        raise SystemExit(subprocess.call(cmd))


if __name__=='__main__':
    main()
