# Novel Consequence Quotient V4 — Frozen Result

## Verdict

```text
VERIFIED_PI_DOMAIN_SHARING_NO_CAUSAL_GAIN
```

Run: `34916095646`  
Job: `104213907784`  
Commit: `488e204c7f8b9727afd0345d0e46253181e1a514`  
Artifact: `10376740600`  
Artifact digest: `sha256:5d4335fe4eadb7a9ec7b32816ae665f3029be22128e9c55d7360024d50b8a648`

All arms passed the complete frozen Arena semantic oracle:

- 103 / 103 good accepted
- 58 / 58 bad rejected

Median CPU on the frozen 24-case held-out workload:

- A0: **0.190754 s**
- Q-domain-ablation: **0.199278 s**
- Q-domain: **0.200876 s**

Paired CPU:

- Q-domain vs A0: **+4.1753%**, wins **1 / 15**
- Q-domain vs ablation: **+0.0963%**, wins **7 / 15**

## Interpretation

Rebinding the Pi body closure to the current raw environment removed the clear
additional harm seen when V3 returned a whole Pi from another operational state.

However, domain reuse itself produced no measurable causal gain against the
same-key/recompute control.

The remaining cost is the consequential key implementation: V4 allocates and
hashes an exact `Vec<usize>` signature on every eligible Pi pointer-cache miss.
That cost is paid broadly while the frozen shadow experiment found only 602
cross-identity reuse opportunities on held-out cases.

The next experiment preserves the exact consequential equality relation but
changes only its compilation economics:

- no Vec key allocation;
- bounded direct-mapped cache at the checker's existing direct-map scale;
- semantic hash only selects a candidate entry;
- full exact representative-by-representative equality is required before reuse;
- collisions cannot authorize a wrong hit.

V4 is rejected and is not stacked as an admitted optimization.
