---
name: ftp-publish
description: Test FTP connection and publish your NiceBox website to FTP server
metadata: {"clawdbot":{"emoji":"[FTP]","requires":{"env":["AIBOX_API_KEY"]},"primaryEnv":"AIBOX_API_KEY"}}
---

# FTP Publish

Test FTP connection and publish your website to FTP server with pre-checks.

## [WARN] 【强制】发布确认机制（三重保障）

**AI 在发布网站时，必须严格遵守以下 3 条规则，不得违反：**

1. **客户主动要求发布时**：必须先询问确认，提示"发布后无法还原"，用户明确确认后才执行
2. **生成网站后**：不得自动发布，必须询问客户是否需要发布，提示"发布后无法还原"
3. **即使客户要求"生成后自动发布"**：生成完成后仍需再次询问确认，不得跳过

**确认提示文案（统一使用）：**

> [WARN] 发布网站将覆盖线上版本，此操作无法撤销还原！确认发布请回复「确认发布」。

## Usage

```bash
# Get FTP configuration
python3 {baseDir}/scripts/ftp_manager.py get-config

# Test FTP connection
python3 {baseDir}/scripts/ftp_manager.py test-connection

# Get FTP server info
python3 {baseDir}/scripts/ftp_manager.py get-server-info

# Get publish task status
python3 {baseDir}/scripts/ftp_manager.py get-task-status

# Cancel publish task
python3 {baseDir}/scripts/ftp_manager.py cancel-task

# Publish website
python3 {baseDir}/scripts/ftp_manager.py publish
```

## Publish Options

| Option | Description | Default |
|---------|-------------|---------|
| `--batch-size` | Number of files per batch | 50 |
| `--overwrite-mode` | Overwrite mode | `all` |
| `--generate-mode` | Generate mode | `all` |

## Example

```bash
# Step 1: Get FTP configuration
python3 {baseDir}/scripts/ftp_manager.py get-config

# Step 2: Test FTP connection
python3 {baseDir}/scripts/ftp_manager.py test-connection

# Step 3: Publish website
python3 {baseDir}/scripts/ftp_manager.py publish

# Publish with custom options
python3 {baseDir}/scripts/ftp_manager.py publish --batch-size 100 --overwrite-mode all

# Check publish task status
python3 {baseDir}/scripts/ftp_manager.py get-task-status

# Cancel publish task
python3 {baseDir}/scripts/ftp_manager.py cancel-task
```

## Node.js Version

```bash
node {baseDir}/scripts/ftp_manager.mjs get-config
node {baseDir}/scripts/ftp_manager.mjs test-connection
node {baseDir}/scripts/ftp_manager.mjs publish
```

## Notes

- Always test FTP connection before publishing
- Publishing overwrites the online version
- Supports multi-batch publishing for large sites
- Use `get-task-status` to monitor publish progress
- Use `cancel-task` to cancel an ongoing publish
