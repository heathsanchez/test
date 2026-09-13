from __future__ import annotations
from itertools import combinations, product
from typing import Any

from basis import World

History = tuple[int,...]

class Kernel:
    @staticmethod
    def words(alphabet_size:int,max_depth:int)->tuple[History,...]:
        out=[()]
        for depth in range(1,int(max_depth)+1):
            out.extend(product(range(int(alphabet_size)),repeat=depth))
        return tuple(out)

    @classmethod
    def authority(cls,world:World)->dict[str,Any] | None:
        if (
            not world.complete
            or world.alphabet_size<1
            or world.prefix_depth<1
            or world.max_future_depth<1
        ):
            return {"status":"UNKNOWN_AUTHORITY"}

        complete_depth=int(world.prefix_depth)+int(world.max_future_depth)
        expected=set(cls.words(world.alphabet_size,complete_depth))
        observed=set()
        for row in world.traces:
            h=tuple(int(x) for x in row.tokens)
            if row.consequence is None:
                return {"status":"UNKNOWN_AUTHORITY"}
            if any(not (0<=x<world.alphabet_size) for x in h):
                return {"status":"INVALID_ENCOUNTER_TOKEN"}
            if len(h)>complete_depth or h in observed:
                return {"status":"UNKNOWN_AUTHORITY"}
            observed.add(h)
        if observed!=expected or len(observed)!=len(world.traces):
            return {"status":"UNKNOWN_AUTHORITY"}
        return None

    @staticmethod
    def canonical_partition(signatures:list[tuple[int,...]])->tuple[int,...]:
        ids={}; out=[]
        for sig in signatures:
            if sig not in ids:
                ids[sig]=len(ids)
            out.append(ids[sig])
        return tuple(out)

    @classmethod
    def trace_map(cls,world:World)->dict[History,int]:
        return {
            tuple(int(x) for x in row.tokens):int(row.consequence)
            for row in world.traces
        }

    @classmethod
    def partition_at(
        cls,world:World,future_depth:int
    )->dict[str,Any]:
        table=cls.trace_map(world)
        prefixes=cls.words(world.alphabet_size,world.prefix_depth)
        suffixes=cls.words(world.alphabet_size,int(future_depth))
        signatures=[
            tuple(table[h+s] for s in suffixes)
            for h in prefixes
        ]
        labels=cls.canonical_partition(signatures)
        return {
            "prefixes":prefixes,
            "suffixes":suffixes,
            "signatures":tuple(signatures),
            "labels":labels,
            "state_count":len(set(labels)),
        }

    @staticmethod
    def same_equivalence(a:dict[str,Any],b:dict[str,Any])->bool:
        la=a["labels"]; lb=b["labels"]
        for i in range(len(la)):
            for j in range(i):
                if (la[i]==la[j])!=(lb[i]==lb[j]):
                    return False
        return True

    @classmethod
    def congruence(
        cls,world:World,part:dict[str,Any]
    )->dict[str,Any]:
        prefixes=part["prefixes"]
        labels=part["labels"]
        index={h:i for i,h in enumerate(prefixes)}
        states=sorted(set(labels))
        state_histories={
            c:[h for h,lab in zip(prefixes,labels) if lab==c]
            for c in states
        }

        transition_maps=[]
        first_obstruction=None
        coverage=True

        for token in range(world.alphabet_size):
            row=[]
            for state in states:
                eligible=[
                    h for h in state_histories[state]
                    if len(h)<world.prefix_depth
                ]
                targets={
                    labels[index[h+(token,)]]
                    for h in eligible
                }
                if not eligible:
                    coverage=False
                    row.append(None)
                    if first_obstruction is None:
                        first_obstruction={
                            "kind":"NO_TRANSITION_COVERAGE",
                            "state":state,
                            "token":token,
                        }
                elif len(targets)!=1:
                    row.append(None)
                    if first_obstruction is None:
                        by_target={}
                        for h in eligible:
                            t=labels[index[h+(token,)]]
                            by_target.setdefault(t,h)
                        hs=list(by_target.values())
                        first_obstruction={
                            "kind":"RIGHT_CONGRUENCE_OBSTRUCTION",
                            "token":token,
                            "history_a":list(hs[0]),
                            "history_b":list(hs[1]),
                        }
                else:
                    row.append(next(iter(targets)))
            transition_maps.append(tuple(row))

        lawful=(
            coverage
            and all(x is not None for row in transition_maps for x in row)
        )
        return {
            "lawful":lawful,
            "coverage":coverage,
            "transition_maps":tuple(transition_maps),
            "obstruction":first_obstruction,
        }

    @classmethod
    def refinement_witness(
        cls,a:dict[str,Any],b:dict[str,Any]
    )->dict[str,Any] | None:
        prefixes=a["prefixes"]
        la=a["labels"]; lb=b["labels"]
        for i,j in combinations(range(len(prefixes)),2):
            if la[i]==la[j] and lb[i]!=lb[j]:
                return {
                    "kind":"FUTURE_REFINEMENT_OBSTRUCTION",
                    "history_a":list(prefixes[i]),
                    "history_b":list(prefixes[j]),
                }
        return None

    @classmethod
    def minimality_witnesses(
        cls,part:dict[str,Any]
    )->tuple[dict[str,Any],...]:
        prefixes=part["prefixes"]
        suffixes=part["suffixes"]
        signatures=part["signatures"]
        labels=part["labels"]
        reps={}
        for i,(h,c) in enumerate(zip(prefixes,labels)):
            reps.setdefault(c,i)

        out=[]
        for a,b in combinations(sorted(reps),2):
            ia=reps[a]; ib=reps[b]
            for pos,suffix in enumerate(suffixes):
                if signatures[ia][pos]!=signatures[ib][pos]:
                    out.append({
                        "state_a":a,
                        "state_b":b,
                        "history_a":list(prefixes[ia]),
                        "history_b":list(prefixes[ib]),
                        "distinguishing_suffix":list(suffix),
                        "suffix_length":len(suffix),
                        "consequence_a":signatures[ia][pos],
                        "consequence_b":signatures[ib][pos],
                    })
                    break
        return tuple(out)

    @staticmethod
    def token_classes(
        transition_maps:tuple[tuple[int|None,...],...]
    )->tuple[tuple[int,...],...]:
        groups={}
        for token,row in enumerate(transition_maps):
            groups.setdefault(tuple(row),[]).append(token)
        return tuple(tuple(v) for _,v in sorted(
            groups.items(),key=lambda kv:kv[1][0]
        ))

    def synthesize(
        self,world:World,*,
        verification_enabled:bool=True,
        maximum_future_depth_override:int | None=None,
        maximum_state_count:int | None=None,
    )->dict[str,Any]:
        auth=self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {"status":"UNKNOWN_NO_VERIFIER","tested_future_depths":0}

        available=int(world.max_future_depth)
        if maximum_future_depth_override is not None:
            available=min(available,int(maximum_future_depth_override))
        if available<1:
            return {
                "status":"UNKNOWN_FUTURE_HORIZON_INSUFFICIENT",
                "tested_future_depths":0,
            }

        tested=[]
        winner=None

        for depth in range(available):
            current=self.partition_at(world,depth)
            next_part=self.partition_at(world,depth+1)
            cong=self.congruence(world,current)
            stable=self.same_equivalence(current,next_part)

            row={
                "future_depth":depth,
                "state_count":current["state_count"],
                "right_congruence":cong["lawful"],
                "stable_to_next_horizon":stable,
            }
            if not cong["lawful"]:
                row["obstruction"]=cong["obstruction"]
            elif not stable:
                row["obstruction"]=self.refinement_witness(current,next_part)
            tested.append(row)

            if cong["lawful"] and stable:
                winner=(depth,current,cong)
                break

        if winner is None:
            return {
                "status":"UNKNOWN_FUTURE_HORIZON_INSUFFICIENT",
                "tested_future_depths":len(tested),
                "tested":tested,
                "available_future_depth":available,
            }

        depth,part,cong=winner
        witnesses=self.minimality_witnesses(part)
        state_count=part["state_count"]
        required_witnesses=state_count*(state_count-1)//2

        if maximum_state_count is not None and state_count>int(maximum_state_count):
            return {
                "status":"CERTIFIED_STATE_BOUND_INADEQUACY",
                "derived_state_count":state_count,
                "maximum_state_count":int(maximum_state_count),
                "pairwise_distinguishing_witnesses":[*witnesses],
                "tested":tested,
            }

        token_classes=self.token_classes(cong["transition_maps"])
        prefixes=part["prefixes"]
        labels=part["labels"]
        reps={}
        for h,c in zip(prefixes,labels):
            if c not in reps or (len(h),h)<(len(reps[c]),reps[c]):
                reps[c]=h

        return {
            "status":"VERIFIED",
            "classification":"BOUNDED_BEHAVIORAL_FLOOR",
            "floor_future_depth":depth,
            "state_count":state_count,
            "token_class_count":len(token_classes),
            "token_classes":[list(c) for c in token_classes],
            "transition_maps":[list(row) for row in cong["transition_maps"]],
            "state_representatives":[list(reps[c]) for c in sorted(reps)],
            "prefixes":[list(h) for h in prefixes],
            "history_class_labels":[int(x) for x in labels],
            "pairwise_distinguishing_witnesses":[*witnesses],
            "pairwise_distinguishing_witness_count":len(witnesses),
            "pairwise_distinguishability_complete":len(witnesses)==required_witnesses,
            "maximum_minimal_distinguishing_depth":max(
                (w["suffix_length"] for w in witnesses),default=0
            ),
            "right_congruence":True,
            "stable_to_next_horizon":True,
            "tested_future_depths":len(tested),
            "tested":tested,
        }
