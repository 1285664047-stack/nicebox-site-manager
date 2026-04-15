---
name: nicebox-site-manager
description: Manage AI-built websites via NiceBox OpenClaw API. Supports article publishing, viewing messages, and checking site status.
metadata: {"clawdbot":{"emoji":"🛠️","requires":{"bins":["python3"],"env":["AIBOX_API_KEY"]},"primaryEnv":"AIBOX_API_KEY"}}
---

# NiceBox Site Manager

Manage AI-built websites through the NiceBox OpenClaw API.

Base URL:

```bash
http://aidev.nicebox.cn/api/openclaw
```

Authentication:

```bash
Authorization: $AIBOX_API_KEY
```

This skill provides 5 main capabilities:

* Publish article
* Publish product
* List product categories
* View messages
* Check site status

## Publish article

Publish an article to your site.

```bash
python3 {baseDir}/scripts/publish_article.py \
  --title "Hello World" \
  --content "<p>This is article content</p>" \
  --summary "Optional summary" \
  --author "NiceBox AI" \
  --cover "https://example.com/cover.jpg" \
  --status publish
```

Options:

* `--title`: Article title (required)
* `--content`: Article content, usually HTML (required)
* `--summary`: Article summary (optional)
* `--author`: Author name (optional)
* `--cover`: Cover image URL (optional)
* `--status`: `draft` or `publish` (default: `publish`)

## Publish product

Publish a product to your site.

```bash
python3 {baseDir}/scripts/publish_product.py \
  --name "Smartphone X" \
  --price 5999.99 \
  --content "High-quality smartphone with advanced features" \
  --images "https://example.com/image1.jpg" "https://example.com/image2.jpg" \
  --status publish
```

Options:

* `--name`: Product name (required)
* `--price`: Product price (required, numeric)
* `--content`: Product content (optional)
* `--description`: Product description (optional)
* `--category-id`: Product category ID (optional, numeric)
* `--currency`: Currency code (default: CNY)
* `--sort-order`: Sort order (optional, numeric)
* `--status`: `draft` or `publish` (default: `publish`)
* `--images`: Product image URLs (optional, multiple values allowed)
* `--locale`: Locale (default: zh-CN)
* `--filename`: Filename (optional)
* `--seo-title`: SEO title (optional)
* `--keywords`: Keywords (optional)

## List product categories

List product categories from your site.

```bash
python3 {baseDir}/scripts/list_product_categories.py
python3 {baseDir}/scripts/list_product_categories.py --parent-id 1
python3 {baseDir}/scripts/list_product_categories.py --keyword "electronics"
python3 {baseDir}/scripts/list_product_categories.py --locale "zh-CN"
```

Options:

* `--keyword`: Search keyword (optional)
* `--parent-id`: Parent category ID (optional, numeric)
* `--locale`: Locale (optional)

## View messages

List messages, inquiries, or leads from your site.

```bash
python3 {baseDir}/scripts/list_messages.py
python3 {baseDir}/scripts/list_messages.py --page 1 --page-size 20
python3 {baseDir}/scripts/list_messages.py --is-read 0
```

Options:

* `--page`: Page number (default: `1`)
* `--page-size`: Number of items per page (default: `20`)
* `--is-read`: Filter by read status, `0` unread / `1` read (optional)

## Check site status

Check the current status of your site.

```bash
python3 {baseDir}/scripts/site_status.py
```

No additional options required.

## Environment

Set your API key before using this skill:

```bash
export AIBOX_API_KEY="your_api_key"
```

Optional override for base URL:

```bash
export AIBOX_BASE_URL="http://aidev.nicebox.cn/api/openclaw"
```

## Default endpoint assumptions

This skill assumes the following API paths:

* `POST /article/publish`
* `POST /product/publish`
* `GET /product/categories`
* `GET /message/getlist`
* `GET /site/status`

If your actual backend uses different paths, update the `ENDPOINT_*` constants in the Python scripts.

## Notes

* All requests use the HTTP `Authorization` header.
* The API key is sent as plain header value:

  * `Authorization: YOUR_KEY`
* Output is printed as formatted JSON for easier debugging and agent use.
* If your API field names differ, update the payload fields in the scripts.
