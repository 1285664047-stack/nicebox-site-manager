#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
import urllib.request
import urllib.error

from config_reader import get_api_key, get_base_url, check_config

ENDPOINT_PUBLISH_ARTICLE = "/article/publish"


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def build_url(base_url: str, endpoint: str) -> str:
    return base_url.rstrip("/") + endpoint


def http_post_json(url: str, api_key: str, payload: dict, timeout: int = 30):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=data,
        method="POST",
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "qidc-openclaw-skill/1.0",
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
    parser = argparse.ArgumentParser(description="Publish article to AiWebSite OpenClaw API")
    parser.add_argument("--title", required=True, help="Article title")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--content", help="Article HTML/content (use --content-file for large content)")
    group.add_argument("--content-file", help="Path to file containing article content (recommended for Chinese/HTML content)")
    parser.add_argument("--summary", default="", help="Article summary")
    parser.add_argument("--author", default="", help="Author name")
    parser.add_argument("--cover", default="", help="Cover image URL")
    parser.add_argument("--status", default="publish", choices=["draft", "publish"], help="Article status")
    parser.add_argument("--category-id", type=int, default=0, help="Article category ID (0 for uncategorized)")
    parser.add_argument("--base-url", default=get_base_url(), help="API base URL")
    return parser.parse_args()


def main():
    args = parse_args()

    if not check_config():
        sys.exit(2)

    api_key = get_api_key()
    if not api_key:
        eprint("Error: API key is not set")
        sys.exit(2)

    content = args.content
    if args.content_file:
        try:
            # Read with UTF-8, fallback to system encoding
            try:
                with open(args.content_file, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Windows GBK fallback for legacy files
                with open(args.content_file, "r", encoding="cp936") as f:
                    content = f.read()
        except FileNotFoundError:
            eprint(f"Error: content file not found: {args.content_file}")
            sys.exit(1)
        except Exception as e:
            eprint(f"Error reading content file: {e}")
            sys.exit(1)

    payload = {
        "title": args.title,
        "content": content,
        "summary": args.summary,
        "author": args.author,
        "cover": args.cover,
        "status": args.status,
        "category_id": args.category_id,
    }

    # 去掉空字段，避免某些后端严格校验
    payload = {k: v for k, v in payload.items() if v != ""}

    url = build_url(args.base_url, ENDPOINT_PUBLISH_ARTICLE)

    try:
        status_code, raw = http_post_json(url, api_key, payload)
    except RuntimeError as e:
        eprint(str(e))
        sys.exit(1)

    try:
        parsed = json.loads(raw)
        print(json.dumps({
            "ok": 200 <= status_code < 300,
            "status_code": status_code,
            "request_url": url,
            "payload": payload,
            "response": parsed,
        }, ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        print(json.dumps({
            "ok": 200 <= status_code < 300,
            "status_code": status_code,
            "request_url": url,
            "payload": payload,
            "response_raw": raw,
        }, ensure_ascii=False, indent=2))

    sys.exit(0 if 200 <= status_code < 300 else 1)


if __name__ == "__main__":
    main()
