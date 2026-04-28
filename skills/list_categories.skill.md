---
name: list-categories
description: List article and product categories from your AiWebSite site
metadata: {"clawdbot":{"emoji":"[CATEG]","requires":{"file":["scripts/config.json"]}}}
---

# List Categories

List article categories or product categories from your site.

## Usage

```bash
# List article categories
python3 {baseDir}/scripts/list_article_categories.py

# Search article categories by keyword
python3 {baseDir}/scripts/list_article_categories.py --keyword "technology"

# Filter article categories by locale
python3 {baseDir}/scripts/list_article_categories.py --locale "zh-CN"

# List product categories
python3 {baseDir}/scripts/list_product_categories.py

# Search product categories by keyword
python3 {baseDir}/scripts/list_product_categories.py --keyword "electronics"
```

## Options for Article Categories

| Option | Description | Required |
|---------|-------------|-----------|
| `--keyword` | Search keyword | No |
| `--locale` | Locale (e.g., `zh-CN`) | No |

## Options for Product Categories

| Option | Description | Required |
|---------|-------------|-----------|
| `--keyword` | Search keyword | No |
| `--locale` | Locale (e.g., `zh-CN`) | No |
| `--parent-id` | Filter by parent category ID | No |

## Examples

```bash
# List all article categories
python3 {baseDir}/scripts/list_article_categories.py

# Search for article categories containing "technology"
python3 {baseDir}/scripts/list_article_categories.py --keyword "technology"

# List all product categories
python3 {baseDir}/scripts/list_product_categories.py

# Search for product categories containing "electronics"
python3 {baseDir}/scripts/list_product_categories.py --keyword "electronics"
```

## Notes

- Returns category ID, name, and other metadata
- Use category ID when publishing articles or products
- Supports pagination through `--page` option
