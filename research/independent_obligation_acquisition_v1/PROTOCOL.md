# Independent authoritative requirement acquisition V1 — frozen before source retrieval

Date: 2026-10-21. This experiment is distinct from synthetic SQLite V1/V2.
**Source owner:** SQLite project documentation (independent of MathGraph).
**Selected source:** https://www.sqlite.org/lang_createtable.html
**Selection rule:** first relevant *CHECK constraint* normative sentence in document order matching one of the fixed semantic templates below. No switching pages or source after outcome.
**Source risk:** live official HTML not commit-pinned before access; record SHA256/URL/UTC retrieval and fail CLOSED if missing, if parser uncertain, or if source text not attributable. Do not infer universal permanence from snapshot.

## Fixed templates and negative controls
1. CHECK expression evaluates to zero -> constraint violation (zero rejected).
2. CHECK expression evaluates to nonzero -> constraint satisfied (nonzero admitted).
3. CHECK expressions may not contain a subquery -> subquery DDL rejected.
Only explicit text in CHECK section is authoritative; hypothetical/troubleshooting/negated instructions are excluded. Any other requirement -> UNKNOWN, no hand-authored obligation target injected into compiler.
The compiler is a human-authored finite grammar and native witness-template library, NOT autonomous language understanding or discovery of new operation TYPES.
Construct witness SQL directly from the extracted clause. Candidate observations must run in fresh in-memory SQLite with rollback or disposable DB only. No production source changes.

## Comparators
(a) SQLite baseline direct native test designed by a fully informed conventional engineer given identical text; coded reference templates are NOT an actual measured human study. Where no human timed trial exists, advantage UNKNOWN.
(b) A native direct query may be cheaper; count execute calls but no cost superiority from single illustrative setup.
(c) Independent oracle is SQLite engine outcome; it confirms observed behavior, not that prose interpretation was unique.

## Protected decision
Determine if native SQLite rejects CHECK predicate evaluating to zero. No hardcoded expected result may be passed into the compiler; accepted/rejected oracle expectation must be parsed from source sentence. A source sentence that does not map unambiguously results in UNKNOWN.

## Stop
Freeze this file + algorithm before reading the official document. No source-specific post-hoc edits after seeing the page; preserve negative, stop instead of tuning. R7.2, CLC, MathGraph Check remain untouched and not invoked end-to-end.
