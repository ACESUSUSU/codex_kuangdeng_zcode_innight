#!/usr/bin/env python3
"""Offline behavior tests; temporary fixtures only, no ZCode requests."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import zcode_task as z


class PacketAndWindowTests(unittest.TestCase):
    def test_public_default_does_not_apply_another_users_pause(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(z, "PREFERENCES", Path(tmp) / "preferences.json"):
            now = datetime.fromisoformat("2026-09-09T15:00:00+08:00")
            self.assertTrue(z.dispatch_policy(now)["dispatch_allowed_by_time"])
            self.assertIsNone(z.dispatch_policy(now)["seconds_until_pause"])
            z.PREFERENCES.write_text('{"pause_beijing_workdays": true}')
            self.assertFalse(z.dispatch_policy(now)["dispatch_allowed_by_time"])
            z.PREFERENCES.write_text('{"pause_beijing_workdays": "false"}')
            with self.assertRaises(ValueError):
                z.dispatch_policy(now)

    def test_user_schedule_uses_normal_quota_outside_promotion(self):
        examples = {
            "2026-09-09T10:00:00+08:00": (True, "normal_plan_usage"),
            "2026-09-09T13:59:59+08:00": (True, "normal_plan_usage"),
            "2026-09-09T14:00:00+08:00": (False, "defer_workday_14_18"),
            "2026-09-09T17:59:59+08:00": (False, "defer_workday_14_18"),
            "2026-09-09T18:00:00+08:00": (True, "normal_plan_usage"),
            "2026-09-12T14:30:00+08:00": (True, "normal_plan_usage"),
            "2026-09-09T01:00:00+08:00": (True, "prefer_night_promotion"),
            "2026-09-22T01:00:00+08:00": (True, "normal_plan_usage"),
        }
        for stamp, expected in examples.items():
            with self.subTest(stamp=stamp):
                p = z.dispatch_policy(datetime.fromisoformat(stamp), pause_weekdays=True)
                self.assertEqual((p["dispatch_allowed_by_time"], p["usage_mode"]), expected)

    def test_user_schedule_is_beijing_and_weekend_resumes_monday(self):
        # Los Angeles Tuesday 23:30 PDT is Beijing Wednesday 14:30.
        p = z.dispatch_policy(datetime.fromisoformat("2026-09-08T23:30:00-07:00"), pause_weekdays=True)
        self.assertFalse(p["dispatch_allowed_by_time"])
        self.assertEqual(p["resume_at"], "2026-09-09T18:00:00+08:00")
        p = z.dispatch_policy(datetime.fromisoformat("2026-09-11T18:00:00+08:00"), pause_weekdays=True)
        self.assertEqual(p["next_pause_at"], "2026-09-14T14:00:00+08:00")

    def test_window_boundaries_and_expiry(self):
        examples = {
            "2026-09-03T22:59:59+08:00": False,
            "2026-09-03T23:00:00+08:00": True,
            "2026-09-04T08:59:59+08:00": True,
            "2026-09-04T09:00:00+08:00": False,
            "2026-09-20T23:59:59+08:00": True,
            "2026-09-21T00:00:00+08:00": False,
            "2027-09-08T01:00:00+08:00": False,
        }
        for stamp, expected in examples.items():
            with self.subTest(stamp=stamp):
                result = z.window(datetime.fromisoformat(stamp))
                self.assertEqual(result["time_window_candidate"], expected)
                self.assertFalse(result["zero_debit_verified"])
        self.assertIsNone(z.window(datetime(2027, 1, 1, tzinfo=timezone.utc))["next_candidate_start"])

    def test_timezone_and_final_window(self):
        # September PDT: 08:00 in Los Angeles equals 23:00 in Beijing.
        result = z.window(datetime.fromisoformat("2026-09-08T08:00:00-07:00"))
        self.assertTrue(result["time_window_candidate"])
        self.assertEqual(result["seconds_to_close"], 36000)
        self.assertEqual(z.window(datetime.fromisoformat("2026-09-20T23:59:59+08:00"))["seconds_to_close"], 1)

    def test_prepare_is_non_dispatching_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = root / "body.md"
            task.write_text("Create report.md based on supplied text.")
            run = root / "run"
            record = z.prepare(root, task, run, [], [run / "report.md"])
            self.assertEqual(record["dispatch_state"], "prepared_only")
            self.assertEqual(z.digest(run / "packet.md"), record["packet_sha256"])
            self.assertFalse((run / "RESULT.json").exists())
            with self.assertRaises(ValueError):
                z.prepare(root, task, run, [], [])
            self.assertEqual(z.digest(run / "packet.md"), record["packet_sha256"])

    def test_write_boundary_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            task = root / "body.md"
            task.write_text("A bounded task")
            (root / "escape").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                z.prepare(root, task, root / "run", [root / "escape"], [])
            self.assertFalse((root / "run").exists())


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = self.root / "cli/db/db.sqlite"
        self.db.parent.mkdir(parents=True)
        conn = sqlite3.connect(self.db)
        conn.executescript("""
            CREATE TABLE session(id TEXT,title TEXT,directory TEXT,time_created INTEGER,time_updated INTEGER);
            CREATE TABLE message(id TEXT,data TEXT);
            CREATE TABLE part(session_id TEXT,message_id TEXT,data TEXT,time_created INTEGER);
            CREATE TABLE model_usage(session_id TEXT,provider_id TEXT,model_id TEXT,status TEXT,started_at INTEGER,
                duration_ms INTEGER,input_tokens INTEGER,output_tokens INTEGER);
            CREATE TABLE turn_usage(session_id TEXT,turn_id TEXT,status TEXT,started_at INTEGER,completed_at INTEGER,
                tool_call_count INTEGER,tool_error_count INTEGER);
        """)
        for sid, role in [("sess_1", "user"), ("sess_decoy", "assistant")]:
            conn.execute("INSERT INTO session VALUES (?,?,?,?,?)", (sid, "自动生成的新标题", "/work", 1, 2))
            conn.execute("INSERT INTO message VALUES (?,?)", (sid, json.dumps({"role": role})))
            conn.execute("INSERT INTO part VALUES (?,?,?,?)", (sid, sid, json.dumps({"type": "text", "text": "ZCODE_MARKER_123"}), 1))
        conn.execute("INSERT INTO model_usage VALUES (?,?,?,?,?,?,?,?)",
                     ("sess_1", "builtin:bigmodel-coding-plan", "GLM-5.3-Flash", "completed", 1, 25, 10, 20))
        conn.execute("INSERT INTO turn_usage VALUES (?,?,?,?,?,?,?)", ("sess_1", "turn_1", "running", 1, None, 0, 0))
        conn.commit()
        conn.close()

    def tearDown(self):
        self.temp.cleanup()

    def test_marker_survives_title_change_and_ignores_assistant_quote(self):
        conn = z.open_ro(self.db)
        try:
            self.assertEqual([r["id"] for r in z.locate(conn, "ZCODE_MARKER_123", "/work")], ["sess_1"])
            self.assertEqual(z.locate(conn, "ZCODE_MARKER_123", "/other"), [])
        finally:
            conn.close()

    def test_database_is_read_only_and_missing_path_not_created(self):
        before = z.digest(self.db)
        conn = z.open_ro(self.db)
        try:
            with self.assertRaises(sqlite3.OperationalError):
                conn.execute("DELETE FROM session")
        finally:
            conn.close()
        self.assertEqual(z.digest(self.db), before)
        missing = self.root / "absent.sqlite"
        with self.assertRaises(FileNotFoundError):
            z.open_ro(missing)
        self.assertFalse(missing.exists())

    def test_duplicate_dispatch_marker_is_ambiguous(self):
        conn = sqlite3.connect(self.db)
        conn.execute("UPDATE message SET data=? WHERE id='sess_decoy'", (json.dumps({"role": "user"}),))
        conn.commit()
        conn.close()
        result = z.status(self.root, marker="ZCODE_MARKER_123", workspace="/work")
        self.assertEqual(result["lookup_state"], "ambiguous")
        self.assertEqual(len(result["matches"]), 2)

    def test_execution_model_does_not_imply_finished_or_free(self):
        conn = z.open_ro(self.db)
        try:
            result = z.inspect_session(conn, "sess_1")
            self.assertTrue(result["actual_model_verified"])
            self.assertEqual(result["latest_turn"]["status"], "running")
            self.assertFalse(result["zero_debit_verified"])
            self.assertEqual(result["semantic_acceptance"], "not_performed_by_this_script")
            self.assertFalse(z.inspect_session(conn, "sess_1", "other/model")["actual_model_verified"])
            self.assertEqual(z.inspect_session(conn, "missing")["lookup_state"], "not_found")
            with self.assertRaises(ValueError):
                z.require_columns(conn, "session", ["not_a_real_column"])
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
