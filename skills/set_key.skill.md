---
name: set-key
description: View or update your AIBOX API Key (config file)
metadata: {"clawdbot":{"emoji":"[KEY]","requires":{"file":["scripts/config.json"]}}}
---

# Set API Key

View or update your API key in the configuration file.

## Usage

```bash
# 查看当前 API 密钥
python3 {baseDir}/scripts/set-key.py

# 更新 API 密钥（**强制**通过 API 获取 base_url 和 site_from）
python3 {baseDir}/scripts/set-key.py "your_new_api_key"

# 清除/重置 API 密钥
python3 {baseDir}/scripts/set-key.py --clear
```

## 强制行为

设置密钥时，脚本会**强制**执行以下操作：
1. 将密钥写入 `scripts/config.json`
2. **必须**通过 API 获取 `base_url` 和 `site_from`（最多重试 3 次）
3. 验证写入结果，确保两个字段都有值
4. 如果获取失败，返回错误，**不会写入不完整的配置**

> **警告**：如果 `base_url` 或 `site_from` 获取失败，整个设置操作将失败。

## 备用 URL 列表

脚本会依次尝试以下 URL（任一个成功即停止）：
- `http://aidev.nicebox.cn/api/openclaw`
- `https://ai.nicebox.cn/api/openclaw`
- `https://ai.qidc.cn/api/openclaw`

## 示例

```bash
# 查看当前密钥
python3 {baseDir}/scripts/set-key.py
# 输出：4_455_e6****

# 设置新密钥（将强制获取 base_url 和 site_from）
python3 {baseDir}/scripts/set-key.py "4_455_e6f8a1b2c3..."
# 输出：[INFO] 正在通过 API 获取站点配置信息...
#       [OK] 站点配置获取成功：base_url=http://aidev.nicebox.cn/api/openclaw, site_from=aidev
#       [OK] API 密钥已更新：4_455_e6f8****
#       [OK] 站点配置已验证：base_url=http://aidev.nicebox.cn/api/openclaw, site_from=aidev

# 如果获取失败：
# 输出：[ERROR] API 获取站点配置失败，无法继续
#       [INFO] 请检查 API 密钥是否正确，或网络连接是否正常
```

## 隐私说明

绑定成功后仅显示密钥掩码（首位+末位+****），不显示 base_url 和 site_from。
客户可通过直接查看 `config.json` 文件或 NiceBox 后台查询。

## Notes

- API 密钥格式：`Authorization: YOUR_KEY`（无 Bearer 前缀）
- 所有脚本统一从 `config.json` 读取配置，不依赖环境变量
- 配置文件为唯一配置来源
- **base_url 和 site_from 必须通过 API 获取，不支持手动设置**
