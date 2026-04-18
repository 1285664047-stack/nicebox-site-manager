#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FTP配置管理和网站发布工具

功能：
1. 获取FTP配置
2. 更新FTP配置
3. 测试FTP连接
4. 发布网站

使用示例：
1. 获取FTP配置：python ftp_manager.py get-config
2. 更新FTP配置：python ftp_manager.py update-config --host ftp.example.com --port 21 --username user --password pass --path www
3. 测试FTP连接：python ftp_manager.py test-connection
4. 发布网站：python ftp_manager.py publish
"""

import argparse
import json
import requests
import os
import sys

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

# API端点
ENDPOINT_GET_CONFIG = '/api/openclaw/site_publish/getConfig'
ENDPOINT_UPDATE_CONFIG = '/api/openclaw/site_publish/updateFtpConfig'
ENDPOINT_TEST_CONNECTION = '/api/openclaw/site_publish/testFtpConnection'
ENDPOINT_PUBLISH = '/api/openclaw/site_publish/publish'
ENDPOINT_GET_TASK_STATUS = '/api/openclaw/site_publish/getTaskStatus'
ENDPOINT_CANCEL_TASK = '/api/openclaw/site_publish/cancelTask'
ENDPOINT_PREPARE_PUBLISH = '/api/openclaw/site_publish/preparePublish'


def load_config():
    """加载配置文件"""
    if not os.path.exists(CONFIG_FILE):
        print("错误：配置文件不存在，请先运行 generate_website.py 进行配置")
        sys.exit(1)
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_api_url(config, endpoint):
    """获取完整的API URL"""
    return f"{config['api_url']}{endpoint}"


def get_headers(config):
    """获取请求头"""
    return {
        'Authorization': config['api_key'],
        'Content-Type': 'application/json'
    }


def get_ftp_config():
    """获取FTP配置"""
    print("正在获取FTP配置...")
    
    config = load_config()
    url = get_api_url(config, ENDPOINT_GET_CONFIG)
    headers = get_headers(config)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get('code') == 0:
            print("\nFTP配置信息：")
            print(f"FTP主机: {result['data']['ftp_host']}")
            print(f"FTP端口: {result['data']['ftp_port']}")
            print(f"FTP用户名: {result['data']['ftp_username']}")
            # 密码脱敏显示：空字符串=未配置，******=已配置（后端脱敏返回）
            pwd = result['data'].get('ftp_password', '')
            pwd_display = '（未配置）' if (not pwd or pwd == '') else '******（已配置）'
            print(f"FTP密码: {pwd_display}")
            print(f"FTP路径: {result['data']['ftp_path']}")
            print(f"FTP模式: {'被动' if result['data']['ftp_passive'] else '主动'}")
            print(f"发布模式: {result['data']['publish_mode']}")
            print(f"站点地图URL: {result['data']['sitemap_url']}")
            return result['data']
        else:
            print(f"错误: {result.get('message', '获取配置失败')}")
            return None
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return None


def update_ftp_config(args):
    """更新FTP配置"""
    print("正在更新FTP配置...")
    
    config = load_config()
    url = get_api_url(config, ENDPOINT_UPDATE_CONFIG)
    headers = get_headers(config)
    
    # 构建更新参数
    update_data = {}
    if args.host:
        update_data['ftp_host'] = args.host
    if args.port:
        update_data['ftp_port'] = args.port
    if args.username:
        update_data['ftp_username'] = args.username
    if args.password:
        update_data['ftp_password'] = args.password
    if args.path:
        update_data['ftp_path'] = args.path
    if args.passive is not None:
        update_data['ftp_passive'] = 1 if args.passive else 0
    if args.publish_mode:
        update_data['publish_mode'] = args.publish_mode
    
    if not update_data:
        print("错误：请至少提供一个要更新的配置项")
        return False
    
    try:
        response = requests.post(url, headers=headers, json=update_data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get('code') == 0:
            print("\nFTP配置更新成功！")
            # 显示更新后的配置
            get_ftp_config()
            return True
        else:
            print(f"错误: {result.get('message', '更新配置失败')}")
            return False
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return False


def test_ftp_connection():
    """测试FTP连接"""
    print("正在测试FTP连接...")
    
    config = load_config()
    url = get_api_url(config, ENDPOINT_TEST_CONNECTION)
    headers = get_headers(config)
    
    try:
        response = requests.post(url, headers=headers, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        if result.get('code') == 0:
            print("\nFTP连接测试成功！")
            print(f"服务器信息: {result['data'].get('message', '连接正常')}")
            return True
        else:
            print(f"错误: {result.get('message', '连接测试失败')}")
            return False
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return False


def get_server_info():
    """获取FTP服务器信息"""
    print("正在获取FTP服务器信息...")
    
    config = load_config()
    url = get_api_url(config, '/api/openclaw/site_publish/getServerInfo')
    headers = get_headers(config)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get('code') == 0:
            print("\nFTP服务器信息获取成功！")
            print(f"服务器信息: {result['data'].get('message', '获取成功')}")
            if result['data'].get('server_info'):
                print("详细信息:")
                print(json.dumps(result['data']['server_info'], ensure_ascii=False, indent=2))
            return True
        else:
            print(f"错误: {result.get('message', '获取服务器信息失败')}")
            return False
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return False


def get_task_status():
    """获取发布任务状态"""
    print("正在获取发布任务状态...")
    
    config = load_config()
    url = get_api_url(config, ENDPOINT_GET_TASK_STATUS)
    headers = get_headers(config)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get('code') == 0:
            print("\n发布任务状态获取成功！")
            print(f"任务状态: {result['data'].get('status', '未知')}")
            if result['data'].get('message'):
                print(f"任务信息: {result['data']['message']}")
            return result['data']
        else:
            print(f"错误: {result.get('message', '获取任务状态失败')}")
            return None
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return None


def cancel_task():
    """取消发布任务"""
    print("正在取消发布任务...")
    
    config = load_config()
    url = get_api_url(config, ENDPOINT_CANCEL_TASK)
    headers = get_headers(config)
    
    try:
        response = requests.post(url, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get('code') == 0:
            print("\n发布任务取消成功！")
            return True
        else:
            print(f"错误: {result.get('message', '取消任务失败')}")
            return False
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return False


def prepare_publish(options):
    """准备发布（生成文件，创建任务）"""
    print("正在准备发布...")
    
    config = load_config()
    url = get_api_url(config, ENDPOINT_PREPARE_PUBLISH)
    headers = get_headers(config)
    
    data = {
        'options': options,
        'batch_number': 1
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        if result.get('code') == 0:
            print("\n发布准备成功！")
            if result.get('data'):
                print("准备结果:")
                print(json.dumps(result['data'], ensure_ascii=False, indent=2))
            return result.get('data')
        else:
            print(f"错误: {result.get('message', '准备发布失败')}")
            return None
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return None


def publish_website(args):
    """发布网站
    
    安全机制：必须传入 confirmed=True 才会执行发布，否则返回确认提示
    这确保 AI 在发布前一定会询问用户确认
    """
    # 发布前强制确认检查
    if not getattr(args, 'confirmed', False):
        print(json.dumps({
            "need_confirm": True,
            "stage": "publish",
            "message": "⚠️ 发布网站将覆盖线上版本，此操作无法撤销还原！是否确认发布？",
            "options": ["确认发布", "取消"],
            "tip": "回复「确认发布」继续发布，回复「取消」终止操作"
        }, ensure_ascii=False))
        return False
    
    print("正在发布网站...\n")
    step_num = [1]  # 用列表实现闭包可变
    def next_step(label):
        print(f"\n步骤{step_num[0]}：{label}")
        step_num[0] += 1

    # 检查FTP配置
    next_step("检查FTP配置")
    ftp_config = get_ftp_config()
    
    if not ftp_config:
        print("错误：无法获取FTP配置")
        return False
    
    # 注意：ftp_password 为 ****** 时表示后台已配置（脱敏返回）
    # 只检查 host 和 username，不检查 password（脱敏后无法判断）
    required_fields = ['ftp_host', 'ftp_username']
    missing_fields = [f for f in required_fields if not ftp_config.get(f)]
    
    if missing_fields:
        print(f"错误：缺少必要的FTP配置项：{', '.join(missing_fields)}")
        print("请先使用 update-config 命令更新FTP配置")
        return False
    
    # 测试FTP连接（改为警告而非硬阻断）
    next_step("测试FTP连接")
    ftp_ok = test_ftp_connection()
    if not ftp_ok:
        print("\n⚠️ FTP连接测试失败，但仍尝试发布（服务端可能可连接）")
    
    # 检测发布任务状态
    next_step("检测发布任务状态")
    task_status = get_task_status()
    
    # 检查是否正在发布
    if task_status and task_status.get('status') == 'running':
        print("\n检测到有正在进行的发布任务！")
        confirm = input("是否要强行终止并发布新的任务？(y/N): ").strip().lower()
        if confirm == 'y':
            next_step("终止之前的发布任务")
            if not cancel_task():
                print("错误：无法终止之前的发布任务")
                return False
        else:
            print("取消发布操作")
            return False
    
    # 准备发布
    next_step("准备发布")
    prepare_options = {
        'batch_size': args.batch_size,
        'overwrite_mode': args.overwrite_mode,
        'generate_mode': args.generate_mode,
        'batch_number': 1  # batch_number 必须放在 options 内部
    }
    
    prepare_result = prepare_publish(prepare_options)
    if not prepare_result:
        print("错误：准备发布失败")
        return False
    
    # 处理多批次
    total_batches = prepare_result.get('total_batches', 1) if prepare_result else 1
    current_batch = 1
    
    while current_batch <= total_batches:
        next_step(f"开始发布网站（批次 {current_batch}/{total_batches}）")
        config = load_config()
        url = get_api_url(config, ENDPOINT_PUBLISH)
        headers = get_headers(config)
        
        # 构建发布选项 — batch_number 必须在 options 内部，否则 PHP 后端报 "Undefined array key batch_number"
        publish_options = {
            'batch_size': args.batch_size,
            'overwrite_mode': args.overwrite_mode,
            'generate_mode': args.generate_mode,
            'batch_number': current_batch
        }
        
        # 禁用流式输出，使用普通模式
        data = {
            'options': publish_options,
            'disable_streaming': True
        }
        
        # 带重试的发布（最多3次）
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=300)
                response.raise_for_status()
                result = response.json()
                
                if result.get('code') == 0:
                    next_step("发布完成")
                    print("网站发布成功！")
                    print(f"发布结果: {result.get('message', '发布完成')}")
                    if result.get('data'):
                        stats = result['data'].get('stats', {})
                        if stats.get('files_uploaded'):
                            print(f"  上传文件: {stats['files_uploaded']} 个")
                        if stats.get('files_failed'):
                            print(f"  失败文件: {stats['files_failed']} 个")
                        if stats.get('duration'):
                            print(f"  耗时: {stats['duration']} 秒")
                    if prepare_result.get('has_more') and current_batch < total_batches:
                        current_batch += 1
                        break  # 跳出重试循环，进入下一批次
                    return True
                else:
                    # 400/401/403 业务错误不重试
                    if result.get('code') in (400, 401, 403):
                        print(f"错误: {result.get('message', '发布失败')}")
                        return False
                    # 500 类错误可重试
                    if attempt < max_retries:
                        print(f"  第 {attempt} 次尝试失败: {result.get('message', '')}，3 秒后重试...")
                        import time; time.sleep(3)
                        continue
                    print(f"错误: {result.get('message', '发布失败')}")
                    return False
            except requests.RequestException as e:
                if attempt < max_retries:
                    print(f"  第 {attempt} 次请求异常: {e}，3 秒后重试...")
                    import time; time.sleep(3)
                    continue
                print(f"请求失败: {e}")
                return False
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='FTP配置管理和网站发布工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 获取配置命令
    subparsers.add_parser('get-config', help='获取FTP配置')
    
    # 更新配置命令
    update_parser = subparsers.add_parser('update-config', help='更新FTP配置')
    update_parser.add_argument('--host', type=str, help='FTP主机地址')
    update_parser.add_argument('--port', type=int, help='FTP端口')
    update_parser.add_argument('--username', type=str, help='FTP用户名')
    update_parser.add_argument('--password', type=str, help='FTP密码')
    update_parser.add_argument('--path', type=str, help='FTP路径')
    update_parser.add_argument('--passive', action='store_true', help='启用被动模式')
    update_parser.add_argument('--active', dest='passive', action='store_false', help='启用主动模式')
    update_parser.add_argument('--publish-mode', type=str, choices=['dynamic', 'static'], help='发布模式')
    
    # 测试连接命令
    subparsers.add_parser('test-connection', help='测试FTP连接')
    
    # 获取服务器信息命令
    subparsers.add_parser('get-server-info', help='获取FTP服务器信息')
    
    # 发布网站命令
    publish_parser = subparsers.add_parser('publish', help='发布网站')
    publish_parser.add_argument('--batch-size', type=int, default=30, choices=[20, 30, 50], help='批次大小')
    publish_parser.add_argument('--overwrite-mode', type=str, default='smart', choices=['smart', 'force'], help='覆盖模式')
    publish_parser.add_argument('--generate-mode', type=str, default='default', choices=['default', 'full_static'], help='HTML生成模式')
    publish_parser.add_argument('--confirmed', action='store_true', help='已确认发布（必须用户明确确认后才能传入）')
    
    args = parser.parse_args()
    
    if args.command == 'get-config':
        get_ftp_config()
    elif args.command == 'update-config':
        update_ftp_config(args)
    elif args.command == 'test-connection':
        test_ftp_connection()
    elif args.command == 'get-server-info':
        get_server_info()
    elif args.command == 'publish':
        publish_website(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
