# GPU Developmental Hardware Promotion V1 — Frozen Contract

This experiment is a **separate hardware authority gate** for the two finite-IR
transformations already qualified in GPU Developmental Optimization V1:

- `fuse_adjacent_affine`
- `remove_identity`

The finite gate is not modified by this experiment.

## Authority

A Runpod GPU executes Triton kernels using exact `int32` arithmetic over a
fixed 2^22-element input vector.

Correctness authority is bit-exact equality between the cold and transformed
GPU outputs.

Performance authority is the median CUDA-event time after compilation and
warmup, measured over 60 repetitions.

## Frozen comparisons

### Adjacent affine fusion

COLD:

```text
x -> affine(a1,b1) -> global-memory intermediate
  -> affine(a2,b2) -> output
```

WARM:

```text
x -> fused affine a2*(a1*x+b1)+b2 -> output
```

### Identity removal

COLD:

```text
x -> affine(a1,b1) -> identity kernel -> output
```

WARM:

```text
x -> affine(a1,b1) -> output
```

## Primary gate

Both transformed outputs must be bit-exact equal to their cold references.

Both median hardware speedups must exceed 1.05x.

A failure or unavailable GPU remains an explicit hardware obstruction; it does
not invalidate the already-qualified finite-IR developmental result.

## Provider

Runpod Flash provisions an NVIDIA GeForce RTX 4090 endpoint. The workflow uses
only the `RUNPOD_API_KEY` repository secret and does not print the key.
