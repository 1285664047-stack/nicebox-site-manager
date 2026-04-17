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

Generate or regenerate a website through AI-guided multi-turn dialogue.
**All answers are manually entered by the customer** - AI only asks questions, never auto-answers.

### Process flow:
1. Check if site languages exist
2. If languages exist, prompt user whether to initialize the site (clears existing pages, products, articles, messages)
3. Initialize site if requested
4. Start multi-turn dialogue - AI asks questions, customer manually answers one by one
5. Generate summary and confirm with user
6. Call `getCompanyInfo` API to get company info text
7. Call `generateWebsite` API to generate website

```bash
python3 {baseDir}/scripts/generate_website.py
```

### How it works:
1. The script will check if site languages exist
2. If languages exist, ask if user wants to initialize (clear existing content)
3. If user confirms initialization, call initialize API
4. Start multi-turn dialogue - AI asks questions one by one:
   - Company/Website name
   - Industry
   - Business scope
   - Business features
   - Culture and philosophy
   - Core advantages
   - Contact phone
   - Contact email
   - Company address
   - Logo URL
   - Visual style
5. **For each question:**
   - AI displays the question and example
   - Customer types their answer manually and presses Enter
   - AI cannot auto-answer - all answers must come from customer input
   - Customer can skip questions or exit at any time
6. After all questions or user finishes, show summary for confirmation
7. If user confirms:
   - Call `POST /ai/getCompanyInfo` with collected data
   - Use returned info as requirement
   - Call `POST /ai_tools/generateWebsite` to generate website

### User commands:
- **Answer normally**: Type your answer and press Enter (customer must provide their own answer)
- **Skip question**: Type 'skip' or '跳过' to skip the current question
- **Finish dialogue**: Type 'finish' or '结束' to end dialogue and generate summary
- **Exit**: Type 'exit' or '退出' to quit

### Important:
- **All answers are manually entered by the customer** - AI only asks questions
- AI never auto-answers or generates answers for the customer
- Each question requires the customer to type their own response
- If customer doesn't answer, the question will be asked again until answered or skipped

No additional options required.

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
* `POST /ai_tools/getCompanyInfo`
* `POST /ai_tools/generateWebsite`
* `GET /message/getlist`
* `GET /site/status`

If your actual backend uses different paths, update the `ENDPOINT_*` constants in the Python scripts.

## Notes

* All requests use the HTTP `Authorization` header.
* The API key is sent as plain header value:

  * `Authorization: YOUR_KEY`
* Output is printed as formatted JSON for easier debugging and agent use.
* If your API field names differ, update the payload fields in the scripts.
