# V161 AST-role experiential rescue — frozen protocol

## Question
Does the V160 effect survive removal of the numeric world-id scaffold? Specifically, can a repair operator learned from prior executable-verified programs be represented over AST/source roles and later instantiated into held-out programs with unrelated identifier names after the neural model has regressed?

## Frozen checkpoints
- stable pre-interference AB checkpoint: `river://ae6fa294-181b-46af-b078-429ce7e6c882/weights/quix_AB_step1`
- V160 first-regression checkpoint after C-only consolidation step 5: `river://8c23d218-606e-4b90-a4df-d8a9c86ef554/weights/v160_first_regression_step5`
- base model: `Qwen/Qwen3.5-9B`
- seed: `20260831`

## Experience and protected split
Prior verified experience consists of two heterogeneous-name source programs for A and two for B. Protected evaluation consists of eight new heterogeneous-name source programs per task. No identifier string, numeric suffix, or answer line is shared as a routing key between experience and protected programs.

## Map construction
For each admitted prior repair, parse the candidate line and its source AST and translate concrete identifiers into source roles.

Supported role vocabulary is frozen before outcomes:
- `A_APPEND_STACK_LOOP_ITEM`: expression statement calling `.append` on the local empty-list variable that participates in the operator-stack while condition, with the current `for` target as its argument.
- `B_RETURN_SINGLETON_ARG`: return a singleton list containing the function's first argument.

A task map is installed only if both prior executable-verified experiences induce the same role descriptor. This is a supplied small meta-language, not unrestricted operator invention.

## Frozen-weight arms on protected programs
At the V160 first-regression checkpoint compare:
1. neural only;
2. raw verified memory: the two admitted heterogeneous prior repair examples are included in the prompt;
3. compiled experiential map: instantiate the learned AST-role descriptor from the protected source AST, without using the protected answer;
4. shuffled map: swap the learned A/B descriptors with equal controller budget.

All candidate repairs are decided by compile/execute verification.

## Decisive success
PASS iff:
- both experience maps are learned from verifier-admitted prior episodes;
- compiled-map verified hits on A+B exceed neural-only and raw-memory A+B;
- compiled-map verified hits exceed shuffled-map A+B.

## Claim boundary
A pass establishes bounded causal reuse of AST-role structure learned from prior verified coding experience across heterogeneous identifier names at a frozen regressed neural checkpoint. It does not establish unrestricted program repair, unrestricted AST abstraction learning, or natural-world open-ended development.
