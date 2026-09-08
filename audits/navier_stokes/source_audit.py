#!/usr/bin/env python3
"""Reproducible source-level comparison; not a semantic or authorship verdict."""
import argparse, collections, hashlib, json, pathlib, re, subprocess

SOURCES = {
    'openai': ('8937a8f4cbc7abaab5e9e97d1cc7f5d2319d9538', ['NavierStokes']),
    'alpoge_buckmaster': ('d0124689230b58b4f86e7b90ac59de06404b3b6b', ['affinecore', 'boussinesq-blowup', 'euler-blowup']),
}
DECL = re.compile(r'^\s*(?:(?:private|protected|noncomputable|unsafe|partial|local|scoped)\s+)*(?:theorem|lemma|def|abbrev|structure|class|inductive|instance|axiom|opaque)\s+([^\s(:{]+)', re.M)
IMPORT = re.compile(r'^\s*import\s+(.+)$', re.M)
TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|\'[^\'\n]*\'|[\w\u0080-\uffff]+|[^\s]', re.UNICODE)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def clean(text):
    """Erase nested Lean comments, preserving newlines and string literals."""
    out = []; i = 0; depth = 0; quoted = False
    while i < len(text):
        if depth:
            if text.startswith('/-', i): depth += 1; out.extend('  '); i += 2
            elif text.startswith('-/', i): depth -= 1; out.extend('  '); i += 2
            else:
                out.append('\n' if text[i] == '\n' else ' '); i += 1
        elif quoted:
            ch = text[i]; out.append(ch); i += 1
            if ch == '\\' and i < len(text): out.append(text[i]); i += 1
            elif ch == '"': quoted = False
        elif text.startswith('/-', i): depth = 1; out.extend('  '); i += 2
        elif text.startswith('--', i):
            while i < len(text) and text[i] != '\n': out.append(' '); i += 1
        elif text[i] == '"': quoted = True; out.append('"'); i += 1
        else: out.append(text[i]); i += 1
    if depth: raise ValueError('Unclosed block comment')
    return ''.join(out)

def tokens(text):
    return TOKEN.findall(text)

def declarations(text):
    text = clean(text)
    matches = list(DECL.finditer(text))
    result = []
    for i, m in enumerate(matches):
        body = text[m.start():matches[i+1].start() if i+1 < len(matches) else len(text)]
        ts = tokens(body)
        result.append({'name': m.group(1), 'line': text.count('\n', 0, m.start()) + 1,
                       'tokens': len(ts), 'fingerprint': sha('\0'.join(ts).encode())})
    return result

def run(*args, cwd=None):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()

def collect(root, label):
    expected, folders = SOURCES[label]
    actual = run('git', 'rev-parse', 'HEAD', cwd=root)
    if actual != expected: raise RuntimeError(f'{label}: expected {expected}, got {actual}')
    paths = sorted(p for p in pathlib.Path(root).rglob('*.lean') if '.lake' not in p.parts and '.git' not in p.parts)
    paths = [p for p in paths if p.relative_to(root).parts[0] in folders]
    files = []; all_decls = []
    for p in paths:
        rel = p.relative_to(root).as_posix(); data = p.read_bytes(); text = data.decode('utf-8')
        stripped = clean(text); ts = tokens(stripped)
        imports = [word for m in IMPORT.finditer(stripped) for word in m.group(1).split()]
        ds = declarations(text)
        for d in ds: all_decls.append(dict(d, file=rel))
        files.append({'path': rel, 'sha256': sha(data), 'token_sha256': sha('\0'.join(ts).encode()),
                      'bytes': len(data), 'lines': len(text.splitlines()), 'imports': imports,
                      'declaration_candidates': len(ds)})
    return {'commit': actual, 'files': files, 'declarations': all_decls}

def compare(a, b):
    def matches(key, left, right):
        ix = collections.defaultdict(list)
        for r in right: ix[r[key]].append(r['path'])
        return [{'left': r['path'], 'right': ix[r[key]], 'fingerprint': r[key]}
                for r in left if r[key] in ix]
    def decl_matches(left, right):
        ix = collections.defaultdict(list)
        for d in right:
            if d['tokens'] >= 80: ix[d['fingerprint']].append({'file': d['file'], 'line': d['line'], 'name': d['name']})
        return [{'left': {'file': d['file'], 'line': d['line'], 'name': d['name']}, 'right': ix[d['fingerprint']], 'fingerprint': d['fingerprint']}
                for d in left if d['tokens'] >= 80 and d['fingerprint'] in ix]
    exact = matches('sha256', a['files'], b['files'])
    normalized = matches('token_sha256', a['files'], b['files'])
    decls = decl_matches(a['declarations'], b['declarations'])
    return {'scope': 'project Lean sources only; comments/whitespace normalization is not semantic equivalence',
            'counts': {key: {'files': len(v['files']), 'lines': sum(f['lines'] for f in v['files']),
                             'declaration_candidates': len(v['declarations'])} for key,v in [('openai',a),('alpoge_buckmaster',b)]},
            'exact_file_matches': exact, 'normalized_file_matches': normalized,
            'normalized_declaration_span_matches_min80tokens': decls,
            'limitations': ['Declaration spans are heuristic and may include adjacent commands.',
                            'Names, matching text and shared dependencies do not establish mathematical equivalence or provenance.',
                            'No source comparison determines whether the Clay problem is solved.']}

def selftest():
    s = 'theorem a : True := by\n  /- nested /- sorry -/ -/\n  trivial\n-- sorry\ntheorem b : True := by trivial\n'
    assert len(declarations(s)) == 2
    assert 'sorry' not in clean(s)
    assert clean('def x := "-- /- text"\n').count('"') == 2
    assert tokens('a  + b') == tokens('a+b')
    assert sha(b'a') != sha(b'b')
    print('SOURCE_AUDIT_SELFTEST_PASS')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--openai'); ap.add_argument('--ab'); ap.add_argument('--output', default='audit-results'); ap.add_argument('--selftest', action='store_true')
    args = ap.parse_args()
    if args.selftest: selftest(); return
    out = pathlib.Path(args.output); out.mkdir(parents=True, exist_ok=True)
    a = collect(pathlib.Path(args.openai), 'openai'); b = collect(pathlib.Path(args.ab), 'alpoge_buckmaster')
    result = compare(a,b)
    for name, value in [('openai_inventory',a),('alpoge_buckmaster_inventory',b),('source_comparison',result)]:
        (out/(name+'.json')).write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'counts':result['counts'], 'exact_file_matches':len(result['exact_file_matches']), 'normalized_file_matches':len(result['normalized_file_matches']), 'normalized_declaration_spans':len(result['normalized_declaration_span_matches_min80tokens'])}, indent=2))
    print('SOURCE_COMPARISON_COMPLETE')
if __name__ == '__main__': main()
