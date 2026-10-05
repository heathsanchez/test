# Arena eight-UNKNOWN checkpoint

**Superseded by `arena-major-dispatch-v1`.** The replay below is historical.
A later regression exposed an invalid recursor-major shortcut. Removing it
changes two folded-constant ACCEPT results to UNKNOWN. This checkpoint must
not be used as current checker authority.

Candidate: `e06da5873684f0e58c736bae3d00c6316eb0a7ba`.
Corpus: Lean Kernel Arena `b1d6e91d6de351f9bcf21e6b039f4d51d6b9bb42`, all 196 cases.

Exact replay: 117 ACCEPT / 71 REJECT / 8 UNKNOWN / 0 wrong / 0 errors.
The release test suite passes; its complete output is retained alongside the replay.
Each replay row records the input SHA-256, process exit code, stderr and elapsed time.
The per-case timeout was ten seconds. The full replay completed in approximately three seconds.

Compared with the preceding 116 / 71 / 9 checkpoint, `perf/args-before-unfold`
now accepts. Conversion first tries sufficient positive congruence for identical
constant heads, including universe arguments. Its failed premises fall through to
ordinary conversion. Probes share an attempt limit, have a depth limit, skip
definitions with provably discarded arguments, and compare arguments in reverse
order to preserve cheap refutation behavior. An unrestricted full-budget probe
timed out on three cases and was not admitted.

This is local exact-corpus qualification, not an official Arena ranking.

Reproduce from this repository:

```sh
cargo test --release --locked --manifest-path metatron-kernel/Cargo.toml
python metatron-kernel/scripts/replay_exact_arena.py \
  metatron-kernel/target/release/metatron-kernel /path/to/arena-tests \
  /tmp/arena-replay.json \
  --candidate e06da5873684f0e58c736bae3d00c6316eb0a7ba \
  --arena b1d6e91d6de351f9bcf21e6b039f4d51d6b9bb42 --timeout 10
```
