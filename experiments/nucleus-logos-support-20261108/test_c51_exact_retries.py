"""C51 exact-recurrence observer contract; no partial proof authority."""

import unittest

from probe_c51_exact_retries import parse_retries, summarize_retries


class C51ExactRetries(unittest.TestCase):
    def test_first_request_and_exact_retry(self):
        raw = (
            b'NUCLEUS_C51_FAILED_ROOT:{"seq":0,"stage":"owner-exhausted",'
            b'"recursor":147,"goal":"completed","entry_budget":512,'
            b'"entry_owner":512,"spine_len":5,"prior_failure":null,'
            b'"stored_failed_roots":0}\n'
            b'NUCLEUS_C51_FAILED_ROOT:{"seq":1,"stage":"owner-exhausted",'
            b'"recursor":147,"goal":"completed","entry_budget":512,'
            b'"entry_owner":512,"spine_len":5,"prior_failure":0,'
            b'"stored_failed_roots":1}\n'
        )
        got = parse_retries(raw)
        self.assertEqual(len(got), 2)
        self.assertEqual(summarize_retries(got)["exact_failed_root_retries"], 1)
        self.assertFalse(summarize_retries(got)["partial_state_is_a_proof"])

    def test_bad_prior_reference_fails_closed(self):
        raw = (
            b'NUCLEUS_C51_FAILED_ROOT:{"seq":0,"stage":"owner-exhausted",'
            b'"recursor":147,"goal":"completed","entry_budget":512,'
            b'"entry_owner":512,"spine_len":5,"prior_failure":1,'
            b'"stored_failed_roots":0}\n'
        )
        with self.assertRaises(ValueError):
            parse_retries(raw)

    def test_no_recurrence_is_distinct_from_no_failures(self):
        raw = (
            b'NUCLEUS_C51_FAILED_ROOT:{"seq":0,"stage":"owner-exhausted",'
            b'"recursor":170,"goal":"one-step","entry_budget":262144,'
            b'"entry_owner":262144,"spine_len":4,"prior_failure":null,'
            b'"stored_failed_roots":0}\n'
        )
        self.assertEqual(summarize_retries(parse_retries(raw))["exact_failed_root_retries"], 0)
        self.assertEqual(summarize_retries([])["failed_requests"], 0)


if __name__ == "__main__":
    unittest.main()
