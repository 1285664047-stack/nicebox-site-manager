---
name: set-key
description: View or update your AIBOX API Key (config file)
metadata: {"clawdbot":{"emoji":"[KEY]","requires":{"file":["scripts/config.json"]}}}
---

# Set API Key

View or update your API key in the configuration file.

## Usage

```bash
# View current API key
python3 {baseDir}/scripts/set-key.py

# Update API key (writes to config file, auto-fetches site info)
python3 {baseDir}/scripts/set-key.py "your_new_api_key"

# Clear/reset API key (reinitializes config file)
python3 {baseDir}/scripts/set-key.py --clear
```

## Options

| Option | Description | Required |
|---------|-------------|-----------|
| (no args) | View current API key | - |
| `api_key` | New API key to set | No |
| `--clear` | Clear/reset API key (reinitializes config) | No |

## Example

```bash
# View current key
python3 {baseDir}/scripts/set-key.py
# Output: Current API Key: 4_455_14ed****

# Set new key
python3 {baseDir}/scripts/set-key.py "4_455_14ed156fdba64c6ccdb7a0cf233ac712078382681f3cb237"
# Output:
# [OK] API 密钥已更新：4_455_14ed****
# [INFO] 正在获取站点配置信息...
# [OK] 站点配置已更新：domain=<domain_from_api>, site_from=oem
```

## How It Works

When setting a new key:
1. Writes API key to `scripts/config.json`
2. Automatically calls `/site/getFromUrl` API to fetch:
   - `domain` - The correct domain for this site
   - `site_from` - Site type (nicebox, oem, aidev)
3. Updates `base_url` and `site_from` in the config file

## Configuration File

All settings are stored in `scripts/config.json`:

```json
{
  "api_key": "your_api_key",
  "base_url": "<dynamic_from_config>",
  "site_from": "oem",
  "site_info": { ... }
}
```

> **Note**: `base_url` is dynamically set from API response when configuring a new key. Read from `scripts/config.json` at runtime.

## Manual Configuration

If automatic fetch fails, you can manually set values:

```bash
# Set API key
python3 {baseDir}/scripts/config_manager.py --key "your_api_key"

# Set base URL (domain will be different for each site)
python3 {baseDir}/scripts/config_manager.py --url "https://<your_domain>/api/openclaw"

# Set site_from (nicebox, oem, aidev)
python3 {baseDir}/scripts/config_manager.py --set site_from "oem"
```

## Notes

- The API key is sent as plain header value: `Authorization: YOUR_KEY` (no Bearer prefix)
- All scripts read API key from `scripts/config.json` only
- The config file is the single source of truth for API configuration
- No environment variables are needed
