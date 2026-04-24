#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Initialize site data - clears existing pages, products, articles, messages.

WARNING: This operation clears ALL site content. Use with caution.
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error


DEFAULT_BASE_URL = "https://ai.nicebox.cn/api/openclaw"
ENDPOINT_INITIALIZE = "/template/initializeData"


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def get_env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def build_url(base_url: str, endpoint: str) -> str:
    return base_url.rstrip("/") + endpoint


def http_post_json(url: str, api_key: str, payload: dict, timeout: int = 60):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=data,
        method="POST",
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "nicebox-openclaw-skill/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        return e.code, raw
    except Exception as e:
        raise RuntimeError(f"Request failed: {e}") from e


def parse_args():
    parser = argparse.ArgumentParser(
        description="Initialize NiceBox site data (WARNING: clears all content)",
        epilog="Example: python initialize_site.py"
    )
    parser.add_argument(
        "--base-url",
        default=get_env("AIBOX_BASE_URL", DEFAULT_BASE_URL),
        help="API base URL"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    api_key = get_env("AIBOX_API_KEY")
    if not api_key:
        eprint("Error: AIBOX_API_KEY is not set")
        sys.exit(2)

    url = build_url(args.base_url, ENDPOINT_INITIALIZE)

    print(f"[WARN] WARNING: Initializing site will CLEAR all existing pages, products, articles, and messages.", file=sys.stderr)
    print(f"[INFO] Endpoint: {url}", file=sys.stderr)

    try:
        status_code, raw = http_post_json(url, api_key, {})
    except RuntimeError as e:
        eprint(str(e))
        sys.exit(1)

    try:
        parsed = json.loads(raw)
        print(json.dumps({
            "ok": 200 <= status_code < 300,
            "status_code": status_code,
            "request_url": url,
            "response": parsed,
        }, ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        print(json.dumps({
            "ok": 200 <= status_code < 300,
            "status_code": status_code,
            "request_url": url,
            "response_raw": raw,
        }, ensure_ascii=False, indent=2))

    sys.exit(0 if 200 <= status_code < 300 else 1)


if __name__ == "__main__":
    main()
