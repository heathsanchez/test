# Korovin V12B — Representation-Adjusted Usefulness Proxy

Frozen before protected V12B task generation.

Source worlds: V10 root `KOROVIN_V10_PUBLIC_COMPLETION_TRANSFER_2026-08-22`, residual-bearing indices 4, 5, 11.
Protected task root: `KOROVIN_V12B_EXPLANATORY_PROXY_2026-08-22`.

Conditions:
- RAW: primitive 4-point generator maps only.
- OBJECT: verified canonical finite object: shortest representatives + complete state×generator transition table.
- SHAM: same object/table dimensions and same representative payload size, but deterministic random transition destinations.

For each source world:
- 400 state-prediction queries, word lengths 100..1000.
- 300 balanced equivalence queries, word lengths 80..500.
- 300 canonical-representative queries, word lengths 100..700.

Cost model:
- RAW primitive transformation update = 4 point-cell operations per token.
- OBJECT/SHAM state transition = 1 table operation per token.
- RAW canonical representative requires outward search from primitive maps; search transitions cost 4 point-cell operations each.
- Description cost is charged once per world: RAW = 8 generator cells + 2 labels; OBJECT/SHAM = state×token destination cells + canonical-representative symbols + 2 labels.
- Leverage = correct answers / (reasoning operations + one-time description cost).

Frozen gates:
G0 exactly worlds [4,5,11].
G1 reproduced state counts [25,79,43].
G2 OBJECT accuracy = 1.
G3 RAW accuracy = 1.
G4 SHAM accuracy < .75.
G5 OBJECT reasoning operations < RAW.
G6 OBJECT leverage > 2× RAW.
G7 OBJECT leverage > SHAM.
G8 OBJECT perfect independently on every world.

Claim boundary:
This is an algorithmic human-facing usefulness proxy measuring exact task leverage and representation-adjusted cost. It is not evidence from blinded human mathematicians.

Local frozen precommit SHA-256: `fc73183d6cafeabf76628e14cf90db9ae22303f3d447bc6a08a09c619a0a6bb0`.
