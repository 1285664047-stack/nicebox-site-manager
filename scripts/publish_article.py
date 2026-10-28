#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Article API fallback: cover -> draft -> preview -> confirmed publish."""

import argparse
import sys

from openclaw_client import OpenClawError, output, request


def read_text(value, filename):
    if not filename:
        return value or ""
    for encoding in ("utf-8", "cp936"):
        try:
            with open(filename, "r", encoding=encoding) as stream:
                return stream.read()
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            raise RuntimeError("无法读取内容文件：%s" % exc) from exc
    raise RuntimeError("无法识别内容文件编码：%s" % filename)


def parse_args():
    parser = argparse.ArgumentParser(description="文章草稿、预览和正式发布 API 回退工具")
    parser.add_argument("--title", default="")
    parser.add_argument("--content", default="")
    parser.add_argument("--content-file", default="")
    parser.add_argument("--summary", default="")
    parser.add_argument("--author", default="")
    parser.add_argument("--cover", default="")
    parser.add_argument("--ai-cover", action="store_true")
    parser.add_argument("--cover-ratio", choices=["1:1", "4:3", "3:2", "16:9", "2:3", "3:4", "9:16"])
    parser.add_argument("--category-id", type=int, default=0)
    parser.add_argument("--locale", default="zh-CN")
    parser.add_argument("--publish-saved", type=int, default=0, metavar="ARTICLE_ID")
    parser.add_argument("--confirmed", action="store_true")
    parser.add_argument("--status", choices=["draft", "publish"], default="draft", help="兼容旧命令；始终先保存草稿")
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        if args.publish_saved:
            if not args.confirmed:
                output({
                    "need_confirm": True,
                    "message": "请先查看文章预览。确认正式发布这篇文章吗？",
                    "article_id": args.publish_saved,
                })
                return 3
            data = request("POST", "/article/publishSaved", {"article_id": args.publish_saved})
            output({"action": "published", "data": data})
            return 0

        if not args.title or (not args.content and not args.content_file):
            raise RuntimeError("保存文章草稿需要 --title，以及 --content 或 --content-file")
        cover = args.cover
        if not cover and not args.ai_cover:
            output({
                "need_cover_choice": True,
                "message": "文章还没有封面。请上传/提供可访问的图片 URL，或选择通过 AI 生成封面。",
                "options": ["提供封面URL", "AI生成封面"],
            })
            return 3
        if not cover:
            if not args.cover_ratio:
                output({
                    "need_cover_ratio": True,
                    "message": "请选择 AI 文章封面的图片比例。",
                    "options": ["1:1", "4:3", "3:2", "16:9", "2:3", "3:4", "9:16"],
                })
                return 3
            cover_data = request("POST", "/ai_tools/generateContentCover", {
                "content_type": "article", "title": args.title,
                "aspect_ratio": args.cover_ratio,
            })
            generated_url = cover_data["cover_url"]
            upload_data = request("POST", "/image/upload", {
                "image_url": generated_url,
                "purpose": "article_cover",
                "original_name": "article-cover",
            })
            cover = upload_data["image_url"]

        payload = {
            "title": args.title,
            "content": read_text(args.content, args.content_file),
            "summary": args.summary,
            "author": args.author,
            "cover": cover,
            "category_id": args.category_id,
            "locale": args.locale,
            "status": 0,
        }
        draft = request("POST", "/article/save", {key: value for key, value in payload.items() if value != ""})
        preview = request("GET", "/site/generateContentShareUrl", {
            "content_type": "article", "content_id": draft["article_id"],
        })
        output({
            "action": "draft_created",
            "article_id": draft["article_id"],
            "cover_url": cover,
            "preview_url": preview["share_url"],
            "need_publish_confirm": True,
            "message": "文章已保存为草稿，请先查看预览。是否需要正式发布这篇文章？",
            "publish_command": "--publish-saved %s --confirmed" % draft["article_id"],
        })
        return 0
    except (OpenClawError, RuntimeError) as exc:
        output({"error": str(exc), "error_code": getattr(exc, "code", "LOCAL_ERROR")}, ok=False)
        return 1


if __name__ == "__main__":
    sys.exit(main())
