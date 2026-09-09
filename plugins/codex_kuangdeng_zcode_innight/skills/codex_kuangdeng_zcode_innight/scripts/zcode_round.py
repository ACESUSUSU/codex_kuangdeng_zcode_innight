#!/usr/bin/env python3
"""Read one marker-bound ZCode turn, never a previous completed turn. No model calls."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
import time

import zcode_task as task

TERMINAL = {"completed", "error", "cancelled"}
LOOKUP_ERRORS = {"session_not_found", "ambiguous_marker", "ambiguous_turn"}


def inspect_round(zcode_home, session_id, marker, workspace=None):
    if not marker or len(marker) < 8:
        raise ValueError("Use a unique per-round marker of at least 8 characters")
    conn = task.open_ro(task.resolved(zcode_home) / "cli/db/db.sqlite")
    result = {"session_id": session_id, "marker": marker,
              "observed_at": datetime.now(timezone.utc).isoformat(),
              "semantic_acceptance": "pending_codex_review", "zero_debit_verified": False}
    try:
        task.require_columns(conn, "session", ["id", "directory", "title"])
        row = conn.execute("SELECT id,directory,title FROM session WHERE id=?", (session_id,)).fetchone()
        if row is None:
            return {**result, "status": "session_not_found"}
        if workspace and row["directory"] != str(task.resolved(workspace)):
            raise ValueError("Session does not belong to the requested workspace")
        result.update(workspace=row["directory"], title=row["title"])
        task.require_columns(conn, "message", ["id", "data"])
        task.require_columns(conn, "part", ["session_id", "message_id", "data", "time_created"])
        matches = set()
        for r in conn.execute("SELECT p.message_id,p.data,m.data AS message_data FROM part p "
                              "JOIN message m ON m.id=p.message_id WHERE p.session_id=? AND instr(p.data,?)>0",
                              (session_id, marker)):
            part, msg = json.loads(r["data"]), json.loads(r["message_data"])
            if (msg.get("semantics") or {}).get("origin") == "agent_runtime" or (msg.get("anchor") or {}).get("origin") == "synthetic":
                continue
            if msg.get("role") == "user" and part.get("type") == "text" and marker in part.get("text", ""):
                matches.add(r["message_id"])
        if len(matches) != 1:
            return {**result, "status": "not_started" if not matches else "ambiguous_marker",
                    "matching_user_messages": sorted(matches)}
        user_id = next(iter(matches))
        result["user_message_id"] = user_id
        columns = ["session_id", "user_message_id", "turn_id", "status", "started_at", "completed_at", "error_type", "error_code"]
        task.require_columns(conn, "turn_usage", columns)
        turns = list(conn.execute("SELECT turn_id,status,started_at,completed_at,error_type,error_code "
                                  "FROM turn_usage WHERE session_id=? AND user_message_id=?",
                                  (session_id, user_id)))
        if len(turns) != 1:
            # ZCode may persist the turn summary only at completion; absence does not prove it is queued.
            return {**result, "status": "pending_turn_record" if not turns else "ambiguous_turn"}
        turn = dict(turns[0])
        result.update(status=turn["status"], turn=turn)
        columns = ["session_id", "turn_id", "provider_id", "model_id", "status", "started_at", "duration_ms"]
        task.require_columns(conn, "model_usage", columns)
        calls = [dict(r) for r in conn.execute("SELECT provider_id,model_id,status,started_at,duration_ms "
                                               "FROM model_usage WHERE session_id=? AND turn_id=? ORDER BY started_at",
                                               (session_id, turn["turn_id"]))]
        result["model_calls"] = calls
        result["actual_model_verified"] = bool(calls) and any(c["status"] == "completed" for c in calls) and all(
            c["provider_id"] + "/" + c["model_id"] == task.MODEL for c in calls)
        texts, tools = [], []
        # parentID links all assistant messages/tool parts for this user input; timestamps alone are insufficient.
        for r in conn.execute("SELECT p.data,m.data AS message_data FROM part p JOIN message m ON m.id=p.message_id "
                              "WHERE p.session_id=? AND instr(m.data,?)>0 ORDER BY p.time_created",
                              (session_id, user_id)):
            part, msg = json.loads(r["data"]), json.loads(r["message_data"])
            if msg.get("role") != "assistant" or msg.get("parentID") != user_id:
                continue
            if part.get("type") == "text":
                texts.append(part.get("text", ""))
            elif part.get("type") == "tool":
                state = part.get("state", {})
                inputs = state.get("input", {})
                tools.append({"tool": part.get("tool"), "status": state.get("status"),
                              "file_path": inputs.get("file_path") if isinstance(inputs, dict) else None})
        response = texts[-1] if texts else ""
        result.update(response=response[:16000], response_truncated=len(response) > 16000,
                      tools=tools, ready_for_codex_review=result["status"] in TERMINAL)
        return result
    finally:
        conn.close()


def wait_round(zcode_home, session_id, marker, workspace=None, wait_seconds=0, poll_seconds=3):
    if not 0 <= wait_seconds <= 60 or poll_seconds <= 0:
        raise ValueError("wait-seconds must be 0-60 and poll-seconds must be positive")
    deadline = time.monotonic() + wait_seconds
    while True:
        result = inspect_round(zcode_home, session_id, marker, workspace)
        if result["status"] in TERMINAL | LOOKUP_ERRORS or time.monotonic() >= deadline:
            result["dispatch_policy"] = task.dispatch_policy()
            return result
        time.sleep(min(poll_seconds, max(0, deadline-time.monotonic())))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--marker", required=True)
    parser.add_argument("--workspace")
    parser.add_argument("--zcode-home", default=str(Path.home() / ".zcode"))
    parser.add_argument("--wait-seconds", type=float, default=0)
    parser.add_argument("--poll-seconds", type=float, default=3)
    parser.add_argument("--output", help="Save this round snapshot to an explicit local path")
    args = parser.parse_args()
    try:
        result = wait_round(args.zcode_home, args.session_id, args.marker, args.workspace,
                            args.wait_seconds, args.poll_seconds)
        if args.output:
            task.dump(task.resolved(args.output), result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "completed" else (1 if result["status"] in TERMINAL | LOOKUP_ERRORS else 2)
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        print(json.dumps({"status": "inspection_error", "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
