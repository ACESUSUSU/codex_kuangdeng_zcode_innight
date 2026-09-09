#!/usr/bin/env python3
"""Prepare ZCode packets and read local execution evidence. No model calls or DB writes."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import plistlib
import shutil
import sqlite3
import sys
import uuid
from zoneinfo import ZoneInfo

MODEL = "builtin:bigmodel-coding-plan/GLM-5.3-Flash"
SOURCE = "https://docs.bigmodel.cn/cn/coding-plan/notice/event-glm-5.3-flash"
BJ = ZoneInfo("Asia/Shanghai")
START = datetime(2026, 9, 3, 23, tzinfo=BJ)
# Conservative calendar cutoff: the official notice does not specify the final overnight tail.
CUTOFF = datetime(2026, 9, 21, 0, tzinfo=BJ)
PREFERENCES = Path(__file__).resolve().parents[1] / "preferences.json"


def window(now=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("A timezone-aware time is required")
    local = now.astimezone(BJ)
    active = START <= local < CUTOFF and (local.hour >= 23 or local.hour < 9)
    close = None
    if active:
        morning = local.replace(hour=9, minute=0, second=0, microsecond=0)
        if local.hour >= 23:
            morning += timedelta(days=1)
        close = min(morning, CUTOFF)
    candidate = max(local.replace(hour=23, minute=0, second=0, microsecond=0), START)
    if candidate <= local:
        candidate += timedelta(days=1)
    return {
        "beijing_now": local.isoformat(), "time_window_candidate": active,
        "candidate_window_closes": close.isoformat() if close else None,
        "seconds_to_close": int((close-local).total_seconds()) if close else None,
        "next_candidate_start": candidate.isoformat() if candidate < CUTOFF else None,
        "rules_checked_date": "2026-09-08", "rules_source": SOURCE,
        "conservative_cutoff": CUTOFF.isoformat(),
        "entitlement_verified": False, "zero_debit_verified": False,
        "notice": "Recheck current official rules, paid plan, quota and channel before dispatch.",
    }


def dispatch_policy(now=None, pause_weekdays=None):
    """Report time eligibility; user-specific pauses are opt-in, not task authorization."""
    if pause_weekdays is None:
        preferences = json.loads(PREFERENCES.read_text(encoding="utf-8")) if PREFERENCES.is_file() else {}
        pause_weekdays = preferences.get("pause_beijing_workdays", False)
        if not isinstance(pause_weekdays, bool):
            raise ValueError("pause_beijing_workdays must be a JSON boolean")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("A timezone-aware time is required")
    local = now.astimezone(BJ)
    blocked = pause_weekdays and local.weekday() < 5 and 14 <= local.hour < 18
    pause = None
    for offset in range(8) if pause_weekdays else ():
        candidate = (local + timedelta(days=offset)).replace(hour=14, minute=0, second=0, microsecond=0)
        if candidate.weekday() < 5 and candidate > local:
            pause = candidate
            break
    promotion = window(now)
    return {
        "beijing_now": local.isoformat(),
        "dispatch_allowed_by_time": not blocked,
        "usage_mode": "defer_workday_14_18" if blocked else (
            "prefer_night_promotion" if promotion["time_window_candidate"] else "normal_plan_usage"),
        "pause_beijing_workdays": pause_weekdays,
        "authorization_notice": "Time eligibility does not authorize a task or model request.",
        "workdays": "Monday-Friday in Asia/Shanghai",
        "resume_at": local.replace(hour=18, minute=0, second=0, microsecond=0).isoformat() if blocked else None,
        "next_pause_at": pause.isoformat() if pause else None,
        "seconds_until_pause": int((pause-local).total_seconds()) if pause else None,
        "promotion": promotion,
    }


def resolved(path):
    return Path(path).expanduser().resolve()


def within(path, root):
    return path == root or root in path.parents


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prepare(workspace, task_file, run_dir, allow_write, expected):
    workspace, task_file, run_dir = map(resolved, (workspace, task_file, run_dir))
    if not workspace.is_dir() or not task_file.is_file():
        raise ValueError("Workspace and task-file must exist")
    if not within(run_dir, workspace) or run_dir == workspace:
        raise ValueError("run-dir must be a new subdirectory of the workspace")
    if run_dir.exists():
        raise ValueError("run-dir already exists; use its existing packet or choose a fresh directory")
    allowed = list(dict.fromkeys([run_dir] + [resolved(x) for x in allow_write]))
    outputs = list(dict.fromkeys([resolved(x) for x in expected] + [run_dir / "RESULT.json"]))
    for path in allowed:
        if not within(path, workspace):
            raise ValueError(f"Write path outside workspace: {path}")
    for path in outputs:
        if not any(within(path, root) for root in allowed):
            raise ValueError(f"Expected output outside allowed paths: {path}")
        if path in (run_dir / "packet.md", run_dir / "manifest.json", run_dir / "dispatch.txt"):
            raise ValueError("Expected output conflicts with packet metadata")
    body = task_file.read_text(encoding="utf-8").strip()
    if not body:
        raise ValueError("Task body is empty")
    task_id = "zcode-" + uuid.uuid4().hex
    marker = "ZCODE_DISPATCH_" + task_id[6:]
    packet = "\n".join([
        f"# {marker}", "", f"task_id: {task_id}", f"工作目录：{workspace}",
        f"期望执行模型：{MODEL}", "", "允许修改的路径：",
        *[f"- {p}" for p in allowed], "", "交付物：", *[f"- {p}" for p in outputs],
        "", "## 任务", body, "", "## 执行约定",
        "遵守当前有效的项目规则及原任务权限。其他 Agent 可能同时工作，不撤销或覆盖其改动。",
        "任务之外的发布、消息发送、硬件执行或付费操作没有因本工作包获得额外授权。",
        "不要修改 packet.md、manifest.json、dispatch.txt。不要创建递归委派给 Codex 的任务。",
        f"最后写入 {run_dir / 'RESULT.json'}，包含 task_id、status、files_changed、checks_run、limitations。",
        "status 使用 completed 或 blocked；检查仅记录实际运行的内容，证据不足明确标记。",
        "完成后在对话中列出交付物绝对路径，由 Codex 独立验收。", "",
    ])
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "packet.md").write_text(packet, encoding="utf-8")
    prompt = f"{marker}：请读取并执行 {run_dir / 'packet.md'}。遵守其路径边界和验收要求。\n"
    (run_dir / "dispatch.txt").write_text(prompt, encoding="utf-8")
    manifest = {
        "schema_version": 1, "task_id": task_id, "marker": marker,
        "prepared_at": datetime.now(timezone.utc).isoformat(), "workspace": str(workspace),
        "expected_model": MODEL, "allowed_write_paths": [str(p) for p in allowed],
        "expected_outputs": [str(p) for p in outputs],
        "packet_sha256": digest(run_dir / "packet.md"), "dispatch_state": "prepared_only",
    }
    dump(run_dir / "manifest.json", manifest)
    return {**manifest, "run_dir": str(run_dir), "dispatch_text": prompt, "window": dispatch_policy()}


def open_ro(path):
    path = resolved(path)
    if not path.is_file():
        raise FileNotFoundError(f"Missing ZCode database: {path}; inspect the app instead")
    conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    return conn


def require_columns(conn, table, columns):
    # Table names only come from constants below, never command-line input.
    found = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    if not set(columns) <= found:
        raise ValueError(f"Unsupported ZCode schema: {table}; inspect the app instead")


def locate(conn, marker, workspace=None):
    if not marker or len(marker) < 8:
        raise ValueError("Use a unique marker of at least 8 characters")
    require_columns(conn, "session", ["id", "title", "directory", "time_created"])
    require_columns(conn, "part", ["session_id", "message_id", "data"])
    require_columns(conn, "message", ["id", "data"])
    sql = ("SELECT DISTINCT s.id,s.title,s.directory,s.time_created,p.data,m.data AS message_data "
           "FROM session s JOIN part p ON p.session_id=s.id "
           "JOIN message m ON m.id=p.message_id WHERE instr(p.data,?)>0")
    params = [marker]
    if workspace:
        sql += " AND s.directory=?"
        params.append(str(resolved(workspace)))
    found = {}
    for row in conn.execute(sql, params):
        part, message = json.loads(row["data"]), json.loads(row["message_data"])
        if message.get("role") == "user" and part.get("type") == "text" and marker in part.get("text", ""):
            found[row["id"]] = {k: row[k] for k in ("id", "title", "directory", "time_created")}
    return list(found.values())


def inspect_session(conn, session_id, expected_model=MODEL):
    require_columns(conn, "session", ["id", "title", "directory", "time_created", "time_updated"])
    row = conn.execute("SELECT id,title,directory,time_created,time_updated FROM session WHERE id=?", (session_id,)).fetchone()
    if row is None:
        return {"lookup_state": "not_found", "session_id": session_id}
    result = {"lookup_state": "found", "session": dict(row), "zero_debit_verified": False,
              "semantic_acceptance": "not_performed_by_this_script"}
    require_columns(conn, "model_usage", ["session_id", "provider_id", "model_id", "status", "started_at"])
    calls = [dict(r) for r in conn.execute(
        "SELECT provider_id,model_id,status,started_at,duration_ms,input_tokens,output_tokens "
        "FROM model_usage WHERE session_id=? ORDER BY started_at", (session_id,))]
    result["model_calls"] = calls
    result["actual_model_verified"] = bool(calls) and any(r["status"] == "completed" for r in calls) and all(
        r["provider_id"] + "/" + r["model_id"] == expected_model for r in calls)
    require_columns(conn, "turn_usage", ["session_id", "turn_id", "status", "started_at"])
    turn = conn.execute("SELECT turn_id,status,started_at,completed_at,tool_call_count,tool_error_count "
                        "FROM turn_usage WHERE session_id=? ORDER BY started_at DESC LIMIT 1", (session_id,)).fetchone()
    result["latest_turn"] = dict(turn) if turn else None
    require_columns(conn, "part", ["session_id", "message_id", "data", "time_created"])
    rows = list(conn.execute("SELECT p.data,m.data AS message_data FROM part p JOIN message m ON m.id=p.message_id "
                             "WHERE p.session_id=? ORDER BY p.time_created DESC LIMIT 200", (session_id,)))
    tools, texts = [], []
    for r in reversed(rows):
        part, msg = json.loads(r["data"]), json.loads(r["message_data"])
        if part.get("type") == "text" and msg.get("role") == "assistant":
            texts.append(part.get("text", ""))
        if part.get("type") == "tool":
            state = part.get("state", {})
            inputs = state.get("input", {})
            tools.append({"tool": part.get("tool"), "status": state.get("status"),
                          "file_path": inputs.get("file_path") if isinstance(inputs, dict) else None})
    result["recent_tools"] = tools
    result["latest_assistant_text"] = texts[-1][-4000:] if texts else None
    result["parts_window_limit"] = 200
    return result


def artifact_evidence(run_dir, manifest):
    root = resolved(manifest["workspace"])
    evidence = {"packet_hash_matches": digest(run_dir / "packet.md") == manifest["packet_sha256"], "files": []}
    for name in manifest["expected_outputs"]:
        path = resolved(name)
        if not within(path, root):
            raise ValueError("Manifest output resolves outside the workspace")
        item = {"path": str(path), "exists": path.is_file()}
        if path.is_file():
            item.update(size_bytes=path.stat().st_size, sha256=digest(path))
        evidence["files"].append(item)
    receipt = run_dir / "RESULT.json"
    if receipt.is_file():
        try:
            data = json.loads(receipt.read_text(encoding="utf-8"))
            evidence["agent_reported"] = {"task_id_matches": data.get("task_id") == manifest["task_id"],
                                           "status": data.get("status"),
                                           "checks_run": data.get("checks_run"),
                                           "limitations": data.get("limitations")}
        except (ValueError, AttributeError):
            evidence["agent_reported"] = {"error": "Invalid RESULT.json"}
    return evidence


def status(zcode_home, session_id=None, marker=None, workspace=None, run_dir=None):
    home, manifest = resolved(zcode_home), None
    if run_dir:
        run_dir = resolved(run_dir)
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        workspace, marker = manifest["workspace"], manifest["marker"]
    conn = open_ro(home / "cli/db/db.sqlite")
    try:
        if not session_id:
            matches = locate(conn, marker, workspace)
            if len(matches) != 1:
                return {"lookup_state": "not_found" if not matches else "ambiguous", "matches": matches,
                        "artifacts": artifact_evidence(run_dir, manifest) if manifest else None}
            session_id = matches[0]["id"]
        result = inspect_session(conn, session_id, manifest.get("expected_model", MODEL) if manifest else MODEL)
        if workspace and result.get("lookup_state") == "found" and result["session"]["directory"] != str(resolved(workspace)):
            raise ValueError("Session directory does not match the requested workspace")
    finally:
        conn.close()
    index = home / "v2/tasks-index.sqlite"
    if index.is_file():
        idx = open_ro(index)
        try:
            require_columns(idx, "tasks", ["task_id", "workspace_path", "title", "task_status", "model", "updated_at"])
            row = idx.execute("SELECT task_id,title,workspace_path,task_status,model,updated_at FROM tasks "
                              "WHERE task_id=? AND workspace_path=?", (session_id, result.get("session", {}).get("directory"))).fetchone()
            result["desktop_index"] = dict(row) if row else None
        finally:
            idx.close()
    if manifest:
        result["artifacts"] = artifact_evidence(run_dir, manifest)
    return result


def doctor(home):
    home = resolved(home)
    app = Path("/Applications/ZCode.app")
    cli = app / "Contents/Resources/glm/zcode.cjs"
    version = None
    plist = app / "Contents/Info.plist"
    if plist.is_file():
        with plist.open("rb") as stream:
            version = plistlib.load(stream).get("CFBundleShortVersionString")
    candidates = [cli, Path("/opt/ZCode/resources/glm/zcode.cjs"), home / "server/agents/glm/zcode.cjs"]
    return {"platform": sys.platform, "zcode_home": str(home), "desktop_version": version,
            "mac_bundled_cli": str(cli) if cli.is_file() else None, "node": shutil.which("node"),
            "official_runtime_candidates": [str(p) for p in candidates if p.is_file()],
            "session_db_exists": (home / "cli/db/db.sqlite").is_file(),
            "desktop_index_exists": (home / "v2/tasks-index.sqlite").is_file(),
            "credentials_read": False, "window": dispatch_policy()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("window", help="Check the user's Beijing schedule and the separate dated promotion")
    doc = subs.add_parser("doctor", help="Read installation metadata; never credentials")
    doc.add_argument("--zcode-home", default=str(Path.home() / ".zcode"))
    prep = subs.add_parser("prepare", help="Create a new packet; does not dispatch it")
    for opt in ("workspace", "task-file", "run-dir"):
        prep.add_argument("--" + opt, required=True)
    prep.add_argument("--allow-write", action="append", default=[])
    prep.add_argument("--expect", action="append", default=[])
    stat = subs.add_parser("status", help="Read only a specified task's local execution records")
    group = stat.add_mutually_exclusive_group(required=True)
    group.add_argument("--session-id")
    group.add_argument("--marker")
    group.add_argument("--run-dir")
    stat.add_argument("--workspace")
    stat.add_argument("--zcode-home", default=str(Path.home() / ".zcode"))
    args = parser.parse_args()
    try:
        if args.command == "window":
            result = dispatch_policy()
        elif args.command == "doctor":
            result = doctor(args.zcode_home)
        elif args.command == "prepare":
            result = prepare(args.workspace, args.task_file, args.run_dir, args.allow_write, args.expect)
        else:
            result = status(args.zcode_home, args.session_id, args.marker, args.workspace, args.run_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return {"not_found": 2, "ambiguous": 3}.get(result.get("lookup_state"), 0)
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        print(json.dumps({"error": str(exc), "action": "Inspect the app or correct explicit paths; do not modify its database"}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
