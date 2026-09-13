from __future__ import annotations
from itertools import combinations, product
from math import prod
from typing import Any

from basis import World

History = tuple[int,...]
Support = tuple[int,...]

class Kernel:
    MAX_EXACT_COMPLETIONS=65536

    @staticmethod
    def words(alphabet_size:int,max_depth:int)->tuple[History,...]:
        out=[()]
        for depth in range(1,int(max_depth)+1):
            out.extend(product(range(int(alphabet_size)),repeat=depth))
        return tuple(out)

    @classmethod
    def authority(cls,world:World)->dict[str,Any] | None:
        if (
            not world.packet_complete
            or world.alphabet_size<1
            or world.consequence_alphabet_size<1
            or world.prefix_depth<1
            or world.max_future_depth<1
        ):
            return {"status":"UNKNOWN_AUTHORITY"}

        total_depth=int(world.prefix_depth)+int(world.max_future_depth)
        universe=set(cls.words(world.alphabet_size,total_depth))

        closed=[tuple(int(x) for x in h) for h in world.closed_histories]
        if len(set(closed))!=len(closed) or any(h not in universe for h in closed):
            return {"status":"UNKNOWN_AUTHORITY"}

        seen_by_history={}
        for row in world.samples:
            h=tuple(int(x) for x in row.tokens)
            y=int(row.consequence)
            if h not in universe:
                return {"status":"INVALID_ENCOUNTER_HISTORY"}
            if not (0<=y<world.consequence_alphabet_size):
                return {"status":"INVALID_CONSEQUENCE_TOKEN"}
            seen_by_history.setdefault(h,set()).add(y)

        for h in closed:
            if not seen_by_history.get(h):
                return {"status":"INVALID_EMPTY_CLOSED_SUPPORT"}

        return None

    @classmethod
    def observed_supports(cls,world:World)->dict[History,Support]:
        total_depth=int(world.prefix_depth)+int(world.max_future_depth)
        out={h:() for h in cls.words(world.alphabet_size,total_depth)}
        tmp={h:set() for h in out}
        for row in world.samples:
            tmp[tuple(int(x) for x in row.tokens)].add(int(row.consequence))
        return {h:tuple(sorted(v)) for h,v in tmp.items()}

    @staticmethod
    def all_nonempty_subsets(n:int)->tuple[Support,...]:
        values=range(int(n))
        out=[]
        for r in range(1,int(n)+1):
            out.extend(tuple(c) for c in combinations(values,r))
        return tuple(out)

    @classmethod
    def support_options(
        cls,world:World,observed:dict[History,Support]
    )->dict[History,tuple[Support,...]]:
        closed=set(tuple(int(x) for x in h) for h in world.closed_histories)
        all_supports=cls.all_nonempty_subsets(world.consequence_alphabet_size)
        out={}
        for h,seen in observed.items():
            seen_set=set(seen)
            if h in closed:
                out[h]=(seen,)
            else:
                opts=tuple(
                    s for s in all_supports
                    if seen_set.issubset(set(s))
                )
                out[h]=opts
        return out

    @staticmethod
    def relation_kind(table:dict[History,Support])->str:
        if all(len(s)==1 for s in table.values()):
            return "DETERMINISTIC_SUPPORT"
        return "BRANCHING_SUPPORT"

    @staticmethod
    def canonical_partition(signatures:list[tuple[Support,...]])->tuple[int,...]:
        ids={}; out=[]
        for sig in signatures:
            if sig not in ids:
                ids[sig]=len(ids)
            out.append(ids[sig])
        return tuple(out)

    @classmethod
    def partition_at(
        cls,world:World,table:dict[History,Support],future_depth:int
    )->dict[str,Any]:
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
        maps=[]
        obstruction=None
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
                if not eligible or len(targets)!=1:
                    row.append(None)
                    if obstruction is None:
                        obstruction={
                            "kind":"RIGHT_CONGRUENCE_OBSTRUCTION",
                            "state":state,
                            "token":token,
                        }
                else:
                    row.append(next(iter(targets)))
            maps.append(tuple(row))
        lawful=all(x is not None for row in maps for x in row)
        return {
            "lawful":lawful,
            "transition_maps":tuple(maps),
            "obstruction":obstruction,
        }

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

    @classmethod
    def floor_from_table(
        cls,world:World,table:dict[History,Support]
    )->dict[str,Any]:
        available=int(world.max_future_depth)
        tested=[]
        for depth in range(available):
            current=cls.partition_at(world,table,depth)
            next_part=cls.partition_at(world,table,depth+1)
            cong=cls.congruence(world,current)
            stable=cls.same_equivalence(current,next_part)
            tested.append({
                "future_depth":depth,
                "state_count":current["state_count"],
                "right_congruence":cong["lawful"],
                "stable_to_next_horizon":stable,
            })
            if cong["lawful"] and stable:
                return {
                    "status":"FLOOR",
                    "floor_future_depth":depth,
                    "state_count":current["state_count"],
                    "history_class_labels":current["labels"],
                    "transition_maps":cong["transition_maps"],
                    "token_classes":cls.token_classes(cong["transition_maps"]),
                    "law_kind":cls.relation_kind(table),
                    "tested":tuple(tested),
                }
        return {
            "status":"NO_FLOOR_WITHIN_HORIZON",
            "law_kind":cls.relation_kind(table),
            "tested":tuple(tested),
        }

    @staticmethod
    def fingerprint(floor:dict[str,Any])->tuple:
        if floor["status"]!="FLOOR":
            return (
                floor["status"],
                floor["law_kind"],
            )
        return (
            "FLOOR",
            floor["floor_future_depth"],
            floor["state_count"],
            tuple(floor["history_class_labels"]),
            tuple(tuple(x for x in row) for row in floor["transition_maps"]),
            tuple(tuple(x for x in c) for c in floor["token_classes"]),
        )

    @classmethod
    def extreme_completion(
        cls,world:World,options:dict[History,tuple[Support,...]],mode:str
    )->dict[History,Support]:
        table={}
        for h,opts in options.items():
            if mode=="minimal":
                table[h]=min(opts,key=lambda s:(len(s),s))
            elif mode=="maximal":
                table[h]=max(opts,key=lambda s:(len(s),s))
            else:
                raise ValueError(mode)
        return table

    @staticmethod
    def completion_witness(
        table:dict[History,Support],floor:dict[str,Any]
    )->dict[str,Any]:
        return {
            "law_kind":floor["law_kind"],
            "floor_status":floor["status"],
            "floor_future_depth":floor.get("floor_future_depth"),
            "state_count":floor.get("state_count"),
            "token_classes":[list(c) for c in floor.get("token_classes",())],
            "support_table":{
                ",".join(map(str,h)):list(s)
                for h,s in table.items()
            },
        }

    @classmethod
    def exact_completions(
        cls,options:dict[History,tuple[Support,...]]
    ):
        histories=tuple(options)
        choices=tuple(options[h] for h in histories)
        for picked in product(*choices):
            yield dict(zip(histories,picked))

    def synthesize(
        self,world:World,*,
        verification_enabled:bool=True,
        maximum_exact_completions:int | None=None,
    )->dict[str,Any]:
        auth=self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {
                "status":"UNKNOWN_NO_VERIFIER",
                "tested_completions":0,
            }

        observed=self.observed_supports(world)
        options=self.support_options(world,observed)
        completion_count=prod(len(v) for v in options.values())
        max_exact=(
            self.MAX_EXACT_COMPLETIONS
            if maximum_exact_completions is None
            else int(maximum_exact_completions)
        )

        forced_branching=[
            h for h,s in observed.items() if len(s)>1
        ]
        forced_singleton_closed=[
            h for h in world.closed_histories
            if len(observed[tuple(h)])==1
        ]

        low=self.extreme_completion(world,options,"minimal")
        high=self.extreme_completion(world,options,"maximal")
        low_floor=self.floor_from_table(world,low)
        high_floor=self.floor_from_table(world,high)
        low_fp=self.fingerprint(low_floor)
        high_fp=self.fingerprint(high_floor)

        if low_fp!=high_fp:
            return {
                "status":"UNKNOWN_IDENTIFIABILITY",
                "reason":"COMPATIBLE_COMPLETIONS_DISAGREE",
                "completion_count":completion_count,
                "tested_completions":2,
                "forced_branching_histories":[list(h) for h in forced_branching],
                "forced_singleton_closed_histories":[list(h) for h in forced_singleton_closed],
                "witness_a":self.completion_witness(low,low_floor),
                "witness_b":self.completion_witness(high,high_floor),
            }

        if completion_count>max_exact:
            return {
                "status":"UNKNOWN_COMPLETION_SPACE_RESOURCE_BOUND",
                "completion_count":completion_count,
                "maximum_exact_completions":max_exact,
                "tested_completions":2,
                "forced_branching_histories":[list(h) for h in forced_branching],
                "extreme_fingerprint_agreement":True,
            }

        fingerprints={}
        representative={}
        law_kinds=set()
        tested=0

        for table in self.exact_completions(options):
            floor=self.floor_from_table(world,table)
            fp=self.fingerprint(floor)
            fingerprints[fp]=fingerprints.get(fp,0)+1
            representative.setdefault(fp,(table,floor))
            law_kinds.add(floor["law_kind"])
            tested+=1
            if len(fingerprints)>1:
                rows=list(representative.values())
                return {
                    "status":"UNKNOWN_IDENTIFIABILITY",
                    "reason":"EXACT_VERSION_SPACE_DISAGREES",
                    "completion_count":completion_count,
                    "tested_completions":tested,
                    "forced_branching_histories":[list(h) for h in forced_branching],
                    "witness_a":self.completion_witness(*rows[0]),
                    "witness_b":self.completion_witness(*rows[1]),
                }

        only_fp=next(iter(fingerprints))
        table,floor=representative[only_fp]
        if floor["status"]!="FLOOR":
            return {
                "status":"UNKNOWN_FUTURE_HORIZON_INSUFFICIENT",
                "completion_count":completion_count,
                "tested_completions":tested,
                "law_kinds":sorted(law_kinds),
            }

        return {
            "status":"VERIFIED_IDENTIFIABLE_BEHAVIORAL_FLOOR",
            "completion_count":completion_count,
            "tested_completions":tested,
            "floor_future_depth":floor["floor_future_depth"],
            "state_count":floor["state_count"],
            "history_class_labels":[int(x) for x in floor["history_class_labels"]],
            "transition_maps":[list(row) for row in floor["transition_maps"]],
            "token_classes":[list(c) for c in floor["token_classes"]],
            "law_kinds_consistent_with_evidence":sorted(law_kinds),
            "determinism_identifiable":law_kinds=={"DETERMINISTIC_SUPPORT"},
            "forced_branching_histories":[list(h) for h in forced_branching],
            "forced_singleton_closed_histories":[list(h) for h in forced_singleton_closed],
        }
