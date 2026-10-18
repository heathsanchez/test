"""Prospective metadata-only curation; never fetches source or executes tasks.

The repository universe and selection rules are constants chosen before queries.
GitHub's --jq projection removes body, patch, source URLs, and CI fields before
anything reaches this process's stdout capture or a persisted file.
"""
from __future__ import annotations

import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import re
import subprocess
from typing import Any

OUTPUT = pathlib.Path('/workspace/qualification/admission-v2-fresh-metadata.json')
PREQUERY = pathlib.Path('/workspace/qualification/admission-v2-fresh-prequery.json')
UNIVERSE = (
    'dateutil/dateutil',
    'grahamdumpleton/wrapt',
    'jab/bidict',
    'pallets/click',
    'pallets/markupsafe',
    'pypa/packaging',
)
RESEARCH = pathlib.Path('/workspace/udm-v54/research/unified_consequence_runtime')
HISTORICAL_METADATA = (
    'capability_index.json',
    'sources.json',
    'developmental_sources.json',
    'native_policy.json',
    'archaeology/decisive-native/FRESH_TASK_METADATA.json',
    'archaeology/decisive-native/CODING_AGENT_FREEZE.json',
    'archaeology/decisive-native/QUALIFICATION_FREEZE.json',
    'archaeology/decisive-native/PROTOCOL.json',
    'archaeology/decisive-native/AUTHOR_TEST_BLOBS.json',
    'archaeology/v54-continuation/PROSPECTIVE_FRONTIER_FROZEN.json',
    'archaeology/v54-continuation/SOURCE_MANIFEST.json',
    'archaeology/recursive-frontier/GREEN_MAINTENANCE_FREEZE.json',
    'archaeology/programme-closure/REPOSITORIES.json',
    'archaeology/programme-closure/FROZEN_UNIVERSE.json',
    'archaeology/programme-closure/DISCOVERED_CANDIDATES.json',
    'archaeology/programme-closure/CROSS_FRONTIER_SOURCE_INDEX.json',
    'external_pr_v1/FROZEN_PROTOCOL.json',
    'external_pr_v1/admission_policy.json',
    'native_semantic_genesis_v1/FROZEN_PROTOCOL.json',
    'native_unbounded_v1/FROZEN_PROTOCOL.json',
    'typed_semantic_method_v1/FROZEN_PROTOCOL.json',
)
PR_FIELDS = '[.[] | {number,title,merged_at,closed_at,updated_at,labels:[.labels[].name],base:{sha:.base.sha},head:{sha:.head.sha},merge_commit_sha,url:.html_url}]'
FILE_FIELDS = '[.[] | {filename,status,additions,deletions,changes,sha}]'
COMMIT_FIELDS = '{sha,tree_sha:.tree.sha,parents:[.parents[].sha]}'
TREE_FIELDS = '{sha,truncated,tree:[.tree[] | {path,mode,type,sha,size}]}'


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: pathlib.Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def historical_exclusions() -> tuple[dict[str, list[str]], list[dict[str, Any]]]:
    evidence: dict[str, list[str]] = {}
    inputs: list[dict[str, Any]] = []

    def strings(value: Any, key: str = ''):
        if isinstance(value, dict):
            for child_key, child in value.items():
                yield from strings(child, child_key)
        elif isinstance(value, list):
            for child in value:
                yield from strings(child, key)
        elif isinstance(value, str):
            yield key, value

    for relative in HISTORICAL_METADATA:
        path = RESEARCH / relative
        if not path.exists():
            inputs.append({'path': str(path), 'status': 'MISSING'})
            continue
        value = json.loads(path.read_text())
        repos: set[str] = set()
        for key, string in strings(value):
            for match in re.findall(r'(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)', string):
                repos.add(match.removesuffix('.git'))
            if ('repo' in key.lower() or key.lower() in {'repository_order', 'repositories'}) and re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', string):
                repos.add(string.removesuffix('.git'))
        for repo in repos:
            evidence.setdefault(repo.lower(), []).append(str(path))
        inputs.append({'path': str(path), 'sha256': digest(path), 'repositories': sorted(repos)})
    # The capability's native domain is named in its stable identifier, while
    # its repository field names the enclosing research repository.
    evidence.setdefault('go-chi/chi', []).append(str(RESEARCH / 'capability_index.json') + '#jpl-observation-quotient-native-chi-servemux')
    return evidence, inputs


def prequery_plan() -> dict[str, Any]:
    exclusions, inputs = historical_exclusions()
    return {
        'schema': 'UDM_NATIVE_ADMISSION_V2_METADATA_PREQUERY_V1',
        'created_at_utc': now(),
        'curation_code_sha256': digest(pathlib.Path(__file__)),
        'repository_universe_fixed_before_github_queries': list(UNIVERSE),
        'universe_order': 'Ascending lexicographic repository full name; fixed six repositories, no expansion on shortfall.',
        'requested_tasks': 3,
        'role_assignment': ['TRAINING', 'PROTECTED_FUTURE', 'PROTECTED_FUTURE'],
        'selection_algorithm': 'For each eligible repository, examine the latest 100 closed PRs from page 1, per_page=100, sort=updated, direction=desc. Evaluate every listed PR under the fixed metadata predicates and retain every candidate with a reason. Choose the first eligible PR in returned order per repository, then the first three qualifying repositories in fixed sorted order. No alternative is selected using source, tests, outcomes, or viability.',
        'metadata_predicates': {
            'merged': True,
            'title_or_label': 'Case-insensitive title starts fix OR a label contains bug.',
            'production_py_files_min': 1,
            'test_py_files_min': 1,
            'production_total_deletions_inclusive': [1, 4],
            'production_total_additions_max': 6,
            'no_changed_file_renamed_or_removed': True,
            'tests_classifier': 'A .py file with a test/tests/testing path component, a test_ basename, an _test.py basename, or conftest.py. Production means other .py files.',
            'file_metadata_pagination': 'Page from 1 with per_page=100 until a page has fewer than 100 entries; reject if API pagination cannot be closed.',
        },
        'historical_metadata_inputs': inputs,
        'historically_touched_repository_exclusions': dict(sorted(exclusions.items())),
        'untouched_assessment': {
            'basis': 'Absence from the explicitly listed accessible historical metadata, prior repository universes, frozen metadata, and known native-domain identifiers. The previous itsdangerous and blinker queries are exclusions even without a selected task.',
            'boundary': 'This establishes a bounded accessible-record check, not absolute unfamiliarity or absence of all prior human/model knowledge. Absence from the 70-entry index alone is not treated as proof.',
        },
        'api_allowlist': {
            'closed_pr_list': PR_FIELDS,
            'changed_file_pages': FILE_FIELDS,
            'git_commit_metadata': COMMIT_FIELDS,
            'git_tree_metadata': TREE_FIELDS,
        },
        'exposure_boundary': {
            'target_source_read': False,
            'test_contents_read': False,
            'production_patches_read': False,
            'pr_bodies_read': False,
            'ci_results_read': False,
            'outcomes_read': False,
            'native_execution': False,
            'repository_edits': False,
            'git_fetch_or_clone': False,
            'raw_patch_or_body_persisted': False,
            'filter': 'gh api --jq projects allowed metadata before stdout capture or disk. No contents/blob endpoints, PR body, patch, raw URLs, CI fields, or commit messages are requested for output.',
        },
        'freeze_status': 'PROSPECTIVE_METADATA_ONLY_NOT_FROZEN; admission gate and root authorization required before freeze.',
    }


def gh(endpoint: str, projection: str, coverage: list[dict[str, Any]]) -> Any:
    record = {'endpoint': endpoint, 'projection': projection, 'requested_at_utc': now()}
    coverage.append(record)
    proc = subprocess.run(['gh', 'api', endpoint, '--jq', projection], text=True, capture_output=True)
    record['returncode'] = proc.returncode
    if proc.returncode:
        status = re.search(r'HTTP (\d{3})', proc.stderr)
        record['status'] = 'API_ERROR'
        if status:
            record['http_status'] = int(status.group(1))
        # stderr is deliberately neither printed nor persisted.
        raise RuntimeError('GITHUB_METADATA_API_ERROR' + (f'_HTTP_{status.group(1)}' if status else ''))
    value = json.loads(proc.stdout)
    record['status'] = 'OK'
    if isinstance(value, list):
        record['entries_returned'] = len(value)
    return value


def is_test(name: str) -> bool:
    path = pathlib.PurePosixPath(name)
    return name.endswith('.py') and (
        any(part in {'test', 'tests', 'testing'} for part in path.parts)
        or path.name.startswith('test_')
        or path.name.endswith('_test.py')
        or path.name == 'conftest.py'
    )


def scan(repo: str, exclusions: dict[str, list[str]]) -> dict[str, Any]:
    out: dict[str, Any] = {'repo': repo, 'query_coverage': [], 'candidates': []}
    if repo.lower() in exclusions:
        out.update(status='EXCLUDED_PREVIOUS_RESEARCH_EXPOSURE', reasons=['HISTORICAL_METADATA_EXPOSURE'], evidence=exclusions[repo.lower()])
        return out
    try:
        items = gh(f'repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=100&page=1', PR_FIELDS, out['query_coverage'])
    except RuntimeError as exc:
        out.update(status='UNAVAILABLE', reasons=[str(exc)])
        return out
    out['closed_pr_count'] = len(items)
    out['closed_pr_window'] = {'page': 1, 'per_page': 100, 'scope': 'Latest at most 100 closed PRs; older pages outside the fixed universe.', 'sort': 'updated', 'direction': 'desc'}
    for rank, pr in enumerate(items, 1):
        candidate = dict(pr, rank_within_repository=rank)
        reasons: list[str] = []
        if not pr['merged_at']:
            reasons.append('NOT_MERGED')
        if not (re.match(r'^fix', pr['title'], re.I) or any('bug' in label.lower() for label in pr['labels'])):
            reasons.append('TITLE_NOT_FIX_AND_NO_BUG_LABEL')
        if not reasons:
            files: list[dict[str, Any]] = []
            page = 1
            try:
                while True:
                    chunk = gh(f'repos/{repo}/pulls/{pr["number"]}/files?per_page=100&page={page}', FILE_FIELDS, out['query_coverage'])
                    files.extend(chunk)
                    if len(chunk) < 100:
                        break
                    page += 1
                    if page > 30:
                        reasons.append('FILES_API_3000_FILE_LIMIT_PAGINATION_NOT_CLOSED')
                        break
            except RuntimeError as exc:
                reasons.append(str(exc))
            candidate['files'] = files
            candidate['file_pagination'] = {'pages_requested': page, 'entries_returned': len(files), 'closed': not any('ERROR' in reason or 'PAGINATION_NOT_CLOSED' in reason for reason in reasons)}
            if any(file['status'] in {'renamed', 'removed'} for file in files):
                reasons.append('RENAMED_OR_REMOVED_CHANGED_FILE')
            tests = [file for file in files if is_test(file['filename'])]
            production = [file for file in files if file['filename'].endswith('.py') and not is_test(file['filename'])]
            additions = sum(file['additions'] for file in production)
            deletions = sum(file['deletions'] for file in production)
            candidate['metadata_stats'] = {'test_py_files': len(tests), 'production_py_files': len(production), 'production_additions': additions, 'production_deletions': deletions}
            if not tests:
                reasons.append('NO_CHANGED_TEST_PY')
            if not production:
                reasons.append('NO_CHANGED_PRODUCTION_PY')
            if not 1 <= deletions <= 4:
                reasons.append('PRODUCTION_DELETIONS_OUTSIDE_1_TO_4')
            if additions > 6:
                reasons.append('PRODUCTION_ADDITIONS_ABOVE_6')
        candidate['status'] = 'REJECTED_METADATA_PREDICATES' if reasons else 'QUALIFIES_METADATA_ONLY'
        candidate['reasons'] = reasons
        out['candidates'].append(candidate)
    qualifiers = [candidate for candidate in out['candidates'] if not candidate['reasons']]
    out['status'] = 'QUALIFYING_METADATA_CANDIDATE' if qualifiers else 'NO_QUALIFYING_CANDIDATE'
    out['qualifying_prs'] = [candidate['number'] for candidate in qualifiers]
    if qualifiers:
        out['first_qualifying_pr'] = qualifiers[0]['number']
        for candidate in qualifiers[1:]:
            candidate['selection_disposition'] = 'NOT_FIRST_ELIGIBLE_PR_IN_FIXED_ORDER'
    return out


def bind_tree_metadata(selected: dict[str, Any]) -> None:
    coverage: list[dict[str, Any]] = []
    selected['tree_query_coverage'] = coverage
    bindings = selected['git_metadata_binding'] = {}
    for side in ('base', 'head'):
        commit_sha = selected[f'{side}_commit']
        commit = gh(f'repos/{selected["repo"]}/git/commits/{commit_sha}', COMMIT_FIELDS, coverage)
        if commit['sha'] != commit_sha:
            raise RuntimeError('COMMIT_METADATA_SHA_MISMATCH')
        tree = gh(f'repos/{selected["repo"]}/git/trees/{commit["tree_sha"]}?recursive=1', TREE_FIELDS, coverage)
        if tree['truncated']:
            raise RuntimeError('TRUNCATED_TREE_METADATA')
        entries = {entry['path']: entry for entry in tree['tree']}
        changed = {}
        for file in selected['files']:
            path = file['filename']
            changed[path] = entries.get(path)
            if side == 'head' and file['status'] != 'removed':
                if path not in entries or entries[path]['sha'] != file['sha']:
                    raise RuntimeError('HEAD_CHANGED_BLOB_ID_MISMATCH')
        bindings[side] = {'commit_sha': commit['sha'], 'tree_sha': commit['tree_sha'], 'parents': commit['parents'], 'tree_truncated': False, 'tree_entry_count': len(tree['tree']), 'changed_paths': changed}
    selected['metadata_binding_status'] = 'EXACT_COMMIT_TREE_AND_CHANGED_BLOB_IDS_BOUND_WITHOUT_SOURCE_CONTENTS'


def main() -> None:
    plan = prequery_plan()
    if PREQUERY.exists() or OUTPUT.exists():
        raise SystemExit('Refusing to replace existing prequery/report metadata; preserve the first curation.')
    write_json(PREQUERY, plan)
    exclusions = plan['historically_touched_repository_exclusions']
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        pending = {repo: pool.submit(scan, repo, exclusions) for repo in UNIVERSE}
        results = [pending[repo].result() for repo in UNIVERSE]
    selected: list[dict[str, Any]] = []
    for result in results:
        if result['status'] != 'QUALIFYING_METADATA_CANDIDATE':
            continue
        first = next(candidate for candidate in result['candidates'] if not candidate['reasons'])
        if len(selected) == 3:
            first['selection_disposition'] = 'REPOSITORY_AFTER_FIRST_THREE_QUALIFYING_REPOSITORIES'
            continue
        first['selection_disposition'] = 'PROVISIONALLY_SELECTED_NOT_FROZEN'
        selected.append({
            'repo': result['repo'], 'pr': first['number'], 'metadata_url': first['url'],
            'base_commit': first['base']['sha'], 'head_commit': first['head']['sha'],
            'merge_commit_sha': first['merge_commit_sha'],
            'role': 'TRAINING' if not selected else 'PROTECTED_FUTURE',
            'files': first['files'], 'metadata_stats': first['metadata_stats'],
            'selection_status': 'PROVISIONAL_METADATA_SELECTION_NOT_FROZEN',
        })
    report = dict(plan, schema='UDM_NATIVE_ADMISSION_V2_FRESH_METADATA_CURATION_V1', completed_at_utc=now(), prequery_file=str(PREQUERY), prequery_sha256=digest(PREQUERY), repositories=results, selected=selected, selection_shortfall=max(0, 3 - len(selected)))
    # Persist the complete candidate record before additional selected metadata
    # queries, and preserve binding errors instead of changing selection.
    write_json(OUTPUT, report)
    for subject in selected:
        try:
            bind_tree_metadata(subject)
        except RuntimeError as exc:
            subject['metadata_binding_status'] = 'BINDING_ERROR_SELECTION_NOT_RETARGETED'
            subject['metadata_binding_error'] = str(exc)
        write_json(OUTPUT, report)
    report['completed_at_utc'] = now()
    report['selection_uncertainty'] = [
        'Metadata predicates do not establish a genuine bug, build viability, solvability, independent contract adequacy, or prospective success.',
        'Titles, labels, paths, line counts, commit IDs, and tree/blob identifiers were exposed only to this metadata curator; source/test bytes and outcomes were not accessed.',
        'Role assignments and selection are provisional. No frontier freeze, target execution, ROS update, commit, or promotion occurred.',
        'Any admission-gate failure, shortfall, or metadata binding failure is retained; it does not authorize expansion or retargeting.',
    ]
    write_json(OUTPUT, report)
    print(json.dumps({'path': str(OUTPUT), 'sha256': digest(OUTPUT), 'prequery_path': str(PREQUERY), 'prequery_sha256': digest(PREQUERY), 'freeze_status': report['freeze_status'], 'selection_shortfall': report['selection_shortfall'], 'selected': [{key: item[key] for key in ('repo', 'pr', 'role', 'base_commit', 'head_commit', 'metadata_binding_status')} for item in selected], 'repository_status': [{'repo': item['repo'], 'status': item['status'], 'candidates': len(item['candidates'])} for item in results]}, indent=2))


if __name__ == '__main__':
    main()
