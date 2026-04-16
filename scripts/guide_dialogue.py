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
ENDPOINT_GUIDE_DIALOGUE = "/ai_tools/guideDialogue"
ENDPOINT_GUIDE_COLLECT = "/ai_tools/guideCollect"


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


def http_post(url: str, api_key: str, data=None, timeout: int = 30):
    headers = {
        "Authorization": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "nicebox-openclaw-skill/1.0",
    }
    
    req_data = None
    if data:
        req_data = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(
        url=url,
        method="POST",
        headers=headers,
        data=req_data
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


def start_guide_dialogue(base_url, api_key):
    """启动引导对话（多轮交互）"""
    url = build_url(base_url, ENDPOINT_GUIDE_DIALOGUE)
    session = ""
    
    try:
        # 初始请求
        status_code, raw = http_post(url, api_key)
        if 200 <= status_code < 300:
            parsed = json.loads(raw)
            if parsed.get('code') == 200:
                session = parsed.get('data', {}).get('session', '')
                message = parsed.get('data', {}).get('message', '')
                is_complete = parsed.get('data', {}).get('is_complete', False)
                
                eprint(f"AI: {message}")
                
                # 多轮交互
                while not is_complete:
                    # 获取用户输入
                    user_input = input("You: ")
                    
                    # 检查是否退出
                    if user_input.lower() == 'exit':
                        eprint("对话已退出")
                        return False, "对话已退出", ""
                    
                    # 发送用户输入
                    data = {"message": user_input, "session_id": session}
                    status_code, raw = http_post(url, api_key, data)
                    
                    if 200 <= status_code < 300:
                        parsed = json.loads(raw)
                        if parsed.get('code') == 200:
                            session = parsed.get('data', {}).get('session', session)
                            message = parsed.get('data', {}).get('message', '')
                            is_complete = parsed.get('data', {}).get('is_complete', False)
                            eprint(f"AI: {message}")
                        else:
                            return False, f"引导对话失败: {parsed.get('message', '未知错误')}", ""
                    else:
                        return False, f"HTTP错误: {status_code}", ""
                
                return True, "引导对话完成", session
            else:
                return False, parsed.get('message', '引导对话失败'), ""
        return False, f"HTTP错误: {status_code}", ""
    except Exception as e:
        return False, f"引导对话失败: {e}", ""

def collect_guide_info(base_url, api_key, session):
    """收集引导对话信息"""
    url = build_url(base_url, ENDPOINT_GUIDE_COLLECT)
    try:
        # 发送会话ID
        data = {"session": session}
        status_code, raw = http_post(url, api_key, data)
        
        if 200 <= status_code < 300:
            parsed = json.loads(raw)
            if parsed.get('code') == 200:
                summary = parsed.get('data', {}).get('summary', '')
                eprint("\n=== 网站信息汇总 ===")
                eprint(summary)
                eprint("===================")
                return True, "信息汇总完成"
            else:
                return False, parsed.get('message', '信息汇总失败')
        return False, f"HTTP错误: {status_code}"
    except Exception as e:
        return False, f"信息汇总失败: {e}"

def parse_args():
    parser = argparse.ArgumentParser(description="Guide dialogue for website generation with NiceBox OpenClaw API")
    parser.add_argument("--base-url", default=get_env("AIBOX_BASE_URL", DEFAULT_BASE_URL), help="API base URL")
    parser.add_argument("--collect", action="store_true", help="Collect and show summary after dialogue")
    return parser.parse_args()

def main():
    args = parse_args()

    api_key = get_env("AIBOX_API_KEY")
    if not api_key:
        eprint("Error: AIBOX_API_KEY is not set")
        sys.exit(2)

    eprint("启动引导对话...")
    eprint("AI 将逐步询问网站需求，请根据提示回答。")
    eprint("输入 'exit' 可以退出对话。")
    eprint("======================================")
    
    # 启动引导对话
    success, message, session = start_guide_dialogue(args.base_url, api_key)
    eprint(f"\n引导对话结果: {message}")
    
    if success and session and args.collect:
        # 收集汇总信息
        eprint("\n收集汇总信息...")
        success, message = collect_guide_info(args.base_url, api_key, session)
        eprint(f"汇总结果: {message}")

    # 输出最终结果
    print(json.dumps({
        "ok": success,
        "message": message,
        "session": session
    }, ensure_ascii=False, indent=2))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
