#!/usr/bin/env python3
import argparse, json, math, time
from pathlib import Path
from z3 import BitVec, BitVecVal, Extract, If, LShR, SolverFor, UGE, ULE, sat, unsat

DEFAULT_L = 2075 * (1 << 60)
DEFAULT_U = (1 << 72) - 1

def required_odds(H):
    req=[0]*(H+1); q=0; p3=1; p2=1
    for t in range(1,H+1):
        p2 <<= 1
        while p3 < p2:
            q += 1; p3 *= 3
        req[t]=q
    return req

def replay(n, limit):
    x=n; q=0; fc=None; fd=None
    for t in range(1,limit+1):
        if x&1:
            q += 1; x=(3*x+1)//2
        else:
            x//=2
        if fc is None and pow(3,q) < (1<<t): fc=t
        if fd is None and x<n: fd=t
        if fc is not None and fd is not None: break
    return {'first_contract':fc,'first_descent':fd,'stopped_at':t,'x':x,'q':q}

def cps(s,H):
    a=sorted({int(x) for x in s.split(',') if x.strip() and int(x)<=H})
    if H not in a:a.append(H)
    return a

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--lower',type=int,default=DEFAULT_L)
    ap.add_argument('--upper',type=int,default=DEFAULT_U)
    ap.add_argument('--shards',type=int,default=1)
    ap.add_argument('--shard-index',type=int,default=0)
    ap.add_argument('--max-horizon',type=int,default=1000)
    ap.add_argument('--checkpoints',default='500,700,800,900,1000')
    ap.add_argument('--timeout-ms',type=int,default=900000)
    ap.add_argument('--out',default='bv.json')
    A=ap.parse_args()
    total=A.upper-A.lower+1
    lo=A.lower + total*A.shard_index//A.shards
    hi=A.lower + total*(A.shard_index+1)//A.shards - 1
    if A.shard_index==A.shards-1: hi=A.upper
    H=A.max_horizon
    req=required_odds(H)
    checkpoints=cps(A.checkpoints,H); cp=set(checkpoints)
    seed_bits=max(1,A.upper.bit_length())
    W=seed_bits + math.ceil(H*math.log2(1.5)) + 2
    QW=(H+1).bit_length()+1
    print(f'BV_EXACT shard={A.shard_index}/{A.shards} lo={lo} hi={hi} H={H} W={W}')
    s=SolverFor('QF_BV'); s.set(timeout=A.timeout_ms)
    x=[BitVec('x_0',W)]
    q=[BitVec('q_0',QW)]
    s.add(UGE(x[0],BitVecVal(lo,W)), ULE(x[0],BitVecVal(hi,W)), q[0]==0)
    results=[]; start=time.time()
    for t in range(H):
        odd = Extract(0,0,x[t]) == BitVecVal(1,1)
        xn=BitVec(f'x_{t+1}',W); qn=BitVec(f'q_{t+1}',QW)
        odd_num = 3*x[t] + BitVecVal(1,W)
        s.add(xn == If(odd, LShR(odd_num,1), LShR(x[t],1)))
        s.add(qn == q[t] + If(odd,BitVecVal(1,QW),BitVecVal(0,QW)))
        s.add(UGE(qn,BitVecVal(req[t+1],QW)))
        x.append(xn); q.append(qn)
        h=t+1
        if h not in cp: continue
        c=time.time(); st=s.check(); sec=time.time()-c
        row={'horizon':h,'status':str(st),'seconds':sec}
        if st==sat:
            m=s.model(); n=m.eval(x[0]).as_long(); xx=m.eval(x[h]).as_long(); qq=m.eval(q[h]).as_long()
            rep=replay(n,H+100)
            row.update(witness=n,x_horizon=xx,q=qq,replay=rep)
            xr=n; qr=0
            for _ in range(h):
                if xr&1: qr+=1; xr=(3*xr+1)//2
                else: xr//=2
            assert xr==xx and qr==qq, (xr,xx,qr,qq)
            print(f'SAT h={h} n={n} q={qq} x={xx} sec={sec:.3f} replay={rep}')
        elif st==unsat:
            print(f'UNSAT h={h} sec={sec:.3f}')
            results.append(row); break
        else:
            row['reason_unknown']=s.reason_unknown(); print(f'UNKNOWN h={h} sec={sec:.3f} reason={row["reason_unknown"]}')
        results.append(row)
    summary={'kind':'exact_qf_bv_collatz_coefficient_persistence','shard':A.shard_index,'shards':A.shards,'lo':lo,'hi':hi,'H':H,'W':W,'results':results,'wall_seconds':time.time()-start}
    Path(A.out).write_text(json.dumps(summary,indent=2)+'\n')
    print('RESULT_JSON',json.dumps(summary,separators=(',',':')))

if __name__=='__main__':
    main()
