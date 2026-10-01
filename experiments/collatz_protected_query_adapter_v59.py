"""Carry the protected source through lawful coalescent consequences.

This is an adapter qualification, not a new Collatz discovery. Its rejection
fixtures reuse ROS's known origin-loss obstruction. No new cylinder search.
"""
from dataclasses import dataclass, asdict
import hashlib
import json
import collatz_crystal_parameter_quotient_v25 as bank
import collatz_owner_renewal_affine_v0 as owner
import collatz_crystal_owner_cylinder_reclosure_v54 as symbolic
from collatz_live_splice_guard_v58 import compiled_exit

@dataclass(frozen=True)
class ProtectedQuery:
    source: int
    current: int
    source_steps: int=0
    owner_steps: int=0
    P: int=1
    A: int=1
    C: int=0

    def extend(self,b):
        assert b.source==self.current
        total=owner.AffineMap(self.P,self.A,self.C).compose(b.affine)
        left,right=self.source_steps,self.owner_steps
        if b.source_steps>=right:
            left+=b.source_steps-right
            right=b.owner_steps
        else:
            right+=b.owner_steps-b.source_steps
        out=ProtectedQuery(self.source,b.owner,left,right,total.P,total.A,total.C)
        assert total.apply_exact(self.source)==out.current
        assert owner.iterate(self.source,left)==owner.iterate(out.current,right)
        assert out.margin()==out.P*(out.source-out.current)
        return out

    def margin(self):
        return (self.P-self.A)*self.source-self.C

    def decision(self):
        if self.current>0 and self.margin()>0:
            return 'LOWER_SOURCE_EXIT'
        return 'UNKNOWN'

def main():
    n0=bank.N0+bank.NC*900;s=bank.NC*1024
    # Symbolic existing capability saturation, with no parameter splitting.
    a,c=n0,s;total=owner.AffineMap(1,1,0);rows=[]
    for i in range(4):
        z=symbolic.symbolic_block(a,c)
        assert not z['split']
        p,ps=z['owner0'],z['owner_slope']
        total=total.compose(z['affine'])
        assert total.apply_exact(n0)==p and total.A*s==total.P*ps
        assert p>n0 and ps>s
        rows.append(dict(block=i+1,local_contraction=p<a,
            original_source_margin0=str(total.P*(n0-p)),
            original_source_margin_slope=str(total.P*(s-ps))))
        a,c=p,ps
    assert rows[0]['local_contraction'] is False
    assert rows[3]['local_contraction'] is True
    seam=symbolic.symbolic_block(a,c)
    assert seam['split']

    # A survivor of the V58 guard (u=1). Only the compiled guard is avoided;
    # this is not claimed to be an all-future no-Exit orbit.
    n=n0+s
    assert compiled_exit(10,900,1) is None
    q=ProtectedQuery(n,n);execution=[]
    for i in range(5):
        b=owner.renewal_block(q.current)
        prior=q
        q=q.extend(b)
        local=b.owner<b.source
        execution.append(dict(block=i+1,local_descent=local,
            protected_decision=q.decision(),origin_margin=str(q.margin()),
            current=str(q.current),source_steps=q.source_steps,owner_steps=q.owner_steps))
        if i==0:
            assert q.current-q.source>prior.current-prior.source
        if i==3:
            assert local and q.decision()=='UNKNOWN'
        if i==4:
            assert q.decision()=='LOWER_SOURCE_EXIT'
    # Origin erasure incorrectly promotes the fourth local descent.
    assert execution[3]['local_descent'] and execution[3]['protected_decision']=='UNKNOWN'
    result=dict(schema='COLLATZ_PROTECTED_QUERY_ADAPTER_V59',
        objective='exclude infinite source-coherent no-original-source-exit itinerary',
        parent_guard='V58: t=900 modulo 16777216',
        main_residual='universal source-relative eventual progress OR warranted original-source exit',
        adaptation=[
            dict(candidate='avoiding compiled exit guards forces per-return origin debt decrease',
                status='REJECTED_ON_WEAKER_COMPILED_GUARD_AVOIDANCE_PREMISE',witness_block=1),
            dict(candidate='a later local contraction closes the original-source query',
                status='REJECTED_EXISTING_ROS_OBSTRUCTION_REUSED',witness_block=4),
            dict(candidate='compose admitted affine/coalescent edges; close only on positive fixed-origin margin',
                status='EXECUTED_SCOPED_ADAPTER_OF_EXISTING_WARRANT')],
        symbolic_four_block_reclosure=rows,
        execution=execution,
        ablation=dict(origin_retained='UNKNOWN at block 4',origin_erased='unsupported EXIT certificate at block 4'),
        surviving_obligation=dict(owner0=str(a),owner_slope=str(c),source0=str(n0),source_slope=str(s),
            next_event='first nonuniform valuation; no split performed',
            required_law='all source-admitted continuations eventually produce a positive composed origin margin, or another original-source exit',
            status='UNKNOWN'),
        next_experiment='test a proposed continuation law at this exact admitted seam; require source applicability and origin-margin consequence together',
        boundary='four uniform blocks checked by exact symbolic arithmetic; one actual source replayed; no all-future no-Exit witness or new universal closure',
        universal_progress='UNKNOWN',new_whole_live_closures=0,global_collatz='UNKNOWN')
    result['certificate_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__':main()
