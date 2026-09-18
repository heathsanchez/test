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
