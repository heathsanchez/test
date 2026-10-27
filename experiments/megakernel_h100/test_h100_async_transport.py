"""Bounded async RunPod execution and evidence preservation controls."""

import asyncio
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


BRIDGE = Path(__file__).with_name("runpod_flash_h100_bridge.py")


class FakeEndpoint:
    job = None
    payload = None

    def __init__(self, **kwargs):
        self.params = kwargs

    def __call__(self, fn):
        return fn

    async def run(self, payload):
        self.__class__.payload = payload
        return self.__class__.job


fake_flash = types.ModuleType("runpod_flash")
fake_flash.Endpoint = FakeEndpoint
fake_flash.GpuType = types.SimpleNamespace(NVIDIA_H100_80GB_HBM3="H100")
with patch.dict(sys.modules, {"runpod_flash": fake_flash}):
    spec = importlib.util.spec_from_file_location("h100_async_bridge_for_tests", BRIDGE)
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)


class FakeJob:
    id = "bounded-job-42"
    output = {"status": "PASS", "checks": {}, "source_pin": "test-pin"}
    error = None

    def __init__(self, mode="complete"):
        self.mode = mode
        self.cancelled = False
        self._data = {"status": "COMPLETED"}

    async def wait(self, timeout):
        assert timeout <= 1200
        if self.mode == "timeout":
            raise TimeoutError("remote job exceeded client bound")
        if self.mode == "failed":
            self.error = "worker failed"
            self._data["status"] = "FAILED"
            self.output = None

    async def cancel(self):
        self.cancelled = True


class AsyncRunPodTests(unittest.TestCase):
    def test_lookup_rejects_missing_or_duplicate_endpoint(self):
        rows = [{"name": "one", "id": "id-1"}, {"name": "other", "id": "id-2"}]
        self.assertEqual(bridge.select_endpoint_id(rows, "one"), "id-1")
        with self.assertRaises(ValueError):
            bridge.select_endpoint_id(rows, "missing")
        with self.assertRaises(ValueError):
            bridge.select_endpoint_id(rows + [rows[0]], "one")
        with self.assertRaises(ValueError):
            bridge.select_endpoint_id([{"name": "one", "id": ""}], "one")

    def test_endpoint_lookup_reads_flash_app_environment_authoritatively(self):
        class App:
            id = "flash-app-id"

            @classmethod
            async def from_name(cls, name):
                self.assertEqual(name, "isolated-h100-app")
                return cls()

            async def get_environment_by_name(_, env):
                self.assertEqual(env, "production")
                return {"id": "flash-env-id"}

        class GraphQL:
            async def __aenter__(client):
                return client

            async def __aexit__(client, *_):
                return None

            async def get_flash_environment(client, query):
                self.assertEqual(query, {"flashEnvironmentId": "flash-env-id"})
                return {"endpoints": [{"name": bridge.ENDPOINT_NAME,
                                       "id": "server-side-endpoint"}]}

        mod_api = types.ModuleType("runpod_flash.core.api.runpod")
        mod_api.RunpodGraphQLClient = GraphQL
        mod_app = types.ModuleType("runpod_flash.core.resources.app")
        mod_app.FlashApp = App
        with patch.dict(sys.modules, {"runpod_flash.core.api.runpod": mod_api,
                                      "runpod_flash.core.resources.app": mod_app}):
            with patch.dict(os.environ, {"FLASH_APP": "isolated-h100-app",
                                        "FLASH_ENV": "production"}):
                endpoint_id = asyncio.run(bridge.resolve_deployed_endpoint_id())
        self.assertEqual(endpoint_id, "server-side-endpoint")

    def test_submit_records_job_before_wait_and_preserves_gpu_report(self):
        FakeEndpoint.job = FakeJob()
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "evidence.json"
            async def fake_resolve():
                return "endpoint-123"

            with patch.object(bridge, "resolve_deployed_endpoint_id", fake_resolve):
                result = asyncio.run(bridge.run_async_differential("gate text", out))
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["runpod_job_id"], "bounded-job-42")
            self.assertEqual(result["runpod_endpoint_id"], "endpoint-123")
            self.assertEqual(FakeEndpoint.payload, {"gate_source": "gate text"})
            self.assertEqual(json.loads(out.read_text()), result)

    def test_timeout_cancels_job_and_retains_unknown_artifact(self):
        FakeEndpoint.job = FakeJob("timeout")
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "evidence.json"
            async def fake_resolve():
                return "endpoint-123"

            with patch.object(bridge, "resolve_deployed_endpoint_id", fake_resolve):
                result = asyncio.run(bridge.run_async_differential("gate text", out))
            self.assertTrue(FakeEndpoint.job.cancelled)
            self.assertEqual(result["status"], "UNKNOWN_CLIENT_TIMEOUT")
            self.assertEqual(result["runpod_job_id"], "bounded-job-42")
            self.assertEqual(json.loads(out.read_text()), result)

    def test_remote_job_failure_is_not_pass(self):
        FakeEndpoint.job = FakeJob("failed")
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "evidence.json"
            async def fake_resolve():
                return "endpoint-123"

            with patch.object(bridge, "resolve_deployed_endpoint_id", fake_resolve):
                result = asyncio.run(bridge.run_async_differential("gate text", out))
            self.assertEqual(result["status"], "UNKNOWN_REMOTE_JOB_FAILED")
            self.assertTrue(out.exists())

    def test_failed_job_cannot_promote_stale_pass_output(self):
        job = FakeJob()
        job._data["status"] = "FAILED"
        FakeEndpoint.job = job
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "evidence.json"
            async def fake_resolve():
                return "endpoint-123"
            with patch.object(bridge, "resolve_deployed_endpoint_id", fake_resolve):
                result = asyncio.run(bridge.run_async_differential("gate text", out))
            self.assertEqual(result["status"], "UNKNOWN_REMOTE_JOB_FAILED")
            self.assertEqual(result["runpod_status"], "FAILED")
            self.assertEqual(result["runpod_job_id"], job.id)

    def test_pre_submission_failure_writes_artifact_and_redacts_secret(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "evidence.json"
            async def fake_resolve():
                raise RuntimeError("broken credential secret-string")

            with patch.dict(os.environ, {"RUNPOD_API_KEY": "secret-string"}):
                with patch.object(bridge, "resolve_deployed_endpoint_id", fake_resolve):
                    result = asyncio.run(bridge.run_async_differential("gate text", out))
            self.assertEqual(result["status"], "UNKNOWN_CLIENT_FAILURE")
            self.assertNotIn("secret-string", out.read_text())
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
