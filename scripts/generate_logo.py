#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate an AI logo candidate through the OpenClaw API."""

import argparse
import sys

from openclaw_client import OpenClawError, output, request


def main():
    parser = argparse.ArgumentParser(description="生成网站 AI Logo 候选图")
    parser.add_argument("--company-name", required=True)
    parser.add_argument("--industry", default="")
    parser.add_argument("--style", default="")
    parser.add_argument("--ratio", choices=["1:1", "5:2", "3:2", "4:3", "3:4", "2:3"], required=True)
    args = parser.parse_args()

    title = " ".join(filter(None, [args.company_name, args.industry, args.style]))[:200]
    try:
        data = request("POST", "/ai_tools/generateContentCover", {
            "content_type": "logo",
            "title": title,
            "aspect_ratio": args.ratio,
        })
        output({
            "action": "logo_generated",
            "logo_url": data.get("logo_url") or data.get("cover_url"),
            "aspect_ratio": data.get("aspect_ratio", args.ratio),
            "message": "Logo 候选图已生成。请展示给用户确认，接受后再用于网站企业资料。",
        })
        return 0
    except OpenClawError as exc:
        output({"error": str(exc), "error_code": exc.code}, ok=False)
        return 1


if __name__ == "__main__":
    sys.exit(main())
