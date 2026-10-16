"""Independent pure-filesystem metadata audit; never imports the curator."""
import ast
import collections
import datetime
import hashlib
import json
import pathlib
import re

BASE = pathlib.Path('/workspace/qualification/native-authority-v41-screening-audit/metadata-preaudit')
COMMITTED = BASE / 'committed'
SOURCE = BASE / 'source-binding/research/unified_consequence_runtime/archaeology'
INPUT_NAMES = ('PREQUERY.json', 'METADATA_CURATION.json', 'FROZEN_POOL.json')
raw = {name: (COMMITTED / name).read_bytes() for name in INPUT_NAMES}
plan, metadata, frozen = (json.loads(raw[name]) for name in INPUT_NAMES)
checks = []


def check(name, actual, expected=True, detail=None):
    result = {'check': name, 'passed': actual == expected}
    if actual != expected:
        result.update(actual=actual, expected=expected)
    if detail is not None:
        result['detail'] = detail
    checks.append(result)
    return result['passed']


def digest(data):
    return hashlib.sha256(data).hexdigest()


def test_file(name):
    # Independently transcribed from the precommitted plain-English classifier.
    path = pathlib.PurePosixPath(name)
    return name.endswith('.py') and (
        any(part in ('test', 'tests', 'testing') for part in path.parts)
        or path.name.startswith('test_') or path.name.endswith('_test.py')
        or path.name == 'conftest.py')


source_paths = {
    'v41_wrapper': COMMITTED / 'curate_frontier.py',
    'v4_wrapper': SOURCE / 'native-authority-v4/curate_frontier.py',
    'v3_curator': SOURCE / 'native-environment-v3/curate_frontier.py',
    'v2_scan_and_classifier': SOURCE / 'native-frontier-v2/curate_metadata.py',
}
source_bytes = {key: path.read_bytes() for key, path in source_paths.items()}
source_hashes = {key: digest(data) for key, data in source_bytes.items()}
source_expected = {
    'v41_wrapper': plan['curation_code_sha256'],
    'v4_wrapper': 'bfd0f38de30b12021090eb9592aebc79c60317c1bccdbcac3487da15f0e1b413',
    'v3_curator': '44455d61c8144261e2db2ce2a6de8b6b2671d9ca504353e03bb9dcd487fa3c14',
    'v2_scan_and_classifier': plan['original_curator']['sha256'],
}
for key in source_paths:
    check('retained_source_hash_' + key, source_hashes[key], source_expected[key])
v2_ast = ast.parse(source_bytes['v2_scan_and_classifier'])
scan = next(node for node in v2_ast.body if isinstance(node, ast.FunctionDef) and node.name == 'scan')
loops = [node for node in ast.walk(scan) if isinstance(node, ast.For)]
check('static_scan_enumerates_items_directly', any(
    isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name)
    and node.iter.func.id == 'enumerate' and len(node.iter.args) == 2
    and isinstance(node.iter.args[0], ast.Name) and node.iter.args[0].id == 'items'
    and isinstance(node.iter.args[1], ast.Constant) and node.iter.args[1].value == 1
    for node in loops))
check('static_scan_contains_no_sort_operation', not any(
    isinstance(node, ast.Call) and (
        isinstance(node.func, ast.Name) and node.func.id == 'sorted'
        or isinstance(node.func, ast.Attribute) and node.func.attr == 'sort')
    for node in ast.walk(scan)))

check('prequery_snapshot_unchanged', raw['PREQUERY.json'], (BASE / 'prequery-committed/PREQUERY.json').read_bytes())
check('curator_snapshot_unchanged', source_bytes['v41_wrapper'], (BASE / 'prequery-committed/curate_frontier.py').read_bytes())
check('metadata_plan_hash', metadata['prequery_plan_sha256'], digest(raw['PREQUERY.json']))
check('frozen_metadata_hash', frozen['metadata_curation_sha256'], digest(raw['METADATA_CURATION.json']))
check('frozen_pool_exactly_equals_metadata_pool', frozen['pool'], metadata['pool'])
check('execution_receipt_hash_agrees', metadata['prequery_execution_sha256'], frozen['prequery_execution_sha256'])
check('requested_roles', frozen['requested_roles'], plan['requested_roles'])
check('screening_budget_exactly_preserved', frozen['screening_budget'], plan['screening_budget'])
check('metadata_budget_exactly_preserved', metadata['costs']['metadata_budget_seconds'], plan['metadata_seconds'])
check('metadata_reported_wall_within_prequery_budget', 0 <= metadata['costs']['metadata_wall_seconds'] <= plan['metadata_seconds'])
check('metadata_reported_total_wall_within_prequery_budget', 0 <= metadata['costs']['total_curation_wall_seconds'] <= plan['metadata_seconds'])
check('metadata_reports_zero_native_calls', metadata['costs']['native_calls'], 0)
check('metadata_reports_zero_collection_calls', metadata['costs']['collection_calls'], 0)
universe = plan['repository_universe_fixed_before_github_queries']
check('universe_sorted_unique', universe, sorted(set(universe)))
check('universe_case_budget', len(universe) <= plan['screening_budget']['maximum_cases'])
check('all_nine_repository_results_in_prequery_order', [row['repo'] for row in metadata['repositories']], universe)
check('universe_exclusions_disjoint', set(universe).isdisjoint(plan['historically_touched_repository_exclusions']))

reason_counts = collections.Counter()
status_counts = collections.Counter()
repo_reports = []
selected_expected = []
inversions = []
file_rows = 0
candidate_fields = {'number','title','merged_at','closed_at','updated_at','labels','base','head','merge_commit_sha','url'}
file_fields = {'filename','status','additions','deletions','changes','sha'}
for repository in metadata['repositories']:
    repo = repository['repo']
    before = len(checks)
    candidates = repository['candidates']
    qualifying = []
    gate_count = 0
    rejection_histogram = collections.Counter()
    check(repo + ':closed_list_count', repository['closed_pr_count'], len(candidates))
    check(repo + ':fixed_100_closed_pr_window', len(candidates), 100)
    check(repo + ':candidate_rank_sequence', [c['rank_within_repository'] for c in candidates], list(range(1, len(candidates) + 1)))
    check(repo + ':unique_candidate_ids', len({c['number'] for c in candidates}), len(candidates))
    check(repo + ':query_window', {key:repository['closed_pr_window'][key] for key in ('page','per_page','sort','direction')},
          {'page':1,'per_page':100,'sort':'updated','direction':'desc'})
    for left, right in zip(candidates, candidates[1:]):
        if left['updated_at'] < right['updated_at']:
            inversions.append({'repo':repo, 'left_rank':left['rank_within_repository'], 'left_pr':left['number'],
                'left_updated_at':left['updated_at'], 'right_rank':right['rank_within_repository'],
                'right_pr':right['number'], 'right_updated_at':right['updated_at']})
    for candidate in candidates:
        label = f'{repo}#{candidate["number"]}'
        check(label + ':projected_fields_retained', candidate_fields <= set(candidate))
        check(label + ':base_head_metadata_only', set(candidate['base']) == {'sha'} and set(candidate['head']) == {'sha'})
        reasons = []
        if not candidate['merged_at']:
            reasons.append('NOT_MERGED')
        if not (re.match(r'^fix', candidate['title'], re.I) or any('bug' in value.lower() for value in candidate['labels'])):
            reasons.append('TITLE_NOT_FIX_AND_NO_BUG_LABEL')
        if not reasons:
            gate_count += 1
            check(label + ':file_scan_present_after_cheap_predicates', 'files' in candidate)
            files = candidate.get('files', [])
            file_rows += len(files)
            for row in files:
                check(label + ':file_exact_allowed_fields:' + row['filename'], set(row), file_fields)
                check(label + ':file_stats_nonnegative:' + row['filename'], all(isinstance(row[key], int) and row[key] >= 0 for key in ('additions','deletions','changes')))
                check(label + ':changes_equals_additions_plus_deletions:' + row['filename'], row['changes'], row['additions'] + row['deletions'])
            check(label + ':unique_changed_paths', len({row['filename'] for row in files}), len(files))
            pagination = candidate['file_pagination']
            check(label + ':pagination_entries_exact', pagination['entries_returned'], len(files))
            check(label + ':pagination_closed', pagination['closed'])
            check(label + ':pagination_one_closed_page', pagination['pages_requested'] == 1 and len(files) < 100)
            if any(row['status'] in ('renamed','removed') for row in files):
                reasons.append('RENAMED_OR_REMOVED_CHANGED_FILE')
            tests = [row for row in files if test_file(row['filename'])]
            production = [row for row in files if row['filename'].endswith('.py') and not test_file(row['filename'])]
            additions = sum(row['additions'] for row in production)
            deletions = sum(row['deletions'] for row in production)
            stats = {'test_py_files':len(tests), 'production_py_files':len(production), 'production_additions':additions, 'production_deletions':deletions}
            check(label + ':independent_file_classification_and_totals', candidate['metadata_stats'], stats)
            if not tests:
                reasons.append('NO_CHANGED_TEST_PY')
            if not production:
                reasons.append('NO_CHANGED_PRODUCTION_PY')
            if not 1 <= deletions <= 4:
                reasons.append('PRODUCTION_DELETIONS_OUTSIDE_1_TO_4')
            if additions > 6:
                reasons.append('PRODUCTION_ADDITIONS_ABOVE_6')
            # V3 filters this additional constraint only after all V2 reasons clear.
            if not reasons and any(row['status'] != 'modified' for row in production):
                reasons.append('PRODUCTION_PY_NOT_ALL_PREEXISTING_MODIFIED')
        else:
            check(label + ':no_file_scan_after_cheap_rejection', not any(key in candidate for key in ('files','metadata_stats','file_pagination')))
        check(label + ':independently_recomputed_ordered_reasons', candidate['reasons'], reasons)
        expected_status = 'REJECTED_METADATA_PREDICATES' if reasons else 'QUALIFIES_METADATA_ONLY'
        check(label + ':independent_predicate_status', candidate['status'], expected_status)
        reason_counts.update(reasons)
        status_counts.update([expected_status])
        rejection_histogram.update(reasons)
        if not reasons:
            qualifying.append(candidate)
            check(label + ':first_or_later_selection_disposition', candidate['selection_disposition'],
                'FIRST_METADATA_ELIGIBLE_IN_FROZEN_REPOSITORY_ORDER' if len(qualifying) == 1 else 'NOT_FIRST_ELIGIBLE_PR_IN_FIXED_ORDER')
        else:
            check(label + ':no_rejected_candidate_selection_disposition', 'selection_disposition' not in candidate)
    check(repo + ':all_qualifiers_in_retained_returned_order', repository['qualifying_prs'], [candidate['number'] for candidate in qualifying])
    check(repo + ':repository_status', repository['status'], 'QUALIFYING_METADATA_CANDIDATE' if qualifying else 'NO_QUALIFYING_CANDIDATE')
    if qualifying:
        first = qualifying[0]
        check(repo + ':first_qualifying_pr', repository['first_qualifying_pr'], first['number'])
        selected_expected.append((repo, first))
    else:
        check(repo + ':no_first_qualifying_pr_for_no_case', 'first_qualifying_pr' not in repository)
    by_timestamp = sorted(candidates, key=lambda value: value['updated_at'], reverse=True)
    first_by_timestamp = next((row['number'] for row in by_timestamp if not row['reasons']), None)
    repo_reports.append({'repo':repo, 'candidate_count':len(candidates), 'file_scans_expected':gate_count,
        'recomputed_qualifying_prs_in_retained_returned_order':[row['number'] for row in qualifying],
        'first_qualifying_pr':qualifying[0]['number'] if qualifying else None,
        'first_qualifying_rank':qualifying[0]['rank_within_repository'] if qualifying else None,
        'first_qualifier_unchanged_by_timestamp_sort_diagnostic':first_by_timestamp == (qualifying[0]['number'] if qualifying else None),
        'no_qualifying_case_independently_supported':not qualifying,
        'rejection_reason_counts':dict(sorted(rejection_histogram.items())),
        'checks':len(checks)-before, 'failed_checks':sum(not item['passed'] for item in checks[before:])})

check('frozen_pool_size_matches_first_qualifier_each_repository', len(frozen['pool']), len(selected_expected))
check('frozen_pool_repository_order_matches_selection', [row['repo'] for row in frozen['pool']], [repo for repo, _ in selected_expected])
for selected, (repo, first) in zip(frozen['pool'], selected_expected):
    expected = {'repo':repo,'pr':first['number'],'metadata_url':first['url'],'base_commit':first['base']['sha'],
        'head_commit':first['head']['sha'],'merge_commit_sha':first['merge_commit_sha'],'files':first['files'],
        'metadata_stats':first['metadata_stats'],'selection_status':'FROZEN_ORDERED_POOL_CANDIDATE_NOT_AN_ADMITTED_TASK'}
    check(repo + ':selected_metadata_exact_first_qualifier', {key:selected[key] for key in expected}, expected)
check('selection_shortfall_independently_recomputed', metadata['selection_shortfall_before_admission'], max(0, plan['requested_roles'] - len(selected_expected)))
check('pool_bounded_by_maximum_cases', len(frozen['pool']) <= plan['screening_budget']['maximum_cases'])

v3_ast = ast.parse(source_bytes['v3_curator'])
v3_constants = {}
for node in v3_ast.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in ('METADATA_SECONDS','SCREENING_BUDGET'):
                v3_constants[target.id] = ast.literal_eval(node.value)
check('prequery_screening_budget_exact_static_constant', plan['screening_budget'], v3_constants['SCREENING_BUDGET'])
check('prequery_metadata_budget_exact_static_constant', plan['metadata_seconds'], v3_constants['METADATA_SECONDS'])
receipts = []
expected_receipts = {}
for repository in metadata['repositories']:
    repo = repository['repo']
    receipts.extend(repository['query_coverage'])
    expected_receipts[f'repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=100&page=1'] = (
        'closed_pr_list', len(repository['candidates']))
    for candidate in repository['candidates']:
        if 'files' in candidate:
            # These retained scans all closed on one page; there is no unretained intermediate page.
            expected_receipts[f'repos/{repo}/pulls/{candidate["number"]}/files?per_page=100&page=1'] = (
                'changed_file_pages', len(candidate['files']))
for selected in frozen['pool']:
    repo = selected['repo']
    receipts.extend(selected['tree_query_coverage'])
    for side in ('base','head'):
        binding = selected['git_metadata_binding'][side]
        check(repo + ':' + side + ':commit_binding_matches_selected', binding['commit_sha'], selected[side + '_commit'])
        check(repo + ':' + side + ':tree_reports_nontruncated', binding['tree_truncated'], False)
        expected_receipts[f'repos/{repo}/git/commits/{selected[side + "_commit"]}'] = ('git_commit_metadata', None)
        expected_receipts[f'repos/{repo}/git/trees/{binding["tree_sha"]}?recursive=1'] = ('git_tree_metadata', None)
        check(repo + ':' + side + ':binding_retains_exact_changed_path_set',
            set(binding['changed_paths']), {row['filename'] for row in selected['files']})
        if side == 'head':
            for row in selected['files']:
                entry = binding['changed_paths'][row['filename']]
                check(repo + ':head:changed_path_and_file_blob_agree:' + row['filename'], entry is not None and entry['path'] == row['filename'] and entry['sha'] == row['sha'])
check('receipt_count_independently_counted', len(receipts), 137)
check('receipt_count_matches_reported_cost', len(receipts), metadata['costs']['metadata_api_calls'])
check('receipt_endpoints_all_unique', len({row['endpoint'] for row in receipts}), len(receipts))
check('receipt_expected_endpoint_set_exact', set(row['endpoint'] for row in receipts), set(expected_receipts))
receipt_kinds = collections.Counter()
timeline = []
receipt_durations = []
for receipt in receipts:
    endpoint = receipt['endpoint']
    kind, entries = expected_receipts[endpoint]
    receipt_kinds.update([kind])
    check(endpoint + ':exact_allowlisted_projection', receipt['projection'], plan['api_allowlist'][kind])
    check(endpoint + ':successful_retained_exit_status', receipt['status'] == 'OK' and receipt['returncode'] == 0)
    check(endpoint + ':within_per_call_timeout', 0 <= receipt['wall_seconds'] <= 60)
    if entries is not None:
        check(endpoint + ':entries_returned_matches_retained_rows', receipt['entries_returned'], entries)
    start = datetime.datetime.fromisoformat(receipt['requested_at_utc'])
    finish = start + datetime.timedelta(seconds=receipt['wall_seconds'])
    timeline.extend([(start, 1), (finish, -1)])
    receipt_durations.append(receipt['wall_seconds'])
timeline.sort()
concurrent = peak = 0
for when, change in timeline:
    concurrent += change
    peak = max(peak, concurrent)
span = (max(when for when, _ in timeline) - min(when for when, _ in timeline)).total_seconds()
check('retained_receipt_timestamp_span_within_metadata_wall', span <= metadata['costs']['metadata_wall_seconds'])
check('retained_receipt_peak_concurrency_at_most_three', peak <= 3)
check('reported_curation_wall_includes_metadata_wall', metadata['costs']['total_curation_wall_seconds'] >= metadata['costs']['metadata_wall_seconds'])

report = {
    'schema':'UDM_V41_METADATA_PREDICATE_SUBAUDIT_V1',
    'method':'Independent pure filesystem Python audit; parsed JSON and AST only; original curator was never imported or executed.',
    'authority':'Precommitted PREQUERY predicates, retained actual candidate sequence, exact retained curator source hashes, METADATA_CURATION, FROZEN_POOL.',
    'input_sha256':{name:digest(data) for name,data in raw.items()},
    'static_source_sha256':source_hashes,
    'boundaries':{'git_commands':0,'network_calls':0,'target_source_reads':0,'patch_reads':0,'native_executions':0,'outcome_reads':0,'original_curator_executions':0},
    'status':'PASS_WITH_RETAINED_EVIDENCE_LIMITATIONS' if all(item['passed'] for item in checks) else 'FAIL',
    'check_count':len(checks), 'passed_check_count':sum(item['passed'] for item in checks),
    'failed_checks':[item for item in checks if not item['passed']],
    'independent_totals':{'repositories':len(repo_reports),'candidates':sum(row['candidate_count'] for row in repo_reports),
        'file_scans':sum(row['file_scans_expected'] for row in repo_reports),'file_metadata_rows':file_rows,
        'qualifying_candidates':status_counts['QUALIFIES_METADATA_ONLY'],'rejected_candidates':status_counts['REJECTED_METADATA_PREDICATES'],
        'frozen_pool_members':len(selected_expected),'no_qualifying_repositories':sum(row['no_qualifying_case_independently_supported'] for row in repo_reports)},
    'reason_counts':dict(sorted(reason_counts.items())),
    'repositories':repo_reports,
    'API_receipt_audit':{
        'receipt_count':len(receipts), 'unique_endpoints':len({row['endpoint'] for row in receipts}),
        'receipt_kind_counts':dict(sorted(receipt_kinds.items())),
        'all_expected_endpoints_present_once':len(receipts) == len(expected_receipts) and set(row['endpoint'] for row in receipts) == set(expected_receipts),
        'all_exact_prequery_projections':all(row['projection'] == plan['api_allowlist'][expected_receipts[row['endpoint']][0]] for row in receipts),
        'all_status_OK_and_returncode_zero':all(row['status'] == 'OK' and row['returncode'] == 0 for row in receipts),
        'summed_call_seconds':sum(receipt_durations), 'minimum_call_seconds':min(receipt_durations),
        'maximum_call_seconds':max(receipt_durations), 'estimated_receipt_span_seconds':span,
        'estimated_peak_concurrent_calls':peak,
        'reported_metadata_wall_seconds':metadata['costs']['metadata_wall_seconds'],
        'reported_total_curation_wall_seconds':metadata['costs']['total_curation_wall_seconds'],
        'prequery_metadata_budget_seconds':plan['metadata_seconds'],
        'reported_tree_entry_total':sum(selected['git_metadata_binding'][side]['tree_entry_count'] for selected in frozen['pool'] for side in ('base','head')),
        'retained_changed_tree_entries':sum(entry is not None for selected in frozen['pool'] for side in ('base','head') for entry in selected['git_metadata_binding'][side]['changed_paths'].values()),
        'retained_null_changed_tree_entries':sum(entry is None for selected in frozen['pool'] for side in ('base','head') for entry in selected['git_metadata_binding'][side]['changed_paths'].values()),
        'static_guard_inspected':'V3 metadata_api fullmatches four endpoint patterns, requires exact projection and frozen-universe membership, records attempt before subprocess, uses timeout min(60,remaining), and marks OK after exit zero and projected JSON parsing. V41 and V4 retain that function.',
        'independent_second_reader':'A delegated pure-filesystem receipt audit independently obtained the same 137-count split, coverage, projection, timing and retention limitations.'},
    'returned_order_observations':{
        'selection_uses_retained_sequence_without_resorting':True,
        'static_original_scan_enumerates_API_items_without_sorting':True,
        'updated_at_nonincreasing_for_all_repositories':not inversions,
        'adjacent_updated_at_inversions':inversions,
        'first_qualifiers_unchanged_by_timestamp_sort_diagnostic':all(row['first_qualifier_unchanged_by_timestamp_sort_diagnostic'] for row in repo_reports),
        'interpretation':'The endpoint requests updated descending, but one retained semver adjacent timestamp pair is inverted. The committed algorithm uses API returned order, so the audit preserves the retained sequence. This alone does not establish its cause or authenticity.'},
    'limitations':[
        'No live API call was made. Retained candidate rows are the only retained closed-list payload; their external API authenticity and whether additional unretained calls occurred cannot be independently proven by these local artifacts.',
        'Receipts omit raw response stdout, response hashes, HTTP headers and successful HTTP status codes; OK means retained exit zero plus projected JSON parsing. Full recursive tree responses were discarded, so their reported entry totals, nonchanged schema and duplicate path absence cannot be reconstructed from only retained changed-path bindings.',
        'Only the latest at most 100 closed PRs per repository were declared; NO_QUALIFYING_CANDIDATE does not cover older pages or all repository history.',
        'One retained updated_at ordering inversion is documented without repairing, re-sorting, or retargeting the frozen pool.',
        'All 100 observed file scans close on their first page; multi-page, ceiling, timeout, error and refusal branches were inspected statically but not exercised.',
        'Metadata predicates do not demonstrate semantic bug relevance, native viability, test contents, native outcomes, independent admission, learning or G2/G3/G4.',
        'Native and collection call counts of zero are retained cost declarations supported by the inspected metadata query path, not a global observation of all external activity.'
    ],
}
destination = BASE / 'PREDICATE_SUBAUDIT.json'
destination.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps({'path':str(destination),'status':report['status'],'checks':report['check_count'],
    'failed_checks':report['failed_checks'],'independent_totals':report['independent_totals'],
    'inversions':inversions}, indent=2))
