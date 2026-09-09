#!/usr/bin/env python3
"""Offline checks for the actual launcher boundaries; no model requests."""
from datetime import datetime
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess
import sys

import zcode_run as run
import zcode_task as task


class LauncherTests(unittest.TestCase):
    def test_stop_targets_only_its_owned_process_group(self):
        children = [subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     start_new_session=True) for _ in range(2)]
        try:
            run.stop_owned_process(children[0])
            self.assertIsNotNone(children[0].poll())
            self.assertIsNone(children[1].poll())
        finally:
            for child in children:
                if child.poll() is None:
                    child.terminate()
                child.wait(timeout=5)

    def test_budget_stops_before_reserved_window(self):
        policy = task.dispatch_policy(datetime.fromisoformat("2026-09-09T13:59:00+08:00"), pause_weekdays=True)
        self.assertEqual(run.budget_seconds(policy, 1800), 40)
        policy = task.dispatch_policy(datetime.fromisoformat("2026-09-09T13:59:40+08:00"), pause_weekdays=True)
        self.assertEqual(run.budget_seconds(policy, 1800), 0)
        policy = task.dispatch_policy(datetime.fromisoformat("2026-09-09T14:00:00+08:00"), pause_weekdays=True)
        self.assertEqual(run.budget_seconds(policy, 1800), 0)
        policy = task.dispatch_policy(datetime.fromisoformat("2026-09-09T18:00:00+08:00"), pause_weekdays=True)
        self.assertEqual(run.budget_seconds(policy, 1800), 1800)

    def test_profile_keeps_the_correct_plan_and_official_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "v2").mkdir()
            path = home / "v2/config.json"
            profile = {"enabled": True, "models": {"GLM-5.3-Flash": {}},
                       "options": {"apiKey": "TEST_KEY_NOT_REAL", "baseURL": run.OFFICIAL_ENDPOINT}}
            path.write_text(json.dumps({"provider": {run.PROVIDER: profile}}))
            self.assertEqual(run.load_profile(home), "TEST_KEY_NOT_REAL")
            profile["enabled"] = False
            path.write_text(json.dumps({"provider": {run.PROVIDER: profile}}))
            with self.assertRaises(ValueError):
                run.load_profile(home)
            profile["enabled"] = True
            profile["options"]["baseURL"] = "https://unrelated.invalid"
            path.write_text(json.dumps({"provider": {run.PROVIDER: profile}}))
            with self.assertRaises(ValueError):
                run.load_profile(home)

    def test_reserved_window_never_reads_credential_or_starts_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            body = root / "task.md"
            body.write_text("Write a short report.")
            packet = root / "run"
            task.prepare(root, body, packet, [], [])
            policy = task.dispatch_policy(datetime.fromisoformat("2026-09-09T15:00:00+08:00"), pause_weekdays=True)
            with patch.object(task, "dispatch_policy", return_value=policy), patch.object(run, "load_profile") as auth, patch.object(run.subprocess, "Popen") as spawn:
                result, code = run.run(packet, root / ".zcode")
                self.assertEqual(code, 4)
                self.assertEqual(result["state"], "deferred_time_policy")
                auth.assert_not_called()
                spawn.assert_not_called()
                self.assertFalse((packet / "launch.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
