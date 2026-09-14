# MDA Historical Holdout Audit V1 — frozen before protected logs

This audit is explicitly designed to address overfitting concerns around the recursive-residue kernel.

## Kernel already frozen conceptually

The semantic rule under audit is:

[
\mathcal R_{t+1} =
\begin{cases}
\mathcal R_t, & \text{warrant inadequate},\\
\operatorname{Min}_{\preceq}\{P:A_{\Omega_t}(P)\}, & \text{otherwise}.
\end{cases}
]

The domain-specific adequacy criteria below are not invented by this audit. They are taken from each experiment's pre-existing frozen PRECOMMIT.md.

## Blind-to-this-audit cases

The following four historical protected run logs have not been opened during this audit at the time this manifest and adjudicator are committed:

1. `active_latent_disambiguation_v1`
2. `right_question_transfer_v1`
3. `target_quotient_right_question_v1`
4. `verified_comparative_quotient_v1`

The adjudicator in `scripts/mda_historical_holdout_adjudicator_v1.py` is frozen before those logs are inspected.

## Rules

- Do not edit the adjudicator after seeing these four outcomes.
- Extract only metrics named by the precommits/scorers.
- Store extracted outcomes separately.
- The audit may return RETAIN, RESIDUAL, REJECT, or UNKNOWN.
- Failure/null results are valid and must not be rescued by changing thresholds.
- Claims remain bounded to the original experiment scope.
- Retrospective cases already inspected earlier in the conversation are calibration only and are not counted as blind holdouts.

## Why this is stronger than the recent toy suites

The selected experiments predate the current MDA compression and were designed for different scientific questions. Their protected outcomes therefore cannot have been generated to make the current four-commitment meta-kernel pass.
