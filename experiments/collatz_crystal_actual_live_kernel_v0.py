#!/usr/bin/env python3
"""Actual-source protected-future corpus for the existing Crystal quotient compiler.

Discovery only.  Nodes are exact occurrences (source n, depth k); transitions are
actual shortcut steps. EXIT is sound terminal/direct descent relative to the fixed
source.  We deliberately do not label "eventual exit" from future knowledge.
"""
from collatz_crystal_future_quotient_v1 import compile_with_separators

def T(n):
    return n//2 if n%2==0 else (3*n+1)//2

def build(N=1<<12,K=128):
    rows=[]
    for n in range(1,N):
        y=n
        ids=[]
        for k in range(K+1):
            i=(n,k)
            exit_now=(y in (1,2)) or (0<y<n)
            rows.append({
                "id":i,
                "next":() if k==K else ((n,k+1),),
                "exit":exit_now,
                "source":n,
                "depth":k,
                "endpoint":y,
                "source_bits":n.bit_length(),
                "endpoint_mod3":y%3,
                "endpoint_parity":y%2,
            })
            ids.append(i)
            y=T(y)
    return rows

def main():
    rows=build()
    # First query: no presentation identity at all.  Candidate separators are
    # admitted only if they alter the stable protected-future partition.
    out=compile_with_separators(
        rows,
        base_fields=[],
        separator_bank=[
            "endpoint_parity",
            "endpoint_mod3",
            "source_bits",
        ],
    )
    print("ROWS",len(rows))
    print("STATUS",out["status"])
    print("ADMITTED",out["admitted_separators"])
    print("KERNEL_SIZE",len(out["kernel"]))
    print("OBSTRUCTION",out["obstruction"])

if __name__=="__main__":
    main()

# qualification trigger after workflow install
