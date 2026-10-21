#!/usr/bin/env python3
"""Experimental purely operational, source-owned Nucleus replay/cache ablation.

The original evaluator stops interning exact beta frames and completed
source-authorized recursor results after 8192 distinct entries.
Five versions are compared on one exact source and one pinned corpus:
  baseline, 32k binding interner, 32k completed replay, both 32k,
  4x source judgment budget (diagnostic budget-only control).

The cache edits have NO effects on kernel typing/conversion semantics:
all memo keys still contain the original immutable frames, source expressions,
universes and registered recursor certificates. Increasing a bound alone
is NOT a production soundness or performance improvement.

Fail closed on source drift; only this script modifies research copies.
"""
from pathlib import Path
import sys
if len(sys.argv)!=3:
    raise SystemExit("usage: patch.py CHECKER_COPY arm")
root=Path(sys.argv[1]); arm=sys.argv[2]
m=root/"src/machine.rs";c=root/"src/checker.rs"
mtext=m.read_text()
bneedle="if entries.bindings.len()<8192 {entries.bindings.insert(key,frame.clone());}"
rneedle="if entries.completed_replay_count>=8192 {"
assert mtext.count(bneedle)==1,("beta binding source mismatch",mtext.count(bneedle))
assert mtext.count(rneedle)==1,("completed recursor source mismatch",mtext.count(rneedle))
if arm in ("bindings","both"):
    mtext=mtext.replace(bneedle,"if entries.bindings.len()<32768 {entries.bindings.insert(key,frame.clone());}")
if arm in ("replays","both"):
    mtext=mtext.replace(rneedle,"if entries.completed_replay_count>=32768 {")
m.write_text(mtext)
if arm=="fuel4x":
    s=c.read_text();old="judgment_steps: 65_536,"
    assert s.count(old)==1,("budget source mismatch",s.count(old))
    c.write_text(s.replace(old,"judgment_steps: 262_144,"))
assert arm in ("baseline","bindings","replays","both","fuel4x")
print("NUCLEUS_RETENTION_ARM="+arm,flush=True)
