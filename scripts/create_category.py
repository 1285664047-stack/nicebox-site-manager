#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create an article or product category through the OpenClaw REST API."""

import argparse
import sys

from openclaw_client import OpenClawError, output, request


ENDPOINTS = {
    "article": "/article/createCategory",
    "product": "/product/createCategory",
}


def parse_args():
    parser = argparse.ArgumentParser(description="创建 Nicebox 文章或产品分类")
    parser.add_argument("content_type", choices=sorted(ENDPOINTS), help="分类类型")
    parser.add_argument("--name", required=True, help="分类名称")
    parser.add_argument("--parent-id", type=int, default=0, help="父分类 ID，顶级分类为 0")
    parser.add_argument("--sort-order", type=int, help="排序值，不传则由服务端自动设置")
    parser.add_argument("--locale", default="zh-CN", help="语言代码，例如 zh-CN")
    return parser.parse_args()


def main():
    args = parse_args()
    name = args.name.strip()
    if not name:
        output({"error": "分类名称不能为空", "error_code": "CATEGORY_NAME_REQUIRED"}, ok=False)
        return 2
    if args.parent_id < 0 or (args.sort_order is not None and args.sort_order < 0):
        output({"error": "父分类 ID 和排序值不能小于 0", "error_code": "INVALID_ARGUMENTS"}, ok=False)
        return 2

    payload = {
        "name": name,
        "parent_id": args.parent_id,
        "locale": args.locale,
    }
    if args.sort_order is not None:
        payload["sort_order"] = args.sort_order

    try:
        data = request("POST", ENDPOINTS[args.content_type], payload)
        output({"content_type": args.content_type, "data": data})
        return 0
    except OpenClawError as exc:
        output({"error": str(exc), "error_code": exc.code, "data": exc.data}, ok=False)
        return 1


if __name__ == "__main__":
    sys.exit(main())
