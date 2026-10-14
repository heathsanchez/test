// Exact unchanged MathGraph Check v0 vs original outside-owner pull request.
// Read-only PR/Actions access; NO external Check/PR write, LLM judgement or fitted source adapter.
import {readFile,writeFile,mkdir} from "node:fs/promises";
import {pathToFileURL} from "node:url";
import {resolve,dirname} from "node:path";
import {createHash} from "node:crypto";
import {performance} from "node:perf_hooks";
const repo="open-policy-agent/opa",prNumber=9216;
const HEAD="d231b0381efd880597db736efdd74e6681000b54";
const PARENT="37030a09d6088821a473f486fd75dd81ef394b74";
const URL="https://api.github.com/repos/"+repo;
const main=await import(pathToFileURL(resolve(process.argv[2]||"research/aria_scaling_trust/opa_9216/pinned-analysis.mjs")).href);
if(typeof main.analyze!=="function"||typeof main.checkOutput!=="function"||
main.VERSION!=="mathgraph.github-pr-evidence.v0")throw Error("PINNED_ANALYZER_IDENTITY");
const access=process.env.GH_PUBLIC_TOKEN||"";
let calls=0;
async function get(path) {
  const headers={"Accept":"application/vnd.github+json",
    "X-GitHub-Api-Version":"2022-11-28","User-Agent":"MathGraph-heldout-evaluation"};
  if(access)headers.Authorization="Bearer "+access;
  const response=await fetch(URL+path,{headers,signal:AbortSignal.timeout(15000)});
  calls++;
  if(!response.ok)throw Error("PUBLIC_GITHUB_HTTP_"+response.status);
  return response.json();
}
const t0=performance.now(),pr=await get("/pulls/"+prNumber);
if(pr.head?.sha!==HEAD||pr.base?.repo?.full_name!==repo||pr.head?.repo?.full_name!==repo)
 throw Error("FROZEN_PR_SOURCE_MOVED");
const files=[],maxPages=3;
let filesVisibility="COMPLETE";
for(let page=1;page<=maxPages;page++){
 const a=await get("/pulls/"+prNumber+"/files?per_page=100&page="+page);
 if(!Array.isArray(a))throw Error("PUBLIC_GITHUB_FILE_LIST_INVALID");
 files.push(...a);
 if(a.length<100)break;
 if(page===maxPages)filesVisibility="TRUNCATED_AT_300";
}
let runs=[],ciVisibility="COMPLETE";
try{
 const d=await get("/actions/runs?head_sha="+HEAD+"&per_page=100");
 if(!Array.isArray(d.workflow_runs))throw Error("PUBLIC_GITHUB_CI_BAD");
 runs=d.workflow_runs;
 if(d.total_count>runs.length)ciVisibility="TRUNCATED";
}catch(e){
 if(/PUBLIC_GITHUB_HTTP_(403|404)/.test(String(e)))ciVisibility="UNKNOWN_NO_ACTIONS_ACCESS";
 else throw e;
}
const snap={repository:repo,number:prNumber,sha:HEAD,files,runs,
 files_visibility:filesVisibility,ci_visibility:ciVisibility};
const t1=performance.now();
const result=main.analyze(snap),check=main.checkOutput(result);
const t2=performance.now();
const sourceSpecific=/strings[.]replace_n|topdown|webassembly|wasm|replacen|empty.pattern|overlapping.pattern/i
  .test(result.finding.code+"\n"+result.finding.next_action);
const evidenceSpecific=result.declared_limits.some(x=>
  /strings[.]replace_n|topdown|wasm|empty.pattern|overlap/i.test(x.name));
const strongBaselineFromAvailablePRBody={
  names_operation:/strings[.]replace_n/.test(pr.body||""),
  names_runtime_difference:/Wasm/i.test(pr.body||"")&&/topdown/i.test(pr.body||""),
  names_input_overlap:/overlap/i.test(pr.body||""),
  names_empty_pattern:/empty key|empty pattern/i.test(pr.body||""),
  note:"Automated availability audit of original author-provided PR description, NOT a blinded human reviewer or independent reasoning."
};
const report={
 schema:"metalogic.mathgraph-check.opa-heldout-product-v1",
 original_repo:repo,pr:prNumber,base_sha:PARENT,head_sha:HEAD,
 source:"actual public original PR, changed-file API, and original exact-head CI",
 source_files_count:files.length,files_visibility:filesVisibility,ci_visibility:ciVisibility,
 head_runs:runs.filter(x=>x.head_sha===HEAD).map(x=>({
  id:x.id,name:x.name,conclusion:x.conclusion,status:x.status})),
 baseline_available_evidence:strongBaselineFromAvailablePRBody,
 product_version:main.VERSION,
 actual_unmodified_product_result:result,
 neutral_check_preview:{name:check.name,status:check.status,conclusion:check.conclusion,
  title:check.output.title,summary:check.output.summary},
 meaningfully_specific_semantic_finding:sourceSpecific||evidenceSpecific,
 product_source_specific_discovery:sourceSpecific||evidenceSpecific?"POTENTIAL":"NOT_DETECTED",
 fairness_limits:["Original PR author reveals original bug/fix in description to BOTH baselines",
  "No independent human reviewer, so human-time savings and decision advantage cannot be measured",
  "No GitHub App installation on OPA, all data read-only",
  "Only exact original historical PR and CI, no current OPA release security assurance"],
 measurement:{public_API_requests:calls,
  request_elapsed_ms:+(t1-t0).toFixed(3),analyze_and_render_ms:+(t2-t1).toFixed(3),
  human_review_time:"NOT_MEASURED"},
 action_authorization:"NONE"
};
const out=resolve(process.argv[3]||"research/aria_scaling_trust/opa_9216/eval_result.json");
await mkdir(dirname(out),{recursive:true});
await writeFile(out,JSON.stringify(report,null,2)+"\n");
console.log("OPA_HELDOUT_EXISTING_MATHGRAPH_CHECK "+JSON.stringify({
 pr:prNumber,head:HEAD,CI:result.ci.state,
 finding:result.finding.code,specificSemanticDiscovery:report.product_source_specific_discovery,
 baselineHasOriginalSemanticBugInPR:strongBaselineFromAvailablePRBody.names_runtime_difference,
 apiRequests:calls,analyzerMs:report.measurement.analyze_and_render_ms}));
