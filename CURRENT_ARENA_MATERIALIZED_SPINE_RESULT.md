# Current Arena Materialized-Key Spine Transfer — Result

Run: `34930557381`  
Job: `104257690312`  
Artifact: `10381219791`  
Artifact digest: `sha256:1c40abbcdd3a777586c801e78dea31a4b36c17956abb14e5951ea6aee5f0b56d`

## Verdict

```text
CURRENT_MATERIALIZED_STOP_DEVELOPMENT
```

## Frozen official baseline

```text
intgrah/sokonanoda
28c03d0103e004610e4d47a4828965efb2b70af9
```

No A6 patch was applied.

## Semantics

All three arms passed exactly:

- current official baseline: 103 / 103 good, 58 / 58 bad
- S-only raw prehashed table: 103 / 103 good, 58 / 58 bad
- materialized-key raw table: 103 / 103 good, 58 / 58 bad

## Development economics

30 paired randomized-order repetitions over the frozen four-case development
workload.

Materialized-key raw vs current official baseline:

- median paired CPU delta: **+0.0977%**
- wins: **13 / 30**

S-only raw vs current official baseline:

- median paired CPU delta: **+1.2801%**
- wins: **4 / 30**

Materialized-key raw vs S-only raw:

- median paired CPU delta: **-1.2525%**
- wins: **24 / 30**

Median CPU:

- current: **1.800109 s**
- rawkey: **1.807711 s**
- raws: **1.822997 s**

The development admission rule therefore failed and held-out was correctly not
run.

## Interpretation

Materializing the exact key remains a real improvement over the S-only raw
representation, reproducing the mechanism discovered on A6.

However, on the current official upstream lineage, replacing the existing
`FxHashMap` authoritative spine interner no longer pays overall.

Therefore:

```text
identity materialization is not the current Arena frontier
```

The correct next step is to profile the current official checker itself and
localize its present dominant residual before proposing another optimization.

No pull request is authorized or created by this result.
