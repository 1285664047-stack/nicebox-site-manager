#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

from openclaw_client import OpenClawError, output, request


def parse_args():
    parser = argparse.ArgumentParser(description="Update Nicebox article or product sort order")
    parser.add_argument("content_type", choices=["article", "product"])
    parser.add_argument("--id", type=int, required=True, help="Real article/product ID")
    parser.add_argument("--sort-order", type=int, required=True, help="Non-negative sort order")
    parser.add_argument("--current-sort-order", type=int, required=True, help="Sort order shown to the user before confirmation")
    parser.add_argument("--confirmed", action="store_true", help="User confirmed the displayed record and sort change")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.id <= 0 or args.current_sort_order < 0 or args.sort_order < 0:
        output({"error": {"code": "VALIDATION_FAILED", "message": "ID必须为正整数，排序必须为非负整数"}}, False)
        return 2
    if not args.confirmed:
        output({"error": {"code": "CONFIRMATION_REQUIRED", "message": "必须先展示内容信息和排序变化并取得用户明确确认"}}, False)
        return 2
    id_field = "article_id" if args.content_type == "article" else "product_id"
    try:
        data = request("POST", "/%s/updateSort" % args.content_type, {
            id_field: args.id,
            "current_sort_order": args.current_sort_order,
            "sort_order": args.sort_order,
            "confirmed": True,
        })
        output({"data": data})
        return 0
    except OpenClawError as exc:
        output({"error": {"code": exc.code, "message": str(exc), "data": exc.data}}, False)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
