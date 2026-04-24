#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import requests
import json

# 基础URL
BASE_URL = os.environ.get("AIBOX_BASE_URL", "https://ai.nicebox.cn/api/openclaw")

# API路径
ENDPOINT_SHARE_URL = "/site/generateShareUrl"
ENDPOINT_LANG_URL = "/site_pages/getLanguageList"

def load_config():
    """加载配置"""
    # 从环境变量构造
    base_url = os.environ.get("AIBOX_BASE_URL", "https://ai.nicebox.cn/api/openclaw")
    api_key = os.environ.get("AIBOX_API_KEY", "")
    
    if not api_key:
        print("错误：缺少 API 配置，请设置 AIBOX_API_KEY 环境变量")
        sys.exit(1)
    
    return {
        "api_url": base_url,
        "api_key": api_key
    }

def check_site_has_content(config):
    """检查站点是否有内容"""
    url = f"{config['api_url']}{ENDPOINT_LANG_URL}"
    headers = {
        "Authorization": config['api_key'],
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        result = response.json()

        if result.get("code") != 0 or not result.get("data"):
            print(f"错误：无法获取站点语言配置 — {result.get('message', '未知错误')}")
            sys.exit(1)

        data = result.get("data", {})
        total = data.get("total", 0)
        list_data = data.get("list", [])

        if total == 0:
            print("\n[操作终止] 站点暂无网站内容，请先生成并发布网站后再生成分享链接。")
            sys.exit(1)

        print(f"[OK] 站点内容检测通过（语言配置 {total} 项）")
        return total

    except Exception as e:
        print(f"错误：{str(e)}")
        sys.exit(1)

def generate_share_url(config):
    """生成临时分享地址"""
    url = f"{config['api_url']}{ENDPOINT_SHARE_URL}"
    headers = {
        "Authorization": config['api_key'],
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        result = response.json()
        
        if result.get("code") == 0:
            data = result.get("data", {})
            share_url = data.get("share_url", "")
            print("\n[OK] 临时分享链接生成成功：")
            print(f"   分享链接：{share_url}")
            print(f"   有效期：  2 小时\n")
        else:
            print(f"错误：{result.get('message', '生成分享地址失败')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"错误：{str(e)}")
        sys.exit(1)

def main():
    """主函数"""
    config = load_config()
    check_site_has_content(config)
    generate_share_url(config)

if __name__ == "__main__":
    main()
