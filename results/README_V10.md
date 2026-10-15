# ARC400 V10 gate semantics

The V10 gate is deliberately stricter than V9.  The learned residual representation must support explicit abstention (`BOT`) as well as constructor predictions (`S`,`B`).  A constructor prediction counts only when its post-hoc finite-carrier oracle label agrees and the extension produces an exact causal solve.  The decisive anti-overgeneralization checks are zero false non-BOT predictions on both held-out training and source-distinct evaluation.

All negative and completeness claims are relative to the declared finite observable carrier and constructor carrier `{U,S,B}`.
