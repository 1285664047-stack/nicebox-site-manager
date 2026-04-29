# -*- coding: utf-8 -*-
"""
设置 API 秘钥 - 写入配置文件
用法：
  python set-key.py <新密钥>        设置并保存到配置文件（自动获取 base_url 和 site_from）
  python set-key.py                查看当前密钥

功能：设置 API 密钥后，自动调用接口获取 base_url 和 site_from 信息
"""
import sys
import os

# Windows GBK 环境下 emoji 和中文可能崩溃，强制 UTF-8 输出
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 确保同目录下的模块可以被导入
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from config_manager import (
    set_api_key, init_config, load_config, clear_api_key
)


def get_current_key():
    """获取当前 API 密钥（从配置中读取）"""
    config = load_config()
    if not config:
        return None
    return config.get('api_key', None)


def main():
    new_key = sys.argv[1] if len(sys.argv) > 1 else ''

    if not new_key:
        current = get_current_key()
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

    # 调用 config_manager 设置密钥（强制获取 base_url 和 site_from）
    set_api_key(new_key)


if __name__ == '__main__':
    main()
