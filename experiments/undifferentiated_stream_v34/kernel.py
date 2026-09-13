from __future__ import annotations
from collections import defaultdict
from typing import Any

from basis import Machine, World, run_machine

class Kernel:
    @staticmethod
    def authority(world: World) -> dict[str,Any] | None:
        if not world.complete or not world.rows:
            return {"status":"UNKNOWN_AUTHORITY"}
        n=len(world.rows[0].stream)
        if any(len(r.stream)!=n or r.consequence is None for r in world.rows):
            return {"status":"UNKNOWN_AUTHORITY"}
        if any(any(int(b) not in (0,1) for b in r.stream) for r in world.rows):
            return {"status":"INVALID_SYMBOL_ALPHABET"}
        observed={tuple(r.stream) for r in world.rows}
        if len(observed)!=(1<<n):
            return {"status":"UNKNOWN_AUTHORITY"}
        if len(observed)!=len(world.rows):
            return {"status":"INVALID_DUPLICATE_ENCOUNTER"}
        return None

    @staticmethod
    def _mapping(world: World) -> dict[tuple[int,...],int]:
        return {tuple(r.stream):int(r.consequence) for r in world.rows}

    def synthesize(self, world: World, *, verification_enabled: bool=True) -> dict[str,Any]:
        auth=self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {"status":"UNKNOWN_NO_VERIFIER","state_count":0}

        mapping=self._mapping(world)
        n=len(world.rows[0].stream)

        states:list[tuple[Any,...]]=[]
        terminal_ids:dict[int,int]={}
        step_ids:dict[tuple[int,int],int]={}

        def terminal(label:int)->int:
            if label not in terminal_ids:
                terminal_ids[label]=len(states)
                states.append(("OUT",int(label)))
            return terminal_ids[label]

        ids={stream:terminal(label) for stream,label in mapping.items()}
        residual_counts=[]

        for depth in range(n-1,-1,-1):
            prefixes=sorted({stream[:depth] for stream in mapping})
            new={}
            layer_signatures=set()
            for p in prefixes:
                lo=ids[p+(0,)]
                hi=ids[p+(1,)]

                # If both continuations are already the same terminal, all
                # remaining symbols are consequence-irrelevant and the terminal
                # can absorb them.  Otherwise a STEP is required to consume one
                # anonymous symbol before continuing.
                if lo==hi and states[lo][0]=="OUT":
                    sid=lo
                    sig=("OUT",states[lo][1])
                else:
                    key=(int(lo),int(hi))
                    if key not in step_ids:
                        step_ids[key]=len(states)
                        states.append(("STEP",int(lo),int(hi)))
                    sid=step_ids[key]
                    sig=("STEP",int(lo),int(hi))
                new[p]=sid
                layer_signatures.add(sig)
            residual_counts.append({
                "depth":depth,
                "prefix_count":len(prefixes),
                "distinct_residual_count":len(layer_signatures),
            })
            ids=new

        machine=Machine(ids[()],tuple(states))
        replay=[run_machine(machine,tuple(r.stream)) for r in world.rows]
        exact=all(v==int(r.consequence) for v,r in zip(replay,world.rows))

        neutral=sum(
            1 for s in machine.states
            if s[0]=="STEP" and int(s[1])==int(s[2])
        )
        branching=sum(
            1 for s in machine.states
            if s[0]=="STEP" and int(s[1])!=int(s[2])
        )
        terminals=sum(1 for s in machine.states if s[0]=="OUT")

        return {
            "status":"VERIFIED" if exact else "REPLAY_FAILED",
            "stream_length":n,
            "state_count":len(machine.states),
            "terminal_count":terminals,
            "neutral_transition_count":neutral,
            "branching_transition_count":branching,
            "residual_counts":list(reversed(residual_counts)),
            "machine":machine.data(),
            "exact_replay":exact,
            "_machine":machine,
        }

    @staticmethod
    def structural_signature(result: dict[str,Any]) -> dict[str,Any]:
        states=result.get("machine",{}).get("states",[])
        return {
            "state_count":result.get("state_count"),
            "terminal_count":result.get("terminal_count"),
            "neutral_transition_count":result.get("neutral_transition_count"),
            "branching_transition_count":result.get("branching_transition_count"),
            "transition_shape":sorted(
                (s[0], s[1]==s[2] if len(s)==3 else None)
                for s in states
            ),
        }
