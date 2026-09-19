# GPU Developmental Hardware V1 — Qualified Result

Authoritative GitHub Actions run:
https://github.com/heathsanchez/test/actions/runs/35412218742

Artifact:
`10574349230`

Artifact digest:
`sha256:b386f11d3af43d20722bb10d5cce37726a9909df79f0b4d042655cf968801873`

Head SHA:
`e7a2dfd472fc33aeeefa6d675a8b5416050aeee2`

## Hardware authority

Runpod Flash provisioned an **NVIDIA GeForce RTX 4090** and executed the frozen
Triton promotion gate for the two transformations already earned in the finite
GPU-kernel IR experiment.

Environment:

- GPU: NVIDIA GeForce RTX 4090
- compute capability: 8.9
- PyTorch: 2.9.1+cu128
- Triton: 3.5.1
- dtype: int32
- elements: 4,194,304
- warmup iterations: 12
- measured repetitions: 60

Both transformed outputs were bit-exact equal to their cold references.

## Measured result

### Adjacent affine fusion

Cold:

```text
affine(a1,b1)
→ global-memory intermediate
→ affine(a2,b2)
```

Warm:

```text
fused affine a2*(a1*x+b1)+b2
```

Median:

- two-pass: **0.038112 ms**
- fused: **0.025568 ms**
- speedup: **1.4906×**

### Identity removal

Cold:

```text
affine(a1,b1)
→ identity kernel
```

Warm:

```text
affine(a1,b1)
```

Median:

- affine + identity: **0.038768 ms**
- identity removed: **0.024576 ms**
- speedup: **1.5775×**

## Qualification

The frozen hardware gate required:

- CUDA available;
- bit-exact correctness for both transformations;
- median speedup > 1.05× for both.

All gates passed.

Marker:

`PASS_GPU_HARDWARE_AUTHORITY_V1`

## Claim boundary

This is measured RTX 4090 / Triton evidence for the two exact retained
transformation shapes only. It does not establish universal GPU optimization,
portability to every GPU architecture, or that the finite structural cost model
predicts every hardware workload.

It does close the specific authority gap left by GPU Developmental Optimization
V1: the two verified IR capabilities were promoted to real hardware and produced
measured improvements while preserving exact frozen semantics.
