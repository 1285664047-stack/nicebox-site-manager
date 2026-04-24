---
name: troubleshooting
description: Troubleshooting guide for NiceBox site management issues
metadata: {"clawdbot":{"emoji":"[TROUBLE]","requires":{"env":["AIBOX_API_KEY"]},"primaryEnv":"AIBOX_API_KEY"}}
---

# Troubleshooting Guide

Common issues and solutions for NiceBox site management.

## SIGKILL Problem (Fixed)

**Symptom**: Process killed during website generation, or `UnicodeEncodeError` after outputting Chinese/emoji

**Root Cause (Fixed)**:  
1. `html_content += chunk` — frequent Python realloc from SSE chunks causes memory spike → OOM
2. Emoji characters in Windows PowerShell GBK environment cause `UnicodeEncodeError`

**Solution (Applied in `_full_gen.py`)**:
1. SSE reception uses `list` accumulation + `b''.join()` to avoid memory reallocation
2. `sys.stdout.reconfigure(encoding='utf-8')` forces UTF-8 output
3. All print statements use pure ASCII, no emoji

**Usage**: Run `python3 {baseDir}/scripts/_full_gen.py` directly, no extra parameters needed.

## "公司名称/网站名称不能为空"

The `getCompanyInfo` API requires `company_name` field to be non-empty. Unfilled fields should be stored as `"未填写"`.

## Logo Field is Empty

Use a placeholder image URL:
```
https://via.placeholder.com/200x80/8B4513/FFFFFF?text=Logo
```
Color codes: `8B4513` (brown), `00A86B` (green), `1E3A8A` (blue), `D4AF37` (gold)

## SSE Streaming Error

If `generateWebsite` returns `{"type":"error","content":"参数缺失，无法创建页面"}`, this is an internal `AiEditor` error, not a parameter issue. The request only needs `requirement`. Check if the site was properly initialized first.

## FTP Interface 404: Wrong Path

FTP-related endpoints use `site_publish` path, NOT `ftp`. Full paths:
- `https://ai.nicebox.cn/api/openclaw/site_publish/getConfig`
- `https://ai.nicebox.cn/api/openclaw/site_publish/getServerInfo`
- `https://ai.nicebox.cn/api/openclaw/site_publish/updateFtpConfig`
- `https://ai.nicebox.cn/api/openclaw/site_publish/testFtpConnection`
- `https://ai.nicebox.cn/api/openclaw/site_publish/publish`

**Never guess API paths from memory.**

## Python / Node.js Selection

**Q&A Flow**: Python or Node.js both work

```bash
# Python (recommended, native UTF-8)
python3 {baseDir}/scripts/generate_website.py <command>

# Node.js (backup)
node {baseDir}/scripts/generate_website.mjs <command>
```

**Website Generation (generate)**: Use Python one-shot script

```bash
# [X] May encounter SIGKILL:
python3 {baseDir}/scripts/generate_website.py generate
node {baseDir}/scripts/generate_website.mjs generate

# [OK] Recommended:
python3 {baseDir}/scripts/_full_gen.py
```

## FTP Path Common Mistake

**FTP-related endpoints use `site_publish`, not `ftp`!**

First-time testers often use `/ftp/getConfig` etc. (guessed paths), causing 404 errors. Always check the endpoint list in the API reference skill.

**Lesson**: For any API path issues, read the endpoint list first, don't guess from memory.

## When to Use Direct API

| Problem | Solution |
|---------|----------|
| Python script SIGKILL | Use Python one-shot script (`urllib.request` handles SSE directly) |
| Node.js script SIGKILL | Same as above, Python is more stable |
| PowerShell encoding garbled | Use Python script (native UTF-8) |
| Process hangs with no output | Check network, retry with Python script |
| SSE stream interrupted | Check network, retry with Python script |

## Node.js Version Notes

- [OK] Q&A flow (ask-init / answer / summary / confirm / status / reset) works normally
- [X] `generate` and `direct-generate` commands may encounter SIGKILL on Windows
- **For generate, use Python one-shot script** (`_full_gen.py`)

## Chinese Encoding

**Python**: Native UTF-8 support, can pass Chinese parameters directly.

**Node.js**: Windows PowerShell defaults to GBK encoding. Use `--input-file` option:
```bash
node {baseDir}/scripts/generate_website.mjs answer --input-file /tmp/user_input.txt
```

**Auto-fix**: Scripts have built-in garbled text detection. If Chinese in state file is garbled, it auto-resets the state.
