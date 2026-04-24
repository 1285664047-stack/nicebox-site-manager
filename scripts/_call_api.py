import urllib.request, json, os

BASE = 'https://ai.nicebox.cn/api/openclaw'
API_KEY = os.environ.get('AIBOX_API_KEY', '456_478_b2130323e69bcac2cbb31ddfa2e80867a96fdd81fc34d6e8')

data = {
    'company_name': '墙饰装饰',
    'industry': '墙饰装饰',
    'business_scope': '墙纸、壁画、软包、背景墙定制与安装',
    'logo': 'https://via.placeholder.com/200x80/8B4513/FFFFFF?text=QSZS',
    'advantages': '未填写',
    'phone': '未填写',
    'email': '未填写',
    'address': '未填写',
    'style': '未填写',
    'other': '未填写'
}

body = json.dumps(data, ensure_ascii=False).encode('utf-8')
req = urllib.request.Request(
    BASE + '/ai_tools/getCompanyInfo',
    data=body,
    headers={
        'Authorization': API_KEY,
        'Content-Type': 'application/json; charset=utf-8'
    },
    method='POST'
)

try:
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read().decode('utf-8'))
    print(json.dumps(result, ensure_ascii=False, indent=2))
except urllib.error.HTTPError as e:
    error_body = e.read().decode('utf-8', errors='replace')
    print(f'HTTP {e.code}: {error_body}')
