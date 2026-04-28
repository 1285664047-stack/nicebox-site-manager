#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_share_url.py - 生成临时分享链接
修复：移除 requests 依赖，改用 urllib（与其他脚本保持一致）
"""

import os
import sys
import json
import urllib.request
import urllib.error

# Windows PowerShell 默认 GBK 编码，强制 UTF-8 输出
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from config_reader import get_api_key, get_base_url, check_config


def load_config():
    """加载配置"""
    if not check_config():
        sys.exit(1)
    return {
        "api_url": get_base_url(),
        "api_key": get_api_key()
    }


def check_site_has_content(config):
    """检查站点是否有内容（通过语言列表检测）"""
    url = f"{config['api_url']}/site_pages/getLanguageList"
    headers = {
        "Authorization": config['api_key'],
        "Content-Type": "application/json"
    }
    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read().decode('utf-8'))

        if result.get("code") != 0 or not result.get("data"):
            print(f"[ERROR] 无法获取站点语言配置 - {result.get('message', '未知错误')}")
            sys.exit(1)

        data = result.get("data", {})
        total = data.get("total", 0)

        if total == 0:
            print("\n[ERROR] 站点暂无网站内容，请先生成并发布网站后再生成分享链接。")
            sys.exit(1)

        print(f"[OK] 站点内容检测通过（语言配置 {total} 项）")
        return total

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='replace')
        print(f"[ERROR] HTTP {e.code}: {error_body}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        sys.exit(1)


def generate_share_url(config):
    """生成临时分享地址"""
    url = f"{config['api_url']}/site/generateShareUrl"
    headers = {
        "Authorization": config['api_key'],
        "Content-Type": "application/json"
    }

    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read().decode('utf-8'))

        if result.get("code") == 0:
            data = result.get("data", {})
            share_url_path = data.get("share_url", "")
            site_id = data.get("site_id", "")

            # share_url 是相对路径（如 /api/template/preview/share/token/xxx），需提取 origin 拼接
            if share_url_path and not share_url_path.startswith('http'):
                from urllib.parse import urlparse
                origin = f"{urlparse(config['api_url']).scheme}://{urlparse(config['api_url']).netloc}"
                share_url = origin + share_url_path
            else:
                share_url = share_url_path

            print("\n[OK] 临时分享链接生成成功：")
            if site_id:
                print(f"   Site ID： {site_id}")
            print(f"   分享链接：{share_url}")
            print(f"   有效期：  2 小时\n")
        else:
            print(f"[ERROR] {result.get('message', '生成分享地址失败')}")
            sys.exit(1)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='replace')
        print(f"[ERROR] HTTP {e.code}: {error_body}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        sys.exit(1)


def main():
    """主函数"""
    config = load_config()
    check_site_has_content(config)
    generate_share_url(config)


if __name__ == "__main__":
    main()
