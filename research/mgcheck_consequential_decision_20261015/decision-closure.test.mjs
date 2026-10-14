import test, {after} from "node:test";
import assert from "node:assert/strict";
import {readFileSync,writeFileSync,mkdirSync} from "node:fs";
import {resolve} from "node:path";
import {decide,reclose,ROOTS,VERSION} from "./decision-closure.mjs";

const e=resolve(process.argv[2]||"research/mgcheck_consequential_decision_20261015/evidence");
const take=p=>readFileSync(resolve(e,p));
const json=p=>JSON.parse(take(p));
const runs=p=>p.runs.map(([id])=>json("runs/"+id+".json"));
const obj=(p,extra={})=>({subject:{...p.subject},runReadbacks:runs(p),...extra});
const yaml=obj(ROOTS.yaml,{reportBytes:take("yaml-source-report.json")});
const gimmes=obj(ROOTS.gimmes,{
 reportBytes:take("gimmes-review/review-resolution/review_resolution.json"),
 nativeBytes:take("gimmes-native/receipt.json"),
 reviewZip:take("gimmes-review.zip"),nativeZip:take("gimmes-native.zip"),
 logs:Object.fromEntries([
  "original_review_witness.log","candidate_review_and_suite.log",
  "physically_restored_observer.log","wrong_candidate_negative.log"
 ].map(n=>[n,take("gimmes-native/"+n)]))
});
const first=reclose([
 {id:"go-yaml",root:"yaml",input:yaml},
 {id:"gimmes",root:"gimmes",input:gimmes}
]);
const byID=id=>first.states.find(x=>x.id===id);
test("admit exact pinned Go YAML original native evidence, not blanket merge assurance",()=>{
 const r=byID("go-yaml");
 assert.equal(r.status,"WARRANTED_BOUNDED_SOURCE_SPECIFIC");
 assert.deepEqual(r.claims.map(c=>c.cases),[69,0,20]);
 assert.equal(r.claims[2].causal_repair.ablation,20);
 assert.match(r.action,/SEPARATE/);
 assert.equal(r.merge,"UNKNOWN");
 assert.equal(r.authorization,"NONE");
 assert.equal(r.native_executed_in_this_consumer,false);
});
test("preserve one confirmed Python reviewer defect and two independent contract unknowns",()=>{
 const r=byID("gimmes");
 assert.equal(r.status,"WARRANTED_BOUNDED_SOURCE_SPECIFIC",r.reason);
 assert.equal(r.claims.length,3);
 assert.equal(r.claims.filter(x=>x.state.includes("WARRANTED_BOUNDED")).length,1);
 assert.equal(r.claims.filter(x=>x.state==="UNKNOWN_NORMATIVE_CONTRACT").length,2);
 assert.equal(r.merge,"UNKNOWN");
});
test("withdrawing only YAML root leaves independent Python support valid",()=>{
 const r=reclose([
  {id:"go-yaml",root:"yaml",input:{...yaml,withdrawn:true}},
  {id:"gimmes",root:"gimmes",input:gimmes}
 ]);
 assert.equal(r.warranted,1);
 assert.equal(r.states[0].status,"STALE_SUPPORT_WITHDRAWN");
 assert.equal(r.states[1].status,"WARRANTED_BOUNDED_SOURCE_SPECIFIC");
});
test("withdrawing only Python root preserves YAML, including inherited-vs-introduced distinction",()=>{
 const r=reclose([
  {id:"go-yaml",root:"yaml",input:yaml},
  {id:"gimmes",root:"gimmes",input:{...gimmes,withdrawn:true}}
 ]);
 assert.equal(r.warranted,1);
 assert.equal(r.states[1].status,"STALE_SUPPORT_WITHDRAWN");
 assert.equal(r.states[0].claims[1].cases,0);
});
test("stale head, wrong subject and forged upstream revision fail closed",()=>{
 for(const root of ["yaml","gimmes"]){
  const p=root==="yaml"?yaml:gimmes;
  const badHead=decide(root,{...p,subject:{...p.subject,head:"a".repeat(40)}});
  assert.equal(badHead.status,"STALE_SOURCE_HEAD");
  const badRepo=decide(root,{...p,subject:{...p.subject,repository:"different/project"}});
  assert.equal(badRepo.status,"UNKNOWN_WRONG_SUBJECT");
 }
});
test("one forged run or changed original report never promotes native claims",()=>{
 assert.equal(decide("yaml",{...yaml,
  runReadbacks:yaml.runReadbacks.map((r,i)=>i===0?{...r,conclusion:"failure"}:r)}).status,"UNKNOWN_EVIDENCE_NOT_QUALIFIED");
 const altered=Buffer.concat([yaml.reportBytes,Buffer.from("\n")]);
 assert.equal(decide("yaml",{...yaml,reportBytes:altered}).status,
  "UNKNOWN_EVIDENCE_NOT_QUALIFIED");
 const alteredReview=Buffer.concat([gimmes.reportBytes,Buffer.from(" ")]);
 assert.equal(decide("gimmes",{...gimmes,reportBytes:alteredReview}).status,
  "UNKNOWN_EVIDENCE_NOT_QUALIFIED");
});
test("missing or tampered native log refuses Python witness",()=>{
 const logs={...gimmes.logs, "original_review_witness.log":Buffer.from("forged")};
 const r=decide("gimmes",{...gimmes,logs});
 assert.equal(r.status,"UNKNOWN_EVIDENCE_NOT_QUALIFIED");
 assert.equal(r.claims.length,0);
});
test("unknown recipient and source ambiguity never confer action authority",()=>{
 assert.equal(decide("nonexistent",yaml).status,"UNKNOWN_UNRECOGNIZED_CAPABILITY");
 assert.equal(first.merge_authority,"UNKNOWN");
 assert.equal(first.autonomous_action,"NONE");
});
test("cold reclosure deterministic byte-equivalent",()=>{
 assert.equal(JSON.stringify(first),JSON.stringify(reclose([
  {id:"go-yaml",root:"yaml",input:yaml},{id:"gimmes",root:"gimmes",input:gimmes}])));
});
test("equally informed executable ledger has all the same evidence and ties",()=>{
 // Strong ledger baseline has EXACT same original source bytes, full tests,
 // policy and verified source identity. It is not denied methods or authority.
 const y=json("yaml-source-report.json");
 const g=json("gimmes-review/review-resolution/review_resolution.json");
 const expectedY=[y.decision.fixed_by_author_case_count,
   y.decision.introduced_case_count,y.decision.unresolved_inherited_count];
 const expectedG=[g.records.filter(x=>x.status.startsWith("WARRANTED_")).length,
   g.records.filter(x=>x.status==="UNKNOWN_NORMATIVE_CONTRACT").length];
 assert.deepEqual(byID("go-yaml").claims.map(x=>x.cases),expectedY);
 assert.deepEqual([
  byID("gimmes").claims.filter(x=>x.state.startsWith("WARRANTED_")).length,
  byID("gimmes").claims.filter(x=>x.state==="UNKNOWN_NORMATIVE_CONTRACT").length
 ],expectedG);
});
after(()=>{
 mkdirSync(e,{recursive:true});
 const summary={
  schema:VERSION,subject_count:2,
  historical_decisions:first.states.map(x=>({
   subject:x.subject,status:x.status,claims:x.claims,
   next_action:x.action,unresolved:x.unresolved||[],
   merger_authority:x.merge
  })),
  reviewer_model_inference:"NOT_RUN",native_tests_rerun:"NO",
  original_artifacts_independently_read:"YES_FROM_ARCHIVED_GITHUB_RUNS",
  policy_reuse:"SOURCE_BOUND_REVIEWED_RULES",
  causal_resilience:"SOURCE_WITHDRAWAL_AND_CROSS_SUBJECT_NONINTERFERENCE",
  strong_executable_ledger:"TIE_WITH_SAME_INFORMATION",
  complete_lifetime_cost:"UNKNOWN",
  commercial_superiority:"UNKNOWN",
  autonomous_new_method_language:"NOT_TESTED",
  no_merge_authority:true
 };
 writeFileSync(resolve(e,"consequential-decision-summary.json"),JSON.stringify(summary,null,2)+"\n");
});
