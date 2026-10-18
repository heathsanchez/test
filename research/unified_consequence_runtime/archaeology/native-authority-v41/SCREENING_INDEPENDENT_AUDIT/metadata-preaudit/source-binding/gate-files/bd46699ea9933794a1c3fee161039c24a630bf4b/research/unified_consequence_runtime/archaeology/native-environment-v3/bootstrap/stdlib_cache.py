"""Original-interpreter bytecode preparation, compatible with Python 3.6."""
import hashlib
import json
import os
from pathlib import Path
import py_compile
import sys

RUNTIME_SUFFIXES = ('.py', '.pyc', '.pyo', '.so', '.pyd', '.dll', '.dylib')


def files(roots):
    result = set()
    for name in sorted(set(roots)):
        root = Path(name).absolute()
        if not root.exists():
            continue
        if root.is_symlink() or not root.is_dir():
            raise ValueError('original stdlib root must be a real directory')
        for folder, directories, names in os.walk(str(root)):
            directories[:] = sorted(name for name in directories
                if name not in ('site-packages', 'dist-packages')
                and not Path(folder, name).is_symlink())
            result.update(Path(folder, name).absolute() for name in names)
    return sorted(result)


def manifest(roots, suffixes=None, exclude_bytecode=False):
    result = {}
    for path in files(roots):
        if exclude_bytecode and path.suffix in ('.pyc', '.pyo'):
            continue
        if suffixes is not None and not str(path).endswith(suffixes):
            continue
        result[str(path.resolve())] = hashlib.sha256(path.read_bytes()).hexdigest()
    return [[name, result[name]] for name in sorted(result)]


def compile_sources(roots):
    compiled = 0; failures = []
    for path in files(roots):
        if path.suffix != '.py':
            continue
        for optimize in (0, 1, 2):
            try:
                py_compile.compile(str(path), doraise=True, optimize=optimize)
                compiled += 1
            except py_compile.PyCompileError as error:
                if error.exc_type_name not in ('SyntaxError', 'IndentationError', 'TabError'):
                    raise
                failures.append({'path': str(path), 'optimize': optimize,
                                 'exception': error.exc_type_name, 'message': error.msg})
    return {'compiled': compiled, 'failures': failures, 'optimization_modes': [0, 1, 2]}


if __name__ == '__main__':
    print(json.dumps(compile_sources(json.loads(sys.argv[1])), sort_keys=True))
