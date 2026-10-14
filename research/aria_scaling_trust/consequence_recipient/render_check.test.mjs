import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { formatNativeConsequence } from "./render_check.mjs";

const PIN = "c62eebae9a3757ae6de638a51d0363a6db684e76f47d91b0d477914a41382eec";
const data = readFileSync(new URL("./output/review.json",import.meta.url));
assert.equal(createHash("sha256").update(data).digest("hex"),PIN);
const payload = JSON.parse(data);
const targets = payload.receipts.map(item=>({
 repository:item.subject.repository,pr:item.subject.pr,sha:item.subject.head_sha
}));
function run(target,params={}) {
 return formatNativeConsequence({raw:data,trustedSha256:PIN,target,...params});
}
const id = n=>targets.find(t=>t.repository.startsWith(n));

test("all three historically admitted original source scopes render as neutral",()=>{
 for(const target of targets){
   const result=run(target);
   assert.equal(result.check.conclusion,"neutral");
   assert.equal(result.check.status,"completed");
   assert.equal(result.check.head_sha,target.sha);
   assert.equal(result.authority,"ADVISORY_ONLY");
   assert.equal(result.reason,"WARRANTED_BOUNDED_NATIVE_EVIDENCE_PRESENT");
   assert.equal(result.promoted,false);
   assert.match(result.check.output.summary,/NOT_MEASURED/);
   assert.match(result.check.output.summary,/NOT_CHECKED/);
 }
});
test("two independently executed differential receipts remain distinguishable",()=>{
 const a=run(id("open-policy-agent/"));
 const b=run(id("itchyny/"));
 assert.match(a.check.output.summary,/Unknown\/incomplete cases: 8/);
 assert.match(b.check.output.summary,/Unknown\/incomplete cases: 0/);
 assert.match(a.check.output.summary,/base and reference disagree/);
 assert.match(b.check.output.summary,/base and reference disagree/);
});
test("unchanged protected test is named only for exact HowlFrame subject",()=>{
 const r=run(id("howlcipher/"));
 assert.match(r.check.output.summary,/TestSerializeSSAIntegerDivisionFailsClosed/);
 assert.match(r.check.output.summary,/restoration reintroduced the failure/);
 assert.doesNotMatch(run(id("itchyny/")).check.output.summary,
                     /TestSerializeSSAIntegerDivisionFailsClosed/);
});
test("newer unverified PR head is stale, not proof invalidation",()=>{
 const t={...id("howlcipher/"),sha:"f".repeat(40)};
 const r=run(t);
 assert.equal(r.reason,"STALE_SOURCE_REVISION");
 assert.equal(r.accepted_receipt,false);
 assert.doesNotMatch(r.check.output.summary,/TestSerializeSSAIntegerDivisionFailsClosed/);
 assert.match(r.check.output.summary,/old proof is retained/);
});
test("cross-repository attribution cannot reuse evidence",()=>{
 const t={...id("howlcipher/"),repository:"metalogiclabs/go-ethereum"};
 const r=run(t);
 assert.equal(r.reason,"UNKNOWN_NO_AUTHORIZED_SUBJECT");
 assert.doesNotMatch(r.check.output.summary,/TestSerializeSSAIntegerDivisionFailsClosed/);
});
test("withdrawal removes reusable support but retains historical evidence",()=>{
 const r=run(id("open-policy-agent/"),{withdrawn:true});
 assert.equal(r.reason,"STALE_EVIDENCE_WITHDRAWN");
 assert.equal(r.accepted_receipt,false);
 assert.doesNotMatch(r.check.output.summary,/Original base:/);
});
test("an attacker cannot supply a self-hash instead of independent policy",()=>{
 assert.throws(()=>formatNativeConsequence({
   raw:Buffer.concat([data,Buffer.from(" ")]),
   trustedSha256:PIN,target:id("itchyny/")}),
   /UNAUTHORIZED_RECEIPT_BYTES/);
});
test("absence of an independently authorized digest fails closed",()=>{
 assert.throws(()=>formatNativeConsequence({raw:data,target:id("itchyny/")}),
               /EXTERNAL_RECEIPT_PIN_REQUIRED/);
});
test("invalid subject or method never gets decision authority",()=>{
 assert.throws(()=>run({...id("itchyny/"),sha:"not-a-SHA"}),
               /INVALID_TARGET_SCOPE/);
 assert.throws(()=>run(id("itchyny/"),{withdrawn:"false"}),
               /UNSUPPORTED_WITHDRAWAL_INPUT/);
});
test("neutral result never asserts present-day external defect or value advantage",()=>{
 const combined=targets.map(t=>run(t).check.output.summary).join("\n");
 assert.doesNotMatch(combined,/READY_TO_MERGE|SAFE_TO_DEPLOY|PROVEN_CURRENT_DEFECT/);
 assert.match(combined,/not a source-to-intent proof/);
 assert.match(combined,/fully informed conventional reviewer/);
});
