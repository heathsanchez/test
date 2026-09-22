import json
import tempfile
import unittest
from pathlib import Path

from scripts.lka_semantic_atlas import (
    CasePath,
    analyze_case,
    build_atlas,
    numbered_cases,
)


META = {
    "meta": {
        "format": {"version": "3.1.0"},
        "exporter": {"name": "test", "version": "0"},
        "lean": {"version": "test", "githash": "0" * 40},
    }
}


def write_case(root: Path, number: int, good: bool, records: list[dict]) -> Path:
    directory = root / ("good" if good else "bad")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{number:03d}_case.ndjson"
    payload = [META, *records]
    path.write_text("\n".join(json.dumps(record) for record in payload) + "\n")
    return path


class AtlasInputTests(unittest.TestCase):
    def test_numbered_cases_requires_exact_numbered_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_case(root, 1, True, [])
            write_case(root, 2, False, [])
            cases = numbered_cases(root, 1, 2)
            self.assertEqual([case.expected_exit for case in cases], [0, 1])
            self.assertEqual([case.number for case in cases], [1, 2])

    def test_indexed_inductive_dimension_is_structural(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = write_case(
                root,
                43,
                True,
                [
                    {"in": 1, "str": {"pre": 0, "str": "Eq"}},
                    {"in": 2, "str": {"pre": 0, "str": "u"}},
                    {"il": 1, "param": 2},
                    {"ie": 0, "sort": 1},
                    {
                        "inductive": {
                            "types": [
                                {
                                    "all": [1],
                                    "ctors": [1],
                                    "isRec": False,
                                    "isReflexive": False,
                                    "isUnsafe": False,
                                    "levelParams": [2],
                                    "name": 1,
                                    "numIndices": 1,
                                    "numNested": 0,
                                    "numParams": 1,
                                    "type": 0,
                                }
                            ],
                            "ctors": [
                                {
                                    "cidx": 0,
                                    "induct": 1,
                                    "isUnsafe": False,
                                    "levelParams": [2],
                                    "name": 1,
                                    "numFields": 0,
                                    "numParams": 1,
                                    "type": 0,
                                }
                            ],
                            "recs": [
                                {
                                    "all": [1],
                                    "isUnsafe": False,
                                    "k": False,
                                    "levelParams": [2],
                                    "name": 1,
                                    "numIndices": 1,
                                    "numMinors": 1,
                                    "numMotives": 1,
                                    "numParams": 1,
                                    "rules": [
                                        {"ctor": 1, "nfields": 0, "rhs": 0}
                                    ],
                                    "type": 0,
                                }
                            ],
                        }
                    },
                ],
            )
            row = analyze_case(CasePath(43, path, 0))
            dims = set(row["structural"]["dimensions"])
            self.assertIn("inductive", dims)
            self.assertIn("indices", dims)
            self.assertIn("parameters", dims)
            self.assertIn("equality_family", dims)
            self.assertIn("universe_polymorphism", dims)

    def test_atlas_separates_first_occurrence_from_sealed_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path1 = write_case(
                root,
                1,
                True,
                [{"ie": 0, "sort": 0}, {"def": {"name": 0}}],
            )
            path2 = write_case(
                root,
                2,
                True,
                [{"ie": 0, "proj": {"typeName": 0}}, {"def": {"name": 0}}],
            )
            atlas = build_atlas(
                [CasePath(1, path1, 0), CasePath(2, path2, 0)],
                checker=None,
                sealed_end=1,
                report_start=2,
            )
            row = atlas["cases"][0]
            self.assertIn("projection", row["new_dimensions_vs_sealed"])
            self.assertIn("unsupported_expr:proj", row["first_occurrence_dimensions"])


if __name__ == "__main__":
    unittest.main()
