---
name: site-status
description: Check current status of your AiWebSite site
metadata: {"clawdbot":{"emoji":"[STATUS]","requires":{"file":["scripts/config.json"]}}}
---

# Site Status

Check the current status of your AiWebSite site.

## Usage

```bash
python3 {baseDir}/scripts/site_status.py
```

## Options

No additional options required.

## Example

```bash
# Check site status
python3 {baseDir}/scripts/site_status.py
```

## Response Format

Returns comprehensive site status information:
```json
{
  "code": 0,
  "data": {
    "site_name": "My Business Site",
    "site_url": "https://mysite.example.com",
    "pages_count": 5,
    "products_count": 10,
    "articles_count": 8,
    "messages_count": 3,
    "last_updated": "2024-01-01 12:00:00",
    "status": "active"
  }
}
```

## Notes

- Returns comprehensive site information
- Includes counts for all content types
- Shows last update timestamp
- Useful for monitoring site activity
