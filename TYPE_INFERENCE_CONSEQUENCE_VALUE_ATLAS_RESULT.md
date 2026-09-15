# Type-Inference Consequence Value Atlas — Result

Run: `34919925962`  
Job: `104225522830`  
Commit: `c456098b58fb833457e2eac711d2626d524afcc5`  
Artifact: `10377782498`  
Artifact digest: `sha256:259e7af5b1266999ee19c74b0c376f9f6ce70afbeadfa6f7c0745c229230f17e`

The atlas was shadow-only. Existing `type_cache` remained authoritative.

The dependency-complete shadow identity included:

- expression;
- inference/check mode;
- universe-check scope;
- projected environment mask and level substitution;
- already-earned representatives of projected environment values;
- already-earned representatives of exactly the local context types addressable
  by the expression's loose variables.

## Frozen corpus result

Across **199,747** real type-cache misses:

- dependency-complete repeated signatures: **253**
- recursive inference calls spent on those repeats: **1,359**
- mean recursive inference calls per repeat: **5.37**
- maximum for one repeat: **22**
- measured repeated-miss time: **163,781 ns** total
- maximum measured repeat: **2,213 ns**
- repeated results that were closed: **253 / 253**

Root expression classes:

- App: **191**
- Pi: **62**
- Lambda: 0
- Let: 0
- Proj: 0

Cost distribution:

- 1 call: 0
- 2–4 calls: **149**
- 5–16 calls: **98**
- 17–64 calls: **6**
- 65+ calls: 0

## Concentration

The repeat opportunity is extremely concentrated:

### grind-ring-5

- repeats: **142**
- recursive inference calls: **876**
- mean: **6.17**
- max: **22**

### init-prelude

- repeats: **110**
- recursive inference calls: **481**
- mean: **4.37**
- max: **17**

### all other 101 good cases combined

- repeats: **1**
- recursive inference calls: **2**

## Conclusion

Type inference is a real but narrow portable-consequence frontier. It is
strictly more valuable than the conversion frontier, but its total avoided work
is still modest and almost entirely concentrated in two workloads.

Do not implement another cache layer yet.

The next atlas should search at a higher consequence granularity where one
portable result can eliminate whole reduction/proof-checking subcomputations.
