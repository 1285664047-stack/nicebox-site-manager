---
name: set-key
description: Configure the Nicebox connection without exposing credentials or internal addresses
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
5. 新密钥与旧密钥不同时，自动清空旧站点的 `site_info` 和任务上下文，并重新读取绑定站点名称、域名和 `connection_id`
6. 设置成功后，下一次业务操作必须先展示新站点名称和域名并让用户确认；不得继续使用旧文章、产品、报告或任务 ID

> **警告**：如果 `base_url` 或 `site_from` 获取失败，整个设置操作将失败。

## 内部连接探测

脚本从内部配置读取候选服务并依次探测，任一个成功即停止。候选地址、认证格式和探测过程不得输出给用户。

## 示例

```bash
# 查看当前密钥
python3 {baseDir}/scripts/set-key.py
# 输出：4_455_e6****

# 设置新密钥（将强制获取 base_url 和 site_from）
python3 {baseDir}/scripts/set-key.py "4_455_e6f8a1b2c3..."
# 内部输出会验证站点配置；面向用户只回复“连接已更新”，不转述地址、来源、密钥掩码或认证细节

# 如果获取失败：
# 输出：[ERROR] API 获取站点配置失败，无法继续
#       [INFO] 请检查 API 密钥是否正确，或网络连接是否正常
```

## 隐私说明

绑定成功后不显示密钥、密钥掩码、服务地址、站点来源或认证格式。面向用户只展示新绑定站点的名称和业务域名，并等待确认。

## Notes

- 认证格式由内部脚本处理，不向用户展示
- 所有脚本统一从 `config.json` 读取配置，不依赖环境变量
- 配置文件为唯一配置来源
- **base_url 和 site_from 必须通过 API 获取，不支持手动设置**
