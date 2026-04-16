#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error


DEFAULT_BASE_URL = "http://aidev.nicebox.cn/api/openclaw"
ENDPOINT_LIST_LANGUAGES = "/site_pages/getLanguageList"
ENDPOINT_INITIALIZE_SITE = "/template/initializeData"
ENDPOINT_GUIDE_DIALOGUE = "/aitools/guideDialogue"
ENDPOINT_GUIDE_COLLECT = "/aitools/guideCollect"


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def get_env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def build_url(base_url: str, endpoint: str, params: dict = None) -> str:
    url = base_url.rstrip("/") + endpoint
    if params:
        clean = {k: v for k, v in params.items() if v is not None and v != ""}
        if clean:
            url += "?" + urllib.parse.urlencode(clean)
    return url


def http_get(url: str, api_key: str, timeout: int = 30):
    req = urllib.request.Request(
        url=url,
        method="GET",
        headers={
            "Authorization": api_key,
            "Accept": "application/json",
            "User-Agent": "nicebox-openclaw-skill/1.0",
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


def http_post(url: str, api_key: str, timeout: int = 30):
    req = urllib.request.Request(
        url=url,
        method="POST",
        headers={
            "Authorization": api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "nicebox-openclaw-skill/1.0",
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


def check_site_languages(base_url, api_key):
    """检查站点语言是否存在"""
    url = build_url(base_url, ENDPOINT_LIST_LANGUAGES)
    try:
        status_code, raw = http_get(url, api_key)
        if 200 <= status_code < 300:
            parsed = json.loads(raw)
            if parsed.get('code') == 200:
                languages = parsed.get('data', {}).get('list', [])
                return len(languages) > 0
        return False
    except Exception as e:
        eprint(f"检查站点语言失败: {e}")
        return False


def initialize_site(base_url, api_key):
    """初始化站点"""
    url = build_url(base_url, ENDPOINT_INITIALIZE_SITE)
    try:
        status_code, raw = http_post(url, api_key)
        if 200 <= status_code < 300:
            parsed = json.loads(raw)
            if parsed.get('code') == 200:
                return True, "初始化成功"
            else:
                return False, parsed.get('message', '初始化失败')
        return False, f"HTTP错误: {status_code}"
    except Exception as e:
        return False, f"初始化失败: {e}"


def start_guide_dialogue(base_url, api_key):
    """启动引导对话"""
    url = build_url(base_url, ENDPOINT_GUIDE_DIALOGUE)
    try:
        status_code, raw = http_post(url, api_key)
        if 200 <= status_code < 300:
            return True, "引导对话已启动"
        return False, f"HTTP错误: {status_code}"
    except Exception as e:
        return False, f"引导对话失败: {e}"


def collect_guide_info(base_url, api_key):
    """收集引导对话信息"""
    url = build_url(base_url, ENDPOINT_GUIDE_COLLECT)
    try:
        status_code, raw = http_post(url, api_key)
        if 200 <= status_code < 300:
            return True, "信息汇总完成"
        return False, f"HTTP错误: {status_code}"
    except Exception as e:
        return False, f"信息汇总失败: {e}"


def parse_args():
    parser = argparse.ArgumentParser(description="Generate website with AI assistance from NiceBox OpenClaw API")
    parser.add_argument("--base-url", default=get_env("AIBOX_BASE_URL", DEFAULT_BASE_URL), help="API base URL")
    return parser.parse_args()


def main():
    args = parse_args()

    api_key = get_env("AIBOX_API_KEY")
    if not api_key:
        eprint("Error: AIBOX_API_KEY is not set")
        sys.exit(2)

    # 1. 检查站点语言是否存在
    eprint("步骤1: 检查站点语言...")
    languages_exist = check_site_languages(args.base_url, api_key)
    eprint(f"站点语言存在: {languages_exist}")

    # 2. 如果存在语言，提示是否需要初始化网站
    if languages_exist:
        eprint("\n步骤2: 站点已存在语言，需要初始化网站吗？")
        eprint("初始化网站会清除站点现有的页面、产品、文章、留言等内容。")
        # 注意：在实际使用中，这里应该通过交互方式获取用户输入
        # 这里为了演示，默认选择不初始化
        initialize = False
        eprint("默认选择: 不初始化")

        if initialize:
            eprint("\n步骤3: 初始化网站...")
            success, message = initialize_site(args.base_url, api_key)
            eprint(f"初始化结果: {message}")
            if not success:
                eprint("初始化失败，退出流程")
                sys.exit(1)
    else:
        eprint("\n步骤2: 站点不存在语言，跳过初始化步骤")

    # 3. 启动引导对话收集网站信息
    eprint("\n步骤4: 启动引导对话，收集网站信息...")
    success, message = start_guide_dialogue(args.base_url, api_key)
    eprint(f"引导对话结果: {message}")
    if not success:
        eprint("引导对话失败，退出流程")
        sys.exit(1)

    # 4. 显示最后整理的汇总内容
    eprint("\n步骤5: 整理汇总内容...")
    success, message = collect_guide_info(args.base_url, api_key)
    eprint(f"汇总结果: {message}")
    if not success:
        eprint("汇总失败，退出流程")
        sys.exit(1)

    eprint("\n网站生成流程完成！")

    # 输出最终结果
    print(json.dumps({
        "ok": True,
        "message": "网站生成流程已完成",
        "steps": [
            {"step": 1, "name": "检查站点语言", "result": f"语言存在: {languages_exist}"},
            {"step": 2, "name": "初始化网站", "result": "跳过" if not languages_exist else "未执行"},
            {"step": 3, "name": "引导对话", "result": "成功"},
            {"step": 4, "name": "信息汇总", "result": "成功"}
        ]
    }, ensure_ascii=False, indent=2))

    sys.exit(0)


if __name__ == "__main__":
    main()
