# Current Environment Capacity Retention Atlas — Result

Run: `34931781774`  
Job: `104261313015`  
Official sokonanoda pin: `28c03d0103e004610e4d47a4828965efb2b70af9`

## Verdict

```text
NO_TABLE_QUALIFIES
```

The diagnostic was semantic-only and the complete frozen oracle remained green.

## Frozen promotion rule

A table qualified only if, on `perf/grind-ring-5`:

```text
discard_count >= 2
```

Then the highest prior Callgrind-cost qualifier would be selected in the fixed
order:

```text
wide_prune > env_hc > frames
```

No table passed.

## grind-ring-5

Session clears: **9**

### env_hc

- actual inserts: **917,828**
- capacity growth events: **15**
- maximum capacity: **917,504**
- oversized capacity discards: **1**
- largest discarded capacity: **917,504**

### frames

- actual inserts: **1,060,555**
- capacity growth events: **15**
- maximum capacity: **917,504**
- oversized capacity discards: **1**
- largest discarded capacity: **917,504**

### wide_prune

- actual inserts: **768**
- capacity growth events: **6**
- maximum capacity: **896**
- oversized capacity discards: **0**

## Controls

No table crossed the discard threshold in `init-prelude`, `app-lam`, or
`shift-cascade`.

## Interpretation

The current rehash hotspot is **not** primarily repeated session-reset amnesia.

The heavy environment tables do learn very large capacities, but on
`grind-ring-5` each oversized table is discarded only once despite nine
session clears. Retaining that capacity would therefore not explain the major
rehash cost measured by Callgrind.

The dominant cost is growth/probing **inside the large session itself**.

The next target is the hottest exact authoritative map with the simplest
already-earned identity:

```text
env_hc : (parent pointer, value pointer) -> Env
```

Current Callgrind attributes:

- `env_extend`: **5.231%** self instructions
- exact `env_hc` rehash path: **3.139%**

for roughly **8.37%** combined visible structural cost.

No pull request is authorized or created by this result.
