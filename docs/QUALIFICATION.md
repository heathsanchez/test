# Qualification and limits

## Frozen source qualification

The original [source run](https://github.com/heathsanchez/test/actions/runs/45681083460)
qualified commit `578697991a903ab78d344aa71165d465bef3c3d7` with Rust 1.99.1
and the frozen launch configuration now checked in as `arena-flags.json`.

Its source `src/` tree is `362242c265ee2b1758645c78ad141ad78bf6f8c2`.
The beta input manifest came from revision
`ac0765f269b3cb5d4ed3744301aa59f4ee67ad10` of the preview Arena.

| Executed scope | ACCEPT | REJECT | UNKNOWN |
| --- | ---: | ---: | ---: |
| 356 downloadable beta inputs | 59 | 51 | 246 |
| 138 format-3.2.0 inputs, included above | 29 | 34 | 75 |
| Separate 212-input frozen legacy replay | 122 | 84 | 6 |

The source qualification observed no incorrect decisive results or crashes,
and preserved all 212 legacy verdicts. These scopes overlap and their totals
must not be added. Inputs above the generic 10 MiB allowance are declined;
large-input declines are not successful proof checks.

## Official preview qualification

[Arena PR #3](https://github.com/leanprover/lean-kernel-arena-beta/pull/3) was
merged with the same pinned source and configuration.

The [official PR run](https://github.com/leanprover/lean-kernel-arena-beta/actions/runs/45682758925)
reported 364 result rows: 110 correct prescribed decisions, three permitted
policy-case decisions and 251 declines, with no incorrect results, crashes
or timeouts. Its 138 renovation outcomes were 29 ACCEPT, 34 REJECT and
75 DECLINE. The PR workflow omitted `init`, `std` and
`perf/gf3-matrix-product`; policy cases and omissions differ from the source
qualification above.

## Standalone migration

The initial extraction preserves the original implementation, launcher,
configuration and build manifests. The import identity check compares their
bytes against the qualified source.

The migration replay takes the original qualification artifact, verifies its
SHA-256 and ZIP CRCs, verifies each input's SHA-256, and requires all 356 raw
exit codes to match their recorded outcomes.

```sh
python3 scripts/replay_recorded_beta.py \
  --archive /path/to/nucleus-original-qualification.zip \
  --out /tmp/nucleus-migration-replay.json
```

Original artifact: `nucleus-beta-entry-evidence`, ID `15053582604`.

```text
SHA-256 d8a2cb8b5c92bb14dea63fb019086e6c7f8a6b6183d804681f53a50fb8c145ee
```

Standalone execution results will be recorded here after verification.

## What the evidence establishes

The [initial migration attempt](https://github.com/heathsanchez/test/actions/runs/45731878394)
stopped at a Rust proof-relevance regression because the standalone test setup
omitted three capability flags from the original qualification workflow.
`scripts/test.py` restores that exact test configuration and clears inherited
checker flags. The runtime implementation and its frozen launch configuration
remain bound to the original import manifest.

The results establish the reported behavior on the exact tested inputs,
source and configuration. They do not establish universal soundness, general
format-3.2.0 completeness or full Mathlib acceptance. The abstract Lean model
under `formal/` also does not establish refinement of the Rust implementation.

UNKNOWN is an explicit unresolved result. A future change that admits a new
case needs an explanation of the authorizing source rule, adversarial
controls and regression evidence.
