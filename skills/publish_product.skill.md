---
name: publish-product
description: Publish products to your NiceBox site
metadata: {"clawdbot":{"emoji":"[PRODUCT]","requires":{"env":["AIBOX_API_KEY"]},"primaryEnv":"AIBOX_API_KEY"}}
---

# Publish Product

Publish a product to your site.

## Usage

```bash
python3 {baseDir}/scripts/publish_product.py \
  --name "Smartphone X" \
  --price 5999.99 \
  --content "High-quality smartphone with advanced features" \
  --images "https://example.com/image1.jpg" "https://example.com/image2.jpg" \
  --status publish
```

## Options

| Option | Description | Required |
|---------|-------------|-----------|
| `--name` | Product name | Yes |
| `--price` | Product price | Yes |
| `--content` | Product content | No (use `--content-file` for large/Chinese content) |
| `--content-file` | Path to file containing product content | No (mutually exclusive with `--content`) |
| `--description` | Product description | No (use `--desc-file` for Chinese content) |
| `--desc-file` | Path to file containing product description | No (mutually exclusive with `--description`) |
| `--category-id` | Product category ID | No |
| `--currency` | Currency code (default: CNY) | No |
| `--sort-order` | Sort order | No |
| `--status` | `draft` or `publish` (default: `publish`) | No |
| `--images` | Product image URLs | No |
| `--locale` | Locale (default: zh-CN) | No |
| `--filename` | Filename | No |
| `--seo-title` | SEO title | No |
| `--keywords` | Keywords | No |

## Example

```bash
# Recommended: use --content-file and --desc-file to avoid PowerShell encoding issues
python3 {baseDir}/scripts/publish_product.py \
  --name "智能手表 Pro" \
  --price 2999 \
  --content-file "product_content.html" \
  --desc-file "product_desc.txt" \
  --category-id 1 \
  --images "https://example.com/watch1.jpg" "https://example.com/watch2.jpg" \
  --status publish
```

```bash
# Alternative: inline content (may have encoding issues on Windows PowerShell)
python3 {baseDir}/scripts/publish_product.py \
  --name "Smartphone X" \
  --price 5999.99 \
  --content "High-quality smartphone" \
  --description "Advanced features" \
  --status publish
```

## Notes

- **Always use `--content-file` / `--desc-file` for Chinese content or large HTML** — avoids PowerShell command-line encoding issues
- Content/desc files should be UTF-8 encoded
- Price must be numeric
- Multiple images can be provided
- Use `--list_product_categories.py` to find category IDs
- Content should be in HTML format
