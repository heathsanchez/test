"""C53 cross-Machine exact source-retry observer: no partial proof authority."""

import unittest

from probe_c53_shared_retries import parse_shared_retries, summarize_shared_retries


class C53SharedRetryTests(unittest.TestCase):
    def test_separate_machine_retries_share_exact_owner(self):
        rows = (
            b'NUCLEUS_C53_SHARED_FAILED:{"seq":0,"goal":"completed","stage":"owner-exhausted",'
            b'"recursor":147,"shared_cache":true,"shared_failed_roots":0,'
            b'"shared_prior_failure":null,"machine_failed_roots":0}\n'
            b'NUCLEUS_C53_SHARED_FAILED:{"seq":1,"goal":"completed","stage":"owner-exhausted",'
            b'"recursor":147,"shared_cache":true,"shared_failed_roots":1,'
            b'"shared_prior_failure":0,"machine_failed_roots":0}\n'
        )
        result = summarize_shared_retries(parse_shared_retries(rows))
        self.assertEqual(result["cross_machine_exact_retries"], 1)
        self.assertFalse(result["unfinished_frames_are_proof"])

    def test_rejects_forward_or_malformed_shared_reference(self):
        rows = (
            b'NUCLEUS_C53_SHARED_FAILED:{"seq":0,"goal":"one-step","stage":"owner-exhausted",'
            b'"recursor":147,"shared_cache":true,"shared_failed_roots":0,'
            b'"shared_prior_failure":0,"machine_failed_roots":0}\n'
        )
        with self.assertRaises(ValueError):
            parse_shared_retries(rows)


if __name__ == "__main__":
    unittest.main()
