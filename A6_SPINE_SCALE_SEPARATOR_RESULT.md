# A6 Spine Scale Separator — Result

## Result

Run: `34926408611`  
Job: `104245308579`  
Head: `1c324790eea051ce83a782c21cc06374dae4dace`  
Artifact: `10380425017`  
Artifact digest: `sha256:42d14b803cb4eb4cf8a2b888ca64e6e0432cec57aab7cbb5ec6a0a262b05a5ae`

The diagnostic changed no production result and the frozen semantic replay was
green.

## Frozen feature

```text
peak baseline spine_hc exact-entry count
```

## Development scale

Prior-positive cases:

- `init-prelude`: peak **5,279**
- `perf/grind-ring-5`: peak **773,767**

Prior-control cases:

- `perf/app-lam`: peak **64**
- `perf/shift-cascade`: peak **11**

Therefore:

```text
min(positive) = 5,279
max(control) = 64

5,279 > 64
```

The preregistered separator rule succeeds.

## Frozen threshold

Per protocol:

```text
THRESHOLD = max(control) + 1 = 65
```

No other threshold is admissible in the first adaptive-representation
experiment.

## Held-out scale prediction

Using the already-frozen threshold of 65:

- **6 / 24** held-out cases would activate the raw prehashed representation.
- **18 / 24** remain entirely on the existing A0 `FxHashMap`.

Held-out scale was not used to select or alter the threshold.

## Interpretation

The prior performance separator now has a simple representation-level
explanation:

```text
small spine interner -> existing FxHashMap
large spine interner -> exact prehashed HashTable
```

The smallest prior case that demonstrably benefited from the raw representation
is over **82× larger at peak** than the largest development control:

```text
5279 / 64 ~= 82.5
```

This is enough evidence to test a reversible per-session representation
transition at the frozen 65-entry boundary.

It is not evidence that 65 is globally optimal. The first hybrid experiment is
specifically a test of the preregistered smallest separating threshold.
