# -*- coding: utf-8 -*-
"""
配置文件管理 - 管理 API 密钥和站点信息
用法：
  python config_manager.py                    查看当前配置
  python config_manager.py --key <密钥>      设置 API 密钥
  python config_manager.py --url <URL>       设置 API 基础 URL
  python config_manager.py --init            初始化配置文件
"""
import os
import sys
import json
from datetime import datetime

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

# 确保同目录下的模块可以被导入
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)


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


def get_api_key(default=None):
    """获取当前 API 密钥"""
    config = load_config()
    if not config:
        return default
    return config.get('api_key', default)


def save_config(config):
    """保存配置文件"""
    try:
        config['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f'错误：无法保存配置文件 - {e}')
        return False


def init_config():
    """初始化配置文件"""
    if os.path.exists(CONFIG_FILE):
        print('配置文件已存在，如需重新初始化请先删除现有配置文件')
        return False
    
    default_config = {
        "api_key": "",
        "base_url": "",
        "site_from": "",
        "site_info": {
            "company_name": "",
            "industry": "",
            "business_scope": "",
            "logo": "",
            "advantages": "",
            "phone": "",
            "email": "",
            "address": "",
            "style": "",
            "other": ""
        },
        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "updated_at": ""
    }
    
    if save_config(default_config):
        print('[OK] 配置文件初始化成功')
        print(f'配置文件路径：{CONFIG_FILE}')
        return True
    return False


def show_config():
    """显示当前配置"""
    config = load_config()
    if not config:
        print('配置文件不存在，请先运行：python config_manager.py --init')
        return
    
    print('\n=== 当前配置 ===')
    api_key = config.get("api_key", "")
    print(f'API 密钥：{api_key[:8] + "****" if api_key else "未设置"}')
    
    # 不显示 base_url 和 site_from（根据用户之前的要求）
    # print(f'Base URL：{config.get("base_url", "未设置")}')
    # print(f'Site From：{config.get("site_from", "未设置")}')
    
    print(f'\n=== 站点信息 ===')
    print(f'创建时间：{config.get("created_at", "")}')
    print(f'更新时间：{config.get("updated_at", "")}')
    site_info = config.get('site_info', {})
    for key, value in site_info.items():
        display_value = value if value else '未填写'
        print(f'{key}: {display_value}')
    print()


def set_api_key(api_key):
    """设置 API 密钥，强制通过 API 获取 base_url 和 site_from，并验证写入结果"""
    config = load_config()
    if not config:
        print('配置文件不存在，请先运行：python config_manager.py --init')
        return False

    config['api_key'] = api_key

    # 强制通过 API 获取 base_url 和 site_from
    print('[INFO] 正在通过 API 获取站点配置信息...')
    info = None
    
    try:
        from site_info_fetcher import fetch_site_info
        info = fetch_site_info(api_key)
    except ImportError as e:
        print(f'[ERROR] 无法导入 site_info_fetcher 模块：{e}')
        print('[INFO] 请确保 site_info_fetcher.py 存在于 scripts 目录')
        return False
    except Exception as e:
        print(f'[ERROR] 调用 fetch_site_info 失败：{e}')
        return False
    
    if not info:
        print('[ERROR] API 获取站点配置失败，无法继续')
        print('[INFO] 请检查 API 密钥是否正确，或网络连接是否正常')
        return False
    
    # 更新配置
    config['base_url'] = info['base_url']
    config['site_from'] = info['site_from']
    
    # 保存配置
    if not save_config(config):
        print('[ERROR] 保存配置文件失败')
        return False
    
    # 验证写入结果
    print('[INFO] 验证配置写入结果...')
    verify_config = load_config()
    if not verify_config:
        print('[ERROR] 无法读取刚保存的配置文件')
        return False
    
    saved_base_url = verify_config.get('base_url', '')
    saved_site_from = verify_config.get('site_from', '')
    
    if not saved_base_url or not saved_site_from:
        print(f'[ERROR] 配置验证失败：缺少必要配置项')
        print('[INFO] 尝试重新获取并写入...')
        # 重试一次
        return _retry_set_api_key(api_key)
    
    print(f'[OK] API 密钥已更新：{api_key[:8]}****')
    # 不显示 base_url 和 site_from（用户要求完全禁止显示）
    print('[OK] 站点配置已验证')
    return True


def _retry_set_api_key(api_key, max_retries=2):
    """重试设置 API 密钥（内部函数）"""
    for i in range(max_retries):
        print(f'[INFO] 第 {i+1} 次重试...')
        try:
            from site_info_fetcher import fetch_site_info
            info = fetch_site_info(api_key)
            if info:
                config = load_config()
                config['api_key'] = api_key
                config['base_url'] = info['base_url']
                config['site_from'] = info['site_from']
                if save_config(config):
                    verify_config = load_config()
                    if verify_config.get('base_url') and verify_config.get('site_from'):
                        # 不显示 base_url 和 site_from（用户要求完全禁止显示）
                        print('[OK] 重试成功：站点配置已更新')
                        return True
        except Exception as e:
            print(f'[WARN] 重试失败：{e}')
    
    print('[ERROR] 所有重试均失败，请手动检查网络或 API 密钥')
    return False


def set_base_url(base_url):
    """设置 API 基础 URL"""
    config = load_config()
    if not config:
        print('配置文件不存在，请先运行：python config_manager.py --init')
        return False
    
    config['base_url'] = base_url
    if save_config(config):
        # 根据用户要求，不显示 base_url
        # print(f'[OK] API 基础 URL 已更新：{base_url}')
        print('[OK] API 基础 URL 已更新')
        return True
    return False


def set_site_from(site_from):
    """设置站点来源"""
    config = load_config()
    if not config:
        print('配置文件不存在，请先运行：python config_manager.py --init')
        return False
    
    config['site_from'] = site_from
    if save_config(config):
        # 根据用户要求，不显示 site_from
        # print(f'[OK] 站点来源已更新：{site_from}')
        print('[OK] 站点来源已更新')
        return True
    return False


def set_site_info(key, value):
    """设置站点信息（单个字段）"""
    config = load_config()
    if not config:
        print('配置文件不存在，请先运行：python config_manager.py --init')
        return False
    
    if 'site_info' not in config:
        config['site_info'] = {}
    
    config['site_info'][key] = value
    if save_config(config):
        print(f'[OK] 站点信息已更新：{key} = {value}')
        return True
    return False


def set_site_info_dict(site_info_dict):
    """批量设置站点信息（传入字典）"""
    config = load_config()
    if not config:
        print('配置文件不存在，请先运行：python config_manager.py --init')
        return False
    
    if 'site_info' not in config:
        config['site_info'] = {}
    
    # 批量更新site_info字段
    for key, value in site_info_dict.items():
        if key in config['site_info']:
            config['site_info'][key] = value
    
    if save_config(config):
        print('[OK] 站点信息已批量更新')
        return True
    return False


def get_site_info():
    """获取站点信息字典"""
    config = load_config()
    if not config:
        print('配置文件不存在，请先运行：python config_manager.py --init')
        return {}
    
    return config.get('site_info', {})


def reset_site_info():
    """重置站点信息（清空所有site_info字段）"""
    config = load_config()
    if not config:
        print('配置文件不存在，请先运行：python config_manager.py --init')
        return False
    
    # 重置site_info为默认空值
    config['site_info'] = {
        "company_name": "",
        "industry": "",
        "business_scope": "",
        "logo": "",
        "advantages": "",
        "phone": "",
        "email": "",
        "address": "",
        "style": "",
        "other": ""
    }
    
    if save_config(config):
        print('[OK] 站点信息已重置')
        return True
    return False


def clear_api_key():
    """清除 API 密钥（重置配置文件）"""
    if not os.path.exists(CONFIG_FILE):
        print('配置文件不存在，请先运行：python config_manager.py --init')
        return False
    
    # 删除现有配置文件
    try:
        os.remove(CONFIG_FILE)
    except Exception as e:
        print(f'错误：无法删除配置文件 - {e}')
        return False
    
    # 重新初始化配置文件
    return init_config()


def main():
    if len(sys.argv) == 1:
        show_config()
        return
    
    arg = sys.argv[1]
    
    if arg == '--init':
        init_config()
    elif arg == '--key':
        if len(sys.argv) < 3:
            print('错误：请提供 API 密钥')
            print('用法：python config_manager.py --key <密钥>')
            return
        set_api_key(sys.argv[2])
    elif arg == '--url':
        if len(sys.argv) < 3:
            print('错误：请提供 API 基础 URL')
            print('用法：python config_manager.py --url <URL>')
            return
        set_base_url(sys.argv[2])
    elif arg == '--set':
        if len(sys.argv) < 4:
            print('错误：请提供站点信息键值对')
            print('用法：python config_manager.py --set <键> <值>')
            print('可用键：company_name, industry, business_scope, logo, advantages, phone, email, address, style, other')
            return
        set_site_info(sys.argv[2], sys.argv[3])
    elif arg == '--clear':
        clear_api_key()
    elif arg == '--reset-site':
        reset_site_info()
    else:
        print('未知参数')
        print('可用参数：--init, --key, --url, --set, --clear, --reset-site')
        print('查看帮助：python config_manager.py')


if __name__ == '__main__':
    main()