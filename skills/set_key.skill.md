---
name: set-key
description: View or update your AIBOX API Key (environment variable)
metadata: {"clawdbot":{"emoji":"[KEY]","requires":{"env":[]},"primaryEnv":"AIBOX_API_KEY"}}
---

# Set API Key

View or update your AIBOX_API_KEY environment variable.

## Usage

```bash
# View current API key
python3 {baseDir}/scripts/set-key.py

# Update API key (writes to OS environment variable, immediate + persistent)
python3 {baseDir}/scripts/set-key.py "your_new_api_key"

# Node.js version (backup)
node {baseDir}/scripts/set-key.mjs
node {baseDir}/scripts/set-key.mjs "your_new_api_key"
```

## Options

| Option | Description | Required |
|---------|-------------|-----------|
| (no args) | View current API key | - |
| `api_key` | New API key to set | No |

## Example

```bash
# View current key
python3 {baseDir}/scripts/set-key.py
# Output: Current AIBOX_API_KEY: 4_455_14ed...

# Set new key
python3 {baseDir}/scripts/set-key.py "4_455_14ed156fdba64c6ccdb7a0cf236ac712078382681f3cb237"
# Output: [OK] API Key updated successfully
```

## How It Works

When setting a new key:
1. Writes to current process `process.env.AIBOX_API_KEY` (immediate effect)
2. Calls PowerShell to write user-level OS environment variable `HKCU:\Environment` (persistent, survives restart)

## Temporary Environment Variable (Alternative)

If you only want to set the key for the current terminal session:

```bash
# PowerShell (current session only, lost after close)
$env:AIBOX_API_KEY="your_api_key"

# Bash / Git Bash / WSL (current session only)
export AIBOX_API_KEY="your_api_key"
```

## Base URL (Usually No Need to Modify)

```bash
# Only set if NiceBox API address changes
$env:AIBOX_BASE_URL="https://ai.nicebox.cn/api/openclaw"
```

## Notes

- The API key is sent as plain header value: `Authorization: YOUR_KEY` (no Bearer prefix)
- If other tools (IDE, third-party scripts) need `AIBOX_API_KEY`, verify in system Environment Variables settings
- The set-key script modifies the user-level environment variable, which persists across restarts
