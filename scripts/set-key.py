# -*- coding: utf-8 -*-
"""
设置 API 秘钥 - 写入操作系统环境变量 AIBOX_API_KEY
用法：
  python set-key.py <新密钥>        设置并持久化
  python set-key.py                查看当前密钥

修复：同时写入 Process + User 级别，确保子进程继承正确值
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

    # 1. 写入当前进程（本次会话立即生效）
    os.environ['AIBOX_API_KEY'] = new_key

    # 2. 持久化到 User 级别（重启后依然有效）
    cmd_user = "[Environment]::SetEnvironmentVariable('AIBOX_API_KEY', '{0}', 'User')".format(new_key)
    subprocess.check_output(['powershell', '-Command', cmd_user])

    # 3. 写入 Process 级别（覆盖 QClaw 传入的过期值，确保子进程读到正确值）
    cmd_process = "[Environment]::SetEnvironmentVariable('AIBOX_API_KEY', '{0}', 'Process')".format(new_key)
    subprocess.check_output(['powershell', '-Command', cmd_process])

    print('[OK] 已更新：{0}****（已写入 Process+User 级别）'.format(new_key[:8]))

if __name__ == '__main__':
    main()