#!/usr/bin/env python3
"""Exact quantum-intervention and self-quotient finite laboratory.

Scope: 1-/2-qubit Clifford gate libraries and exact ideal projective readout.
Distinguishes: information impossible through existing interface vs constructible
from available controls, and bounded self-application of the predictive quotient.
No claim of new physics or unconstrained recursive self-improvement.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from itertools import product
import json
from pathlib import Path
import sys

import sympy as s

I = s.I
EYE = s.eye(2)
X = s.Matrix([[0, 1], [1, 0]])
Y = s.Matrix([[0, -I], [I, 0]])
Z = s.diag(1, -1)
H = s.Matrix([[1, 1], [1, -1]]) / s.sqrt(2)
S = s.diag(1, I)
SDG = s.diag(1, -I)
PAULI = {'I': EYE, 'X': X, 'Y': Y, 'Z': Z}


def krons(*matrices):
    result = s.Matrix([[1]])
    for matrix in matrices:
        result = s.kronecker_product(result, matrix)
    return result


def cnot(n: int, control: int, target: int) -> s.Matrix:
    dim = 1 << n
    result = s.zeros(dim)
    for col in range(dim):
        out = col
        if (col >> (n-1-control)) & 1:
            out ^= 1 << (n-1-target)
        result[out, col] = 1
    return result


def gates(n: int, include_h=True, include_entangling=True):
    assert n in (1, 2)
    result = {}
    for q in range(n):
        for name, op in [('H', H), ('S', S), ('Sdg', SDG)]:
            if name == 'H' and not include_h:
                continue
            result[f'{name}{q}'] = krons(*(op if j == q else EYE for j in range(n)))
    if n == 2 and include_entangling:
        result['CX01'] = cnot(2,0,1)
        result['CX10'] = cnot(2,1,0)
    for name,mat in result.items():
        assert s.simplify(mat.H*mat-s.eye(1<<n)) == s.zeros(1<<n),name
    return result


def pmat(label: str) -> s.Matrix:
    return krons(*(PAULI[ch] for ch in label))


def standard_paulis(n):
    return [''.join(p) for p in product('IXYZ', repeat=n) if any(x!='I' for x in p)]


def build_exact_conjugation_table(n, gate_set):
    """Derive finite gate action from exact matrices, not hardcoded Clifford rules."""
    labels=standard_paulis(n)
    matrices={label:pmat(label) for label in labels}
    table={}
    d=1<<n
    for gname,g in gate_set.items():
        transitions={}
        for label,p in matrices.items():
            transported=s.simplify(g.H*p*g)
            hits=[]
            for target,q in matrices.items():
                coeff=s.simplify(s.trace(q*transported)/d)
                if coeff!=0:
                    assert coeff in (-1,1), (gname,label,target,coeff)
                    hits.append((int(coeff),target))
            assert len(hits)==1,(gname,label,hits)
            sign,target=hits[0]
            assert s.simplify(transported-sign*matrices[target])==s.zeros(d)
            transitions[label]=(sign,target)
        table[gname]=transitions
    return table


def forward_step(effect,gate,table):
    sign, label=effect
    new_sign,new_label=table[gate][label]
    return (sign*new_sign,new_label)


def effect_for_program(program,n,gate_set):
    """Independent matrix oracle: apply gates in the listed temporal order."""
    u=s.eye(1<<n)
    for gate in program:
        u=gate_set[gate]*u
    readout=pmat('Z'+'I'*(n-1))
    return s.simplify(u.H*readout*u)


def algebraic_effect(effect):
    sign,label=effect
    return sign*pmat(label)


@dataclass
class Search:
    n: int
    gate_set: dict
    table: dict
    paths: dict
    expanded: int
    transitions: int
    max_depth: int


def quotient_search(n,gate_set):
    """BFS on exact *future-sufficient effects*, not syntax histories."""
    table=build_exact_conjugation_table(n,gate_set)
    initial=(1,'Z'+'I'*(n-1))
    paths={initial:()}
    queue=deque([initial])
    expanded=0
    transitions=0
    while queue:
        effect=queue.popleft()
        expanded+=1
        prog=paths[effect]
        for g in gate_set:
            # New gate occurs before existing program: E' = g^† E g.
            next_effect=forward_step(effect,g,table)
            transitions+=1
            if next_effect not in paths:
                paths[next_effect]=(g,)+prog
                queue.append(next_effect)
    # Independent exact circuit replay for every quotient representative.
    for effect,path in paths.items():
        dense=effect_for_program(path,n,gate_set)
        assert s.simplify(dense-algebraic_effect(effect))==s.zeros(1<<n), (effect,path)
    # Explicitly verify closure of the quotient under every permitted extension.
    assert all(forward_step(e,g,table) in paths for e in paths for g in gate_set)
    return Search(n,gate_set,table,paths,expanded,transitions,max(map(len,paths.values())))


def p0_state(n):
    v=s.zeros(1<<n,1)
    v[0]=1
    return v


def density(v):
    return s.simplify(v*v.H)


def trace_distance(a,b):
    diff=a-b
    assert s.simplify(s.trace(diff))==0
    eigen=diff.eigenvals()
    assert sum(m for m in eigen.values())==a.rows
    return s.simplify(sum(s.Abs(value)*mult for value,mult in eigen.items())/2)


def measurement_gap(effect,rho,sigma):
    matrix=algebraic_effect(effect)
    return s.simplify(s.Abs(s.trace(matrix*(rho-sigma))/2))


def optimal_effect(search,rho,sigma):
    triples=[]
    for effect,path in search.paths.items():
        gap=measurement_gap(effect,rho,sigma)
        triples.append((gap,len(path),str(path),effect,path))
    max_gap=max(t[0] for t in triples)
    winners=[t for t in triples if t[0]==max_gap]
    best=min(winners,key=lambda t:(t[1],t[2]))
    positive=[t for t in triples if t[0]!=0]
    shortest=min(positive,key=lambda t:(t[1],-float(t[0]),t[2])) if positive else None
    # Independently verify candidate against original matrices and source states.
    if max_gap!=0:
        path=best[4]
        actual_p=s.simplify((s.eye(1<<search.n)+effect_for_program(path,search.n,search.gate_set))/2)
        assert s.simplify(s.Abs(s.trace(actual_p*(rho-sigma)))-max_gap)==0
    return dict(max_gap=max_gap,max_path=best[4],max_effect=best[3],
                cheapest_gap=(shortest[0] if shortest else 0),
                cheapest_path=(shortest[4] if shortest else None),
                helstrom=trace_distance(rho,sigma))


def pure_q1(label):
    zero=s.Matrix([1,0]);one=s.Matrix([0,1])
    return {'0':zero,'1':one,'+':(zero+one)/s.sqrt(2),
            '-':(zero-one)/s.sqrt(2),
            '+i':(zero+I*one)/s.sqrt(2),
            '-i':(zero-I*one)/s.sqrt(2)}[label]


def mixed_pauli_pair(p_label):
    n=len(p_label); d=1<<n
    p=pmat(p_label)
    return ((s.eye(d)+p)/d,(s.eye(d)-p)/d)


def quantum_states():
    a=pure_q1('0'); b=pure_q1('1')
    bell_plus=(krons(a,a)+krons(b,b))/s.sqrt(2)
    bell_minus=(krons(a,a)-krons(b,b))/s.sqrt(2)
    return {
        'X single qubit':(1,density(pure_q1('+')),density(pure_q1('-'))),
        'Y single qubit':(1,density(pure_q1('+i')),density(pure_q1('-i'))),
        'Nonorthogonal |0> vs |+>':(1,density(pure_q1('0')),density(pure_q1('+'))),
        'Bell phase (+) vs (-)':(2,density(bell_plus),density(bell_minus)),
        # Heldouts were generated by state *operators*, not by predeclared circuits.
        'heldout XY':(2,*mixed_pauli_pair('XY')),
        'heldout YX':(2,*mixed_pauli_pair('YX')),
        'heldout ZY':(2,*mixed_pauli_pair('ZY')),
        'heldout YY':(2,*mixed_pauli_pair('YY')),
    }


def tomography_states(n):
    # A 4-state spanning preparation basis per qubit; tensor powers give d^2.
    choices=[density(pure_q1(k)) for k in ('0','1','+','+i')]
    result=[krons(*factors) for factors in product(choices,repeat=n)]
    d=1<<n
    matrix=s.Matrix([[state[i,j] for i in range(d) for j in range(d)] for state in result])
    assert matrix.rank()==d*d, ('tomography not informationally complete',n)
    return result


def verified_observation_signatures(search):
    """Prove exact tomography identifies every reachable effect without a Pauli label oracle."""
    states=tomography_states(search.n)
    signatures={}
    for effect in search.paths:
        E=(s.eye(1<<search.n)+algebraic_effect(effect))/2
        signature=tuple(s.simplify(s.trace(E*rho)) for rho in states)
        if signature in signatures:
            assert signatures[signature]==effect, ('observational quotient collision',effect)
        signatures[signature]=effect
    assert len(signatures)==len(search.paths)
    return signatures


def enumeration_equivalent(search,depth):
    """Independent program-language exhaustive enumeration up to bounded depth."""
    oracle=set()
    count=0
    for length in range(depth+1):
        for path in product(search.gate_set,repeat=length):
            effect=(1,'Z'+'I'*(search.n-1))
            # Temporal program p=(g1,..,gk), so pull back readout in reverse order.
            for g in reversed(path):
                effect=forward_step(effect,g,search.table)
            oracle.add(effect)
            count+=1
    minimal_bfs={effect for effect,path in search.paths.items() if len(path)<=depth}
    assert oracle==minimal_bfs,(len(oracle),len(minimal_bfs))
    return count,len(oracle)


def sign_table_mutation_kill(search):
    """Show independent dense-replay check detects deliberately corrupted certificate."""
    witness=next(((ef,path) for ef,path in search.paths.items() if len(path)>0), next(iter(search.paths.items())))
    ef,path=witness
    forged=(-ef[0],ef[1])
    assert s.simplify(effect_for_program(path,search.n,search.gate_set)-algebraic_effect(forged))!=s.zeros(1<<search.n)
    return True



def future_signature(search, rho):
    """Exact signatures of a prepared state against EVERY accessible effect."""
    d=1<<search.n
    return tuple(s.simplify(s.trace((s.eye(d)+algebraic_effect(e))*rho/2))
                 for e in search.paths)


def state_partition(search, candidates):
    """Group states only by physically accessible measurement predictions."""
    groups={}
    for label,rho in candidates.items():
        groups.setdefault(future_signature(search,rho), []).append(label)
    return tuple(sorted((tuple(sorted(v)) for v in groups.values())))


def changing_future_protection(searches):
    """Independent finite witnesses that expanding available operations refines states.

    The general impossibility of a deterministic old->new class reconstruction
    follows from the witnessed collisions of the older quotient.
    """
    one={k:density(pure_q1(k)) for k in ('0','1','+','-','+i','-i')}
    two_states=quantum_states()['Bell phase (+) vs (-)']
    two={'Bell+':two_states[1], 'Bell-':two_states[2]}
    trials=[('single_qubit_add_H',one,searches['single_no_H'],searches['single_full']),
            ('bell_pair_add_CNOT',two,searches['two_no_CNOT'],searches['two_full'])]
    results={}
    for label,states,old,new in trials:
        # Access increases: every older effective measurement remains available.
        assert set(old.paths).issubset(set(new.paths))
        old_p=state_partition(old,states)
        new_p=state_partition(new,states)
        old_index={name:i for i,group in enumerate(old_p) for name in group}
        new_index={name:i for i,group in enumerate(new_p) for name in group}
        # A fine class never joins two previously distinct old classes.
        assert all(len({old_index[name] for name in group})==1 for group in new_p)
        # A collapsed old class splits under the new admissible measurements.
        split={
            ' '.join(group):len({new_index[name] for name in group})
            for group in old_p
            if len({new_index[name] for name in group})>1
        }
        assert split,(label,old_p,new_p)
        k=max(split.values())
        # If only old classes survive, every member of a split group has the
        # same old data but a distinct required refined answer. No deterministic
        # right inverse of the quotient map can recover each member.
        assert k>=2
        bits=(k-1).bit_length()
        results[label]={
            'old_partitions':list(map(list,old_p)),
            'new_partitions':list(map(list,new_p)),
            'old_class_count':len(old_p),'new_class_count':len(new_p),
            'old_classes_that_split':split,
            'largest_split_factor':k,
            'extra_label_bits_or_fresh_evidence_necessary':bits,
            'fine_partition_refines_coarse':True,
            'cannot_recover_without_persisted_source_or_new_interaction':True,
            'reconstructable_if_exact_source_states_preserved':True,
        }
    assert results['single_qubit_add_H']['largest_split_factor']==4
    assert results['single_qubit_add_H']['extra_label_bits_or_fresh_evidence_necessary']==2
    assert results['bell_pair_add_CNOT']['largest_split_factor']==2
    assert results['bell_pair_add_CNOT']['extra_label_bits_or_fresh_evidence_necessary']==1
    return results


def fmt(obj):
    if isinstance(obj,s.Basic): return str(obj)
    if isinstance(obj,tuple): return list(obj)
    return obj


def main():
    searches={
        'single_full':quotient_search(1,gates(1)),
        'single_no_H':quotient_search(1,gates(1,include_h=False)),
        'two_full':quotient_search(2,gates(2)),
        'two_no_CNOT':quotient_search(2,gates(2,include_entangling=False)),
        'two_no_H':quotient_search(2,gates(2,include_h=False)),
    }
    results={'status':'PASS_EXACT_FINITE',
             'boundary':'1-2 ideal qubits; finite Clifford controls, ideal computational readout; exact SymPy algebra',
             'searches':{},'cases':{},'metalevel':{}}
    for k,q in searches.items():
        signatures=verified_observation_signatures(q)
        assert sign_table_mutation_kill(q)
        results['searches'][k]={'gates':list(q.gate_set),'effect_classes':len(q.paths),
                               'max_shortest_circuit_depth':q.max_depth,'expanded':q.expanded,
                               'transitions_checked':q.transitions,
                               'tomographic_probe_count':len(tomography_states(q.n)),
                               'unique_signatures':len(signatures),
                               'closed_under_all_admissible_gate_extensions':True,
                               'dense_matrix_certificate_replay':True,
                               'sign_mutation_killed':True}
        print('SEARCH',k,results['searches'][k],flush=True)
    controls={1:['single_full','single_no_H'],2:['two_full','two_no_CNOT','two_no_H']}
    for label,(n,rho,sigma) in quantum_states().items():
        case={}
        for key in controls[n]:
            result=optimal_effect(searches[key],rho,sigma)
            case[key]={k:fmt(v) for k,v in result.items()}
            case[key]['none_if_saturated']=bool(result['max_gap']==0)
            print('CASE',label,key,case[key],flush=True)
        results['cases'][label]=case
    assert results['cases']['X single qubit']['single_full']['max_gap']=='1'
    assert results['cases']['X single qubit']['single_no_H']['max_gap']=='0'
    assert results['cases']['Y single qubit']['single_full']['max_gap']=='1'
    assert results['cases']['Y single qubit']['single_no_H']['max_gap']=='0'
    assert results['cases']['Bell phase (+) vs (-)']['two_full']['max_gap']=='1'
    assert results['cases']['Bell phase (+) vs (-)']['two_no_CNOT']['max_gap']=='0'
    assert results['cases']['Bell phase (+) vs (-)']['two_no_H']['max_gap']=='0'
    assert results['cases']['Nonorthogonal |0> vs |+>']['single_full']['max_gap']=='1/2'
    assert results['cases']['Nonorthogonal |0> vs |+>']['single_full']['helstrom']=='sqrt(2)/2'
    for k in ('heldout XY','heldout YX','heldout ZY','heldout YY'):
        assert results['cases'][k]['two_full']['max_gap']=='1'
        assert results['cases'][k]['two_no_CNOT']['max_gap']=='0'
    for key,depth in [('single_full',7),('two_full',5),('two_no_CNOT',6)]:
        raw,unique=enumeration_equivalent(searches[key],depth)
        results['metalevel'][key]={'max_enumerated_length':depth,
                                   'syntactic_programs':raw,
                                   'operational_effect_classes_within_length':unique,
                                   'quotient_saturated_effect_classes':len(searches[key].paths),
                                   'oracle_equal_to_depth_bounded_quotient':True,
                                   'quotient_is_future_congruence':True,
                                   'matched_executable_ledger_cost_comparison':'NOT_RUN'}
        print('META',key,results['metalevel'][key],flush=True)
    results['future_expansion']=changing_future_protection(searches)
    for label,outcome in results['future_expansion'].items():
        print('REFINEMENT',label,outcome,flush=True)
    results['conclusions']={
        'WARRANTED':'Closed Clifford effect graph and measurement synthesis with exact independent dense verification; finite future-sufficient quotient of the search engine itself; exact restricted-access no-go witnesses; loss-of-information obstruction to lifting old predictive state classes after admissible interventions expand',
        'REJECTED':'Record-only postprocessing creates inaccessible quantum distinctions; Clifford-only realizes Helstrom optimum for every pair; removing entangling control still separates Bell phases',
        'UNKNOWN':'Global lossless representation for unanticipated future operations; autonomous synthesis of physically new primitive beyond allowed hardware, unrestricted self-improving search-rule invention, independent Stuttgart experimental prediction, speedup over equally cached certified ledger',
    }
    out=Path(__file__).with_name('results.json')
    out.write_text(json.dumps(results,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
    print('RESULT',str(out),flush=True)
    return 0


if __name__=='__main__':
    sys.exit(main())
