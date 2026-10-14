// Read-only MathGraph Check native-evidence preview.
// Trust: exact external SHA-256 of the full, independently admitted recipient
// JSON. Never treat an arbitrary PR-authored status or self-hash as authority.
// No GitHub writes, Cloudflare imports, secrets, or source execution.
import { createHash } from "node:crypto";

const SHA40 = /^[a-f0-9]{40}$/;
const SHA64 = /^[a-f0-9]{64}$/;
const REPO = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;
const SCHEMA = "mathgraph.native-consequence-review-receipt.v1";
export const VERSION = "mathgraph.native-consequence-advisory-preview.v1";

function must(condition, reason) {
  if (!condition) throw Error(reason);
}
function clean(value) {
  return String(value).replace(/[<>]/g, "").replace(/[\r\n]+/g, " ").slice(0, 1200);
}
function neutral(code, scope, body) {
  return {
    schema: VERSION, authority: "ADVISORY_ONLY", promoted: false,
    accepted_receipt: code === "WARRANTED_BOUNDED_NATIVE_EVIDENCE_PRESENT",
    reason: code,
    target: {repository: scope.repository, pr: scope.pr, sha: scope.sha},
    check: {
      name: "MathGraph Check / native evidence scope",
      status: "completed",
      conclusion: "neutral",
      head_sha: scope.sha,
      output: {
        title: code,
        summary: body.slice(0, 60000)
      }
    }
  };
}
export function formatNativeConsequence({ raw, trustedSha256, target, withdrawn = false }) {
  must(Buffer.isBuffer(raw) || typeof raw === "string", "UNSUPPORTED_RAW_RECEIPT");
  const bytes = Buffer.isBuffer(raw) ? raw : Buffer.from(raw, "utf8");
  must(typeof trustedSha256 === "string" && SHA64.test(trustedSha256),
       "EXTERNAL_RECEIPT_PIN_REQUIRED");
  must(createHash("sha256").update(bytes).digest("hex") === trustedSha256,
       "UNAUTHORIZED_RECEIPT_BYTES");
  must(target && REPO.test(target.repository) &&
       Number.isSafeInteger(target.pr) && target.pr > 0 &&
       SHA40.test(target.sha), "INVALID_TARGET_SCOPE");
  const receipt = JSON.parse(bytes.toString("utf8"));
  must(receipt.schema === SCHEMA &&
       receipt.status === "WARRANTED_BOUNDED_HISTORICAL_CONSEQUENCE_RECONCILIATION" &&
       receipt.action_authority === "NONE" &&
       receipt.live_check_published === false &&
       receipt.measured_review_cost_advantage === "NOT_MEASURED" &&
       receipt.generator_self_invention === "NOT_ESTABLISHED" &&
       Array.isArray(receipt.receipts), "RECEIPT_SCOPE_UNAUTHORIZED");
  const found = receipt.receipts.filter(r =>
    r?.subject?.repository === target.repository &&
    r.subject.pr === target.pr);
  if (found.length !== 1) {
    return neutral("UNKNOWN_NO_AUTHORIZED_SUBJECT", target,
      "No separately admitted native evidence for this exact repository and pull request. " +
      "No archived result was attributed across subjects. ADVISORY_ONLY.");
  }
  const item = found[0];
  const { subject, archive } = item;
  must(subject && SHA40.test(subject.base_sha) &&
       SHA40.test(subject.head_sha) &&
       archive && SHA64.test(archive.sha256) &&
       Number.isSafeInteger(archive.artifact_id) &&
       item.action_authority === "NONE" &&
       item.status === "WARRANTED_BOUNDED_HISTORICAL_NATIVE_OBSERVATION" &&
       item.current_upstream === "NOT_CHECKED" &&
       item.full_semantic_fidelity === "NOT_ESTABLISHED",
       "RECIPIENT_RECORD_NOT_WARRANTED");
  if (subject.head_sha !== target.sha) {
    return neutral("STALE_SOURCE_REVISION", target,
      "A bounded historical native receipt exists for " + clean(subject.head_sha) +
      ", but the requested PR head is " + clean(target.sha) +
      ". The old proof is retained; current applicability is UNKNOWN.");
  }
  if (withdrawn === true) {
    return neutral("STALE_EVIDENCE_WITHDRAWN", target,
      "The recipient's trusted policy has withdrawn this evidence. Historical " +
      "native observations remain in its ledger, but no current decision may reuse them.");
  }
  must(withdrawn === false, "UNSUPPORTED_WITHDRAWAL_INPUT");
  const sourceURL = "https://github.com/" + subject.repository + "/pull/" + subject.pr;
  const action = clean(item.next_action);
  let evidence = "";
  if (item.kind === "EXECUTABLE_IMPLEMENTATION_DISAGREEMENT") {
    const w = item.witness;
    must(w && w.reference?.status === "VALUE" &&
         w.base?.status === "VALUE" &&
         w.head?.status === "VALUE" &&
         JSON.stringify(w.reference.value) !== JSON.stringify(w.base.value) &&
         JSON.stringify(w.reference.value) === JSON.stringify(w.head.value) &&
         item.base_mismatch_count >= 1 &&
         item.fixed_head_mismatch_count >= 1 &&
         Number.isSafeInteger(item.unknown_cases),
         "DIFFERENTIAL_WITNESS_NOT_BOUNDED");
    evidence = "**Executable consequence on selected inputs:** base and reference disagree, " +
      "contributor head and reference agree. " +
      "Bounded input: " + clean(JSON.stringify(w.input)) + ". " +
      "Original base: " + clean(JSON.stringify(w.base.value)) + "; " +
      "reference: " + clean(JSON.stringify(w.reference.value)) + "; " +
      "contributor head: " + clean(JSON.stringify(w.head.value)) + ". " +
      "Unknown/incomplete cases: " + item.unknown_cases + ".";
  } else if (item.kind === "PROTECTED_OLD_TEST_CONTRADICTION") {
    must(Array.isArray(item.unchanged_tests) &&
         item.unchanged_tests.length > 0 &&
         item.native_logs_replayed >= 25 &&
         typeof item.causal_controls === "string" &&
         item.causal_controls.includes("RESTORE_RED") &&
         item.unchanged_tests.every(x => /^Test[A-Za-z0-9_]+$/.test(x.test) &&
           typeof x.file === "string" && x.file.endsWith("_test.go") &&
           SHA64.test(x.test_sha256)),
         "PROTECTED_CONTRACT_WITNESS_UNSUPPORTED");
    evidence = "**Conflicting protected evidence:** " +
      item.unchanged_tests.map(x => clean(x.test) + " at " + clean(x.file)).join("; ") +
      ". Original package passed, changed tests passed, unchanged older test failed " +
      "on contributor revision. Suppression of only that older test recovered the package; " +
      "restoration reintroduced the failure.";
  } else {
    throw Error("UNKNOWN_NATIVE_EVIDENCE_KIND");
  }
  const summary = [
    "Historical **source-scoped** observation for " + sourceURL +
    " at " + subject.head_sha + ".",
    "",
    evidence,
    "",
    "**Smallest supported next action:** " + action,
    "",
    "**Underlying original evidence:** archive SHA-256 " + archive.sha256 +
    ", artifact ID " + archive.artifact_id + ".",
    "**Authority:** ADVISORY_ONLY. This is not a source-to-intent proof, " +
    "a finding of an outstanding current bug, or merge authorization.",
    "**Strong equal-information baseline:** a fully informed conventional reviewer " +
    "can obtain the same verdict from original source, CI and native evidence.",
    "**Reviewer time/accuracy/cost advantage:** NOT_MEASURED.",
    "**Current upstream applicability:** NOT_CHECKED."
  ].join("\n");
  return neutral("WARRANTED_BOUNDED_NATIVE_EVIDENCE_PRESENT", target, summary);
}
