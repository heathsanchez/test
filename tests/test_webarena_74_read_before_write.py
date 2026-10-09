"""Protect the benchmark's pristine source observations from earlier writes.

A previous combined suite ran Reddit post creation before Books hot-list reads;
the same read-only capabilities were independently green but became empty
after shared-site mutations. Keep read-before-write qualification explicit.
"""
import re
import unittest
from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/webarena_unified_blind_four_site_74.yml"


def ordering_from_workflow(contents: str):
    match = re.search(r"^\s*ids=([a-z_+]+)\s*$", contents, flags=re.MULTILINE)
    if match is None:
        raise AssertionError("suite ordering declaration missing")
    return match.group(1).split("+")


class ReadBeforeWriteQualification(unittest.TestCase):
    def test_reddit_readonly_precedes_mutations(self):
        names = ordering_from_workflow(WORKFLOW.read_text())
        self.assertEqual(len(names), len(set(names)))
        for mutant in ("reddit", "crosssite"):
            with self.subTest(mutant=mutant):
                self.assertLess(
                    names.index("reddit_retrieval"),
                    names.index(mutant),
                    "read-only Reddit observations must precede forum mutations",
                )

    def test_all_74_ids_still_included_without_duplicates(self):
        contents = WORKFLOW.read_text()
        groups = ordering_from_workflow(contents)
        bindings = {}
        for name in groups:
            m = re.search(
                rf"^\s*{re.escape(name)}=\(([0-9,]+)\)\s*$",
                contents,
                flags=re.MULTILINE,
            )
            self.assertIsNotNone(m, f"missing immutable qualification group {name}")
            bindings[name] = [int(x) for x in m.group(1).split(",")]
        all_ids = [item for name in groups for item in bindings[name]]
        self.assertEqual(len(all_ids), 74)
        self.assertEqual(len(set(all_ids)), 74)


if __name__ == "__main__":
    unittest.main()
