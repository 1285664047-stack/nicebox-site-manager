#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FTP publish REST fallback matching the current MCP contracts."""
import argparse
import json
import sys
from openclaw_client import OpenClawError, output, request

DEFAULT_OPTIONS = {"batch_size": 30, "overwrite_mode": "smart", "generate_mode": "default", "clean_before_publish": False, "include_drafts": False, "upload_mode": "incremental"}

def parse_args():
    parser = argparse.ArgumentParser(description="FTP 配置、发布准备、上传和取消 API 回退工具")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("get-config")
    sub.add_parser("test-connection")
    status = sub.add_parser("get-task-status"); status.add_argument("--task-id", type=int)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--batch-number", type=int, default=1); prepare.add_argument("--task-id", type=int)
    prepare.add_argument("--options-json", default="{}"); prepare.add_argument("--confirmed", action="store_true")
    start = sub.add_parser("start")
    start.add_argument("--task-id", type=int, required=True); start.add_argument("--batch-number", type=int, default=1)
    start.add_argument("--options-json", default="{}"); start.add_argument("--confirmed", action="store_true")
    cancel = sub.add_parser("cancel-task"); cancel.add_argument("--confirmed", action="store_true")
    return parser.parse_args()

def parse_options(raw):
    parsed = json.loads(raw)
    if not isinstance(parsed, dict): raise ValueError("--options-json 必须是 JSON object")
    return {**DEFAULT_OPTIONS, **parsed}

def need_confirmation(action, summary):
    output({"need_confirm": True, "action": action, "summary": summary})
    return 3

def main():
    args = parse_args()
    try:
        if args.action == "get-config": data = request("GET", "/site_publish/getConfig")
        elif args.action == "test-connection": data = request("POST", "/site_publish/testFtpConnection")
        elif args.action == "get-task-status": data = request("GET", "/site_publish/getTaskStatus", {"task_id": args.task_id} if args.task_id else {})
        elif args.action == "prepare":
            opts = parse_options(args.options_json)
            if not args.confirmed: return need_confirmation("prepare", {"batch_number": args.batch_number, "task_id": args.task_id, "options": opts})
            payload = {"options": opts, "batch_number": args.batch_number, "confirmed": True}
            if args.task_id: payload["task_id"] = args.task_id
            data = request("POST", "/site_publish/preparePublish", payload, timeout=300)
        elif args.action == "start":
            opts = parse_options(args.options_json)
            if not args.confirmed: return need_confirmation("start", {"task_id": args.task_id, "batch_number": args.batch_number, "options": opts})
            data = request("POST", "/site_publish/publish", {"task_id": args.task_id, "batch_number": args.batch_number, "options": opts, "disable_streaming": True, "confirmed": True}, timeout=300)
        else:
            if not args.confirmed: return need_confirmation("cancel-task", {"warning": "将取消当前 FTP 发布任务"})
            data = request("POST", "/site_publish/cancelTask", {"confirmed": True})
        output({"action": args.action, "data": data}); return 0
    except (ValueError, json.JSONDecodeError) as exc:
        output({"error": str(exc), "error_code": "INVALID_ARGUMENTS"}, ok=False); return 2
    except OpenClawError as exc:
        output({"error": str(exc), "error_code": exc.code, "data": exc.data}, ok=False); return 1

if __name__ == "__main__": sys.exit(main())
