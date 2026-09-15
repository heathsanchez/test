# Novel Consequence Quotient V5 — Frozen Result

## Verdict

```text
VERIFIED_DM_PI_REUSE_NO_CAUSAL_GAIN
```

Run: `34916447921`  
Job: `104214996258`  
Commit: `d7548f02fd447dc76804ef1279ede3cb3432ec13`  
Artifact: `10376447175`  
Artifact digest: `sha256:1850cd392720ff02b388fa254fec5c503bbc89513970e06362114c7f97e3fa11`

All three arms passed the complete frozen Arena oracle:

- 103 / 103 good accepted
- 58 / 58 bad rejected

Median CPU on the frozen held-out workload:

- A0: **0.269853 s**
- direct-map ablation: **0.270801 s**
- direct-map quotient: **0.277079 s**

Paired CPU:

- quotient vs A0: **+1.8086%**, wins **1 / 15**
- quotient vs same direct-map ablation: **+2.4910%**, wins **2 / 15**

## Interpretation

Removing the allocating Vec/general-map identity machinery substantially reduced
the tax relative to V4, but exact domain reuse itself is now clearly harmful.

The residual therefore moves inside the cached Pi domain value. A domain
`V<'t>` can itself contain closures, spines, rigid heads, and other operational
structure. Semantic equivalence of the parent environment does not imply that
reusing the same allocated domain object is operationally neutral.

The next diagnostic classifies exact direct-map hits by domain Value kind,
canonical status, and closedness to identify the smallest operationally
self-contained consequence class.

V5 is rejected and not admitted.
