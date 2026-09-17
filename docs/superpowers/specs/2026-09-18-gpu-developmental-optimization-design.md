# GPU Developmental Optimization V1 — Design

## Question
Can optimization of earlier compute kernels leave behind a verified, conditional optimization capability that causally reduces the search required to optimize untouched later kernels while preserving exact frozen correctness requirements?

## Domain
Phase A/B uses a hardware-independent kernel IR so the causal hypothesis can be tested prospectively without assuming a CUDA GPU is available. Kernels are finite array computations with reference semantics and explicit cost features representing memory traffic, intermediate materialization, passes, and synchronization. A later hardware promotion may compile the same retained transformations to Triton/CUDA when a GPU runner is available.

## Retained capability
A capability is `(applicability_signature, transformation, correctness_obligation, measured_cost_effect, dependencies)`. It contains no target kernel identity or target answer. Candidate transformations include fusion, redundant-intermediate elimination, algebraic reassociation where exact semantics permit it, layout-aware traversal, and specialization. Only transformations that pass the reference verifier and improve the frozen cost metric may be retained.

## Prospective split
Training/source kernels and target kernels are generated from disjoint sealed seeds. Target kernels are generated only after the transformation family, cost model, scorer, and retained Phase-A capabilities are frozen.

## Arms
COLD searches the full frozen transformation family. WARM begins with retained applicable capabilities, then may search if needed. RESTART reloads only serialized capabilities. SHAM receives matched capabilities whose applicability signatures do not causally help the target family. ABLATION deletes the exact retained transformation/dependency claimed to cause the gain.

## Primary gate
Every arm must produce verifier-equivalent target kernels. WARM total developmental search cost must be lower than COLD, SHAM, and ABLATION; RESTART must reproduce WARM; exact ablation must restore the cold frontier on cases whose gain depends on the retained capability. Execution cost improvements are reported separately from developmental search cost.

## Interpretation boundary
A pass establishes finite verified developmental optimization in the frozen kernel IR. It does not by itself establish CUDA/Triton speedups or GPU hardware performance. Hardware promotion is a separate claim.