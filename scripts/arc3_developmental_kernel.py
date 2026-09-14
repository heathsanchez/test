#!/usr/bin/env python3
"""
ARC-AGI-3 developmental-kernel probe.

The agent is intentionally observation-only. It does not import or inspect a
game implementation. It starts from generic visual component signatures and
available actions, builds an empirical transition model, refines state when
consequence contradicts a quotient, and explores the learned graph toward
untried state/action frontiers.

This is an experiment, not a claimed general ARC-3 solver.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import time
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import numpy as np
import arc_agi
from arcengine import GameState


def latest_grid(obs: Any) -> np.ndarray:
    frames = getattr(obs, "frame", None)
    if frames is None:
        raise RuntimeError("observation has no frame")
    arr = np.asarray(frames[-1] if isinstance(frames, (list, tuple)) else frames)
    if arr.ndim != 2:
        arr = np.squeeze(arr)
    return arr.astype(np.int16, copy=False)


def connected_components(grid: np.ndarray, min_size: int, pos_quant: int) -> tuple:
    h, w = grid.shape
    seen = np.zeros((h, w), dtype=bool)
    comps = []
    for y in range(h):
        for x in range(w):
            if seen[y, x]:
                continue
            c = int(grid[y, x])
            if c < 0:
                seen[y, x] = True
                continue
            stack = [(y, x)]
            seen[y, x] = True
            pts = []
            while stack:
                yy, xx = stack.pop()
                pts.append((yy, xx))
                for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    ny, nx = yy+dy, xx+dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and int(grid[ny, nx]) == c:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            n = len(pts)
            if n < min_size:
                continue
            ys = [p[0] for p in pts]; xs = [p[1] for p in pts]
            y0,y1,x0,x1 = min(ys),max(ys),min(xs),max(xs)
            # Ignore only near-whole-screen connected fields; this removes flat background
            # without assigning any palette semantics.
            if n > 0.70*h*w:
                continue
            cy = int(round((sum(ys)/n)/pos_quant))
            cx = int(round((sum(xs)/n)/pos_quant))
            comps.append((c, int(round(math.log2(n+1)*4)), cy, cx,
                          int(round((y1-y0+1)/pos_quant)),
                          int(round((x1-x0+1)/pos_quant))))
    return tuple(sorted(comps))


def pooled_hist(grid: np.ndarray, block: int, quant: int) -> tuple:
    h, w = grid.shape
    out = []
    vals = np.clip(grid, 0, 15)
    for y0 in range(0, h, block):
        for x0 in range(0, w, block):
            b = vals[y0:min(h,y0+block), x0:min(w,x0+block)].ravel()
            cnt = np.bincount(b, minlength=16)
            out.extend((cnt // quant).tolist())
    return tuple(out)


@dataclass(frozen=True)
class Grain:
    name: str
    min_component: int
    pos_quant: int
    hist_block: int
    hist_quant: int


GRAINS = [
    Grain("coarse", 12, 4, 16, 8),
    Grain("medium", 8, 2, 8, 4),
    Grain("fine", 4, 1, 4, 2),
    Grain("exactish", 1, 1, 2, 1),
]


def percept_signature(grid: np.ndarray, grain: Grain) -> str:
    rep = (
        connected_components(grid, grain.min_component, grain.pos_quant),
        pooled_hist(grid, grain.hist_block, grain.hist_quant),
    )
    return hashlib.sha1(repr(rep).encode()).hexdigest()[:16]


def consequence_key(obs: Any, next_sig: str) -> tuple:
    st = getattr(getattr(obs, "state", None), "name", str(getattr(obs, "state", None)))
    return (next_sig, int(getattr(obs, "levels_completed", 0)), st)


class DevKernelAgent:
    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)
        self.grain_idx = 0
        self.context_depth = 0
        self.records: list[dict[str, Any]] = []
        self.events: list[dict[str, Any]] = []
        self.visits = defaultdict(int)
        self.action_counts = defaultdict(int)
        self.transition_counts = defaultdict(lambda: defaultdict(int))
        self.frontier_tried = defaultdict(set)
        self.last_action_names: deque[str] = deque(maxlen=4)
        self.last_sigs: deque[str] = deque(maxlen=4)
        self.current_level = 0
        self.max_level = 0
        self.model_rebuilds = 0

    @property
    def grain(self) -> Grain:
        return GRAINS[self.grain_idx]

    def base_sig(self, grid: np.ndarray) -> str:
        return percept_signature(grid, self.grain)

    def state_id(self, sig: str) -> str:
        if self.context_depth <= 0:
            return sig
        hs = list(self.last_sigs)[-self.context_depth:]
        ha = list(self.last_action_names)[-self.context_depth:]
        raw = repr((sig, hs, ha)).encode()
        return sig[:8] + ":" + hashlib.sha1(raw).hexdigest()[:8]

    def _record_event(self, kind: str, **kw: Any) -> None:
        e = {"t": len(self.records), "kind": kind, **kw}
        self.events.append(e)
        print("EVENT", json.dumps(e, sort_keys=True), flush=True)

    def observe_initial(self, obs: Any) -> tuple[str, np.ndarray]:
        grid = latest_grid(obs)
        sig = self.base_sig(grid)
        sid = self.state_id(sig)
        self.visits[sid] += 1
        self.current_level = int(getattr(obs, "levels_completed", 0))
        self.max_level = self.current_level
        return sid, grid

    def register_transition(self, prev_grid: np.ndarray, prev_sid: str, action_name: str, obs: Any) -> tuple[str, np.ndarray]:
        grid = latest_grid(obs)
        next_sig = self.base_sig(grid)
        next_sid = self.state_id(next_sig)
        ck = consequence_key(obs, next_sig)
        key = (prev_sid, action_name)
        self.transition_counts[key][ck] += 1
        self.frontier_tried[prev_sid].add(action_name)
        self.action_counts[action_name] += 1
        self.visits[next_sid] += 1

        rec = {
            "i": len(self.records),
            "grain": self.grain.name,
            "context_depth": self.context_depth,
            "from": prev_sid,
            "action": action_name,
            "to": next_sid,
            "from_base": self.base_sig(prev_grid),
            "to_base": next_sig,
            "levels_completed": int(getattr(obs, "levels_completed", 0)),
            "state": getattr(getattr(obs, "state", None), "name", str(getattr(obs, "state", None))),
            "pixel_delta": int(np.count_nonzero(grid != prev_grid)),
        }
        self.records.append(rec)
        self.last_action_names.append(action_name)
        self.last_sigs.append(next_sig)

        lvl = rec["levels_completed"]
        if lvl > self.max_level:
            self._record_event("VERIFIED_PROGRESS", from_level=self.max_level, to_level=lvl, action=action_name)
            self.max_level = lvl
        if lvl != self.current_level:
            self._record_event("LEVEL_BOUNDARY", old=self.current_level, new=lvl)
            self.current_level = lvl
            # New level: keep the developmental machinery, clear only local frontier accounting.
            self.frontier_tried.clear()
            self.visits.clear()
            self.visits[next_sid] += 1

        # Certified empirical contradiction to current quotient: same state/action,
        # multiple observed consequence classes. Refine minimally.
        if len(self.transition_counts[key]) > 1:
            if self.grain_idx + 1 < len(GRAINS):
                old = self.grain.name
                self.grain_idx += 1
                self._record_event("SPLIT_GRAIN", old=old, new=self.grain.name,
                                   witness_state=prev_sid, witness_action=action_name,
                                   consequence_count=len(self.transition_counts[key]))
                self._reset_empirical_model_keep_history()
                next_sig = self.base_sig(grid)
                next_sid = self.state_id(next_sig)
            elif self.context_depth < 3:
                old = self.context_depth
                self.context_depth += 1
                self._record_event("BIRTH_MEMORY", old_depth=old, new_depth=self.context_depth,
                                   witness_state=prev_sid, witness_action=action_name)
                self._reset_empirical_model_keep_history()
                next_sig = self.base_sig(grid)
                next_sid = self.state_id(next_sig)
            else:
                self._record_event("UNKNOWN_EXPRESSIVITY", witness_state=prev_sid,
                                   witness_action=action_name)

        return next_sid, grid

    def _reset_empirical_model_keep_history(self) -> None:
        self.transition_counts.clear()
        self.frontier_tried.clear()
        self.visits.clear()
        self.model_rebuilds += 1

    def choose(self, sid: str, actions: list[Any]) -> tuple[Any, dict[str, Any]]:
        names = [a.name for a in actions]
        # 1) Local experimental frontier: perform every still-untried intervention.
        untried = [a for a in actions if a.name not in self.frontier_tried[sid]]
        if untried:
            # Prefer globally least-used action to avoid an arbitrary fixed ordering.
            a = min(untried, key=lambda x: (self.action_counts[x.name], x.name))
            return a, {"mode":"PROBE", "reason":"untried intervention at current warranted state"}

        # 2) Known graph: find a shortest route to any state with an untried action.
        adj: dict[str, list[tuple[str,str]]] = defaultdict(list)
        for (s, an), cs in self.transition_counts.items():
            if not cs:
                continue
            # Use only unambiguous currently observed edges.
            if len(cs) == 1:
                (nxt, _lvl, terminal), _count = next(iter(cs.items()))
                if terminal != "GAME_OVER":
                    adj[s].append((an, nxt))
        q = deque([(sid, [])])
        seen = {sid}
        while q:
            s, path = q.popleft()
            if s != sid:
                missing = set(names) - self.frontier_tried[s]
                if missing and path:
                    want = path[0]
                    for a in actions:
                        if a.name == want:
                            return a, {"mode":"ROUTE_TO_FRONTIER", "target_state":s,
                                       "reason":"shortest known route to unresolved intervention"}
            for an, nxt in adj.get(s, []):
                if nxt not in seen:
                    seen.add(nxt)
                    q.append((nxt, path+[an]))

        # 3) No reachable unresolved frontier under current model: choose the empirically
        # least-used nonterminal action. This is explicit UNKNOWN/search, not a claim.
        candidates = []
        for a in actions:
            cs = self.transition_counts.get((sid, a.name), {})
            gameovers = sum(n for (nxt,lvl,term), n in cs.items() if term == "GAME_OVER")
            total = sum(cs.values())
            risk = gameovers / total if total else 0.0
            candidates.append((risk, self.action_counts[a.name], a.name, a))
        _, _, _, a = min(candidates)
        return a, {"mode":"UNKNOWN_SEARCH", "reason":"no certified route to an unresolved frontier"}

    def summary(self) -> dict[str, Any]:
        return {
            "grain": self.grain.name,
            "context_depth": self.context_depth,
            "model_rebuilds": self.model_rebuilds,
            "actions": len(self.records),
            "max_levels_completed": self.max_level,
            "events": self.events,
            "action_counts": dict(self.action_counts),
            "records": self.records,
        }


def action_data(action: Any, grid: np.ndarray, rng: random.Random) -> dict[str, int]:
    if not action.is_complex():
        return {}
    # Generic coordinate intervention candidates: centers of non-background connected
    # regions, then center, then random. No game-specific coordinates/palette meanings.
    h,w = grid.shape
    ys,xs = np.where(grid >= 0)
    if len(xs):
        return {"x": int(np.median(xs)), "y": int(np.median(ys))}
    return {"x": rng.randrange(w), "y": rng.randrange(h)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="ls20")
    ap.add_argument("--max-actions", type=int, default=400)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="arc3_developmental_result.json")
    args = ap.parse_args()

    random.seed(args.seed)
    arc = arc_agi.Arcade()
    env = arc.make(args.game, save_recording=True, include_frame_data=True, render_mode=None)
    if env is None:
        raise SystemExit("arc.make returned None")

    obs = env.reset()
    if obs is None:
        raise SystemExit("reset returned None")

    agent = DevKernelAgent(args.seed)
    sid, grid = agent.observe_initial(obs)
    print("START", args.game, "actions", [a.name for a in env.action_space],
          "levels", getattr(obs, "levels_completed", None),
          "win_levels", getattr(obs, "win_levels", None), flush=True)

    resets = 0
    for step in range(args.max_actions):
        actions = list(env.action_space)
        if not actions:
            print("NO_ACTIONS", step, flush=True)
            break
        action, reasoning = agent.choose(sid, actions)
        data = action_data(action, grid, agent.rng)
        prev_grid, prev_sid = grid, sid
        obs = env.step(action, data=data, reasoning=reasoning)
        if obs is None:
            agent._record_event("NULL_OBSERVATION", action=action.name)
            continue
        sid, grid = agent.register_transition(prev_grid, prev_sid, action.name, obs)
        print("STEP", step+1, action.name, reasoning["mode"],
              "delta", agent.records[-1]["pixel_delta"],
              "level", getattr(obs,"levels_completed",None),
              "state", getattr(getattr(obs,"state",None),"name",None),
              "grain", agent.grain.name, "ctx", agent.context_depth, flush=True)

        if obs.state == GameState.WIN:
            agent._record_event("WIN", step=step+1)
            break
        if obs.state == GameState.GAME_OVER:
            resets += 1
            agent._record_event("GAME_OVER", step=step+1, resets=resets)
            if resets >= 4:
                break
            obs = env.reset()
            if obs is None:
                break
            sid, grid = agent.observe_initial(obs)

    result = agent.summary()
    result.update({
        "game": args.game,
        "seed": args.seed,
        "resets": resets,
        "final_state": getattr(getattr(obs, "state", None), "name", None) if obs is not None else None,
        "final_levels_completed": int(getattr(obs, "levels_completed", 0)) if obs is not None else None,
        "win_levels": int(getattr(obs, "win_levels", 0)) if obs is not None else None,
    })
    try:
        sc = arc.close_scorecard()
        if sc is not None:
            if hasattr(sc, "model_dump"):
                result["scorecard"] = sc.model_dump(mode="json")
            else:
                result["scorecard"] = str(sc)
    except Exception as e:
        result["scorecard_error"] = repr(e)

    Path(args.out).write_text(json.dumps(result, indent=2, default=str))
    print("RESULT", json.dumps({k:v for k,v in result.items() if k not in ("records","events","scorecard")}, sort_keys=True), flush=True)
    print("OUTPUT", args.out, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
