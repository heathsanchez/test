from __future__ import annotations
from typing import Any
from basis import World

class Kernel:
    FRAME_MODES = (
        ("UNFRAMED",0),
        ("ORIENTED",1),
        ("ANCHORED",1),
        ("FRAMED",2),
    )

    @staticmethod
    def authority(world: World) -> dict[str,Any] | None:
        if not world.complete or not world.rows:
            return {"status":"UNKNOWN_AUTHORITY"}
        n=len(world.rows[0].cycle)
        if n<1:
            return {"status":"INVALID_EMPTY_BOUNDARY"}
        if any(len(r.cycle)!=n or r.consequence is None for r in world.rows):
            return {"status":"UNKNOWN_AUTHORITY"}
        if any(any(int(b) not in (0,1) for b in r.cycle) for r in world.rows):
            return {"status":"INVALID_SYMBOL_ALPHABET"}
        seen={tuple(r.cycle) for r in world.rows}
        if len(seen)!=(1<<n) or len(seen)!=len(world.rows):
            return {"status":"UNKNOWN_AUTHORITY"}
        return None

    @staticmethod
    def rotations(s: tuple[int,...]) -> tuple[tuple[int,...],...]:
        n=len(s)
        return tuple(s[i:]+s[:i] for i in range(n))

    @staticmethod
    def anchored_reverse(s: tuple[int,...]) -> tuple[int,...]:
        return (s[0],)+tuple(reversed(s[1:]))

    @classmethod
    def orbit(cls, s: tuple[int,...], mode: str) -> tuple[tuple[int,...],...]:
        if mode=="FRAMED":
            return (s,)
        if mode=="ANCHORED":
            return tuple(sorted({s,cls.anchored_reverse(s)}))
        rots=cls.rotations(s)
        if mode=="ORIENTED":
            return tuple(sorted(set(rots)))
        if mode=="UNFRAMED":
            rev=tuple(reversed(s))
            return tuple(sorted(set(rots+cls.rotations(rev))))
        raise ValueError(mode)

    @classmethod
    def representative(cls, s: tuple[int,...], mode: str) -> tuple[int,...]:
        return min(cls.orbit(s,mode))

    @staticmethod
    def canonical_partition(values):
        ids={}; out=[]
        for v in values:
            if v not in ids:
                ids[v]=len(ids)
            out.append(ids[v])
        return tuple(out)

    @classmethod
    def invariant(cls, world: World, mode: str) -> tuple[bool,dict[str,Any] | None]:
        labels={}
        for r in world.rows:
            key=cls.representative(tuple(r.cycle),mode)
            y=int(r.consequence)
            if key in labels and labels[key]!=y:
                return False,{"representative":list(key),"labels":[labels[key],y]}
            labels[key]=y
        return True,None

    @classmethod
    def minimum_event_window(cls, world: World, mode: str) -> int | None:
        target=cls.canonical_partition(int(r.consequence) for r in world.rows)
        reps=[cls.representative(tuple(r.cycle),mode) for r in world.rows]
        n=len(reps[0])
        for k in range(n+1):
            values=[rep[:k] for rep in reps]
            if cls.canonical_partition(values)==target:
                return k
        return None

    def synthesize(self, world: World, *, verification_enabled: bool=True) -> dict[str,Any]:
        auth=self.authority(world)
        if auth:
            return auth
        if not verification_enabled:
            return {"status":"UNKNOWN_NO_VERIFIER","tested_frame_modes":0}

        rows=[]
        obstructions=[]
        for mode,breaks in self.FRAME_MODES:
            ok,witness=self.invariant(world,mode)
            if not ok:
                obstructions.append({"mode":mode,"kind":"SYMMETRY_OBSTRUCTION","witness":witness})
                continue
            k=self.minimum_event_window(world,mode)
            if k is None:
                obstructions.append({"mode":mode,"kind":"EVENT_WINDOW_INADEQUACY"})
                continue
            rows.append({
                "mode":mode,
                "symmetry_breaks":breaks,
                "event_window":k,
            })

        if not rows:
            return {
                "status":"CERTIFIED_EVENT_LANGUAGE_INADEQUACY",
                "obstructions":obstructions,
                "tested_frame_modes":len(self.FRAME_MODES),
            }

        best_metric=min((r["symmetry_breaks"],r["event_window"]) for r in rows)
        frontier=[r for r in rows if (r["symmetry_breaks"],r["event_window"])==best_metric]
        return {
            "status":"VERIFIED",
            "metric":{"symmetry_breaks":best_metric[0],"event_window":best_metric[1]},
            "frontier":frontier,
            "available_solutions":rows,
            "obstructions":obstructions,
            "tested_frame_modes":len(self.FRAME_MODES),
        }
