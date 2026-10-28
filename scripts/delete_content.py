#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

from openclaw_client import OpenClawError, output, request


def parse_args():
    parser = argparse.ArgumentParser(description="Permanently delete one Nicebox article or product")
    parser.add_argument("content_type", choices=["article", "product"])
    parser.add_argument("--id", type=int, required=True)
    parser.add_argument("--expected-name", required=True)
    parser.add_argument("--expected-locale", required=True)
    parser.add_argument("--expected-category-id", type=int, required=True)
    parser.add_argument("--expected-sort-order", type=int, required=True)
    parser.add_argument("--confirmed", action="store_true", help="User confirmed permanent deletion of the displayed record")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.id <= 0 or args.expected_category_id < 0 or args.expected_sort_order < 0:
        output({"error": {"code": "VALIDATION_FAILED", "message": "删除确认参数无效"}}, False)
        return 2
    if not args.expected_name.strip() or not args.expected_locale.strip():
        output({"error": {"code": "VALIDATION_FAILED", "message": "删除确认信息不完整"}}, False)
        return 2
    if not args.confirmed:
        output({"error": {"code": "CONFIRMATION_REQUIRED", "message": "必须先展示完整内容信息、警告删除不可恢复并取得用户明确确认"}}, False)
        return 2
    id_field = "article_id" if args.content_type == "article" else "product_id"
    try:
        data = request("POST", "/%s/delete" % args.content_type, {
            id_field: args.id,
            "expected_name": args.expected_name.strip(),
            "expected_locale": args.expected_locale.strip(),
            "expected_category_id": args.expected_category_id,
            "expected_sort_order": args.expected_sort_order,
            "confirmed": True,
        })
        output({"data": data})
        return 0
    except OpenClawError as exc:
        output({"error": {"code": exc.code, "message": str(exc), "data": exc.data}}, False)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
