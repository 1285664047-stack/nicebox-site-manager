# -*- coding: utf-8 -*-
"""
设置 API 秘钥 - 写入操作系统环境变量 AIBOX_API_KEY
用法：
  python set-key.py <新密钥>        设置并持久化
  python set-key.py                查看当前密钥
"""
import os
import subprocess
import sys

def get_env(name, fallback=''):
    return os.environ.get(name, fallback)

def main():
    new_key = sys.argv[1] if len(sys.argv) > 1 else ''

    if not new_key:
        current = get_env('AIBOX_API_KEY', '')
        print(current[:8] + '****' if current else '当前：未设置')
        print('用法：python set-key.py <新密钥>')
        return

    # 写入当前进程（本次会话立即生效）
    os.environ['AIBOX_API_KEY'] = new_key

    # 持久化到用户级环境变量（重启后依然有效）
    cmd = '[Environment]::SetEnvironmentVariable(\'AIBOX_API_KEY\', \'{0}\', \'User\')'.format(new_key)
    subprocess.check_output(['powershell', '-Command', cmd])

    print('✅ 已更新为：{0}****（已持久化到系统环境变量）'.format(new_key[:8]))

if __name__ == '__main__':
    main()