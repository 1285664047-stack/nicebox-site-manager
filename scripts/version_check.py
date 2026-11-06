#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Opportunistic release check for Nicebox Site Manager.

The check runs only while the Skill is being used. Successful checks are
throttled to once every 24 hours and failures are retried no more than hourly.
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone

from config_manager import ensure_installation, load_config, load_installed_versions, save_config
from mcp_direct_client import DirectMcpError, call_tool
from openclaw_client import OpenClawError, request


CHECK_INTERVAL_SECONDS = 24 * 60 * 60
RETRY_INTERVAL_SECONDS = 60 * 60

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def _output(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _read_installed_versions():
    value = load_installed_versions()
    return {
        "skill": str(value.get("skill_version") or "0.0.0"),
        "mcp": str(value.get("mcp_version") or "0.0.0"),
    }


def _version_tuple(value):
    match = re.match(r"^\s*(\d+)\.(\d+)\.(\d+)(?:[.+-].*)?\s*$", str(value or ""))
    return tuple(int(part) for part in match.groups()) if match else None


def _is_newer(candidate, current):
    candidate_value = _version_tuple(candidate)
    current_value = _version_tuple(current)
    return bool(candidate_value and current_value and candidate_value > current_value)


def _utc_text(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace("+00:00", "Z")


def _timestamp(value):
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _state(config):
    value = config.get("version_check") if isinstance(config, dict) else None
    return value if isinstance(value, dict) else {}


def _due_status(config, now=None):
    now = float(now if now is not None else time.time())
    state = _state(config)
    last_checked = float(state.get("last_checked_timestamp") or 0)
    last_attempt = float(state.get("last_attempt_timestamp") or 0)
    if last_checked > 0 and now - last_checked < CHECK_INTERVAL_SECONDS:
        return False, max(0, int(CHECK_INTERVAL_SECONDS - (now - last_checked)))
    if last_attempt > 0 and now - last_attempt < RETRY_INTERVAL_SECONDS:
        return False, max(0, int(RETRY_INTERVAL_SECONDS - (now - last_attempt)))
    return True, 0


def _extract_release_info(result):
    if not isinstance(result, dict):
        raise ValueError("版本响应格式无效")
    structured = result.get("structuredContent")
    if isinstance(structured, dict) and structured.get("success") is True:
        data = structured.get("data")
    else:
        data = result.get("data") if result.get("success") is True else result
    if not isinstance(data, dict) or not isinstance(data.get("components"), dict):
        raise ValueError("版本响应缺少组件信息")
    return data


def _fetch_release_info():
    capability_missing = False
    try:
        result = call_tool("nicebox_get_release_info", {})
        return _extract_release_info(result), "mcp", capability_missing
    except DirectMcpError as error:
        capability_missing = error.kind == "capability"
        if error.kind == "config":
            raise
    return request("GET", "/site/getReleaseInfo"), "api", capability_missing


def _changes_between(component, installed_version, installed_at, checked_at):
    releases = component.get("releases") if isinstance(component, dict) else []
    selected = []
    for release in releases if isinstance(releases, list) else []:
        if not isinstance(release, dict):
            continue
        version = str(release.get("version") or "")
        released_at = _timestamp(release.get("released_at"))
        if (
            _is_newer(version, installed_version) and
            released_at is not None and
            installed_at < released_at <= checked_at
        ):
            selected.append(release)
    selected.sort(key=lambda item: _version_tuple(item.get("version")) or (0, 0, 0))
    changes = []
    for release in selected:
        for change in release.get("changes") or []:
            text = str(change).strip()
            if text and text not in changes:
                changes.append(text)
    return changes


def _compare(release_info, installed, installed_at, checked_at, capability_missing=False, installation_time_missing=False):
    components = release_info.get("components") or {}
    current_mcp = str(release_info.get("current_mcp_version") or installed["mcp"])
    current = {"skill": installed["skill"], "mcp": current_mcp}
    updates = []
    for key in ("skill", "mcp"):
        component = components.get(key) if isinstance(components, dict) else None
        if not isinstance(component, dict):
            continue
        latest = str(component.get("latest_version") or "")
        installed_version = current[key]
        needs_update = _is_newer(latest, installed_version)
        if key == "mcp" and capability_missing:
            needs_update = True
            installed_version = "未识别（当前服务缺少版本能力）"
        if needs_update:
            changes = [] if installation_time_missing else _changes_between(
                component,
                current[key],
                installed_at,
                checked_at,
            )
            if not installation_time_missing and not changes:
                continue
            updates.append({
                "component": key,
                "name": str(component.get("name") or key),
                "installed_version": installed_version,
                "latest_version": latest,
                "changes": changes,
                "show_changes": not installation_time_missing,
            })
    latest_versions = {
        key: str(value.get("latest_version") or "")
        for key, value in components.items()
        if key in ("skill", "mcp") and isinstance(value, dict)
    }
    return current, latest_versions, updates


def status():
    config = load_config() or {}
    due, retry_after = _due_status(config)
    state = _state(config)
    return {
        "ok": True,
        "due": due,
        "retry_after_seconds": retry_after,
        "installed_versions": _read_installed_versions(),
        "installed_at": (config.get("installation") or {}).get("installed_at"),
        "last_checked_at": state.get("last_checked_at"),
    }


def record_installation():
    config = load_config() or {}
    now = time.time()
    ensure_installation(config, force=True, now=now)
    save_config(config)
    installation = config.get("installation") or {}
    return {
        "ok": True,
        "installed_at": installation.get("installed_at"),
        "installed_versions": {
            "skill": installation.get("skill_version"),
            "mcp": installation.get("mcp_version"),
        },
    }


def check(force=False):
    config = load_config() or {}
    now = time.time()
    previous_installation = config.get("installation")
    previous_installation = previous_installation if isinstance(previous_installation, dict) else {}
    had_installation_time = bool(
        previous_installation.get("installed_at") and
        previous_installation.get("installed_timestamp")
    )
    installation_changed = ensure_installation(config, now=now)
    if installation_changed:
        save_config(config)
    installation = config.get("installation") or {}
    installed = {
        "skill": str(installation.get("skill_version") or _read_installed_versions()["skill"]),
        "mcp": str(installation.get("mcp_version") or _read_installed_versions()["mcp"]),
    }
    installed_at = float(installation.get("installed_timestamp") or now)
    due, retry_after = _due_status(config)
    if not force and not due:
        return {
            "ok": True,
            "checked": False,
            "notify": False,
            "retry_after_seconds": retry_after,
        }

    state = _state(config)
    state["last_attempt_timestamp"] = now
    state["last_attempt_at"] = _utc_text(now)
    config["version_check"] = state
    save_config(config)

    try:
        release_info, source, capability_missing = _fetch_release_info()
        current, latest, updates = _compare(
            release_info,
            installed,
            installed_at,
            now,
            capability_missing,
            installation_time_missing=not had_installation_time,
        )
        state.update({
            "last_checked_timestamp": now,
            "last_checked_at": _utc_text(now),
            "latest_versions": latest,
            "current_versions": current,
            "repository_url": str(release_info.get("repository_url") or ""),
            "updates": updates,
            "update_available": bool(updates),
            "installation_time_missing_at_check": not had_installation_time,
            "update_window": {
                "installed_at": installation.get("installed_at"),
                "checked_at": _utc_text(now),
            },
        })
        config["skill_version"] = installed["skill"]
        config["mcp_version"] = installed["mcp"]
        config["version_check"] = state
        save_config(config)
        return {
            "ok": True,
            "checked": True,
            "notify": bool(updates),
            "repository_url": state["repository_url"],
            "updates": updates,
            "show_changes": had_installation_time,
            "installed_at": installation.get("installed_at"),
            "checked_at": _utc_text(now),
            "source": source,
        }
    except (DirectMcpError, OpenClawError, OSError, ValueError) as error:
        state["last_error_at"] = _utc_text(now)
        config["version_check"] = state
        save_config(config)
        return {
            "ok": False,
            "checked": False,
            "notify": False,
            "message": "版本检查暂时不可用",
            "error_kind": getattr(error, "kind", getattr(error, "code", "VERSION_CHECK_FAILED")),
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Nicebox Site Manager 版本检查")
    parser.add_argument("command", choices=("status", "check", "install"), nargs="?", default="check")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "status":
        result = status()
    elif args.command == "install":
        result = record_installation()
    else:
        result = check(args.force)
    _output(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
