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
| `--content` | Product content | No |
| `--description` | Product description | No |
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
# Publish a product
python3 {baseDir}/scripts/publish_product.py \
  --name "智能手表 Pro" \
  --price 2999 \
  --content "<p>智能手表 Pro，支持心率监测、GPS定位等功能</p>" \
  --description "高端智能手表，功能全面" \
  --category-id 1 \
  --images "https://example.com/watch1.jpg" "https://example.com/watch2.jpg" \
  --status publish
```

## Notes

- Price must be numeric
- Multiple images can be provided
- Use `--list_product_categories.py` to find category IDs
- Content should be in HTML format
