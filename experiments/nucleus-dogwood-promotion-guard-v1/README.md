# Nucleus × Dogwood promotion guard v1

This experiment binds Dogwood's temporal authorizer to one real Nucleus residual lineage.

Pinned Nucleus authority: `98f87d9e66fb97987427d68180f51a653d626fdb`.
Pinned frozen Arena corpus: artifact `10712869614` (193 cases).
Pinned residual evidence: run `36638671203`, artifact `11065053909`, digest
`sha256:15313a7fc30156ad75e090866a6d72510cc5194bd5dabc882110aaa182b0ff5e`.
That evidence contains 30 residual cases, including exactly 11
`application-function-type` cases.

The Dogwood gate permits `Admit` only when the same candidate/authority/corpus/evidence
lineage has, in order, observed the residual, derived the candidate, passed controls,
and passed full reclosure. Any matching rejection blocks admission.

This is a governance qualification only. It does not promote a new Lean-kernel
semantic rule and it does not change the Nucleus checker.
