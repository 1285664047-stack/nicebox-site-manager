---
name: publish-article
description: Publish articles to your NiceBox site
metadata: {"clawdbot":{"emoji":"[ARTICLE]","requires":{"env":["AIBOX_API_KEY"]},"primaryEnv":"AIBOX_API_KEY"}}
---

# Publish Article

Publish an article to your site.

## Usage

```bash
python3 {baseDir}/scripts/publish_article.py \
  --title "Hello World" \
  --content "<p>This is article content</p>" \
  --summary "Optional summary" \
  --author "NiceBox AI" \
  --cover "https://example.com/cover.jpg" \
  --status publish
```

## Options

| Option | Description | Required |
|---------|-------------|-----------|
| `--title` | Article title | Yes |
| `--content` | Article content, usually HTML | Yes |
| `--summary` | Article summary | No |
| `--author` | Author name | No |
| `--cover` | Cover image URL | No |
| `--status` | `draft` or `publish` (default: `publish`) | No |

## Example

```bash
# Publish an article
python3 {baseDir}/scripts/publish_article.py \
  --title "如何使用 NiceBox" \
  --content "<p>NiceBox 是一个强大的网站生成工具...</p>" \
  --summary "NiceBox 使用指南" \
  --author "技术团队" \
  --cover "https://example.com/nicebox.jpg" \
  --status publish
```

## Notes

- Content should be in HTML format
- Use `--status draft` to save as draft
- All special characters in content must be properly encoded
