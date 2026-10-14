# ReviewBench reviewer-input remediation uplift — frozen V1

Date 2026-10-15 NZ. This is a retrospective strong-reviewer evidence-augmentation experiment. Existing native obligation/witness/repair capabilities are already qualified; this is not discovery of a new general mechanism or L7.

Original independent reviewer producer: llm_review:claude-sonnet-4.6, published under review-bench/ReviewBench revision 5bba258937cc7d43577ce9a81a389a6550a20fa9. Its original comments are proposal input, NOT the gold TP/FP adjudications. No paid model inference in this trial.

Subjects, frozen before writing native fixtures:
- ReviewBench test index 18, allan-mobley-jr/gimmes PR 468. Original HEAD e1477f8b3f18c1de6ff87dbca9465a7b106dc193, base 08efd0bbc34fd29de2a4077f07d24f3dc02a63b6. Strong reviewer identifies misleading fallback from zero 24-hour volume to historical cumulative volume, marking inactive markets active. Normative bound is explicit function docstring: unchanged price, low recent activity and unchanged OI trigger staleness. Separate strong reviewer complaint about absolute volume thresholds is a different policy question, not automatically proven false.
- ReviewBench test index 21, scottlz0310/Mcp-Docker PR 29. Original HEAD e7705d269ea374d49e7999bdb8bc42e9480a6b37, base 63baf3dbbc10d271710706f56150dd8425dd4b4a. Reviewer identifies optional PKCE S256 at authorization and code exchange. Here the *assumed security contract* requires PKCE; broader public OAuth client policy is UNKNOWN.

Protected protocol:
1. Review-only is a static already-issued strong review: no executable receipts, no fresh model run, no economic comparison.
2. Reviewer + MathGraph-style evidence uses ORIGINAL source clones pinned by SHA; human-written typed native test is the observer and human-written candidate repair is recorded as such. No original upstream writes.
3. Run exact original native RED, human repair GREEN under protected positive/negative cases and original targeted suite, physically restore original source file bytes to reproduce RED; negative sources/incorrect identities fail closed; all original test fixture files removed.
4. Admit only bounded native test/repair receipts; explicit UNKNOWN if original tests fail, identity not checked, lack of source contract, or removal does not reproduce failure.
5. Record proposed finding, exact original subject+method, test result, repair change, source SHA, raw log, run/compile cost and evidence lineage. The trial does not measure a live strong tool-using coding agent with equal verification tools. No leaderboard position or general reviewer superiority.
6. No production App, Cloudflare, public package, upstream repo writes, code-review comments, outreach, Gmail or Render.

Python observer cases: historical volume positive but recent volume zero; current active volume; exact volume floor; price change; OI change; truly inactive zero volume. Candidate removes fallback to cumulative history. Missing/unreliable 24h metrics still UNKNOWN.

Go observer cases: missing challenge must be rejected both at authorization and exchange; valid S256 verifier must redeem once; wrong verifier fails. Candidate requires PKCE in authorize and code exchange. This is a scoped policy, not a proof of universal OAuth compatibility.

If both scoped tests pass, reviewer-input-to-native-remediation is bounded warranted (human-authored). The independent strong-model comparative benefit, fully charged economics, L7 and general adoption remain UNKNOWN. Do not rerun previous ReviewBench #9/#8 or the old SortedDict/OrderedSet examples.
