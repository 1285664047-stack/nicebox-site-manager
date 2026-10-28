#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SEO/GEO API fallback commands matching the MCP tools."""

import argparse
import sys
import uuid
import urllib.parse

from openclaw_client import OpenClawError, output, request


def normalize_domain(value):
    text = str(value or "").strip()
    parsed = urllib.parse.urlparse(text if "://" in text else "https://" + text)
    return (parsed.hostname or "").rstrip(".").lower() + ((":" + str(parsed.port)) if parsed.port else "")


def parse_args():
    parser = argparse.ArgumentParser(description="SEO/GEO 检测与一键优化 API 回退工具")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("latest")
    report = sub.add_parser("report")
    report.add_argument("--report-id", type=int, required=True)
    items = sub.add_parser("optimizable")
    items.add_argument("--report-id", type=int, required=True)
    sub.add_parser("direct-plan")
    detect = sub.add_parser("start-detect")
    detect.add_argument("--confirmed", action="store_true")
    detect.add_argument("--target-domain", default="")
    detect.add_argument("--request-id", default="")
    detect_status = sub.add_parser("detect-status")
    detect_status.add_argument("--operation-id", required=True)
    optimize = sub.add_parser("start-optimize")
    optimize.add_argument("--report-id", type=int, required=True)
    optimize.add_argument("--items", type=int, nargs="+", required=True)
    optimize.add_argument("--confirmed", action="store_true")
    optimize.add_argument("--request-id", default="")
    optimize_status = sub.add_parser("optimize-status")
    optimize_status.add_argument("--operation-id", required=True)
    direct = sub.add_parser("start-direct-optimize")
    direct.add_argument("--confirmed", action="store_true")
    direct.add_argument("--request-id", default="")
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        if args.action == "latest":
            data = request("GET", "/seo_geo/getLatest")
            if data is None:
                output({"action": args.action, "data": {"found": False, "report": None, "message": "未找到检测报告", "next_action": "direct_optimization"}})
                return 0
        elif args.action == "report":
            data = request("GET", "/seo_geo/getReport", {"report_id": args.report_id})
        elif args.action == "optimizable":
            data = request("GET", "/seo_geo/getOptimizableItems", {"report_id": args.report_id})
        elif args.action == "direct-plan":
            data = request("GET", "/seo_geo/getDirectOptimizationPlan")
        elif args.action == "start-detect":
            site_status = request("GET", "/site/status")
            current_domain = str(site_status.get("domain") or "").strip()
            publish_status = str(site_status.get("publish_status") or "").strip()
            if not args.confirmed:
                output({
                    "need_confirm": True,
                    "current_domain": current_domain,
                    "publish_status": publish_status,
                    "message": "请确保网站已经发布后再检测。当前检测域名：%s。本次检测会消耗 Token 额度，通常需要等待几分钟；只生成报告，不会修改或发布网站。确认对这个域名开始检测吗？" % (current_domain or "未获取到域名"),
                    "options": ["确认开始", "取消"],
                })
                return 3
            if publish_status.lower() not in ("published", "1", "true"):
                output({
                    "error": "当前网站尚未发布，请先发布网站，再进行 SEO/GEO 检测。",
                    "error_code": "SITE_NOT_PUBLISHED",
                    "current_domain": current_domain,
                    "publish_status": publish_status,
                }, ok=False)
                return 1
            if not args.target_domain or normalize_domain(args.target_domain) != normalize_domain(current_domain):
                output({
                    "need_confirm": True,
                    "error_code": "CONFIRMATION_REQUIRED",
                    "message": "当前检测域名未确认或已经变化，请展示最新域名并重新确认。",
                    "current_domain": current_domain,
                })
                return 3
            data = request("POST", "/seo_geo/startDetection", {
                "confirmed": True,
                "target_domain": current_domain,
                "request_id": args.request_id or "legacy-detect-" + uuid.uuid4().hex,
            })
        elif args.action == "detect-status":
            data = request("GET", "/seo_geo/getDetectionStatus", {"operation_id": args.operation_id})
        elif args.action == "start-optimize":
            if not args.confirmed:
                output({
                    "need_confirm": True,
                    "message": "一键优化会修改网站后台内容，但不会自动发布公网。请先展示真实可优化项摘要，确认继续吗？",
                    "report_id": args.report_id,
                    "item_nos": args.items,
                })
                return 3
            data = request("POST", "/seo_geo/startOptimization", {
                "report_id": args.report_id,
                "item_nos": args.items,
                "confirmed": True,
                "request_id": args.request_id or "legacy-optimize-" + uuid.uuid4().hex,
            })
        elif args.action == "start-direct-optimize":
            if not args.confirmed:
                output({
                    "need_confirm": True,
                    "message": "全量一键优化会逐项修改网站后台内容，但不会自动发布公网。请先展示完整优化计划，确认继续吗？",
                })
                return 3
            data = request("POST", "/seo_geo/startDirectOptimization", {
                "confirmed": True,
                "request_id": args.request_id or "legacy-direct-optimize-" + uuid.uuid4().hex,
            })
        else:
            data = request("GET", "/seo_geo/getOptimizationStatus", {"operation_id": args.operation_id})
        output({"action": args.action, "data": data})
        return 0
    except OpenClawError as exc:
        output({"error": str(exc), "error_code": exc.code, "data": exc.data}, ok=False)
        return 1


if __name__ == "__main__":
    sys.exit(main())
