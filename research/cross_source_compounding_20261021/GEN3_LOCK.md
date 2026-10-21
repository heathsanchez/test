# Gen3 prospective acquisition experiment — frozen prior to execution

## Target and source
Use exactly go-ini/ini@e2db55b0e088fa4ee0c128aa4ade263cdc1d7f08. No substitution.
New target Q3: discover a witness for parser/value instability when a serialized
string crosses two successive read/write transformations under controlled string
mutations. The declared search grammar contains candidate strings drawn from the
existing GEN1 corpus plus bounded single-character insertions of #, ;, =, space,
quote, backslash, CR and LF. A candidate is accepted only when independent native
Go execution establishes the changed semantic value with a reproducible witness.

## Competing strategies
Warm: preserve GEN1's qualified fixture representations and candidate enumeration
ordering. Cold: remove these retained procedures, use the same primitive mutation
grammar and native verifier. Strong conventional baseline: gets the exact same
qualified fixtures, grammar, code, source, environment, and opportunity to cache and
reuse earlier findings, including adopting the warm strategy. It may tie or win.

This experiment distinguishes **search proposals** from verified source semantics.
The source verifier must be the same for all arms. Seed corpus, mutation grammar,
budget, cold restart, search counters, wall time and native processes are charged.
All human design and preparation is explicitly uncharged; no full-lifetime claim.

## Required failure reporting
A zero-witness outcome is UNKNOWN, not success. A candidate witness without a
native confirmation is REJECTED. A baseline tie is a tie. No autonomous novel
method generation is claimed because the grammar and transfer are human-provided.
No external writes.
