#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generic REST fallback for one-to-one Nicebox MCP API tools."""

import argparse
import json
import sys
import urllib.parse

from openclaw_client import OpenClawError, output, request
from config_reader import get_base_url


TOOLS = {
    "nicebox_get_site_status": ("GET", "/site/status"),
    "nicebox_get_site_source": ("GET", "/site/getFromUrl"),
    "nicebox_list_languages": ("GET", "/site_pages/getLanguageList"),
    "nicebox_verify_homepage": ("GET", "/site_pages/readIndexHtml"),
    "nicebox_list_article_categories": ("GET", "/article/getCategories"),
    "nicebox_list_product_categories": ("GET", "/product/getCategories"),
    "nicebox_create_article_category": ("POST", "/article/createCategory"),
    "nicebox_create_product_category": ("POST", "/product/createCategory"),
    "nicebox_generate_article_content": ("POST", "/ai_tools/generateNewsContent"),
    "nicebox_generate_product_content": ("POST", "/ai_tools/generateProductContent"),
    "nicebox_generate_content_cover": ("POST", "/ai_tools/generateContentCover"),
    "nicebox_generate_content_preview": ("GET", "/site/generateContentShareUrl"),
    "nicebox_list_messages": ("GET", "/message/list"),
    "nicebox_generate_preview": ("GET", "/site/generateShareUrl"),
    "nicebox_get_ftp_config": ("GET", "/site_publish/getConfig"),
    "nicebox_test_ftp_connection": ("POST", "/site_publish/testFtpConnection"),
    "nicebox_get_publish_status": ("GET", "/site_publish/getTaskStatus"),
    "nicebox_save_company_info": ("POST", "/ai_tools/getCompanyInfo"),
}


def parse_args():
    parser = argparse.ArgumentParser(description="MCP 原子工具的普通 REST API 回退入口")
    parser.add_argument("tool", choices=sorted(TOOLS))
    parser.add_argument("--args-json", default="{}", help="JSON object，字段与 MCP 工具参数一致")
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        payload = json.loads(args.args_json)
        if not isinstance(payload, dict):
            raise ValueError("--args-json 必须是 JSON object")
        if args.tool == "nicebox_generate_content_cover" and not payload.get("aspect_ratio"):
            output({"need_input": True, "message": "请先让用户选择图片比例，再生成封面。"})
            return 3
        method, path = TOOLS[args.tool]
        data = request(method, path, payload)
        if args.tool in ("nicebox_generate_content_preview", "nicebox_generate_preview") and isinstance(data, dict):
            share_url = data.get("share_url")
            if isinstance(share_url, str) and share_url.startswith("/"):
                base = urllib.parse.urlparse(get_base_url())
                data = {**data, "share_url": "%s://%s%s" % (base.scheme, base.netloc, share_url)}
        output({"tool": args.tool, "data": data})
        return 0
    except (ValueError, json.JSONDecodeError) as exc:
        output({"error": str(exc), "error_code": "INVALID_ARGUMENTS"}, ok=False)
        return 2
    except OpenClawError as exc:
        output({"error": str(exc), "error_code": exc.code, "data": exc.data}, ok=False)
        return 1


if __name__ == "__main__":
    sys.exit(main())
