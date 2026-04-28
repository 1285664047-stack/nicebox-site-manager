import urllib.request, json, sys, time as time_module
sys.stdout.reconfigure(encoding='utf-8')
API_KEY = '456_478_b2130323e69bcac2cbb31ddfa2e80867a96fdd81fc34d6e8'
BASE = 'https://ai.qidc.cn/api/openclaw'

print('Step 1: initializeData...')
req_init = urllib.request.Request(BASE+'/template/initializeData',
    data=b'{}', headers={'Authorization':API_KEY,'Content-Type':'application/json'}, method='POST')
with urllib.request.urlopen(req_init, timeout=60) as resp:
    result = json.loads(resp.read())
print(f'init result: code={result.get("code")}')

time_module.sleep(1)

print('Step 2: generateWebsite (direct requirement string, no site_id)...')
req_str = '请为青稞旅行社创建一个旅游服务网站。公司名称：青稞旅行社，行业：旅游，业务范围：组团旅游、门票购买。视觉风格：现代简约，活力创意风，青绿色调。'
body = json.dumps({'requirement': req_str}, ensure_ascii=False).encode('utf-8')
req = urllib.request.Request(BASE+'/ai_tools/generateWebsite', data=body,
    headers={'Authorization':API_KEY,'Content-Type':'application/json','Accept':'text/event-stream'}, method='POST')

section_idx = 0
section_names = ['Header','Hero','Services','About','Team','Contact','Footer','Products','News','FAQ']
html_content = ''
last_save = time_module.time()
complete = False
error_found = False

try:
    with urllib.request.urlopen(req, timeout=600) as resp:
        for line in resp:
            d = line.decode('utf-8', errors='replace')
            if d.startswith('data:'):
                try:
                    ev = json.loads(d[5:].strip())
                    etype = ev.get('type','')
                    if etype == 'section_generating':
                        section_idx += 1
                        name = ev.get('content','') or (section_names[section_idx-1] if section_idx<=len(section_names) else f'区块{section_idx}')
                        print(f'正在生成: {name}...')
                    elif etype == 'section_complete':
                        name = ev.get('content','')
                        print(f'  [OK] {name} 完成')
                    elif etype == 'progressive_content':
                        c = ev.get('content','')
                        if c:
                            html_content += c
                            now = time_module.time()
                            if now - last_save > 30 and html_content:
                                with open('website_draft.html','w',encoding='utf-8') as f:
                                    f.write(html_content)
                                print(f'  [SAVE] 断点保存 {len(html_content)} 字符')
                                last_save = now
                    elif etype == 'complete':
                        print('[COMPLETE] 网站生成完成!')
                        complete = True
                        break
                    elif etype == 'error':
                        err_msg = ev.get('content','') or ev.get('message','')
                        print(f'[ERROR] 错误: {err_msg}')
                        error_found = True
                except json.JSONDecodeError:
                    pass
    if html_content:
        with open('website_final.html','w',encoding='utf-8') as f:
            f.write(html_content)
        print(f'HTML已保存: {len(html_content)} 字符')
except Exception as e:
    print(f'Error: {e}')

# Step 3: verify
print('验证生成结果...')
req3 = urllib.request.Request(BASE+'/site_pages/readIndexHtml',
    headers={'Authorization':API_KEY,'Content-Type':'application/json'}, method='GET')
try:
    with urllib.request.urlopen(req3, timeout=30) as resp:
        r = json.loads(resp.read())
    print(f'readIndexHtml: {r}')
    if r.get('data',{}).get('status'):
        print('[OK] 网站生成成功!')
    else:
        print('[WARN] 网站生成失败，请重试')
except Exception as e:
    print(f'readIndexHtml error: {e}')