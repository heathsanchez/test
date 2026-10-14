// Emit only local, read-only preview material from a previously admitted receipt.
// Never POST a Check Run. No access to App tokens, webhooks or production workers.
import { readFile, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { formatNativeConsequence } from "./render_check.mjs";

const PIN = "c62eebae9a3757ae6de638a51d0363a6db684e76f47d91b0d477914a41382eec";
const input=new URL("./output/review.json",import.meta.url);
const bytes=await readFile(input);
if(createHash("sha256").update(bytes).digest("hex")!==PIN)
 throw Error("PREVIEW_SOURCE_RECEIPT_NOT_SEPARATELY_PINNED");
const report=JSON.parse(bytes);
if(!Array.isArray(report.receipts)||report.receipts.length!==3)
 throw Error("SOURCE_RECEIPT_SET_INCOMPLETE");
const previews=report.receipts.map(record=>{
 const target={repository:record.subject.repository,
               pr:record.subject.pr,sha:record.subject.head_sha};
 return formatNativeConsequence({raw:bytes,trustedSha256:PIN,target});
});
if(previews.some(item=>item.reason!=="WARRANTED_BOUNDED_NATIVE_EVIDENCE_PRESENT" ||
                     item.check.conclusion!=="neutral" ||
                     item.promoted!==false))
 throw Error("UNAUTHORIZED_PREVIEW_PROMOTION");
await writeFile(new URL("./output/check-previews.json",import.meta.url),
 JSON.stringify({schema:"mathgraph.check.read-only-native-preview.v1",
   published:false,checks:previews},null,2)+"\n");
const md=["# MathGraph Check — source-native evidence previews",
 "Research output only: no GitHub Check Runs posted and no production App change.",
 ...previews.map(p=>"## "+p.target.repository+" PR #"+p.target.pr+
 "\n"+p.check.output.summary+"\n")].join("\n\n");
await writeFile(new URL("./output/check-previews.md",import.meta.url),md+"\n");
console.log("PREVIEW_ADMITTED",JSON.stringify({
  total:previews.length,neutral:previews.filter(p=>p.check.conclusion==="neutral").length,
  sourceScoped:previews.every(p=>p.check.head_sha===p.target.sha),
  posted:false}));
