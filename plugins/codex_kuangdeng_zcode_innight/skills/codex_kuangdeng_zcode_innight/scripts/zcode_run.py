#!/usr/bin/env python3
"""Run the installed official ZCode agent with its own locally saved Coding Plan profile."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

import zcode_task as task

PROVIDER = "builtin:bigmodel-coding-plan"
MODEL_NAME = "GLM-5.3-Flash"
OFFICIAL_ENDPOINT = "https://open.bigmodel.cn/api/anthropic"


def runtime_path(explicit=None):
    if explicit:
        path = task.resolved(explicit)
        if not path.is_file():
            raise ValueError("Explicit official runtime path does not exist")
        return path
    for path in [Path("/Applications/ZCode.app/Contents/Resources/glm/zcode.cjs"),
                 Path("/opt/ZCode/resources/glm/zcode.cjs"),
                 Path.home() / ".zcode/server/agents/glm/zcode.cjs"]:
        if path.is_file():
            return path
    raise ValueError("Official bundled zcode.cjs not found; inspect the installation")


def load_profile(zcode_home):
    """Never copy credentials between hosts or persist them in the task directory."""
    path = task.resolved(zcode_home) / "v2/config.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    profile = data.get("provider", {}).get(PROVIDER, {})
    options = profile.get("options", {})
    if profile.get("enabled") is not True or MODEL_NAME not in profile.get("models", {}):
        raise ValueError("Enable the existing BigModel Coding Plan / GLM-5.3-Flash profile in ZCode")
    if options.get("baseURL") != OFFICIAL_ENDPOINT:
        raise ValueError("The saved Coding Plan endpoint differs from the validated official endpoint")
    key = options.get("apiKey")
    if not isinstance(key, str) or not key.strip():
        raise ValueError("No saved Coding Plan credential; connect this host's ZCode account first")
    return key


def budget_seconds(policy, requested):
    if requested <= 0:
        raise ValueError("timeout-seconds must be positive")
    if not policy["dispatch_allowed_by_time"]:
        return 0
    remaining = policy["seconds_until_pause"]
    # Give SIGINT/cleanup room before the user's weekday 14:00 boundary.
    if remaining is not None and remaining <= 30:
        return 0
    return min(requested, remaining - 20) if remaining is not None else requested


def stop_owned_process(proc):
    """Only signal the process group created for this invocation."""
    if proc.poll() is not None:
        return
    for sig, grace in [(signal.SIGINT, 10), (signal.SIGTERM, 5), (signal.SIGKILL, 2)]:
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=grace)
            return
        except subprocess.TimeoutExpired:
            continue


def interrupt_run(signum, frame):
    raise KeyboardInterrupt


def run(run_dir, zcode_home, mode="edit", timeout_seconds=1800, runtime=None, node=None, check=False):
    if os.name != "posix":
        raise ValueError("This launcher is validated on macOS/Linux; use the desktop route on this platform")
    run_dir, zcode_home = task.resolved(run_dir), task.resolved(zcode_home)
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("expected_model") != task.MODEL:
        raise ValueError("This launcher is scoped to the saved BigModel Coding Plan Flash model")
    if task.digest(run_dir / "packet.md") != manifest["packet_sha256"]:
        raise ValueError("Task packet changed after preparation; review and prepare a new packet")
    workspace = task.resolved(manifest["workspace"])
    if not workspace.is_dir() or not task.within(run_dir, workspace):
        raise ValueError("Packet workspace is missing or does not contain run-dir")
    policy = task.dispatch_policy()
    budget = budget_seconds(policy, timeout_seconds)
    if budget == 0:
        return {"state": "deferred_time_policy", "policy": policy, "model_requests_started": False}, 4
    runtime = runtime_path(runtime)
    node = node or shutil.which("node")
    if not node:
        raise ValueError("Node.js is not available in this host's PATH")
    key = load_profile(zcode_home)
    record = {
        "state": "preflight_ready", "task_id": manifest["task_id"], "marker": manifest["marker"],
        "workspace": str(workspace), "runtime": str(runtime), "node": node,
        "model": task.MODEL, "mode": mode, "timeout_seconds": budget,
        "route": "official_bundled_zcode_cli", "credential_source": "this_host_zcode_profile_in_memory",
        "zero_debit_verified": False, "policy": policy,
    }
    if check:
        return record, 0
    receipt = run_dir / "launch.json"
    # An existing receipt may represent a request already accepted by ZCode. Never blindly resend.
    with receipt.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
    env = os.environ.copy()
    env.update(ZCODE_MODEL=task.MODEL, ZCODE_BASE_URL=OFFICIAL_ENDPOINT, ANTHROPIC_API_KEY=key)
    # Use the agent runtime's real CLI: do not spoof client headers or call its model HTTP API ourselves.
    prompt = f"{manifest['marker']}：请读取并执行 {run_dir / 'packet.md'}。严格遵守任务范围，完成后给出结果路径。"
    command = [node, str(runtime), "--cwd", str(workspace), "--mode", mode, "--json", "--prompt", prompt]
    started, proc = time.monotonic(), None
    record["started_at"] = datetime.now(timezone.utc).isoformat()
    stdout_path, stderr_path = run_dir / "runtime.stdout.json", run_dir / "runtime.stderr.log"
    reason = None
    previous_handlers = {sig: signal.signal(sig, interrupt_run) for sig in (signal.SIGTERM, signal.SIGHUP)}
    try:
        with stdout_path.open("w", encoding="utf-8") as out, stderr_path.open("w", encoding="utf-8") as err:
            proc = subprocess.Popen(command, cwd=workspace, env=env, stdin=subprocess.DEVNULL,
                                    stdout=out, stderr=err, start_new_session=True)
            record.update(state="running", pid=proc.pid)
            task.dump(receipt, record)
            try:
                proc.wait(timeout=budget)
            except subprocess.TimeoutExpired:
                reason = "time_limit_reached"
                stop_owned_process(proc)
            except KeyboardInterrupt:
                reason = "interrupted"
                stop_owned_process(proc)
    except OSError as exc:
        reason = "launch_error"
        record["error"] = str(exc).replace(key, "<redacted>")
    except KeyboardInterrupt:
        reason = "interrupted"
    finally:
        if proc is not None and proc.poll() is None:
            stop_owned_process(proc)
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)
        # Runtime normally redacts secrets itself; additionally remove the exact injected key from saved streams.
        for path in (stdout_path, stderr_path):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="replace")
                if key in text:
                    path.write_text(text.replace(key, "<redacted>"), encoding="utf-8")
    record.update(finished_at=datetime.now(timezone.utc).isoformat(),
                  elapsed_seconds=round(time.monotonic()-started, 3),
                  exit_code=proc.returncode if proc else None)
    parsed = None
    try:
        parsed = json.loads(stdout_path.read_text(encoding="utf-8"))
        if not isinstance(parsed, dict):
            parsed = None
    except (OSError, ValueError):
        pass
    if parsed and parsed.get("sessionId"):
        record["session_id"] = parsed["sessionId"]
        try:
            evidence = task.status(zcode_home, session_id=parsed["sessionId"], workspace=workspace)
            task.dump(run_dir / "execution.json", evidence)
            record["actual_model_verified"] = evidence.get("actual_model_verified", False)
            record["latest_turn_status"] = (evidence.get("latest_turn") or {}).get("status")
        except (OSError, ValueError, task.sqlite3.Error) as exc:
            record["evidence_error"] = str(exc)
    completed = (not reason and record["exit_code"] == 0 and record.get("actual_model_verified")
                 and record.get("latest_turn_status") == "completed")
    record["state"] = "runtime_completed" if completed else (reason or "inspect_runtime_result")
    record["semantic_acceptance"] = "pending_codex_review"
    task.dump(receipt, record)
    return record, 0 if completed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--mode", choices=("plan", "edit", "build"), default="edit")
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--runtime", help="Explicit path to a verified official zcode.cjs installation")
    parser.add_argument("--node", help="Node executable; otherwise discovered from PATH")
    parser.add_argument("--check", action="store_true", help="Read preflight only; no model request or run receipt")
    args = parser.parse_args()
    try:
        result, code = run(args.run_dir, Path.home() / ".zcode", args.mode, args.timeout_seconds,
                           args.runtime, args.node, args.check)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"state": "not_started", "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
