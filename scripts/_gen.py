import urllib.request, json, sys

from config_reader import get_api_key, get_base_url

BASE = get_base_url()
API_KEY = get_api_key()

# 构建需求字符串
requirement = """公司名称：墙饰装饰
行业：墙饰装饰
业务范围：墙纸、壁画、软包、背景墙定制与安装
Logo：占位图"""

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

print('正在生成网站（SSE 流式）...')
sys.stdout.flush()

try:
    resp = urllib.request.urlopen(req, timeout=600)
    html_content = b''
    for chunk in iter(lambda: resp.read(8192), b''):
        html_content += chunk
        # 打印进度
        print(f'\r已接收: {len(html_content)} 字节', end='', flush=True)

    print(f'\n共接收: {len(html_content)} 字节')

    # 保存到文件
    with open('C:/Users/MR/.qclaw/skills/website-manager/scripts/generated.html', 'wb') as f:
        f.write(html_content)
    print('已保存到 generated.html')

except Exception as e:
    print(f'\n错误: {e}')
