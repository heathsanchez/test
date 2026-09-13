# V35 post-freeze hygiene correction

The first V35 scientific run (34782557782) passed every substantive gate E1-E14 and E16.

E15 alone failed because the post-freeze hygiene scanner banned the lowercase token `tuple`, which matched Python's built-in type annotation rather than a legacy developmental constructor. The frozen protocol intended to exclude the old constructor family such as READ, ATOM, PAIR, TUPLE3, SWITCH, and APPLY.

The scientific core was not modified.

The post-freeze evaluator was corrected to scan case-sensitive legacy constructor tokens while continuing to reject named domain/challenge concepts.

This file documents the harness-only correction.
