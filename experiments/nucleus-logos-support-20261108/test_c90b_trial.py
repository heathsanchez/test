import unittest

from c90b_c32_cap_sweep import parse_c32, parse_work


class C90BParsing(unittest.TestCase):
    def test_budget_respects_cap_and_owner(self):
        line='NUCLEUS_C32_MAJOR_GRANT:seq=1:head=NameId(147):cap=4096:budget=503:owner=Some(503)'
        rows=parse_c32([line],4096)
        self.assertEqual(rows[0]['budget'],503)
        with self.assertRaises(AssertionError):
            parse_c32([line],512)

    def test_source_work_requires_all_fields(self):
        line='NUCLEUS_C47_INNER_WORK:outer_spent=457:outer_remaining=261687:exposure_transitions=828695:replay_reserved_units=26350:recursor_worklist_steps=4666:conversion_pairs=665'
        self.assertEqual(parse_work([line])['exposure_transitions'],828695)
        with self.assertRaises(AssertionError):
            parse_work([])


if __name__ == '__main__':
    unittest.main()
