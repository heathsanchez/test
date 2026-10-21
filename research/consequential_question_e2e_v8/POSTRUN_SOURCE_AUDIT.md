# V8 independent source-target audit — false positive despite native GREEN

The source-to-question selection selected GitHub Actions run #39540174396 block 25:
"Push item on the heap, then pop and return the smallest item from the heap. The combined action runs more efficiently than heappush() followed by a separate call to heappop()."

This passage is about combined operation **heappushpop**, not the selected protected question **heappop**. It mentions heappop only as a comparator; the lexical locator admitted it because it contained the name and pop/return words. Source-to-question warrant is therefore **REJECTED_TARGET_OPERATION_MISMATCH**. The native heapq.heappop experiments happened to agree with the phrase's "smallest" prediction on both controlled lists, but those outcomes cannot repair the missing source authority link.

The official source SHA was 7654a778bbf6568d63797413005323f0f8ee3f49ccdd824c2c762bb0a86f29c0. Freeze-before-source method head 361f793d9521be4564308952eb5a4e4912fc064b (unchanged). Strong coded baseline also returned the minimum on two native trials; it is not a blinded human comparison and did not independently adjudicate the chosen passage. Both native observations remain valid but do NOT warrant source-faithful inquiry.

Verdict:
- CI execution integrity: GREEN.
- Source/question correctness: REJECTED on this exact selected passage.
- Native min-return outcome: WARRANTED only for 2 specified input lists.
- Full consequence-to-source alignment: REJECTED for V8.
- General semantic acquisition and advantage over expert: UNKNOWN.

This negative preserves prior V6 failure lineage: lexical overlap can select a true but irrelevant source assertion. Do not patch candidate and call V8 prospective success. A next version must precommit claim-identity/operation-role alignment and compare against a semantic fully informed reviewer on a genuinely new source.
