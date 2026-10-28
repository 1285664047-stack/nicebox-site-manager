#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail when an MCP tool has no checked-in ordinary API fallback."""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOLS_FILE = ROOT / "mcp-server" / "src" / "tools.ts"
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
MANIFEST_FILE = SCRIPT_DIR / "fallback_manifest.json"

def main():
    source = TOOLS_FILE.read_text(encoding="utf-8")
    tools = set(re.findall(r"(?:registerApiTool\(|registerTool\()\s*(?:server,\s*client,\s*)?['\"](nicebox_[a-z0-9_]+)['\"]", source))
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    missing = sorted(tools - set(manifest))
    stale = sorted(set(manifest) - tools)
    missing_scripts = []
    for tool, command in manifest.items():
        script = command.split()[0]
        if script.endswith((".py", ".mjs")) and not (SCRIPT_DIR / script).is_file():
            missing_scripts.append("%s -> %s" % (tool, script))
    if missing or stale or missing_scripts:
        print(json.dumps({"ok": False, "mcp_tool_count": len(tools), "fallback_count": len(manifest), "missing": missing, "stale": stale, "missing_scripts": missing_scripts}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"ok": True, "mcp_tool_count": len(tools), "fallback_count": len(manifest), "message": "所有 MCP 工具均已登记普通 API 回退"}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__": sys.exit(main())
