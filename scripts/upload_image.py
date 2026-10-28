#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Upload a local image or import a public image URL into Nicebox cloud assets."""

import argparse
import json
import mimetypes
import os
import sys

import requests

from config_reader import check_config, get_api_key, get_base_url

MAX_SOURCE_BYTES = 10 * 1024 * 1024
PURPOSES = ("logo", "product_cover", "article_cover", "image")


def parse_args():
    parser = argparse.ArgumentParser(description="上传图片到 Nicebox 云资源库")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="本地图片路径")
    source.add_argument("--image-url", action="append", help="公开图片地址，可重复传入以批量上传")
    parser.add_argument("--purpose", choices=PURPOSES, default="image")
    parser.add_argument("--folder-name", help="自定义云资源库文件夹，不存在时自动创建")
    parser.add_argument("--original-name", help="素材库显示文件名")
    return parser.parse_args()


def main():
    args = parse_args()
    if not check_config():
        return 1

    data = {"purpose": args.purpose}
    if args.folder_name:
        data["folder_name"] = args.folder_name
    if args.original_name:
        data["original_name"] = args.original_name

    files = None
    json_payload = None
    stream = None
    try:
        if args.file:
            if not os.path.isfile(args.file):
                raise ValueError("本地图片不存在")
            size = os.path.getsize(args.file)
            if size < 1 or size > MAX_SOURCE_BYTES:
                raise ValueError("图片原文件不能为空且不能超过10MB")
            name = os.path.basename(args.file)
            stream = open(args.file, "rb")
            files = {"file": (name, stream, mimetypes.guess_type(name)[0] or "application/octet-stream")}
        elif len(args.image_url) == 1:
            data["image_url"] = args.image_url[0]
        else:
            json_payload = {**data, "image_urls": args.image_url}

        response = requests.post(
            get_base_url().rstrip("/") + "/image/upload",
            headers={"Authorization": get_api_key(), "Accept": "application/json"},
            data=None if json_payload else data,
            json=json_payload,
            files=files,
            timeout=60,
        )
        payload = response.json()
        if not response.ok or payload.get("code") not in (0, 200):
            raise RuntimeError(payload.get("message") or "图片上传失败")
        print(json.dumps({"ok": True, "data": payload.get("data")}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, RuntimeError, requests.RequestException, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    finally:
        if stream:
            stream.close()


if __name__ == "__main__":
    sys.exit(main())
