"""Frozen entry point for the external MiniF2F protocol.

The first pre-flight run exposed a parser whitespace bug before the external
repository was checked out.  Keep that failed commit as provenance and apply
only the minimal whitespace normalization here so the subsequent freeze remains
untainted by Test.lean bytes.
"""
from __future__ import annotations

from . import external_minif2f as _base


def _parse_expr_stripped(text: str, variable: str):
    return _base._PolynomialParser(text.strip(), variable).parse()


_base._parse_expr = _parse_expr_stripped

extract_candidates = _base.extract_candidates
freeze_source = _base.freeze_source
qualify_external = _base.qualify_external
ExternalMiniF2FAdapter = _base.ExternalMiniF2FAdapter


def main() -> None:
    _base.main()


if __name__ == "__main__":
    main()
