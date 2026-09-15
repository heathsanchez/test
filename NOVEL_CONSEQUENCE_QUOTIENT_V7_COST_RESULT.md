# V7 Avoided Consequence Cost — Result

Run: `34919656578`  
Job: `104224690199`  
Commit: `aa9b27788e0e3c6c9f7e144103de586034faf0b5`  
Artifact: `10377482544`  
Artifact digest: `sha256:c4cb2886f9290391263ea291731d7a716f5352e055ce88e1aa2d26589e941f2d`

This diagnostic ran the exact V7 recompute ablation and measured the number of
recursive `eval()` calls actually incurred at each valid closed reuse
opportunity.

## Set A

- valid closed opportunities measured: **149**
- total recomputation eval calls: **230**
- mean eval calls per opportunity: **1.54**
- maximum: **12**

Distribution:

- 1 call: **120**
- 2–4 calls: **23**
- 5–16 calls: **6**
- 17+ calls: **0**

## Set B

- valid closed opportunities measured: **3**
- total recomputation eval calls: **3**
- mean: **1.0**
- maximum: **1**

All three opportunities cost one eval call.

## Conclusion

The Pi-domain target is economically small.

Neither raw reuse frequency nor avoided evaluator work explains the apparent
directional performance on set B; the confirmatory timing difference there is
too large relative to only three single-call reuses and should not be treated
as evidence of a useful Pi-domain optimization.

This closes the Pi-domain branch.

The next high-value search should mine cache misses whose portable consequences
replace **substantial recursive work**, rather than trying to improve activation
for cheap consequences.

Priority target: raw-environment-keyed type inference, whose misses can trigger
recursive inference, evaluation, sort checks and definitional equality.
