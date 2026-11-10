---
name: manage-categories
description: List, search, create, update and delete article, product and FAQ management categories
metadata: {"clawdbot":{"emoji":"[CATEG]","requires":{"file":["scripts/config.json"]}}}
---

# Manage Categories

List, create, update or delete article, product or standalone FAQ management categories.

FAQ category viewing and searching use `nicebox_list_faq_categories` and `nicebox_search_faq_categories`. FAQ category creation uses `nicebox_create_faq_category`; it creates a category for the FAQ management page, not an article/product category.

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
- MCP tools include `nicebox_create_article_category`, `nicebox_create_product_category`, `nicebox_list_faq_categories`, `nicebox_search_faq_categories` and `nicebox_create_faq_category`.
- REST endpoints are `POST /article/createCategory` and `POST /product/createCategory`.
- After creation, query the category list again and use the returned real category ID for article/product drafts.
- FAQ 分类可按编号精确搜索或按名称模糊搜索。创建子分类前使用真实父分类编号，父子语言必须一致；同级同语言不能重名。

## 修改分类

1. 先按真实编号定位分类；名称搜索有多条时让用户选择，不自动选择。
2. 修改前调用对应 `nicebox_get_*_category_impact`，展示名称、父级、语言、排序、显示状态、直接子分类数量、全部后代数量、直接关联内容数量和整棵分支内容数量。
3. 只允许局部修改 `name`、`parent_id`、`locale`、`sort_order`、`status`；未明确修改的字段保持原值。
4. 修改父级时说明当前分类和全部后代的路径、层级都会更新；关联内容仍归属原分类。父级不能是自己、自己的后代、其他账号分类或不同语言分类。
5. 修改语言会同步修改关联内容语言。存在后代分类时只提供“整棵分支一起修改语言 / 取消”，用户确认整棵分支后传 `locale_scope=branch`。
6. 修改排序或显示状态不改变分类树和内容状态；隐藏分类不等于隐藏分类下的内容。
7. 展示当前值、目标值和影响后取得确认，原样传回 `expected_impact_hash`。数据已变化时重新分析并确认。

## 删除分类

1. 删除前必须调用对应影响分析工具并展示后代数量和关联内容数量。
2. 删除分类不会删除 FAQ、产品或文章；关联内容会改为无分类。分类删除后无法恢复，必须明确提示。
3. 无后代分类时使用 `delete_scope=single`；存在后代时不能只删父分类，提供“删除整棵分类分支 / 取消”。只有用户明确选择整棵分支后才使用 `delete_scope=branch`。
4. 服务端根据最新树计算完整后代集合；不得由对话自行猜测或遗漏分类 ID。
5. 确认后原样传回 `expected_impact_hash`。分类树或关联内容变化时停止并重新确认。
6. 成功后展示实际删除分类数和变为无分类的内容数。
