// Read-only exact-head comparison: original MathGraph Check v0 vs native Go test causal witness.
// The existing MathGraph analyzer is IMPORTED UNCHANGED from frozen OPA branch.
// It never runs untrusted PR code and never posts a GitHub Check or PR comment.
import {readFile,mkdir,writeFile} from "node:fs/promises";
import {createHash} from "node:crypto";
import {fileURLToPath} from "node:url";
import path from "node:path";

const here=path.dirname(fileURLToPath(import.meta.url));
const REPO="howlcipher/howlframe", PR=75,
  HEAD="151a033119a6f1acd3c7adce2524ce0768178be9",
  BASE="21efc6cb4742d7ae101288dfc67819bb549c1307";
const VERSION="mathgraph.github-pr-evidence.v0";
const pinnedAnalyzer=path.join(here,"../opa_9216/pinned-analysis.mjs");
const raw=await readFile(pinnedAnalyzer);
function gitBlob(data) {
  return createHash("sha1").update(Buffer.from("blob "+data.length+"\0")).update(data).digest("hex");
}
if(gitBlob(raw)!=="a21d34622f3b283db989462aa4a5a8ef00bcae77")
 throw Error("UNCHANGED_PRODUCT_ANALYZER_SOURCE_IDENTITY_FAILED");
const {analyze,checkOutput,VERSION:actualVersion}=await import("../opa_9216/pinned-analysis.mjs");
if(actualVersion!==VERSION)throw Error("ORIGINAL_PRODUCT_VERSION_MISMATCH");

const root="https://api.github.com/repos/"+REPO;
let requests=0;
async function get(route){
 const h={"Accept":"application/vnd.github+json",
          "X-GitHub-Api-Version":"2022-11-28",
          "User-Agent":"MathGraph-Check-External-Contract-Collision-Research"};
 const response=await fetch(root+route,{headers:h,signal:AbortSignal.timeout(35000)});
 requests++;
 if(!response.ok)throw Error("READ_ONLY_GITHUB_HTTP_"+response.status);
 return response.json();
}
const pr=await get("/pulls/"+PR);
if(pr.head?.sha!==HEAD || pr.base?.repo?.full_name!==REPO ||
   pr.base?.sha!==BASE)throw Error("FROZEN_ORIGINAL_PR_IDENTITY_CHANGED");
let files=[],files_visibility="COMPLETE";
for(let page=1;page<=4;page++){
 const batch=await get("/pulls/"+PR+"/files?per_page=100&page="+page);
 if(!Array.isArray(batch))throw Error("PR_FILE_LIST_INVALID");
 files.push(...batch);
 if(batch.length<100)break;
 if(page===4)files_visibility="TRUNCATED";
}
const ci=await get("/actions/runs?head_sha="+HEAD+"&per_page=100");
if(!Array.isArray(ci.workflow_runs))throw Error("UPSTREAM_ACTIONS_INVALID");
const ci_visibility=ci.total_count>ci.workflow_runs.length?"TRUNCATED":"COMPLETE";
const snapshot={
 repository:REPO,number:PR,sha:HEAD,files,runs:ci.workflow_runs,
 files_visibility,ci_visibility
};
const v0=analyze(snapshot),preview=checkOutput(v0);
const reportPath=path.join(here,"native_evidence/protected_conflict_report.json");
const native=JSON.parse(await readFile(reportPath,"utf8"));
if(native.status!=="WARRANTED_BOUNDED_ORIGINAL_TEST_CONTRACT_CONFLICT" ||
   native.error!==null || native.source.original_base!==BASE ||
   native.source.contributor_head!==HEAD)throw Error("NATIVE_CAUSAL_EVIDENCE_NOT_ADMITTED");
let digests=0;
for(const s of native.steps){
 if(!/^[a-zA-Z0-9_]+$/.test(s.name))throw Error("EVIDENCE_PATH_UNSAFE");
 const log=await readFile(path.join(here,"native_evidence",s.name+".log"));
 const digest=createHash("sha256").update(log).digest("hex");
 if(digest!==s.sha256 || !s.valid_codes.includes(s.exit_code))
  throw Error("NATIVE_LOG_VERDICT_CHANGED_"+s.name);
 digests++;
}
const conflicts=Object.entries(native.unchanged_old_tests_failing_at_contributor_head)
 .flatMap(([pkg,list])=>list.map(q=>({package:pkg,...q})));
if(conflicts.length!==1 || !conflicts[0].original_test_body_unchanged)
 throw Error("SOURCE_GUARDED_CONFLICT_EXPECTATION");
const [problem]=conflicts;
const select=native.native_package_results[problem.package];
if(!select || select.original_base_suite_exit!==0 ||
   select.head_touched_tests_exit!==0 || select.head_full_suite_exit!==1 ||
   select.head_with_only_conflicting_old_test_ablated_exit!==0 ||
   select.head_reinstated_old_test_exit!==1 ||
   select.ablation_recovered_exit!==0)
 throw Error("INCOMPLETE_PROTECTED_CAUSAL_WITNESS");
const oldName=problem.test;
const publicText=[v0.finding.code,v0.finding.next_action,preview.output?.summary||""].join("\n");
const originalMentionsOldTest=publicText.includes(oldName);
const exactUpstreamRun=ci.workflow_runs.find(r=>r.head_sha===HEAD&&r.conclusion==="failure");
const boundedResponse={
 schema:"mathgraph.check.protected-old-test-reviewer-delta.v1",
 provenance:{
  repo:REPO,pr:PR,original_base:BASE,contributor_head:HEAD,
  unchanged_mathgraph_analyzer_git_blob:gitBlob(raw),
  original_native_log_sha256_checked:digests,
  original_external_files:files.length,
  ci_visibility,files_visibility,
  exact_upstream_ci_failure:exactUpstreamRun?{
   id:exactUpstreamRun.id,conclusion:exactUpstreamRun.conclusion}:null
 },
 unchanged_product:{
  version:v0.schema,
  finding:v0.finding.code,
  action:v0.finding.next_action,
  exact_ci:v0.ci.state,
  conclusion:preview.conclusion,
  names_source_original_failing_test:originalMentionsOldTest,
  author_declared_limits:v0.declared_limits.length,
 },
 candidate_source_native_review:{
  status:"WARRANTED_BOUNDED_ORIGINAL_TEST_CONTRACT_CONFLICT",
  source_unchanged_original_go_test:oldName,
  source_path:problem.original_source,
  checked_package:problem.package,
  original_base_entire_package:"PASS",
  contributor_head_touched_test:"PASS",
  contributor_head_entire_package:"FAIL",
  single_original_test_ablation:"PASS",
  exact_original_test_restoration:"FAIL",
  next_action:"Reconcile unchanged fail-closed native test "+oldName+
    " with the new touched serializer contract; do not treat a green touched-test run as full-package verification.",
  conclusion:"neutral",
  authority:"ADVISORY_ONLY",
  actual_upstream_history:"The original maintainer later committed a correction; not an outstanding current branch defect."
 },
 comparative_boundary:{
  incremental_machine_specificity:!originalMentionsOldTest,
  product_semantic_discovery_v0:"NOT_DETECTED",
  full_information_conventional_baseline:"CAN_FIND_SAME_ERROR_FROM_UPSTREAM_FAILED_CI_AND_LOGS",
  human_reviewer_accuracy_advantage:"NOT_MEASURED",
  review_time_savings:"NOT_MEASURED",
  arbitrary_go_or_wasm_semantic_mapping:"UNKNOWN",
  common_generator_portable_to_OPA_C_YAML:"NOT_ESTABLISHED",
  new_mathgraph_production_code:"NONE",
  upstream_repository_writes:"NONE",
  external_outreach:"NONE"
 },
 measurement:{public_GitHub_reads:requests}
};
if(!exactUpstreamRun || v0.ci.state!=="NOT_ALL_CURRENT_CI_GREEN" ||
   v0.finding.code!=="CURRENT_HEAD_CI_UNRESOLVED" ||
   preview.conclusion!=="neutral")
 throw Error("CONVENTIONAL_CI_BASELINE_NOT_ESTABLISHED");
const out=path.join(here,"native_evidence/check_v0_vs_native_report.json");
await mkdir(path.dirname(out),{recursive:true});
await writeFile(out,JSON.stringify(boundedResponse,null,2)+"\n");
console.log("PROTECTED_TEST_REVIEWER_DELTA "+JSON.stringify({
 original_product_finding:v0.finding.code,
 original_product_named_failing_test:originalMentionsOldTest,
 native_named_failing_test:oldName,
 upstream_CI_status:exactUpstreamRun.conclusion,
 approved_native_log_digests:digests,
 reviewer_advantage:"NOT_MEASURED",
 no_source_write:true
}));
