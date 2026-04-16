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

This skill provides 8 main capabilities:

* Publish article
* List article categories
* Publish product
* List product categories
* List site languages
* Generate website
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

## List article categories

List article categories from your site.

```bash
python3 {baseDir}/scripts/list_article_categories.py
python3 {baseDir}/scripts/list_article_categories.py --keyword "technology"
python3 {baseDir}/scripts/list_article_categories.py --locale "zh-CN"
```

Options:

* `--keyword`: Search keyword (optional)
* `--locale`: Locale (optional)

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
* `--locale`: Locale (optional)

## List site languages

List available languages for your site.

```bash
python3 {baseDir}/scripts/list_site_languages.py
```

No additional options required.

## Generate website

Generate or regenerate website with AI assistance through multi-turn dialogue.

### Process flow:
1. Check if site languages exist
2. If languages exist, prompt for initialization (clears existing content)
3. Initialize site if requested
4. Start multi-turn guide dialogue to collect website information (AI will ask questions about site name, industry, style, etc.)
5. Show final summary and generate website

```bash
python3 {baseDir}/scripts/generate_website.py
```

### How it works:
1. The script will start a conversation with AI
2. AI will ask questions about your website requirements
3. You can respond to each question
4. After all questions are answered, AI will generate a summary of your requirements
5. The website will be generated based on the collected information

### Tips:
- Be specific in your answers to get the best results
- You can type 'exit' at any time to quit the dialogue
- The entire process may take several minutes to complete

## AI Website Generator

This skill helps users generate websites through AI-guided dialogue.

### Available Tools
1. **guide_dialogue**

   Start or continue guided dialogue to collect website requirements.

   ```bash
   python3 {baseDir}/scripts/guide_dialogue.py \
     --message "I want a lawyer website" \
     --session-id ""
   ```

   **Options:**
   - `--message`: User input message (optional for first call)
   - `--session-id`: Session ID from previous step (empty for first call)

2. **guide_collect**

   Summarize collected website requirements.

   ```bash
   python3 {baseDir}/scripts/guide_collect.py \
     --session-id "xxx"
   ```

3. **generate_website**

   Generate website based on collected requirements.

   ```bash
   python3 {baseDir}/scripts/generate_website.py \
     --session-id "xxx"
   ```

### Workflow (VERY IMPORTANT)

When user wants to create a website:

1. ALWAYS start with `guide_dialogue`
2. Continue calling `guide_dialogue` until `is_complete = true`
3. When complete:
   - Call `guide_collect`
   - Show summary to user
   - Then automatically call `generate_website`
   - Inform user that website is being generated

### Rules
- Always keep and reuse `session_id`
- Never skip `guide_dialogue` unless user provides full structured info
- Never call `generate_website` before `guide_collect`
- Do not invent website data — always rely on collected info

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
* `GET /article/getCategories`
* `POST /product/publish`
* `GET /product/getCategories`
* `GET /site_pages/getLanguageList`
* `POST /template/initializeData`
* `POST /ai_tools/guideDialogue`
* `POST /ai_tools/guideCollect`
* `GET /ai_tools/getGuideStyleList`
* `GET /message/getlist`
* `GET /site/status`

If your actual backend uses different paths, update the `ENDPOINT_*` constants in the Python scripts.

## Notes

* All requests use the HTTP `Authorization` header.
* The API key is sent as plain header value:

  * `Authorization: YOUR_KEY`
* Output is printed as formatted JSON for easier debugging and agent use.
* If your API field names differ, update the payload fields in the scripts.
