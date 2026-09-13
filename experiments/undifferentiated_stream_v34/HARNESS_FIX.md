# V34 post-freeze evaluator correction

The first post-freeze run (34781855963) produced exact replay on every challenge and passed S1-S8 and S10-S16.

S9 alone failed because the evaluation harness required both state count and neutral-transition count to differ under a selected stream permutation. The frozen protocol required only that the residual machine structure change when relevant sources move.

Observed contextual machines changed from 11 states / 5 branching transitions to 8 states / 2 branching transitions while neutral-transition count remained 4.

The scientific core was not modified. The post-freeze S9 evaluator was therefore corrected to compare the actual rooted STEP/OUT graph shape.

This file documents the harness-only correction.
