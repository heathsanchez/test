"""V177: independently replay all-offset true two-clock affine compiler.

Three independent base real meetings are drawn from earlier source-
qualified CIs. Entire unbounded families follow mathematically from
the V160 kernel theorem; this script merely checks source/clock
arithmetic and preserves G7 negative countercontrols, not QED.
"""
import json
import hashlib
from pathlib import Path

def T(n,c=1):
    assert n>0 and c>0 and c%2==1
    return n//2 if n%2==0 else (3*n+c)//2

def advance(n,t,c=1):
    a=0
    for _ in range(t):
        a+=n%2
        n=T(n,c)
    return n,a

def base(n,p,i,j,c=1):
    x,a=advance(n,i,c)
    y,b=advance(p,j,c)
    assert x==y,(n,p,i,j,c,x,y)
    L=n*0+(2**i)*(3**b)
    R=(2**j)*(3**a)
    for w in range(0,1000):
        nn=n+L*w
        pp=p+R*w
        assert advance(nn,i,c)[0]==advance(pp,j,c)[0],(c,n,p,i,j,w)
    for w in (1001,32001,1000000):
        assert advance(n+L*w,i,c)[0]==advance(p+R*w,j,c)[0]
    return {'c':c,'n':n,'p':p,'i':i,'j':j,'endpoint':x,
            'odd_count_n':a,'odd_count_p':b,
            'n_source_slope':L,'p_source_slope':R,
            'direct_source_cap_for_all_w_ge_p_plus_one':L>R,
            'lift_zero_is_original_meeting':True}

def main():
    out=[
        base(23,3,7,1),
        base(21,3,3,2),
        base(9,7,6,4),
        base(14,7,1,0,c=7),
    ]
    assert (out[0]['n_source_slope'],out[0]['p_source_slope'])==(384,54)
    assert (out[1]['n_source_slope'],out[1]['p_source_slope'])==(72,12)
    assert (out[2]['n_source_slope'],out[2]['p_source_slope'])==(1728,1296)
    for w in (0,1,2,10,100000):
        assert advance(23+384*w,7)[0]==advance(3+54*w,1)[0]
        assert 3+54*w<23+384*w
    assert advance(5,1,7)[0]==11
    assert advance(11,1,7)[0]==20
    assert advance(20,1,7)[0]==10
    assert advance(10,1,7)[0]==5
    assert advance(7,1,7)[0]==14 and advance(14,1,7)[0]==7
    print(json.dumps({
      'schema':'COLLATZ_V177_ALL_OFFSET_TWO_CLOCK_CERTIFICATE_COMPILER',
      'bases':out,
      'each_base_tested_offsets':1003,
      'real_source_cap_23_3_verified':True,
      'generic_G7_affine_compiler_still_allows_two_real_positive_future_classes':True,
      'new_terminal_class_overlap_proved':False,
      'all_scale_certified_population_contraction_proved':False,
      'global_collatz':'UNKNOWN','qed':False
    },indent=2,sort_keys=True))

if __name__=='__main__':main()
