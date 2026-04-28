#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw 素材上传脚本
功能：上传图片文件到站点资源库，自动判断文件类型
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path

from config_reader import get_api_key, get_base_url, check_config

# API端点（base_url 已包含 /api/openclaw，此处只写相对路径）
ENDPOINT_UPLOAD = "/material/upload"

def load_config():
    """加载配置"""
    if not check_config():
        sys.exit(1)
    
    return {
        "base_url": get_base_url(),
        "api_key": get_api_key()
    }

def detect_file_type(file_path):
    """
    自动检测文件类型
    返回对应的 source 值
    """
    file_name = os.path.basename(file_path).lower()
    
    # 检测 logo 文件
    if any(keyword in file_name for keyword in ['logo']):
        return 'guide_logo'
    
    # 检测产品图片
    if any(keyword in file_name for keyword in ['product', '产品', '商品']):
        return 'openclaw_products'
    
    # 检测新闻图片
    if any(keyword in file_name for keyword in ['news', '新闻', '资讯']):
        return 'openclaw_news'
    
    # 默认类型
    return 'openclaw_other'

def upload_file(file_path, source=None):
    """
    上传文件到站点资源库
    """
    config = load_config()
    api_url = config['api_url']
    api_key = config['api_key']
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误：文件不存在: {file_path}")
        return False
    
    # 检查文件大小
    file_size = os.path.getsize(file_path)
    if file_size > 10 * 1024 * 1024:  # 10MB 限制
        print("错误：文件大小超过 10MB 限制")
        return False
    
    # 自动检测文件类型
    if source is None:
        source = detect_file_type(file_path)
        print(f"自动检测文件类型: {source}")
    
    # 构建请求URL
    url = f"{api_url}{ENDPOINT_UPLOAD}"
    
    # 准备请求头
    headers = {
        'Authorization': api_key
    }
    
    # 准备文件数据
    files = {}
    if source == 'guide_logo':
        files['logoFile'] = open(file_path, 'rb')
    else:
        files['file'] = open(file_path, 'rb')
    
    # 准备表单数据
    data = {
        'source': source
    }
    
    print(f"正在上传文件: {file_path}")
    print(f"目标类型: {source}")
    print(f"请求URL: {url}")
    
    try:
        # 发送请求
        response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        response.raise_for_status()
        
        # 解析响应
        result = response.json()
        
        if result.get('code') == 0:
            print("\n上传成功！")
            print(f"文件ID: {result['data'].get('fileId')}")
            print(f"文件URL: {result['data'].get('filePath')}")
            if result['data'].get('isOld'):
                print("提示：该文件已存在，返回的是已有文件ID")
            return True
        else:
            print(f"\n上传失败: {result.get('message')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n网络错误: {e}")
        return False
    except json.JSONDecodeError:
        print("\n响应解析错误")
        print(f"响应内容: {response.text[:500]}")
        return False
    finally:
        # 关闭文件
        for file in files.values():
            file.close()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='OpenClaw 素材上传工具')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # upload 命令
    upload_parser = subparsers.add_parser('upload', help='上传文件')
    upload_parser.add_argument('file', help='要上传的文件路径')
    upload_parser.add_argument('--source', choices=['guide_logo', 'openclaw_products', 'openclaw_news'], 
                              help='文件类型（不指定则自动检测）')
    
    # 解析参数
    args = parser.parse_args()
    
    if args.command == 'upload':
        success = upload_file(args.file, args.source)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
