# Collatz QCKN V1 Qualification

**Status:** bounded developmental qualification. **Collatz remains unproved.**

This qualification implements the approved design in
`docs/superpowers/specs/2026-09-18-collatz-qckn-domain-adapter-design.md`.

## Qualified causal chain

The CI gate executes the same trust boundary used by the research adapter:

[
	ext{proposal}
	o
	ext{independent exact replay verification}
	o
	ext{causal promotion}
	o
	ext{CompiledPresent}
	o
	ext{canonical restart}
	o
	ext{future reuse}.
]

The sealed CI fixture is deliberately small so the causal semantics are checked on every commit. Source 7 supplies an exact descent episode capability. The future obligation is source 11, which independently reaches the same episode start. WARM may use only the restarted CompiledPresent; it does not replay acquisition.

## Mandatory controls

The qualification emits matched results for:

- **COLD** — no promoted capability;
- **WARM** — canonical restarted CompiledPresent;
- **RAW_HISTORY** — prior proposal material exists but is not active memory;
- **SHAM** — same active-memory shape/count with a stale contract;
- **ANCESTOR_ABLATION** — the promoted capability is causally revoked, recompiled and restarted.

The release gate requires:

[
egin{aligned}
	ext{WARM authoritative hits} &> 0,\
	ext{WARM discovery calls} &=0,\
	ext{COLD hits}&=0,\
	ext{RAW_HISTORY hits}&=0,\
	ext{SHAM hits}&=0,\
	ext{ABLATION hits}&=	ext{COLD hits}.
end{aligned}
]

The larger research result at run 35327397877 remains separate empirical evidence: 481 forward descent macros learned from the declared earlier shell closed 88 of 162 eligible untouched held-out sources. The V1 runtime qualification does not silently generalize that bounded census.

## Evidence record

`python -m collatz_qckn.runner --qualify` emits canonical JSON containing:

- contract digest;
- authority digest;
- training/future source digests;
- verified promotion count;
- CompiledPresent digest;
- revocation event digest;
- per-arm obligation, active-capability, attempt, hit, residual, discovery and search metrics;
- the bounded claim string.

The final line is a SHA-256 closure certificate over the canonical evidence.

CI executes the qualification twice and requires byte-identical output.

## Claim boundary

A green gate establishes only:

> Bounded causal reuse of an independently verified Collatz descent capability through promotion, canonical compilation, exact restart, matched controls and causal ablation.

It does **not** establish Collatz, completeness of the capability language, universal termination, universal lower merge, or a new mathematical theorem about all positive integers.

The mathematical programme continues from its exact residuals. QCKN governs what verified developmental consequences may alter future execution.


## Qualified evidence points — 18 September 2026

### Runtime causal gate

GitHub Actions run **35341498976**: GREEN.

- 30 Collatz QCKN unit tests: PASS.
- deterministic qualification output: PASS;
- COLD: 0/1 authoritative hits;
- WARM: 1/1 authoritative hit with zero discovery;
- RAW_HISTORY: 0/1;
- SHAM: 0/1;
- ANCESTOR_ABLATION: 0/1;
- closure certificate:
  `6d82832cf143b8a3ce47e8da136c2e550c392c82f7a42f5451dc758a85009b30`.

### Full-shell research qualification

GitHub Actions run **35341612114**: GREEN.

Frozen acquisition shell:

[
3le nle8191.
]

Sealed future shell:

[
8193le nle16383.
]

Acquisition accounting:

- 4,095 odd sources scanned;
- 252 eligible training sources;
- 1,051 suffix-macro search expansions / construction attempts;
- 1,051 valid constructions before semantic deduplication;
- 481 deduplicated capabilities;
- 481 independent authority verifications;
- 481 verified causal promotions.

CompiledPresent digest:

`a4f3e1bfa0e615aa72a5988d55959d508f0d761e610eb1d5614b5a51d3b3e81c`

Prospective matched controls on 162 eligible sealed future sources:

| Arm | Active capabilities | Attempts | Authoritative closures | Residuals |
| --- | ---: | ---: | ---: | ---: |
| COLD | 0 | 0 | 0 | 162 |
| WARM | 481 | 57,361 | **88** | **74** |
| RAW_HISTORY | 0 | 0 | 0 | 162 |
| SHAM | 481 | 95,156 | 0 | 162 |
| ANCESTOR_ABLATION | 0 | 0 | 0 | 162 |

WARM performed **zero discovery calls**. The 481 active capabilities came only from the earlier acquisition shell, were independently verified, causally promoted, compiled, serialized, parsed into a fresh CompiledPresent, and then reused.

Revoking the promoted macro family and recompiling restored the cold active result exactly.

Research closure certificate:

`28e78c21cbea3e3f0aad0bf80abed3158eb4c94412f71be10daff590826fd86b`

The result establishes bounded causal developmental advantage of the compiled capability bank under the declared accounting unit. It remains explicitly **not a proof of Collatz**.
