#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

from openclaw_client import OpenClawError, output, request


def parse_args():
    parser = argparse.ArgumentParser(description="List or search Nicebox articles and products")
    parser.add_argument("content_type", choices=["article", "product"])
    parser.add_argument("--keyword", default="", help="Fuzzy title/name keyword")
    parser.add_argument("--id", type=int, default=None, help="Exact article/product ID")
    parser.add_argument("--page", type=int, default=1, help="Page number; page size is fixed at 20")
    parser.add_argument("--locale", default="", help="Optional locale such as zh-CN")
    parser.add_argument("--category-id", type=int, default=None, help="Optional category ID; 0 means uncategorized")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.page < 1:
        output({"error": {"code": "VALIDATION_FAILED", "message": "page must be >= 1"}}, False)
        return 2
    payload = {"page": args.page}
    if args.id is not None:
        if args.id <= 0:
            output({"error": {"code": "VALIDATION_FAILED", "message": "id must be a positive integer"}}, False)
            return 2
        payload["id"] = args.id
    if args.keyword.strip():
        payload["keyword"] = args.keyword.strip()
    if args.locale.strip():
        payload["locale"] = args.locale.strip()
    if args.category_id is not None:
        payload["category_id"] = args.category_id
    try:
        data = request("GET", "/%s/list" % args.content_type, payload)
        output({"data": data})
        return 0
    except OpenClawError as exc:
        output({"error": {"code": exc.code, "message": str(exc), "data": exc.data}}, False)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
