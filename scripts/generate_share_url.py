#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import requests
import json

# 基础URL
BASE_URL = os.environ.get("AIBOX_BASE_URL", "http://aidev.nicebox.cn/api/openclaw")

# API路径
ENDPOINT_SHARE_URL = "/site/generateShareUrl"

def load_config():
    """加载配置"""
    # 从环境变量构造
    base_url = os.environ.get("AIBOX_BASE_URL", "http://aidev.nicebox.cn/api/openclaw")
    api_key = os.environ.get("AIBOX_API_KEY", "")
    
    if not api_key:
        print("错误：缺少 API 配置，请设置 AIBOX_API_KEY 环境变量")
        sys.exit(1)
    
    return {
        "api_url": base_url,
        "api_key": api_key
    }

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
            print("\n✅ 临时分享链接生成成功：")
            print(f"   分享链接: {share_url}")
            print(f"   有效期:   2 小时\n")
        else:
            print(f"错误：{result.get('message', '生成分享地址失败')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"错误：{str(e)}")
        sys.exit(1)

def main():
    """主函数"""
    config = load_config()
    generate_share_url(config)

if __name__ == "__main__":
    main()
