# V7 Activation Funnel — Result

Run: `34919479898`  
Job: `104224147198`  
Commit: `82d79a35390b513b332d69bbf9da90fbaf642c47`  
Artifact: `10376514855`  
Artifact digest: `sha256:e4d99ef7047f39a631dd6e8369c1c381725e8f3bdc557885f13e26aee1a98617`

This diagnostic changed no V7 decision. It measured where recurrence-gated closed
reuse was actually activated.

## Set A — original 24 held-out cases

- Pi pointer-cache misses: **50,182**
- same-expression seed encounters: **19,088**
- exact consequential environment matches: **438**
- closed reusable matches: **152**
- open exact matches: **286**
- seed collisions: **6,818**
- empty seed slots: **24,276**

Rates:

- same-expression / Pi miss: **38.04%**
- exact env match / same-expression: **2.29%**
- closed reuse / Pi miss: **0.303%**
- closed reuse / exact env match: **34.70%**

## Set B — disjoint next 24 cases

- Pi pointer-cache misses: **1,251**
- same-expression seed encounters: **185**
- exact consequential environment matches: **23**
- closed reusable matches: **3**
- open exact matches: **20**
- seed collisions: **6**
- empty seed slots: **1,060**

Rates:

- same-expression / Pi miss: **14.79%**
- exact env match / same-expression: **12.43%**
- closed reuse / Pi miss: **0.240%**
- closed reuse / exact env match: **13.04%**

## Key conclusion

Raw reuse count does not explain performance:

- Set A had **152** closed reuse events and no confirmed gain.
- Set B had only **3** closed reuse events and showed the stronger performance
  direction in confirmation.

Therefore the next decision variable is the **value/cost of the portable
consequence**, not frequency alone.

The retained developmental question is:

```text
verified portability × avoided recomputation cost > activation/lookup cost ?
```
