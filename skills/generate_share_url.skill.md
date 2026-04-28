---
name: generate-share-url
description: Generate temporary share URL for your AiWebSite website
metadata: {"clawdbot":{"emoji":"[URL]","requires":{"file":["scripts/config.json"]}}}
---

# Generate Share URL

Generate a temporary share URL for your AiWebSite website. The share URL allows others to preview your website without publishing it.

## Usage

```bash
python3 {baseDir}/scripts/generate_share_url.py
```

## Options

No additional options required.

## Example

```bash
# Generate share URL
python3 {baseDir}/scripts/generate_share_url.py
```

## Response Format

API returns a relative path that the script automatically combines with the **origin** (protocol + host) from base_url:
```json
{
  "code": 0,
  "data": {
    "site_id": 478,
    "share_url": "/api/template/preview/share/token/xxx"
  }
}
```

**Important:** The script extracts the origin from `base_url` and prepends it to the relative path. It does **NOT** use the full `base_url` (which includes `/api/openclaw`) to avoid path duplication.

The script outputs the full URL, e.g.:
```
https://<dynamic_domain>/api/template/preview/share/token/xxx
```

## Notes

- Share URL is valid for 2 hours
- No parameters needed (the API uses the site_id from the API key)
- The website must have content before generating a share URL
- If the site has no content, the script will prompt an error message
