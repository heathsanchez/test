# FLASH V13 — independently reclosed present, not a sequential solver

**Authority boundary:** finite, synthetic, source-pinned multi-frontier hypergraph. The earlier V10/V11/V12b GitHub runs establish their own bounded repair claims. The cross-frontier edges in this experiment are **simulated rules**, not proven causal relations between real research programs.

## What was frozen when

1. Parent source V12b run `38202495321`, commit `ad5c4cade218c3e67538f05c26463ae590dcde17`.
2. Prospective six-gate protocol `research/flash_v13/PROTOCOL.md`, commit `e9d337cbb7e9d3b80407761282d8b51e75560363`.
3. Independent 14-base-fact, 16-hyperedge, 13-frontier, 19-event fixture `research/flash_v13/fixture.json`, commit `b8236e3605a702e5d1215217b02709b02e45d47a`, Git blob SHA1 `eb6889fc9a6f9e6ff07108466618b6e30636d042`, SHA256 `64060c4cbb419ef8ebe295449c19100a8b227ff07c8c12102096092c8bd2cbf9`.
4. Only then were `flash_engine.py`, independent `reference_oracle.py`, and `verify_v13.py` written.

## Reproduce

```bash
python3 research/flash_v13/verify_v13.py
python3 research/flash_v13/benchmark_v13.py
```

Run with Python 3.11+ and no external packages. The scientific `results.json` is deterministic and should match byte-for-byte. Wall-clock `benchmark_results.json` is inherently environment-specific; compare locally, not byte-for-byte.

## Interpretation

All six original **Flash: Incremental Global Consequence Closure** implementation gates are tested:

- Event-dependent change propagates through all affected frontiers in the closure.
- A source-qualified but previously inactive capability becomes useful under a new future obligation.
- A verified separator invalidates a quotient-dependent candidate and activates a split representation.
- Only frontiers whose truth-dependent inputs changed are reevaluated.
- Revocation retracts dependent consequences while independently supported alternatives survive.
- A SHA256-bound compiled state can be restarted without replaying historical events, and subsequent events match a full rebuild.

A completely independent batch fixed-point reference agrees after 19 deterministic updates, 4,200 seeded event updates and 6,000 updates on 200 random graph topologies, including cyclic hyperedges. Exact negative controls cover malformed authorities, unsupported events, tampered snapshot and changed fixture. Replaying a forged snapshot hash is *not* cryptographic authentication of the source.

The original copying-heavy incremental implementation **lost** to the batch baseline in wall time and is preserved as `flash_engine_baseline.py`. The repaired dependency-cone implementation reduces frontier and rule work and won a local 16,000-event median wall-time comparison against this **specific full-rebuild baseline**. Equally informed optimized truth-maintenance systems may tie or beat it. Total research-source acquisition, CI, device measurements and formal Lean proof costs are not captured.

**WARRANTED (bounded, after independent GitHub CI):** finite typed event reclosure with support-sensitive revocation and restart, six gates and cost counters. **UNKNOWN:** unrestricted constructor invention, direct warrant for the synthetic cross-domain edges, externally measured development compounding, strict gain over fully optimized incremental algorithms, universal fixed-point existence or convergence.
