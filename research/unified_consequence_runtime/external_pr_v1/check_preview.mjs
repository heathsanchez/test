#!/usr/bin/env node
/**
 * Proof-bound MathGraph Check *preview*, consuming the existing App analyzer.
 *
 * Never POST to GitHub. The evidence comes from an independent original
 * source-native Python regression check, not a generated patch or verified
 * mathematical theorem. Head freshness is checked separately, fail closed.
 */
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const argv=new Map();
for(let i=2;i<process.argv.length;i+=2) argv.set(process.argv[i],process.argv[i+1]);
for(const field of ['--core','--receipt','--policy','--output'])
  if(!argv.get(field)) throw Error('MISSING_REQUIRED_ARGUMENT:'+field);
const core=await import(pathToFileURL(resolve(argv.get('--core'))).href);
if(typeof core.loadPR!=='function'||typeof core.analyze!=='function'||
   typeof core.checkOutput!=='function') throw Error('WRONG_APP_ANALYZER');
const bytes=readFileSync(argv.get('--receipt'));
const policy=JSON.parse(readFileSync(argv.get('--policy'),'utf8'));
const receipt=JSON.parse(bytes);
const sha=val=>createHash('sha256').update(val).digest('hex');

if(policy.schema!=='metalogic.external-pr-source-receipt-policy.v1'||
   sha(bytes)!==policy.evidence_receipt_sha256||
   receipt.qualified_count!==2||
   receipt.advisory_conclusion!=='NEUTRAL_REVIEW_EVIDENCE_ONLY'||
   receipt.original_external_repo!=='teorth/IEANTN'||
   receipt.scientific_L7!=='UNKNOWN'||
   receipt.code_repair_generated!=='NO')
  throw Error('SOURCE_NATIVE_EVIDENCE_INVALID');

const results=[];
for(const expected of policy.exact_cases) {
  const row=receipt.cases.find(r=>r.pr===expected.pr);
  if(!row||row.head_sha!==expected.head||row.base_sha!==policy.original_base||
     row.result!=='WARRANTED_BOUNDED_REAL_PR_NATIVE_REGRESSION'||
     row.before_source_with_head_tests.exit_code===0||
     row.after_source_with_head_tests.exit_code!==0||
     row.AST_derived_new_test_methods.length!==expected.discovered_tests||
     row.old_full_suite_on_base.test_count!==expected.base_suite||
     row.full_suite_on_head.test_count!==expected.head_suite)
    throw Error('PR_SCOPED_BEHAVIOR_NOT_QUALIFIED:'+expected.pr);
  const snap=await core.loadPR(policy.external_source_repository,expected.pr,
      process.env.GH_PUBLIC_TOKEN||'');
  if(snap.sha!==expected.head) throw Error('CURRENT_PR_HEAD_CHANGED:'+expected.pr);
  const assessment=core.analyze(snap);
  if(assessment.source.repository!==policy.external_source_repository||
     assessment.source.sha!==expected.head||
     assessment.authority!=='ADVISORY_ONLY')
    throw Error('APP_PR_SOURCE_CORRESPONDENCE_INVALID:'+expected.pr);
  const githubPayload=core.checkOutput(assessment);
  if(githubPayload.status!=='completed'||githubPayload.conclusion!=='neutral'||
     githubPayload.name!=='MathGraph Check / evidence scope')
    throw Error('APP_CHECK_POLICY_ESCALATION');
  const sourceText=[
    '',
    '### Independently replayed native regression evidence',
    '- **Verdict:** WARRANTED_BOUNDED_REAL_PR_NATIVE_REGRESSION',
    '- **Exact PR:** '+assessment.source.url,
    '- **Original common base:** '+policy.original_base,
    '- **Exact PR head:** '+expected.head,
    '- **Original authored regression tests found by AST:** '+row.AST_derived_new_test_methods.length,
    '- **Base source + PR-authored tests:** '+row.before_source_with_head_tests.test_count+
      ' executed, exit '+row.before_source_with_head_tests.exit_code+' (regression demonstrated)',
    '- **PR head source + SAME PR-authored tests:** '+row.after_source_with_head_tests.test_count+
      ' executed, exit '+row.after_source_with_head_tests.exit_code,
    '- **Original complete base suite:** '+row.old_full_suite_on_base.test_count+' tests passed',
    '- **New complete PR suite:** '+row.full_suite_on_head.test_count+' tests passed',
    '- **Bounded original native run:** https://github.com/heathsanchez/test/actions/runs/'+
      policy.producer_run,
    '- **Evidence receipt SHA256:** '+policy.evidence_receipt_sha256,
    '',
    '**Boundary:** These are PR-author-provided repairs and regression tests independently',
    'replayed in Python at exact historical commits. Not a complete correctness theorem,',
    'not automatic patch generation, not a proof of current downstream dependencies,',
    'not an installation, and not an authorization to merge.',
  ].join('\n');
  githubPayload.head_sha=expected.head;
  githubPayload.external_id=policy.external_source_repository+'#'+expected.pr+'@'+expected.head;
  // Keep the original generic analyzer verdict, but give independently
  // replicated source-native evidence priority in the maintainer's preview.
  // This does not change the generic risk classification or Check conclusion.
  const genericContext=githubPayload.output.summary;
  githubPayload.output.summary=(
    sourceText.trimStart()+'\n\n---\n### Additional generic PR analysis\n'+genericContext
  ).slice(0,60000);
  githubPayload.output.title='Exact-revision PR regressions — neutral review evidence';
  if(githubPayload.conclusion!=='neutral') throw Error('ADVISORY_WAS_PROMOTED');
  results.push({
    pr:expected.pr,source:assessment.source,ci:assessment.ci.state,
    finding:assessment.finding.code,
    native_evidence_verdict:'WARRANTED_BOUNDED_REAL_PR_NATIVE_REGRESSION',
    generic_analyzer_finding:assessment.finding.code,
    receipt_id:sha(bytes),
    github_check_run_preview:githubPayload,
    actually_posted:false,app_installed:false,protected_revision:expected.head,
    external_contributor_supplied_fix:true,auto_repair_generated:false,
    scientific_L7:'UNKNOWN',action_authorization:'NONE',
  });
}
mkdirSync(dirname(resolve(argv.get('--output'))),{recursive:true});
writeFileSync(resolve(argv.get('--output')),JSON.stringify({
  schema:'metalogic.mathgraph-check.external-pr-native-preview.v1',
  app_source:'metalogiclabs/mathgraph@mathgraph-check-github-app-shadow-v0',
  native_verifier_source:'heathsanchez/test@'+policy.producer_head,
  advisory_scope:'EXACT_PINNED_NATIVE_PR_REGRESSIONS_ONLY',
  actual_check_runs_posted:0,github_app_installation:'NOT_TESTED',
  results,
},null,2)+'\n');
console.log('MATHGRAPH_CHECK_NATIVE_EXTERNAL_PR_PREVIEWS='+results.length);
for(const r of results)
  console.log('PR_'+r.pr+' '+r.github_check_run_preview.conclusion+
    ' exact_head='+r.protected_revision+' CI='+r.ci+
    ' original_behavior=WARRANTED_BOUNDED_NATIVE_REGRESSION');
console.log('LIVE_GITHUB_CHECKS_POSTED=0 L7=UNKNOWN');
