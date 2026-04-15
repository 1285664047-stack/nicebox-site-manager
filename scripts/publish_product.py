#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
import urllib.request
import urllib.error


DEFAULT_BASE_URL = "https://ai.nicebox.cn/api/openclaw"
ENDPOINT_PUBLISH_PRODUCT = "/product/publish"


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def get_env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


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
    parser = argparse.ArgumentParser(description="Publish product to NiceBox OpenClaw API")
    parser.add_argument("--name", required=True, help="Product name")
    parser.add_argument("--price", required=True, type=float, help="Product price")
    parser.add_argument("--content", default="", help="Product content")
    parser.add_argument("--description", default="", help="Product description")
    parser.add_argument("--category-id", type=int, default=0, help="Product category ID")
    parser.add_argument("--currency", default="CNY", help="Currency code")
    parser.add_argument("--sort-order", type=int, default=0, help="Sort order")
    parser.add_argument("--status", default="publish", choices=["draft", "publish"], help="Product status")
    parser.add_argument("--images", nargs="*", default=[], help="Product image URLs")
    parser.add_argument("--locale", default="zh-CN", help="Locale")
    parser.add_argument("--filename", default="", help="Filename")
    parser.add_argument("--seo-title", default="", help="SEO title")
    parser.add_argument("--seo-keywords", default="", help="SEO keywords")
    parser.add_argument("--seo-description", default="", help="SEO description")
    parser.add_argument("--base-url", default=get_env("AIBOX_BASE_URL", DEFAULT_BASE_URL), help="API base URL")
    return parser.parse_args()


def main():
    args = parse_args()

    api_key = get_env("AIBOX_API_KEY")
    if not api_key:
        eprint("Error: AIBOX_API_KEY is not set")
        sys.exit(2)

    payload = {
        "name": args.name,
        "price": args.price,
        "content": args.content,
        "description": args.description,
        "category_id": args.category_id,
        "currency": args.currency,
        "sort_order": args.sort_order,
        "status": args.status,
        "images": args.images,
        "locale": args.locale,
        "filename": args.filename,
        "seo_title": args.seo_title,
        "seo_keywords": args.seo_keywords,
        "seo_description": args.seo_description,
    }

    # 去掉空字段，避免某些后端严格校验
    payload = {k: v for k, v in payload.items() if v != "" and v != []}

    url = build_url(args.base_url, ENDPOINT_PUBLISH_PRODUCT)

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
