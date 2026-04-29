# -*- coding: utf-8 -*-
"""
站点信息获取模块 - 通过 API 获取 base_url 和 site_from
由 config_manager 和 set-key.py 共用，避免循环导入
"""
import urllib.request
import urllib.error
import json
import time

# 备用 URL 列表（按优先级）
FALLBACK_BASE_URLS = [
    'http://aidev.nicebox.cn/api/openclaw',
    'https://ai.nicebox.cn/api/openclaw',
    'https://ai.qidc.cn/api/openclaw',
]


def fetch_site_info(api_key, max_retries=3, timeout=15):
    """
    通过 API 读取 base_url 和 site_from。
    遍历多个备用 URL，只要有一个成功就停止。
    失败会自动重试（最多 max_retries 次）。
    返回 dict: {'base_url': ..., 'site_from': ...}，失败返回 None
    """
    last_error = None
    
    for attempt in range(max_retries):
        if attempt > 0:
            print(f'[INFO] 第 {attempt+1} 次尝试获取站点配置...')
            time.sleep(2 * attempt)  # 指数退避
        
        for base_url in FALLBACK_BASE_URLS:
            endpoint = '/site/getFromUrl'
            url = f"{base_url.rstrip('/')}{endpoint}"
            req = urllib.request.Request(
                url=url,
                method='GET',
                headers={
                    'Authorization': api_key.strip(),
                    'Accept': 'application/json',
                    'User-Agent': 'qidc-openclaw-skill/1.0',
                }
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw = resp.read().decode('utf-8', errors='replace')
                    data = json.loads(raw)
                    if data.get('code') == 0 and data.get('data'):
                        d = data['data']
                        domain = d.get('domain', '')
                        site_from = d.get('site_from', '')
                        if domain:
                            result = {
                                'base_url': f"{domain}/api/openclaw",
                                'site_from': site_from,
                            }
                            # 不显示 base_url 和 site_from（用户要求完全禁止显示）
                            return result
                        else:
                            last_error = f'API 返回数据缺少 domain 字段：{data}'
                    else:
                        last_error = f'API 返回错误：code={data.get("code")}, msg={data.get("msg")}'
            except Exception as e:
                last_error = str(e)
                continue
        
        # 所有 URL 都失败了，等待后重试
        if attempt < max_retries - 1:
            print(f'[WARN] 第 {attempt+1} 次尝试失败：{last_error}')
    
    print(f'[ERROR] 所有尝试均失败（{max_retries} 次），最后错误：{last_error}')
    return None