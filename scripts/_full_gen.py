#!/usr/bin/env python3
"""
_full_gen.py - NiceBox 网站生成一次性脚本

用法：
  方式1：命令行参数
    python _full_gen.py --company-name "公司名称" --industry "行业" --business-scope "业务范围"
  
  方式2：交互式输入
    python _full_gen.py
  
修复记录：
  2026-04-24: 修复 SIGKILL 问题
    - SSE 接收改用 list 累积 + b''.join()，避免内存重分配
    - sys.stdout.reconfigure(encoding='utf-8') 避免 GBK 编码崩溃
    - 所有输出改为纯 ASCII，无 emoji
  2026-04-24: 添加命令行参数和交互式输入支持
    - 支持从命令行参数获取公司信息
    - 支持交互式输入收集信息
"""

import urllib.request, urllib.error, urllib.parse, json, os, sys, time, pathlib, argparse

# Windows PowerShell 默认 GBK 编码，强制 UTF-8 输出，避免 UnicodeEncodeError
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass  # 非 Windows 环境忽略

BASE = 'https://ai.nicebox.cn/api/openclaw'
API_KEY = os.environ.get('AIBOX_API_KEY', '')


def call_api(endpoint, data=None, headers_extra=None):
    """调用 API 并返回 JSON 结果"""
    url = BASE + endpoint
    headers = {
        'Authorization': API_KEY,
        'Content-Type': 'application/json; charset=utf-8'
    }
    if headers_extra:
        headers.update(headers_extra)

    body = None
    if data:
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')

    req = urllib.request.Request(
        url, data=body, headers=headers,
        method='POST' if data else 'GET'
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {'code': e.code, 'error': e.read().decode('utf-8', errors='replace')}
    except Exception as e:
        return {'code': -1, 'error': str(e)}


def get_user_input():
    """交互式获取用户输入"""
    questions = [
        ('company_name', '公司名称（必填）', '例如：明德律师事务所', True),
        ('industry', '行业', '例如：科技、医疗、教育', False),
        ('business_scope', '业务范围', '例如：软件开发与定制', False),
        ('advantages', '核心优势', '例如：技术领先、价格合理', False),
        ('phone', '联系电话', '例如：400-888-8888', False),
        ('email', '联系邮箱', '例如：contact@example.com', False),
        ('address', '公司地址', '例如：北京市朝阳区', False),
        ('style', '视觉风格', '例如：简约现代风', False),
        ('other', '其他补充', '没有可留空', False),
    ]
    
    company_data = {}
    
    print('\n请输入公司信息：')
    print('=' * 50)
    
    for field, question, example, required in questions:
        if required:
            while True:
                value = input(f'{question}: ').strip()
                if value:
                    company_data[field] = value
                    break
                else:
                    print('  [WARN] 此项为必填，请输入')
        else:
            value = input(f'{question}（{example}）: ').strip()
            company_data[field] = value if value else '未填写'
    
    # Logo 默认占位图
    if not company_data.get('logo') or company_data.get('logo') == '未填写':
        name = company_data.get('company_name', 'Logo')
        company_data['logo'] = f'https://via.placeholder.com/200x80/8B4513/FFFFFF?text={urllib.parse.quote(name[:6])}'
    else:
        company_data.setdefault('logo', '未填写')
    
    print('=' * 50)
    print('\n[OK] 信息收集完成')
    
    return company_data


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='NiceBox 网站生成一次性脚本')
    parser.add_argument('--company-name', dest='company_name', help='公司名称（必填）')
    parser.add_argument('--industry', help='行业')
    parser.add_argument('--business-scope', dest='business_scope', help='业务范围')
    parser.add_argument('--advantages', help='核心优势')
    parser.add_argument('--logo', help='Logo 地址')
    parser.add_argument('--phone', help='联系电话')
    parser.add_argument('--email', help='联系邮箱')
    parser.add_argument('--address', help='公司地址')
    parser.add_argument('--style', help='视觉风格')
    parser.add_argument('--other', help='其他补充')
    
    args = parser.parse_args()
    
    if not API_KEY:
        print('[ERROR] AIBOX_API_KEY env not set')
        print('  Set: $env:AIBOX_API_KEY="your_key"')
        sys.exit(2)
    
    # 获取公司信息（命令行参数优先，否则交互式输入）
    if args.company_name:
        # 使用命令行参数
        company_data = {
            'company_name': args.company_name,
            'industry': args.industry or '未填写',
            'business_scope': args.business_scope or '未填写',
            'advantages': args.advantages or '未填写',
            'phone': args.phone or '未填写',
            'email': args.email or '未填写',
            'address': args.address or '未填写',
            'style': args.style or '未填写',
            'other': args.other or '未填写',
        }
        
        # 处理 Logo
        if args.logo:
            company_data['logo'] = args.logo
        else:
            name = company_data.get('company_name', 'Logo')
            company_data['logo'] = f'https://via.placeholder.com/200x80/8B4513/FFFFFF?text={urllib.parse.quote(name[:6])}'
        
        print('\n[OK] 使用命令行参数')
    else:
        # 交互式输入
        company_data = get_user_input()

    # Step 1: Init site
    print('Step 1: Initializing site...')
    result = call_api('/template/initializeData', {})
    print(f'  code={result.get("code")} msg={result.get("message","")}')
    if result.get('code') != 0:
        print('  [WARN] Init returned non-zero, continuing...')
    time.sleep(1)

    # Step 2: Register company info
    print('Step 2: Registering company info...')
    result = call_api('/ai_tools/getCompanyInfo', company_data)
    print(f'  code={result.get("code")} msg={result.get("message","")}')
    if result.get('code') != 0:
        print('  [ERROR] Registration failed, check company_name')
        sys.exit(1)
    time.sleep(1)

    # Step 3: Generate website (SSE streaming)
    print('Step 3: Generating website (SSE streaming)...')
    sys.stdout.flush()

    # Build requirement
    parts = []
    field_labels = {
        'company_name': '公司名称',
        'industry': '行业',
        'business_scope': '业务范围',
        'advantages': '核心优势',
        'style': '视觉风格',
    }
    for k, v in company_data.items():
        if v and v != '未填写':
            parts.append(f'{field_labels.get(k, k)}：{v}')
    requirement = f'请为"{company_data["company_name"]}"创建网站。\n' + '\n'.join(parts)

    body = json.dumps({'requirement': requirement}, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(
        BASE + '/ai_tools/generateWebsite',
        data=body,
        headers={
            'Authorization': API_KEY,
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'text/event-stream'
        },
        method='POST'
    )

    # Key fix: use list accumulation + join instead of html_content += chunk
    # This avoids repeated memory reallocations that trigger OOM/SIGKILL on Windows
    chunks = []
    total_bytes = 0
    report_every = 50   # report every 50 chunks (~400KB)
    chunk_count = 0
    last_section = ""
    section_count = 0
    html_content = b''  # 初始化 html_content 避免未定义错误

    try:
        resp = urllib.request.urlopen(req, timeout=600)
        for chunk in iter(lambda: resp.read(8192), b''):
            chunks.append(chunk)
            total_bytes += len(chunk)
            chunk_count += 1
            
            # Parse SSE events from buffer
            buffer = b''.join(chunks[-10:])  # Check last 10 chunks for events
            try:
                buffer_str = buffer.decode('utf-8', errors='replace')
                for line in buffer_str.split('\n'):
                    line = line.strip()
                    if line.startswith('data:'):
                        try:
                            event = json.loads(line[5:])
                            etype = event.get('type', '')
                            
                            if etype == 'progress':
                                pct = event.get('percentage')
                                msg = event.get('message', '')
                                if pct is not None:
                                    print(f'\r[PROGRESS] 进度: {pct}%    ', end='', flush=True)
                                elif msg:
                                    print(f'\r[PROGRESS] {msg}    ', end='', flush=True)
                            
                            elif etype == 'section_generating':
                                section_count += 1
                                sec = event.get('section', f'区块{section_count}')
                                last_section = sec
                                print(f'\n[GENERATING] 正在生成: {sec}（{section_count}）')
                            
                            elif etype == 'section_complete':
                                sec = event.get('section', last_section)
                                print(f'\n  [DONE] {sec} 完成')
                            
                            elif etype == 'complete':
                                print(f'\n[COMPLETE] 网站生成完成！共接收 {total_bytes} 字符')
                            
                            elif etype == 'error':
                                print(f'\n[ERROR] 错误: {event.get("content", "")}')
                        except json.JSONDecodeError:
                            pass
            except UnicodeDecodeError:
                pass
            
            if chunk_count % report_every == 0:
                print(f'\r[RECEIVED] 已接收 {total_bytes} 字节', end='', flush=True)
        
        html_content = b''.join(chunks)
        del chunks
        print(f'\n[COMPLETE] 网站生成完成！共接收 {total_bytes} 字节')
    except Exception as e:
        print(f'  [ERROR] SSE stream failed: {e}')
        sys.exit(1)

    # Save raw SSE response (for debugging) - 只替换 HTML 代码内容，保留其他内容
    script_dir = pathlib.Path(__file__).parent
    output_file = script_dir / 'generated.html'
    
    # 处理内容，只替换 HTML 代码
    content_str = html_content.decode('utf-8', errors='replace')
    processed_lines = []
    
    for line in content_str.split('\n'):
        # 检查是否包含 HTML 代码
        if '"content":"<!DOCTYPE html>' in line or '"content":"<html' in line:
            # 替换 HTML 内容为固定文本
            if '"type":"progressive_content"' in line:
                processed_lines.append(line.replace(line.split('"content":"')[1].split('"')[0], 'html输出'))
            elif '"type":"complete_content"' in line:
                # 处理 complete_content 的嵌套结构
                if '"content":{' in line:
                    # 保留外层结构，只替换内层 content
                    parts = line.split('"content":{"content":"')
                    if len(parts) == 2:
                        html_part = parts[1].split('"')[0]
                        processed_lines.append(parts[0] + '"content":{"content":"html输出"' + line.split('"content":"' + html_part + '"')[1])
                    else:
                        processed_lines.append(line)
                else:
                    processed_lines.append(line)
            elif '"content":"' in line:
                # 其他包含 HTML 的 content
                parts = line.split('"content":"')
                if len(parts) == 2:
                    html_part = parts[1].split('"')[0]
                    if html_part.startswith('<!DOCTYPE html>') or html_part.startswith('<html'):
                        processed_lines.append(parts[0] + '"content":"html输出"' + line.split('"content":"' + html_part + '"')[1])
                    else:
                        processed_lines.append(line)
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append(line)
        else:
            # 保留非 HTML 内容
            processed_lines.append(line)
    
    # 保存处理后的内容
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(processed_lines))
    print(f'  Saved to: {output_file}')

    # Check for errors in response
    content_str = html_content.decode('utf-8', errors='replace')
    if '"type":"error"' in content_str or 'code":500' in content_str:
        print('  [WARN] Response contains errors:')
        for line in content_str.split('\n'):
            if 'error' in line.lower():
                print(f'    {line[:300]}')
    else:
        print('  [OK] SSE stream received successfully')

    time.sleep(2)

    # Step 4: Verify
    print('\nStep 4: Verifying website...')
    result = call_api('/site_pages/readIndexHtml', None, {'Accept': 'application/json'})
    status = result.get('data', {}).get('status')
    print(f'  code={result.get("code")} status={status}')

    if result.get('code') == 0 and status == True:
        print('  [OK] Index HTML verified - website generated successfully')
    else:
        print('  [FAIL] Index HTML not found - generation may have failed')

    # Step 5: Get share URL
    print('\nStep 5: Getting share URL...')
    result = call_api('/site/generateShareUrl', None)
    if result.get('code') == 0 and result.get('data', {}).get('share_url'):
        share_url = result['data']['share_url']
        print(f'  [OK] Share URL (expires in 2h):\n     {share_url}')
    else:
        print(f'  [WARN] Failed to get share URL: {result.get("message","")}')

    print('\n[DONE]')


if __name__ == '__main__':
    main()
