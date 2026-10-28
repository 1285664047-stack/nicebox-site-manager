---
name: manage-categories
description: List and create article and product categories on your AiWebSite site
metadata: {"clawdbot":{"emoji":"[CATEG]","requires":{"file":["scripts/config.json"]}}}
---

# Manage Categories

List article categories or product categories from your site.

Create article or product categories through MCP first, or through the REST fallback when MCP is unavailable.

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

# Create a top-level article category through REST fallback
python3 {baseDir}/scripts/create_category.py article --name "公司新闻" --locale "zh-CN"

# Create a child product category through REST fallback
python3 {baseDir}/scripts/create_category.py product --name "智能设备" --parent-id 12 --sort-order 10 --locale "zh-CN"
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
- Before creating, list or search categories of the same type and locale to avoid duplicates.
- `parent_id=0` creates a top-level category. A nonzero parent must exist and belong to the current account.
- MCP tools are `nicebox_create_article_category` and `nicebox_create_product_category`.
- REST endpoints are `POST /article/createCategory` and `POST /product/createCategory`.
- After creation, query the category list again and use the returned real category ID for article/product drafts.
