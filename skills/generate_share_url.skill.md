---
name: generate-share-url
description: Generate temporary share URL for your NiceBox website
metadata: {"clawdbot":{"emoji":"[URL]","requires":{"env":["AIBOX_API_KEY"]},"primaryEnv":"AIBOX_API_KEY"}}
---

# Generate Share URL

Generate a temporary share URL for your NiceBox website. The share URL allows others to preview your website without publishing it.

## Usage

```bash
# Python version
python3 {baseDir}/scripts/generate_share_url.py

# Node.js version
node {baseDir}/scripts/generate_share_url.mjs
```

## Options

No additional options required.

## Example

```bash
# Generate share URL
python3 {baseDir}/scripts/generate_share_url.py

# Generate share URL using Node.js
node {baseDir}/scripts/generate_share_url.mjs
```

## Response Format

Returns the share URL:
```json
{
  "code": 0,
  "data": {
    "share_url": "https://ai.nicebox.cn/share/abc123",
    "expires_in": 7200
  }
}
```

## Notes

- Share URL is valid for 2 hours (7200 seconds)
- The website must have content before generating a share URL
- If the site has no content, the script will prompt an error message
- Use `readIndexHtml` API to verify site has content before generating share URL
- Share URL is automatically generated after successful website generation
