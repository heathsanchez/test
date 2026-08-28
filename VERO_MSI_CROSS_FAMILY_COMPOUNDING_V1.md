# Verified cross-family developmental compounding — V1

This experiment tests whether a structure independently verified in one formal-proof family can causally enlarge the later verified proof frontier on a source-distinct family under a frozen new-construction budget.

The external verifier is Lean, executed with `lake lean` inside the Vero Galoistools benchmark sandbox.

Executable test:

- `.github/scripts/vero_msi_cross_family_compounding_v1.py`
- `.github/workflows/vero-msi-cross-family-compounding-v1.yml`

Decisive run: `33149206252`.

## Source development

The source family is lower-level convolution scaling. Lean independently verifies the retained substrate:

1. modular scalar transport (`add_mod_unreduce`, `mul_left_reduce`, `add_scaled_mod`, normalization lemmas);
2. scaling through `Galoistools.zipAddPad`;
3. left-scaling through `Galoistools.convolve`.

The source artifact is retained only after the complete source file passes Lean.

## Source-distinct target

The later target is the higher-level theorem `gfMul_scale_both_target`, proving two-sided scaling transport through `Galoistools.gfMul`.

The target requires the retained lower-level substrate plus four genuinely new support groups:

1. right-scaling through convolution;
2. two-sided convolution scaling;
3. scaling transport through `gfStrip` under the required zero-preservation condition;
4. reverse/map scaling transport.

All arms use the same target theorem, same Lean verifier, same candidate extension order and the same budget of **four new support groups**.

## Arms

- **WARM** — retains the independently Lean-verified source substrate.
- **COLD** — begins without source substrate.
- **RAW_HISTORY** — source outcome history is not installed as executable lemmas.
- **SHAM** — receives a matched-count irrelevant verified artifact.
- **ANCESTOR_ABLATION** — source development occurs but the retained substrate is removed before the target episode.

## Exact result

| arm | target verified within 4 new groups | new groups used |
|---|---:|---:|
| WARM | **yes** | 4 |
| COLD | no | 4 |
| RAW_HISTORY | no | 4 |
| SHAM | no | 4 |
| ANCESTOR_ABLATION | no | 4 |

The WARM target trace is:

```text
source retained: scalar_mod + zip_transport + convolve_left
new 1: convolve_right    -> target still fails
new 2: convolve_both     -> target still fails
new 3: strip_transport   -> target still fails
new 4: reverse_transport -> target verifies
```

The COLD/RAW/SHAM/ABLATION traces spend the same four-new-group budget rebuilding only through `convolve_right`; they cannot reach the remaining target-specific bridges before the budget closes.

Strict gate:

`PASS_VERIFIED_CROSS_FAMILY_DEVELOPMENTAL_COMPOUNDING`

## Causal statement

Let `D₁` be the source convolution-scaling episode, `K₁` the Lean-certified retained substrate, and `D₂` the higher-level `gfMul` target episode. Under the frozen four-new-group budget `B=4`:

\[
\boxed{
\operatorname{VerifyReach}_B(D_2 + K_1)=\text{true}
}
\]

while

\[
\boxed{
\operatorname{VerifyReach}_B(D_2)=
\operatorname{VerifyReach}_B(D_2+\text{raw})=
\operatorname{VerifyReach}_B(D_2+\text{sham})=
\operatorname{VerifyReach}_B(D_2+K_1-K_1)=\text{false}.
}
\]

Thus a verified developmental product from one theorem family becomes causal substrate for a later source-distinct theorem family.

## Claim boundary

The downstream theorem and all support constructions remain expressible in the supplied Lean language. This experiment therefore establishes **verified capability/discovery compounding and reusable proof-substrate transfer**, not new syntactic formability, new tactic invention, or unrestricted theorem-proving self-extension.

It is nevertheless stronger than simple proof reuse: exact ablation of the retained source development restores the cold later frontier under the matched construction budget.