# Audit chronology erratum

The file `FROZEN_DOWNSTREAM_PREDICTION.md` was committed before the assistant opened the result of `verified_decision_certificate_v1`, so it is a valid blind-to-this-audit out-of-sample prediction.

However, the historical experiment itself ran **before** Verified Comparative Quotient V1:
- Verified Decision Certificate V1 run: 2026-08-24 23:50 UTC.
- Verified Comparative Quotient V1 run: 2026-08-25 00:26 UTC.

Therefore the test must NOT be described as a temporal downstream prediction in repository-history order. It is a blind cross-experiment transfer prediction made on 2026-09-14.

The prediction failed:
- ONE_SHOT_CERTIFICATE: accuracy 0.8541666666666666; decision-complete 0.75.
- VERIFIED_CERTIFICATE: accuracy 0.7708333333333334; decision-complete 0.6666666666666666.

Per the frozen falsifier, the broader claim that verifier-guided repair transfers from comparative quotient ranking to decision-certificate repair is not warranted. The earlier comparative-quotient result remains scoped to that representation/task boundary.
