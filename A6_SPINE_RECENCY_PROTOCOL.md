# A6 Spine Recency Cache — Frozen Diagnostic Protocol

## Residual

The exact 4K spine front cache was causally useful but net negative:

```text
front vs matched front-lookup ablation:
    -2.0205% median CPU, 28/30 wins

front vs A0:
    +1.3579% median CPU, 3/30 wins
```

Locality showed the 4K front bypassed 90.59% of current `spine_hc` hits.

Therefore the residual is not reuse value. It is activation/index cost.

## Hypothesis

A substantial fraction of exact spine keys may recur within only the last few
`spine_snoc_hc` calls.

If so, an exact tiny recency cache can preserve much of the hash-table bypass
value without:

- computing a front hash;
- indexing a 4K table;
- touching a ~96 KiB front structure.

## Diagnostic

Measure exact key recurrence among the preceding:

```text
1, 2, 4, 8, 16
```

spine calls.

The diagnostic changes no production result. The authoritative `spine_hc`
map still decides every return.

## Frozen promotion rule

The 4K experiment observed:

```text
90.59% capture -> 2.0205% causal CPU gain vs matched control
```

A linear first-order estimate gives approximately 1% gross bypass value at
about 45% capture.

Therefore:

```text
select the smallest K in {1,2,4,8,16}
such that exact last-K recurrence captures >= 45%
of current spine_hc map hits.
```

If no K qualifies, close the tiny-recency direction.

Do not choose a larger K after performance measurement.

## Production experiment if qualified

The candidate stores exactly K full:

```text
(spine key, authoritative S pointer)
```

entries in a tiny recency structure.

A result may be returned only on full exact key equality.

The matched ablation performs the same K comparisons and recency updates but
always falls through to the authoritative `spine_hc` map.

Full frozen semantics and Arena-style PGO remain mandatory before any
performance claim.
