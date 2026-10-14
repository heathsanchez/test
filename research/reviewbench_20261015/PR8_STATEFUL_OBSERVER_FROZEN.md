# FROZEN POST-SOURCE OBSERVER — ReviewBench PR8, 2026-10-15

This secondary contract is frozen **AFTER inspecting the exact pinned corpus head** but **BEFORE authoring native test/repair code**. It does not claim fully blind automated new-method invention. Original PR title and current upstream PR's evolving patch were visible; the independently published ReviewBench golden must remain SEALED until the original result, candidate patch, causal removal and reviewer candidate narrative are committed.

## Exact source and independent consumer
ReviewBench test index 8 mirror repo `review-bench/brexhq_CrabTrap`, immutable head `5ef0884c59b3ee1d5a986dd02686a8232570c80f`, immutable base `b29930e93765700608313c0f0d32c4818734e158`. Actual frontend `web/src/stores/auditStore.ts` and `web/src/hooks/useAuditLog.ts` are native source; do not manually replace their semantics in the test. Original package has Zustand and TypeScript dependencies. Only in-memory store is instantiated; no API, database, SSE server or external service.

## Consequential requirement and provenance
PR body declares audit log pagination and live UI. Application store `addEntry` is called from SSE; `loadMore` queries offset plus page size, concatenates existing entries with next page; hasMore is declared `entries.length < total`. The collection/observational contract is conditional: **when a new unique latest entry arrives during pagination, a duplicate fetched item must not cause the UI to mark completion before the older entries were loaded.** This is a plausible user-facing requirement derived from source usage, not a confirmed maintainer-specified policy.

## Frozen adversarial action sequence
Server original ordering A,B,C,D (unique IDs sorted newest→oldest), page limit 2. Initial GET offset0 returns [A,B], total4. Incoming SSE newer unique X makes server order X,A,B,C,D and pushes X into store (total5). Next GET offset2 returns [B,C]. Actual original store `setEntries([...current,..page2],total5,offset2,limit2)` now may contain duplicate B and incorrectly mark hasMore false before unseen D. Independently compare a no-SSE control, and an SSE+dedup candidate.
- Check original source native module with actual TypeScript transpiler and Zustand import. Baseline app behavior must first be recorded, not guessed.
- Candidate patch is a generic stable-identity set deduplicator applied to `setEntries`, with id first and (request_id,timestamp) fallback. No external upstream commit. Test expected repair: after page2 [X,A,B,C], hasMore true; offset4 page3 includes D, final [X,A,B,C,D], hasMore false.
- Restore original file bytes *exactly* after candidate check, rerun, require old failure persists. No assertion is based on hidden ReviewBench golden.
- Negative: no-SSE [A,B]+[C,D] completes normally.
- Pure frontend-state test, NOT native Go API/DB/SSE delivery integration. This cannot establish production failure frequency or other event timings. Repair may be insufficient for late or backfilled SSE events, concurrent request races, or snapshot changes; do not claim universal pagination safety.
- Strong competitor comparison ONLY AFTER original evidence commit: read published ReviewBench golden for task 8 and report whether a producer caught same failure. A golden miss doesn't prove MathGraph superiority because this is human-informed test, and model capabilities/inputs differ.

## Stop rule
If original native store does not show the specified failure, mark hypothesis REJECTED. If original RED, patch GREEN, restoration RED with source identity and no-SSE control, mark `WARRANTED_BOUNDED_RETROSPECTIVE_FRONTEND_STATE_COUNTEREXAMPLE`; classify product reviewer advantage UNKNOWN regardless until a true matched reviewer trial.
