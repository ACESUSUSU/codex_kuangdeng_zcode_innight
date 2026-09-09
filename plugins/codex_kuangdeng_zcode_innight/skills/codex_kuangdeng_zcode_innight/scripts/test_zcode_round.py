#!/usr/bin/env python3
"""Offline tests for correctly binding later replies to their own round."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

import zcode_round as round_tool


class RoundBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        db = self.home / "cli/db/db.sqlite"
        db.parent.mkdir(parents=True)
        self.db = sqlite3.connect(db)
        self.db.executescript("""
            CREATE TABLE session(id TEXT,directory TEXT,title TEXT);
            CREATE TABLE message(id TEXT,data TEXT);
            CREATE TABLE part(session_id TEXT,message_id TEXT,data TEXT,time_created INTEGER);
            CREATE TABLE turn_usage(session_id TEXT,user_message_id TEXT,turn_id TEXT,status TEXT,
                started_at INTEGER,completed_at INTEGER,error_type TEXT,error_code TEXT);
            CREATE TABLE model_usage(session_id TEXT,turn_id TEXT,provider_id TEXT,model_id TEXT,
                status TEXT,started_at INTEGER,duration_ms INTEGER);
            INSERT INTO session VALUES ('sess_test','/work','An auto-generated title');
        """)
        self.user("u0", "ROUND_MARKER_0")
        self.turn("u0", "t0", "completed", "old-provider", "old-model")
        self.assistant("a0", "u0", "Old completed response", 1)
        self.user("u1", "ROUND_MARKER_1")
        self.turn("u1", "t1", "completed")
        self.assistant("a1", "u1", "New round response", 2)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def user(self, mid, marker):
        self.db.execute("INSERT INTO message VALUES (?,?)", (mid, json.dumps({"role": "user"})))
        self.db.execute("INSERT INTO part VALUES (?,?,?,?)", ("sess_test", mid, json.dumps({"type": "text", "text": marker}), 0))

    def turn(self, uid, tid, status, provider="builtin:bigmodel-coding-plan", model="GLM-5.3-Flash"):
        self.db.execute("INSERT INTO turn_usage VALUES (?,?,?,?,?,?,?,?)", ("sess_test", uid, tid, status, 1, 2 if status == "completed" else None, None, None))
        self.db.execute("INSERT INTO model_usage VALUES (?,?,?,?,?,?,?)", ("sess_test", tid, provider, model, status, 1, 1))

    def assistant(self, mid, parent, text, created):
        self.db.execute("INSERT INTO message VALUES (?,?)", (mid, json.dumps({"role": "assistant", "parentID": parent})))
        self.db.execute("INSERT INTO part VALUES (?,?,?,?)", ("sess_test", mid, json.dumps({"type": "text", "text": text}), created))

    def inspect(self, marker):
        self.db.commit()
        return round_tool.inspect_round(self.home, "sess_test", marker, "/work")

    def test_only_new_turn_response_and_model_are_used(self):
        result = self.inspect("ROUND_MARKER_1")
        self.assertEqual(result["turn"]["turn_id"], "t1")
        self.assertEqual(result["response"], "New round response")
        self.assertTrue(result["actual_model_verified"])
        self.assertEqual(result["semantic_acceptance"], "pending_codex_review")
        self.assertFalse(result["zero_debit_verified"])

    def test_old_completion_does_not_finish_unsent_round(self):
        self.assertEqual(self.inspect("ROUND_MARKER_2")["status"], "not_started")

    def test_queued_and_running_round_are_not_completed(self):
        self.user("u2", "ROUND_MARKER_2")
        self.assertEqual(self.inspect("ROUND_MARKER_2")["status"], "pending_turn_record")
        self.turn("u2", "t2", "running")
        result = self.inspect("ROUND_MARKER_2")
        self.assertEqual(result["status"], "running")
        self.assertFalse(result["ready_for_codex_review"])

    def test_assistant_quote_is_not_a_user_dispatch(self):
        self.assistant("quote", "u1", "I saw ROUND_MARKER_2 in an example", 3)
        self.assertEqual(self.inspect("ROUND_MARKER_2")["status"], "not_started")

    def test_runtime_synthetic_user_is_not_a_dispatch(self):
        self.user("synthetic", "ROUND_MARKER_2")
        self.db.execute("UPDATE message SET data=? WHERE id='synthetic'", (json.dumps({
            "role":"user", "anchor":{"origin":"synthetic"}, "semantics":{"origin":"agent_runtime"}
        }),))
        self.assertEqual(self.inspect("ROUND_MARKER_2")["status"], "not_started")

    def test_duplicate_dispatch_is_not_silently_selected(self):
        self.user("u2", "ROUND_MARKER_1")
        self.assertEqual(self.inspect("ROUND_MARKER_1")["status"], "ambiguous_marker")

    def test_wrong_workspace_is_rejected(self):
        with self.assertRaises(ValueError):
            round_tool.inspect_round(self.home, "sess_test", "ROUND_MARKER_1", "/other")


if __name__ == "__main__":
    unittest.main(verbosity=2)
