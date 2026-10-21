# V7 Question–Source Fidelity Prospect: Frozen before retrieval
Date: 2026-10-21. Motivation: V6 Python base64 chose a padding rule unrelated to target strict-decoding question.

Source lock (unopened in this research lane): https://docs.python.org/3/library/collections.html
Protected question: "When assigning a key through collections.ChainMap, which underlying mapping receives the assignment?"
Required independent source authority: official Python standard library prose, with exact retrieved SHA256; no use of assistant expectations as a source oracle. The ground-truth answer is not an input to the candidate.
Scope: Source text locator/selection only. Automatic interpretation of the answer, authorized witness-program construction, and improvement over skilled humans are separate UNKNOWN gates.

Frozen method:
- Parse HTML text from paragraph-like blocks and their nearest section heading using a small standard-library HTMLParser. Do not execute embedded source code.
- First collect blocks that discuss the query's anchor object "ChainMap"; infer anchor by extracting identifier after final period in "collections.ChainMap" (not semantic answer).
- Use generic predeclared query vocabulary mappings: assign/write/update/set/mutate ↔ write/update/setting/assignment and underlying mapping/map/dictionary. These are vocabulary aids, not possible answers.
- Score source passage lexical overlap plus bonus for an action–object relation, and a proximity expansion to at most one neighboring paragraph. Candidate MUST return source span and position. All code frozen before source fetched.
- Strong conventional baseline: BM25-style full-information lexical paragraph ranking with identical document, query, generic tokens. Independently run baseline and record both selections; these two machine baselines are NOT skilled-human review.
- Independent adequacy predicate, preregistered but not shown to locator as a gold answer: selected source passage must explicitly state which mapping receives assignments/writes and must not only mention ChainMap membership or reads. A post-run human semantic reading of the actual source is the authority; a keyword test alone is insufficient. If unclear => UNKNOWN.
- Only after selection, run a SEPARATE native Python ChainMap mutation oracle on in-memory dictionaries; it checks program behavior but not whether the locator understood the source. Do not mark the locator positive based solely on native behavior.

Native experiment: two dictionaries, create ChainMap(first, second), assign a fresh key through ChainMap, observe which dictionary changes; deliberately remove/adapt neither algorithm after source reveal. Probe does not mutate external source/state.
Controls: meaningless query must abstain from confident obligation; simple read-only references must not be mistaken for assignment authority. Target selection failure remains REJECTED_TARGET_MISS, not optimized posthoc.
No transfer beyond this selected page, no model-generated semantics or human cost advantage. R7.2, CLC, MathGraph Check unchanged and NOT invoked. Stop on network failure, changed URL, source ambiguity, absent native scope, and missing comparable baseline.
