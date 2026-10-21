# Structural Obligation IR V1 — pre-code, pre-third-source freeze (2026-10-21)

Objective: replace a CHECK-only result label with a generic, source-span-grounded `(authority, condition, required_effect, witness, verification_status)` record. Existing R7.2, CLC and MathGraph Check remain unmodified and are NOT claimed integrated by this experiment.

TRAINING (EXPOSED) official SQLite docs: CREATE TABLE CHECK passage and FOREIGN KEY section 4.3 ON DELETE CASCADE passage. Candidate IR extraction is **human-authored finite grammar** and may use these exposed sources for development. Require controlled native SQL witness under sqlite3 for each training family; do not pretend native verification creates independent normative intent.

THIRD SOURCE (LOCKED BEFORE OPEN): https://www.sqlite.org/lang_createtrigger.html ; challenge family: CREATE TRIGGER behavior/effect, distinct from CHECK and CASCADE. Freeze the same IR extractor bytes and output schema before fetching. Never add trigger-specific patterns after reveal. If parser cannot extract an unambiguous source-span-backed condition/effect, return UNKNOWN; if it extracts but no existing safe native witness constructor matches, return UNKNOWN_UNSUPPORTED_WITNESS instead of an invented action. If extracted semantics contradict original text or native oracle, preserve RED.

No new grammar TYPE invention, no measured human baseline, no claim of source-independent mathematical intent from a string extraction.
Comparator: fully informed conventional manual parsing + native SQLite test, present but NOT measured unless actually executed. Do not claim advantage against this.
Success levels: (1) EXPOSED training IR compiled and natively qualified, (2) THIRD-SOURCE IR only if exact text supports it, (3) third-source native witness only if frozen witness grammar applies, (4) downstream comparative cost separately measured.
Source URL and retrieved SHA256 retained, approved HTTPS only, no user data/secrets, native SQLite in-memory isolated, rollback and restoration.
