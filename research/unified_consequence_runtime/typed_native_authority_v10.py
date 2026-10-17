"""V10 class-qualified native test authority, over byte-identical V6 verifier.

This is a versioned *selection of an already existing qualified authority*:
V6's source/Git-native collection, import, protected-assertion and mutation
checks are used byte-for-byte. Only the protected node grammar is enlarged to
admit class-qualified pytest methods, never changing tested source or the
meaning of a native PASS/FAIL/UNKNOWN outcome.

The previous V9 Tenacity RED remains RED, not a fresh successful G2 trial.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from types import FunctionType

from . import typed_native_authority_v6 as original

SCHEMA="UDM_V10_CLASS_QUALIFIED_PROTECTED_AUTHORITY"
ORIGINAL_V6_GIT_BLOB="7a813db84ef34a2dd16713b29fd3aced162a4955"
# A class prefix is a name, not a user-supplied file glob. Source path
# validation and actual executed/selected node evidence still belong to V6.
# Require proper pytest class nomenclature (Test*) and terminal test_* name.
_CLASS_NODE=re.compile(
    r"[A-Za-z0-9_./-]+::(?:Test[A-Za-z0-9_]*::)*test_[A-Za-z0-9_]+"
    r"(?:\[[^\]]+\])?\Z"
)


def verified_v6_source():
    """Authenticate the unchanged original verifier's actual Git blob."""
    path=Path(original.__file__).resolve()
    obtained=subprocess.check_output(
        ["git","hash-object",str(path)],text=True,timeout=10).strip()
    if obtained!=ORIGINAL_V6_GIT_BLOB:
        raise ValueError("original V6 verifier differs from qualified source")
    return True


# Rebind exactly the original code object privately: no writes to old globals,
# no monkey-patching V6, and no change to collection/JUnit/source semantics.
_PRIVATE=dict(vars(original), _NODE=_CLASS_NODE)
_RUN=FunctionType(original.run_protected.__code__,_PRIVATE,
                  "run_protected",original.run_protected.__defaults__,
                  original.run_protected.__closure__)
_RUN.__kwdefaults__=original.run_protected.__kwdefaults__


def run_protected(repo,commit,dest,*,required,interpreter=None,timeout=55,paths=None):
    verified_v6_source()
    kwargs={"required":required,"timeout":timeout,"paths":paths}
    if interpreter is not None:kwargs["interpreter"]=interpreter
    return _RUN(repo,commit,dest,**kwargs)


def stage(repo,commit,dest):
    verified_v6_source()
    return original.stage(repo,commit,dest)


def verify_stage(repo,commit,dest):
    verified_v6_source()
    return original.verify_stage(repo,commit,dest)


def accepts_class_method(prefix):
    """Lexical role only; actual native evidence remains independently needed."""
    return isinstance(prefix,str) and _CLASS_NODE.fullmatch(prefix) is not None
