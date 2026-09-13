#!/usr/bin/env python3
"""Frozen V31 Bell-local obstruction + finite quantum replay kernel."""
from __future__ import annotations

import itertools
from typing import Any, Dict, Tuple

from basis import (
    BipartiteExperiment,
    HALF,
    ONE,
    Q2,
    ZERO,
    born_table,
    candidate_states,
    correlators,
    local_marginal_signature,
    product_of_marginals,
    schmidt_rank,
    state_support,
    table_equal,
    valid_probability_table,
)


class Kernel:
    @staticmethod
    def authority(exp:BipartiteExperiment)->Dict[str,Any] | None:
        if not exp.complete:
            return {"status":"UNKNOWN_AUTHORITY","reason":"probability authority incomplete"}
        if not valid_probability_table(exp.probabilities):
            return {"status":"INVALID_PROBABILITY_TABLE"}
        return None

    @staticmethod
    def no_signalling(exp:BipartiteExperiment)->bool:
        t=exp.probabilities
        for x in range(2):
            for ai in range(2):
                left=t[x][0][ai][0]+t[x][0][ai][1]
                right=t[x][1][ai][0]+t[x][1][ai][1]
                if left!=right:return False
        for y in range(2):
            for bi in range(2):
                left=t[0][y][0][bi]+t[0][y][1][bi]
                right=t[1][y][0][bi]+t[1][y][1][bi]
                if left!=right:return False
        return True

    @staticmethod
    def chsh_certificate(table)->Dict[str,Any]:
        e=correlators(table)
        vals=(e[0][0],e[0][1],e[1][0],e[1][1])
        rows=[]
        best=None
        for signs in itertools.product((-1,1),repeat=4):
            prod=1
            for s in signs:prod*=s
            if prod!=-1:continue
            raw=ZERO
            for s,v in zip(signs,vals):raw=raw+Q2.of(s)*v
            mag=raw.abs()
            rows.append({
                "signs":list(signs),
                "value":raw.data(),
                "abs_value":mag.data(),
                "abs_approx":mag.approx(),
            })
            if best is None or mag>best[0]:
                best=(mag,signs,raw)
        assert best is not None
        return {
            "correlators":[[v.data() for v in row] for row in e],
            "max_abs":best[0].data(),
            "max_abs_approx":best[0].approx(),
            "max_signs":list(best[1]),
            "max_signed_value":best[2].data(),
            "violates_local_bound":best[0]>Q2.of(2),
            "local_bound":Q2.of(2).data(),
            "forms":rows,
            "_max":best[0],
        }

    def search_quantum(self,exp:BipartiteExperiment)->Dict[str,Any]:
        auth=self.authority(exp)
        if auth:return auth

        observed=exp.probabilities
        observed_local=local_marginal_signature(observed)
        all_states=candidate_states()

        local_matches=[]
        full_matches=[]
        rows=[]

        for v in all_states:
            table=born_table(v,exp.a_observables,exp.b_observables)
            local_ok=local_marginal_signature(table)==observed_local
            full_ok=table_equal(table,observed)
            row={
                "state":list(v),
                "schmidt_rank":schmidt_rank(v),
                "support":state_support(v),
                "local_match":local_ok,
                "full_match":full_ok,
            }
            rows.append(row)
            if local_ok:local_matches.append(v)
            if full_ok:full_matches.append(v)

        full_matches.sort(key=lambda v:(schmidt_rank(v),state_support(v),v))
        min_rank=min((schmidt_rank(v) for v in full_matches),default=None)
        min_support=min((state_support(v) for v in full_matches if schmidt_rank(v)==min_rank),default=None) if min_rank is not None else None
        selected=next((v for v in full_matches if schmidt_rank(v)==min_rank and state_support(v)==min_support),None)

        return {
            "status":"VERIFIED" if full_matches else "NO_EXACT_QUANTUM_REPLAY_IN_FROZEN_LANGUAGE",
            "candidate_count":len(all_states),
            "local_match_count":len(local_matches),
            "full_match_count":len(full_matches),
            "rank1_full_match_count":sum(1 for v in full_matches if schmidt_rank(v)==1),
            "rank2_full_match_count":sum(1 for v in full_matches if schmidt_rank(v)==2),
            "minimum_schmidt_rank":min_rank,
            "minimum_support_at_min_rank":min_support,
            "selected_state":list(selected) if selected is not None else None,
            "local_matches":[list(v) for v in local_matches],
            "full_matches":[list(v) for v in full_matches],
            "candidate_rows":rows,
            "_local_matches":tuple(local_matches),
            "_full_matches":tuple(full_matches),
            "_selected":selected,
        }

    def analyze(self,exp:BipartiteExperiment)->Dict[str,Any]:
        auth=self.authority(exp)
        if auth:return auth

        chsh=self.chsh_certificate(exp.probabilities)
        search=self.search_quantum(exp)
        local_sig=local_marginal_signature(exp.probabilities)
        product_table=product_of_marginals(exp.probabilities)
        product_chsh=self.chsh_certificate(product_table)

        uniform_local=all(
            tuple(item[2])==(HALF,HALF)
            for item in local_sig
        )

        wrong_same_local=None
        if search.get("status")=="VERIFIED":
            full=set(search["_full_matches"])
            for v in search["_local_matches"]:
                if v not in full:
                    wrong_same_local=v
                    break

        return {
            "status":"VERIFIED" if search.get("status")=="VERIFIED" else search.get("status"),
            "no_signalling":self.no_signalling(exp),
            "valid_probabilities":valid_probability_table(exp.probabilities),
            "uniform_local_marginals":uniform_local,
            "local_signature":[
                [side,idx,[p.data() for p in probs]]
                for side,idx,probs in local_sig
            ],
            "chsh":{k:v for k,v in chsh.items() if not k.startswith("_")},
            "product_marginal_chsh":{k:v for k,v in product_chsh.items() if not k.startswith("_")},
            "search":{k:v for k,v in search.items() if not k.startswith("_")},
            "wrong_same_local_candidate":list(wrong_same_local) if wrong_same_local is not None else None,
            "_search":search,
            "_wrong":wrong_same_local,
        }

    @staticmethod
    def replay_state(exp:BipartiteExperiment,state)->bool:
        if state is None:return False
        return born_table(tuple(state),exp.a_observables,exp.b_observables)==exp.probabilities
