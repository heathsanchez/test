"""Small read-only Git interval audit; index hashes never authorize restoration.

Discovery reads Git administration files directly, before starting Git. Retain
the returned JSON before/after evidence, including absent indexes and failures.
This does not attest to other files, concurrent actions, or native authority.
"""
from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
import subprocess


def _git_directories(repo):
    root = Path(repo).absolute()
    marker = root / '.git'
    if marker.is_dir():
        gitdir = marker
    elif marker.is_file():
        text = marker.read_text().strip()
        if not text.startswith('gitdir: ') or not text[8:]:
            raise ValueError('invalid Git directory marker')
        gitdir = Path(text[8:])
        if not gitdir.is_absolute():
            gitdir = root / gitdir
    elif (root / 'HEAD').is_file() and (root / 'objects').is_dir():
        gitdir = root
    else:
        raise ValueError('Git administration directory unavailable')
    gitdir = gitdir.resolve(strict=True)
    common_file = gitdir / 'commondir'
    common = (gitdir / common_file.read_text().strip()).resolve(strict=True) \
        if common_file.is_file() else gitdir
    return root, gitdir, common


def snapshot_indexes(repo, *, environ=None):
    """Hash common, current, all linked, and inherited alternate index paths."""
    env = os.environ if environ is None else environ
    root, gitdir, common = _git_directories(repo)
    paths = {common / 'index', gitdir / 'index'}
    worktrees = common / 'worktrees'
    if worktrees.exists():
        for entry in worktrees.iterdir():
            if entry.is_symlink() or not entry.is_dir():
                raise ValueError('unexpected linked-worktree administration entry')
            paths.add(entry / 'index')
    if env.get('GIT_INDEX_FILE'):
        alternate = Path(env['GIT_INDEX_FILE'])
        paths.add(alternate if alternate.is_absolute() else root / alternate)
    rows = []
    for path in sorted(paths):
        if path.is_symlink():
            raise ValueError('index symlinks cannot be audited as regular bytes')
        try:
            raw = path.read_bytes()
        except FileNotFoundError:
            raw = None
        rows.append({'path': str(path), 'exists': raw is not None,
                     'size_bytes': len(raw) if raw is not None else None,
                     'sha256': hashlib.sha256(raw).hexdigest() if raw is not None else None})
    return {'schema': 'UDM_GIT_INDEX_SNAPSHOT_V4',
            'git_common_dir': str(common), 'indexes': rows}


def compare_indexes(before, after):
    """Report changed byte/absence records and added/removed inventory paths."""
    old = {row['path']: row for row in before['indexes']}
    new = {row['path']: row for row in after['indexes']}
    return [{'path': path, 'before': old.get(path), 'after': new.get(path)}
            for path in sorted(old.keys() | new.keys()) if old.get(path) != new.get(path)]


def _read_args(args):
    # Closed local read grammar: never accept a mutator, output file, filter,
    # external diff, arbitrary global option, or interactive batch command.
    options = {
        'status': {'--porcelain', '--porcelain=v1', '--porcelain=v2', '-z',
                   '--short', '--branch', '--untracked-files=all', '--untracked-files=no'},
        'rev-parse': {'--verify', '--show-toplevel', '--git-dir', '--absolute-git-dir',
                      '--git-common-dir', '--show-prefix', '--is-bare-repository',
                      '--path-format=absolute', '--git-path'},
        'ls-tree': {'-r', '-z', '--name-only', '--full-tree'},
        'ls-files': {'-z', '--stage', '--cached', '--others', '--exclude-standard'},
        'diff': {'--name-only', '--name-status', '--no-renames', '--stat', '--quiet',
                 '--exit-code', '--no-ext-diff', '--no-textconv', '--cached'},
        'show': {'--no-patch', '--format=%H', '--no-ext-diff', '--no-textconv'},
    }
    if not isinstance(args, (list, tuple)) or not args or any(
            not isinstance(arg, str) or not arg or '\x00' in arg or '\n' in arg
            for arg in args):
        raise ValueError('explicit nonempty read-only Git arguments required')
    args = list(args)
    if args[0] == 'worktree':
        if args not in (['worktree', 'list'], ['worktree', 'list', '--porcelain'],
                        ['worktree', 'list', '--porcelain', '-z']):
            raise ValueError('only worktree list is a permitted read')
    elif args[0] == 'cat-file':
        if len(args) != 3 or args[1] not in ('blob', 'tree', 'commit', '-p', '-t', '-s') \
                or args[2].startswith('-'):
            raise ValueError('only a single immutable cat-file read is permitted')
    elif args[0] not in options or any(
            arg.startswith('-') and arg not in options[args[0]] for arg in args[1:]):
        raise ValueError('unsupported or mutating Git command/options')
    if args[0] in ('diff', 'show'):
        args = [args[0], '--no-ext-diff', '--no-textconv', *args[1:]]
    return args


def audit_git_read(repo, args):
    """Read Git with optional locks disabled, retaining evidence even on failure.

    No index restoration/reset exists. A nonzero command result or index delta
    stays visible to the caller. Keep each returned record, not just its verdict.
    """
    args = _read_args(args)
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    for name in ('GIT_DIR', 'GIT_COMMON_DIR', 'GIT_WORK_TREE'):
        if env.get(name):
            raise ValueError(name + ' override would change the audited repository')
    before = snapshot_indexes(repo, environ=env)
    argv = ['git', '--no-pager', '--no-replace-objects', '-c', 'core.fsmonitor=false',
            '-C', str(Path(repo).absolute()), *args]
    result = {'schema': 'UDM_GIT_INDEX_READ_AUDIT_V4', 'argv': argv,
              'git_optional_locks': '0', 'before': before,
              'returncode': None, 'stdout_base64': '', 'stderr_base64': ''}
    try:
        read = subprocess.run(argv, env=env, stdin=subprocess.DEVNULL,
                              capture_output=True, timeout=60)
        result.update(returncode=read.returncode,
                      stdout_base64=base64.b64encode(read.stdout).decode('ascii'),
                      stderr_base64=base64.b64encode(read.stderr).decode('ascii'))
    except (OSError, subprocess.TimeoutExpired) as error:
        result['error'] = type(error).__name__ + ': ' + str(error)
        if isinstance(error, subprocess.TimeoutExpired):
            result['stdout_base64'] = base64.b64encode(error.stdout or b'').decode('ascii')
            result['stderr_base64'] = base64.b64encode(error.stderr or b'').decode('ascii')
    after = snapshot_indexes(repo, environ=env)
    result['after'] = after
    result['index_changes'] = compare_indexes(before, after)
    result['indexes_unchanged'] = not result['index_changes']
    return result
