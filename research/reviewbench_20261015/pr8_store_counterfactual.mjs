import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import ts from 'typescript';

const root = process.cwd();
const headExpected = process.env.MG_EXPECTED_HEAD;
const file = path.join(root, 'src', 'stores', 'auditStore.ts');
const original = fs.readFileSync(file, 'utf8');
const sha = s => crypto.createHash('sha256').update(s).digest('hex');
const gotHead = spawnSync('git', ['-C', root, 'rev-parse', 'HEAD'], {encoding:'utf8'});
if (gotHead.status !== 0 || gotHead.stdout.trim() !== headExpected) {
  throw new Error('UNKNOWN_WRONG_PINNED_REVIEWBENCH_SOURCE');
}
const oldMarker = 'entries: [...entries].sort((a, b) => {';
const patchMarker = 'entries: [...new Map(entries.map(e => [e.id || e.request_id + "-" + e.timestamp, e])).values()].sort((a, b) => {';
if (original.split(oldMarker).length !== 2) throw new Error('UNKNOWN_UNIQUE_REPAIR_SITE_NOT_FOUND');
const patched = original.replace(oldMarker, patchMarker);
const output = process.env.MG_REPORT_FILE || path.join(root,'mgcheck-pr8-report.json');
const compiled = [];
function mkEntry(id, minute) {
  return {id, request_id: id, timestamp: new Date(Date.UTC(2026,0,1,0,minute)).toISOString(),
    user_id:'u', method:'GET',url:'/audit',operation:'READ',
    decision:'allow',cache_hit:false,response_status:200,duration_ms:1};
}
async function oneModule(mode) {
  const source = fs.readFileSync(file, 'utf8');
  const compiledCode=ts.transpileModule(source, {compilerOptions:{
    module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022
  },fileName:file}).outputText;
  const temp=path.join(root,'src','stores','__mgcheck_pr8_'+mode+'.mjs');
  compiled.push(temp);
  fs.writeFileSync(temp,compiledCode);
  const exports=await import(pathToFileURL(temp).href);
  const store=exports.useAuditStore;
  const A=mkEntry('A',4),B=mkEntry('B',3),C=mkEntry('C',2),D=mkEntry('D',1),X=mkEntry('X',5);
  store.setState({entries:[],filters:{},total:0,offset:0,limit:2});
  store.getState().setEntries([A,B],4,0,2);
  const noSSEbefore=store.getState();
  noSSEbefore.setEntries([...noSSEbefore.entries,C,D],4,2,2);
  const noSSE=store.getState();
  const noSSEids=noSSE.entries.map(e=>e.id);
  const noSSEhasMore=noSSE.entries.length<noSSE.total;
  const noSSEpassed=JSON.stringify(noSSEids)===JSON.stringify(['A','B','C','D'])&&!noSSEhasMore;
  store.setState({entries:[],filters:{},total:0,offset:0,limit:2});
  store.getState().setEntries([A,B],4,0,2);
  store.getState().addEntry(X); // actual source SSE hook routes to this action.
  const liveState=store.getState();
  // Stable-offset API sees current ordering X,A,B,C,D; offset=2,limit=2 => B,C.
  const afterSsePageTwo=[B,C];
  liveState.setEntries([...liveState.entries,...afterSsePageTwo],5,2,2);
  const second=store.getState();
  const secondIDs=second.entries.map(e=>e.id);
  const hasMore=second.entries.length<second.total;
  const duplicate=secondIDs.length!==new Set(secondIDs).size;
  const missingD=!secondIDs.includes('D');
  if(hasMore){
    const next=store.getState();
    next.setEntries([...next.entries,D],5,4,2);
  }
  const last=store.getState();
  const lastIDs=last.entries.map(e=>e.id);
  const finalComplete=JSON.stringify(lastIDs)===JSON.stringify(['X','A','B','C','D']);
  return {mode,noSSEpassed,noSSEids,postInterleavingPageTwo:secondIDs,
    postInterleavingHasMore:hasMore,duplicate,missingOldestD:missingD,
    finalIDs:lastIDs,finalComplete,observedTotal:last.total,
    sourceFileSha256:sha(source)};
}
let record={schema:'mgcheck.reviewbench-pr8.native-state.v0',sourceHead:gotHead.stdout.trim(),
  originalStoreSha256:sha(original),patchStoreSha256:sha(patched),
  experiment:'Actual original TypeScript/Zustand audit store; new live event between offset pages',
  methodOrigin:'human-defined source-informed causal observer; NOT autonomous L7',
  original: null, patched:null, restored:null};
try {
  record.original=await oneModule('original');
  fs.writeFileSync(file,patched);
  record.patched=await oneModule('candidate');
  fs.writeFileSync(file,original);
  record.restored=await oneModule('restored');
  const o=record.original,p=record.patched,z=record.restored;
  const preViolation=o.noSSEpassed && o.duplicate && o.missingOldestD && !o.postInterleavingHasMore;
  const candidateFix=p.noSSEpassed && !p.duplicate && p.postInterleavingHasMore && p.finalComplete;
  const causalRestoration=z.noSSEpassed && z.duplicate && z.missingOldestD && !z.postInterleavingHasMore;
  const byteRestored=fs.readFileSync(file,'utf8')===original;
  record.controls={noSSEControlPassed:o.noSSEpassed && p.noSSEpassed && z.noSSEpassed,
    candidateFix,causalRestoration,byteRestored,sourceSHAConfirmed:true,
    notEstablished:['Live actual SSE network delivery','database serializability',
      'all concurrent interleavings','independent maintainer normative approval','strong reviewer superiority']};
  record.status= preViolation&&candidateFix&&causalRestoration&&byteRestored ?
    'WARRANTED_BOUNDED_RETROSPECTIVE_FRONTEND_STATE_COUNTEREXAMPLE':
    'UNKNOWN_OR_REJECTED_NATIVE_STATE_GATE';
} finally {
  fs.writeFileSync(file,original);
  for(const name of compiled){try{fs.unlinkSync(name)}catch{}}
}
fs.writeFileSync(output,JSON.stringify(record,null,2)+'\n');
console.log('REVIEWBENCH_PR8_RESULT='+JSON.stringify({status:record.status,
  original:record.original?.postInterleavingPageTwo,originalMore:record.original?.postInterleavingHasMore,
  candidate:record.patched?.postInterleavingPageTwo,candidateMore:record.patched?.postInterleavingHasMore,
  candidateComplete:record.patched?.finalComplete,restored:record.restored?.postInterleavingPageTwo,
  sourceHead:record.sourceHead}));
if(record.status!=='WARRANTED_BOUNDED_RETROSPECTIVE_FRONTEND_STATE_COUNTEREXAMPLE')process.exit(3);
