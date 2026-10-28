---
name: list-languages
description: List available languages for your AiWebSite site
metadata: {"clawdbot":{"emoji":"[LANG]","requires":{"file":["scripts/config.json"]}}}
---

# List Site Languages

List available languages configured for your AiWebSite site.

## Usage

```bash
python3 {baseDir}/scripts/list_site_languages.py
```

## Options

No additional options required.

## Example

```bash
# List all available languages
python3 {baseDir}/scripts/list_site_languages.py
```

## Response Format

Returns a list of languages with their configuration:
```json
{
  "code": 0,
  "data": {
    "list": [
      {
        "id": 1,
        "locale": "zh-CN",
        "name": "简体中文"
      }
    ],
    "total": 1
  }
}
```

## Notes

- Returns all languages configured for your site
- Used to check if site has existing data
- Language codes follow standard locale format (e.g., `zh-CN`, `en-US`)
