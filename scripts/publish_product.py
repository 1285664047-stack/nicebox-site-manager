#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
import urllib.request
import urllib.error

from config_reader import get_api_key, get_base_url, check_config

ENDPOINT_PUBLISH_PRODUCT = "/product/publish"


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
    parser = argparse.ArgumentParser(description="Publish product to AiWebSite OpenClaw API")
    parser.add_argument("--name", required=True, help="Product name")
    parser.add_argument("--price", required=True, type=float, help="Product price")
    content_group = parser.add_mutually_exclusive_group()
    content_group.add_argument("--content", default="", help="Product content (use --content-file for large/Chinese content)")
    content_group.add_argument("--content-file", default="", help="Path to file containing product content (recommended for Chinese/HTML)")
    desc_group = parser.add_mutually_exclusive_group()
    desc_group.add_argument("--description", default="", help="Product description (use --desc-file for Chinese content)")
    desc_group.add_argument("--desc-file", default="", help="Path to file containing product description (recommended for Chinese text)")
    parser.add_argument("--category-id", type=int, default=0, help="Product category ID")
    parser.add_argument("--currency", default="CNY", help="Currency code")
    parser.add_argument("--sort-order", type=int, default=0, help="Sort order")
    parser.add_argument("--status", default="publish", choices=["draft", "publish"], help="Product status")
    parser.add_argument("--images", nargs="*", default=[], help="Product image URLs")
    parser.add_argument("--locale", default="zh-CN", help="Locale")
    parser.add_argument("--filename", default="", help="Filename")
    parser.add_argument("--seo-title", default="", help="SEO title")
    parser.add_argument("--keywords", default="", help="Keywords")
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

    # Read content from file if --content-file specified
    content = args.content
    if args.content_file:
        try:
            try:
                with open(args.content_file, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(args.content_file, "r", encoding="cp936") as f:
                    content = f.read()
        except FileNotFoundError:
            eprint(f"Error: content file not found: {args.content_file}")
            sys.exit(1)
        except Exception as e:
            eprint(f"Error reading content file: {e}")
            sys.exit(1)

    # Read description from file if --desc-file specified
    description = args.description
    if args.desc_file:
        try:
            try:
                with open(args.desc_file, "r", encoding="utf-8") as f:
                    description = f.read()
            except UnicodeDecodeError:
                with open(args.desc_file, "r", encoding="cp936") as f:
                    description = f.read()
        except FileNotFoundError:
            eprint(f"Error: desc file not found: {args.desc_file}")
            sys.exit(1)
        except Exception as e:
            eprint(f"Error reading desc file: {e}")
            sys.exit(1)

    payload = {
        "name": args.name,
        "price": args.price,
        "content": content,
        "description": description,
        "category_id": args.category_id,
        "currency": args.currency,
        "sort_order": args.sort_order,
        "status": args.status,
        "images": args.images,
        "locale": args.locale,
        "filename": args.filename,
        "seo_title": args.seo_title,
        "keywords": args.keywords,
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
