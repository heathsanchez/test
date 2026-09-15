# Novel Consequence Quotient V6 — Frozen Result

## Verdict

```text
VERIFIED_CLOSED_REUSE_NO_CAUSAL_GAIN
```

Authoritative run: `34916915834`  
Job: `104216437385`  
Commit: `e2d69d9b99e54b6723d8a5963b25d25eecd61b5f`  
Artifact: `10376202472`  
Artifact digest: `sha256:05288aef5fe80cd1c3ebdac5e5d1753dea2d2ffe962ff5478ae0ceaadadd3647`

All arms passed the complete frozen Arena oracle:

- 103 / 103 good accepted
- 58 / 58 bad rejected

Median CPU:

- A0: **0.272623 s**
- closed-reuse ablation: **0.276236 s**
- closed-reuse candidate: **0.274482 s**

Paired CPU:

- candidate vs A0: **+0.9106%**, wins **6 / 15**
- candidate vs ablation: **−0.4332%**, wins **9 / 15**

## Interpretation

Restricting cross-environment domain reuse to closed consequences reverses the
strong negative effect from V5 and produces the first directional causal benefit
against the same machinery/recompute control.

The evidence is not strong enough for admission under the frozen decision rule,
and the candidate remains net negative against A0.

The remaining residual is activation cost: the exact direct-map identity work is
still performed on every eligible Pi pointer-cache miss, while only a small
subset can possibly encounter a prior equivalent Pi environment.

The next diagnostic measures first-versus-repeat Pi-expression misses to test
whether identity work can be deferred until an expression has evidence of
cross-environment recurrence.

V6 is retained as evidence but not admitted.
