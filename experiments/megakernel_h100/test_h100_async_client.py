"""Mocked RunPod async control-plane and host authorization tests."""
import asyncio
import json
import tempfile
from pathlib import Path
import unittest
from h100_async_client import select_endpoint, run_async, host_accept, SOURCE_PIN


class Job:
    def __init__(self, status="COMPLETED", output=None, timeout=False):
        self.id = "job-c74"
        self._data = {"status": status}
        self.output = output
        self.error = "failure" if status == "FAILED" else None
        self.timeout = timeout
        self.cancelled = False

    async def wait(self, timeout):
        if self.timeout:
            raise TimeoutError("synthetic timeout")
        return self

    async def cancel(self):
        self.cancelled = True


class Client:
    def __init__(self, job):
        self.job = job
        self.calls = 0
        self.input = None

    async def run(self, payload):
        self.calls += 1
        self.input = payload
        return self.job


def positive_worker():
    return {"status": "PASS", "source_pin": SOURCE_PIN, "sm_count": 132,
            "checks": {"rr": {"passed": True}, "dag": {"passed": True}}}


class AsyncTests(unittest.TestCase):
    def run_case(self, job):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "run.json"
            client = Client(job)
            result = asyncio.run(run_async(client, "gate text", out, 90))
            self.assertEqual(result, json.loads(out.read_text()))
            self.assertEqual(result["job_id"], "job-c74")
            self.assertEqual(client.calls, 1)
            self.assertEqual(client.input, {"gate_source": "gate text"})
            return result

    def test_endpoint_match(self):
        self.assertEqual(select_endpoint([{"name": "other", "id": "abc"},
            {"name": "mathgraph-megakernel-h100-20261027", "id": "xyz"}]), "xyz")

    def test_endpoint_missing(self):
        with self.assertRaises(ValueError):
            select_endpoint([])

    def test_endpoint_duplicate(self):
        with self.assertRaises(ValueError):
            select_endpoint([{"name": "mathgraph-megakernel-h100-20261027", "id": "1"},
                             {"name": "mathgraph-megakernel-h100-20261027", "id": "2"}])

    def test_positive(self):
        self.assertTrue(host_accept(self.run_case(Job(output=positive_worker()))))

    def test_remote_failure(self):
        state = self.run_case(Job(status="FAILED"))
        self.assertEqual(state["status"], "UNKNOWN_REMOTE_JOB_NOT_COMPLETED")
        self.assertFalse(host_accept(state))

    def test_non_object_response(self):
        state = self.run_case(Job(output="anything"))
        self.assertEqual(state["status"], "UNKNOWN_MISSING_STRUCTURED_OUTPUT")
        self.assertFalse(host_accept(state))

    def test_timeout_cancels(self):
        job = Job(timeout=True)
        state = self.run_case(job)
        self.assertEqual(state["status"], "UNKNOWN_RUNPOD_JOB_TIMEOUT")
        self.assertTrue(job.cancelled)
        self.assertFalse(host_accept(state))

    def test_reject_unbounded(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                asyncio.run(run_async(Client(Job()), "x", Path(d) / "x.json", 1201))

    def test_wrong_source_pin_fails(self):
        w = positive_worker()
        w["source_pin"] = "other"
        self.assertFalse(host_accept(self.run_case(Job(output=w))))

    def test_missing_comparison_fails(self):
        w = positive_worker()
        del w["checks"]["dag"]
        self.assertFalse(host_accept(self.run_case(Job(output=w))))


if __name__ == "__main__":
    unittest.main()
