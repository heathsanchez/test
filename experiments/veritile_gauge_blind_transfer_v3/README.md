# VeriTile frozen-capability blind transfer v3

## Frozen capability boundary

The generic capability was committed **before this target was selected**:

- source branch: `veritile-gauge-transfer-v2`
- capability commit: `9fa6a451eea2cb68004ce0934ee565763ad7c109`
- theorem: `MathGraphGaugeCapability.common_factor_ratio`
- law: a shared nonzero multiplicative factor is invisible to a normalized ratio.

No changes to the capability are permitted in this experiment.

## Target selection

After the capability was frozen, the pinned VeriTile tree was searched for
independent online-softmax closed-form bridges using direct common-factor
cancellation (`mul_div_mul_left`). A distinct CSR-gathered causal-attention
family was selected:

`bench/tritonbench_g/block_sparse_attn/BlockSparseAttn.lean`

Frozen upstream revision:
`Lizn-zn/VeriTile@95a01f598e2cd1cac4052e5e5ff9145c658e18db`.

The target's existing `bsaStreaming_eq_bsaAttn` bridge proves that the
streaming block-sparse online-softmax ratio equals its gathered closed-form
attention. Its final semantic step is exactly cancellation of the same
nonzero `exp(-m)` factor from numerator and denominator.

## Experiment

Append a new theorem with the same consequence, but:

- do not call `bsaStreaming_eq_bsaAttn`;
- retain the target's own streaming-to-m-shifted lemmas;
- use the **already-frozen** `common_factor_ratio` for the normalization step;
- finish with the target's existing m-free closed-form bridge.

The identical appended theorem must fail without importing the frozen
capability and pass when the capability is imported.

A green result is a stronger transfer test than V1/V2 because the reusable
capability is frozen before target selection and the target is a third,
structurally different kernel family.
