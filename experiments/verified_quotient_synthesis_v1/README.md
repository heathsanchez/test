# Verified Quotient Synthesis V1

Tests whether verifier-guided repair can synthesize the future-relative quotient that previously unlocked near-optimal right-question selection.

The candidate representation is deliberately small and executable: for each available query and possible query outcome, list the target values still possible. Python checks the candidate exactly against the full surviving hypothesis set, returns missing/spurious target values as counterexamples, and permits at most three repairs after the initial proposal.

Downstream query selection is deterministic from the candidate quotient, so the scientific variable is representation construction rather than another LLM decision call.
