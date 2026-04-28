# -*- coding: utf-8 -*-
"""
设置 API 秘钥 - 写入配置文件
用法：
  python set-key.py <新密钥>        设置并保存到配置文件
  python set-key.py                查看当前密钥

功能：设置 API 密钥后，自动调用接口获取 base_url 和 site_from 信息
"""
import sys
import urllib.request
import urllib.error
import json

# Windows GBK 环境下 emoji 和中文可能崩溃，强制 UTF-8 输出
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from config_reader import get_api_key, get_base_url
from config_manager import set_api_key, set_base_url, set_site_from, init_config, load_config, clear_api_key

def get_site_info_from_api(api_key):
    """调用接口获取站点信息（base_url 和 site_from）"""
    # 从配置文件读取 base_url，如果没有设置则使用备用URL
    base_url = get_base_url()
    if not base_url:
        base_url = 'https://ai.qidc.cn/api/openclaw'
    endpoint = '/site/getFromUrl'
    
    url = f"{base_url}{endpoint}"
    req = urllib.request.Request(
        url=url,
        method='GET',
        headers={
            'Authorization': api_key,
            'Accept': 'application/json',
            'User-Agent': 'qidc-openclaw-skill/1.0',
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
            data = json.loads(raw)
            
            if data.get('code') == 0 and data.get('data'):
                return data['data']
            else:
                print(f"警告：接口返回错误 - {data.get('msg', '未知错误')}")
                return None
    except urllib.error.HTTPError as e:
        print(f"警告：HTTP 请求失败 ({e.code})")
        return None
    except Exception as e:
        print(f"警告：无法连接到服务器 - {e}")
        return None

def main():
    new_key = sys.argv[1] if len(sys.argv) > 1 else ''

    if not new_key:
        current = get_api_key('')
        print(current[:8] + '****' if current else '当前：未设置')
        print('用法：python set-key.py <新密钥>')
        print('清除密钥：python set-key.py --clear')
        return
    
    # 清除密钥
    if new_key == '--clear':
        clear_api_key()
        return

    # 确保配置文件存在
    config = load_config()
    if not config:
        init_config()
        config = load_config()
        if not config:
            print('[ERROR] 无法初始化配置文件')
            return

    # 第一步：设置 API 密钥
    config['api_key'] = new_key

    # 第二步：调用接口获取站点信息
    print('[INFO] 正在获取站点配置信息...')
    site_info = get_site_info_from_api(new_key)

    if site_info:
        domain = site_info.get('domain', '')
        site_from = site_info.get('site_from', '')

        # 构建完整的 base_url
        if domain:
            config['base_url'] = f"{domain}/api/openclaw"

        # 设置 site_from
        if site_from:
            config['site_from'] = site_from

    # 一次性保存所有配置（原子写入）
    from config_manager import save_config
    if save_config(config):
        print(f'[OK] API 密钥已更新：{new_key[:8]}****')
    else:
        print('[ERROR] 配置保存失败')

if __name__ == '__main__':
    main()
