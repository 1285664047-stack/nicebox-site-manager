# -*- coding: utf-8 -*-
"""
配置读取模块 - 统一从配置文件读取 API 密钥和站点信息
"""
import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')


def load_config():
    """加载配置文件"""
    if not os.path.exists(CONFIG_FILE):
        return None
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f'错误：无法读取配置文件 - {e}')
        return None


def get_api_key(fallback=''):
    """获取 API 密钥"""
    config = load_config()
    if config and config.get('api_key'):
        return config['api_key'].strip()
    return fallback


def get_base_url():
    """获取 API 基础 URL"""
    config = load_config()
    if config and config.get('base_url'):
        return config['base_url'].rstrip('/')
    return 'https://ai.qidc.cn/api/openclaw'


def get_site_info(key, fallback=''):
    """获取站点信息"""
    config = load_config()
    if config and 'site_info' in config:
        return config['site_info'].get(key, fallback)
    return fallback


def get_all_site_info():
    """获取所有站点信息"""
    config = load_config()
    if config and 'site_info' in config:
        return config['site_info']
    return {}


def get_site_from(fallback=''):
    """获取站点来源 (nicebox, oem, aidev)"""
    config = load_config()
    if config and config.get('site_from'):
        return config['site_from'].strip()
    return fallback


def check_config():
    """检查配置是否完整"""
    config = load_config()
    if not config:
        print('错误：配置文件不存在，请先运行：python config_manager.py --init')
        return False
    
    if not config.get('api_key'):
        print('错误：API 密钥未设置，请运行：python config_manager.py --key <密钥>')
        return False
    
    return True