---
name: nicebox-site-manager
description: Manage AI-built websites via NiceBox OpenClaw API. Supports article publishing, viewing messages, and checking site status.
metadata: {"clawdbot":{"emoji":"🛠️","requires":{"env":["AIBOX_API_KEY"]},"primaryEnv":"AIBOX_API_KEY"}}
---

# NiceBox Site Manager

Manage AI-built websites through the NiceBox OpenClaw API.

Base URL:

```
http://aidev.nicebox.cn/api/openclaw
```

Authentication:

```
Authorization: $AIBOX_API_KEY
```

This skill provides 12 main capabilities:

* Publish article
* List article categories
* Publish product
* List product categories
* List site languages
* Generate website
* View messages
* Check site status
* Manage FTP configuration
* Test FTP connection
* Publish website
* Upload material
* Generate share URL

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

AI-guided multi-turn dialogue to generate a website. **All answers are manually entered by the customer** — AI only asks questions, never auto-answers.

### ⚠️ Important: Use Node.js version

**Python 3 is not available on this system** (only Python 2.7 at `D:\MyInstall\python\python.exe`).
Use the Node.js version instead:

```bash
node {baseDir}/scripts/generate_website.mjs <command> [args]
```

### ⚠️ 【强制】AI 操作流程（必须严格按此顺序执行）

**AI 在帮用户生成网站时，必须严格按以下 4 步顺序执行，不得跳过任何步骤：**

```
第 1 步：ask-init       ← 【必须首先执行】检查站点数据（第1次确认）
第 2 步：answer "内容"  ← 逐题收集企业信息（8 个问题）
第 3 步：summary        ← 显示汇总确认
第 4 步：generate       ← 生成网站（第2次确认）
```

**双重确认机制（两次提示内容完全一致）：**

> ⚠️ **检测到站点已有数据，生成网站将初始化站点，清空已有的所有网站信息，包括页面、产品、文章、留言等。是否确认继续？**

| 确认时机 | 命令 | 逻辑 |
|----------|------|------|
| **第1次** 收集问题前 | `ask-init` | 站点已空 → 直接进入收集问题；有数据 → 弹出确认；取消 → 终止 |
| **第2次** 生成网站前 | `generate` | 站点已空 → 直接生成网站；有数据 → 弹出确认；取消 → 终止 |

**确认回复统一使用 `confirm` 命令（两个阶段共用）：**
- 用户回复「确认」→ 执行 `confirm "确认"` → 初始化站点并继续
- 用户回复「取消」→ 执行 `confirm "取消"` → 终止所有操作

```bash
node {baseDir}/scripts/generate_website.mjs ask-init          # 【第1步】检查站点（第1次确认）
node {baseDir}/scripts/generate_website.mjs confirm "确认"    # 确认（两个阶段通用）
node {baseDir}/scripts/generate_website.mjs confirm "取消"    # 取消（两个阶段通用）
node {baseDir}/scripts/generate_website.mjs status            # 查看进度
node {baseDir}/scripts/generate_website.mjs questions         # 列出全部8问
node {baseDir}/scripts/generate_website.mjs next              # 打印下一题
node {baseDir}/scripts/generate_website.mjs answer "内容"     # 记录回答
node {baseDir}/scripts/generate_website.mjs summary           # 汇总确认
node {baseDir}/scripts/generate_website.mjs generate          # 【第4步】生成网站（第2次确认）
node {baseDir}/scripts/generate_website.mjs reset             # 重置对话
```

### 8 个核心问题（精简版）：

| # | 问题 | 包含信息 | 提示 |
|---|------|---------|------|
| 1 | 公司名称 | company_name（⭐必填） | 可跳过 / 完成 |
| 2 | Logo | logo（无则跳过） | 可跳过 / 完成 |
| 3 | 行业 | industry | 可跳过 / 完成 |
| 4 | 业务范围 | business_scope | 可跳过 / 完成 |
| 5 | 核心优势 | advantages | 可跳过 / 完成 |
| 6 | 联系方式 | phone → 自动追问邮箱/地址 | 可跳过 / 完成 |
| 7 | 视觉风格 | style（含配色） | 可跳过 / 完成 |
| 8 | 其他补充 | other | 可跳过 / 完成 |

> **每题末尾均显式提示**：💡 可回复「跳过」跳过此题，回复「完成」提前结束所有问答

**追问机制**：客户只填了部分联系方式时，自动追问缺失项：
- 只填电话 → 追问邮箱
- 邮箱也没填 → 追问地址

### 初始化确认流程（双重确认，两次提示内容完全一致）

**AI 必须在帮用户生成网站时，首先执行 `ask-init`。生成网站前 `generate` 会再次检查。**

```
用户说"帮我生成网站"
    ↓
AI 执行 ask-init（第1次确认）
    ↓
检查站点语言数据
    ↓
┌── 站点已空 → 直接进入收集问题
│
├── 有数据 → 弹出确认提示
│   ⚠️ 检测到站点已有数据，生成网站将初始化站点，清空已有的所有网站信息，
│      包括页面、产品、文章、留言等。是否确认继续？
│   - 「确认」→ 初始化清空站点 → 进入收集问题
│   - 「取消」→ 终止后续所有操作
│
└── 无数据 → 自动初始化 → 直接开始收集问题
    ↓
收集完8个问题后，AI 执行 generate（第2次确认）
    ↓
再次检查站点语言数据
    ↓
┌── 站点已空 → 直接生成网站
│
├── 有数据 → 弹出确认提示（与第1次完全相同）
│   ⚠️ 检测到站点已有数据，生成网站将初始化站点，清空已有的所有网站信息，
│      包括页面、产品、文章、留言等。是否确认继续？
│   - 「确认」→ 初始化清空站点 → 生成网站
│   - 「取消」→ 终止后续所有操作
│
└── 无数据（已被第1次确认后初始化清空）→ 直接生成网站
```

### 用户回复约定：

| 回复 | 含义 |
|------|------|
| 正常内容 | 记录为回答 |
| **「跳过」** | 该字段记为"未填写"，继续下一题 |
| **「完成」** | 提前结束所有问答，进入汇总确认 |
| **「确认」** | 仅在初始化确认提示中：确认初始化并继续（两个阶段通用） |
| **「取消」** | 仅在初始化确认提示中：终止后续所有操作（两个阶段通用） |
| 空回复 | 记为"未填写" |

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

## Manage FTP configuration

Manage FTP configuration for website publishing.

### Python version:
```bash
python3 {baseDir}/scripts/ftp_manager.py get-config
python3 {baseDir}/scripts/ftp_manager.py update-config --host ftp.example.com --port 21 --username user --password pass
python3 {baseDir}/scripts/ftp_manager.py test-connection
```

### Node.js version:
```bash
node {baseDir}/scripts/ftp_manager.mjs get-config
node {baseDir}/scripts/ftp_manager.mjs update-config --host ftp.example.com --port 21 --username user --password pass
node {baseDir}/scripts/ftp_manager.mjs test-connection
```

### Commands:
- `get-config` - Get current FTP configuration
- `update-config` - Update FTP configuration (supports partial updates)
  - `--host`: FTP host
  - `--port`: FTP port
  - `--username`: FTP username
  - `--password`: FTP password
  - `--path`: FTP path
  - `--passive`: FTP passive mode (true/false)
  - `--publish-mode`: Publish mode (dynamic/static)
- `test-connection` - Test FTP connection
- `get-server-info` - Get FTP server information
- `get-task-status` - Get publish task status
- `cancel-task` - Cancel publish task
- `publish` - Publish website

### Publish process flow:
1. Check FTP configuration (warning only if test fails, does not block publish)
2. Test FTP connection (failure → warning, still attempts publish)
3. Check publish status (using `get-task-status`)
4. Cancel existing task if running (using `cancel-task`)
5. Prepare publish (using `preparePublish` API)
6. Publish website (using `publish` API, with auto-retry up to 3 times)
7. Show completion message with upload stats

**Important**: The `batch_number` parameter **MUST be inside the `options` object**, not at the top level of the request body. This is a PHP backend requirement — placing it outside causes `Undefined array key "batch_number"` error.

Correct:
```json
{
  "options": {
    "batch_size": 30,
    "overwrite_mode": "smart",
    "generate_mode": "default",
    "batch_number": 1
  },
  "disable_streaming": true
}
```

Wrong (will fail):
```json
{
  "options": {
    "batch_size": 30,
    "overwrite_mode": "smart",
    "generate_mode": "default"
  },
  "batch_number": 1,
  "disable_streaming": true
}
```

## Publish website

Publish your website to FTP server with pre-checks.

### ⚠️ 【强制】发布确认机制（三重保障）

**AI 在发布网站时，必须严格遵守以下 3 条规则，不得违反：**

1. **客户主动要求发布时**：必须先询问确认，提示"发布后无法还原"，用户明确确认后才执行
2. **生成网站后**：不得自动发布，必须询问客户是否需要发布，提示"发布后无法还原"
3. **即使客户要求"生成后自动发布"**：生成完成后仍需再次询问确认，不得跳过

**确认提示文案（统一使用）：**

> ⚠️ 发布网站将覆盖线上版本，此操作无法撤销还原！是否确认发布？
> - 回复「确认发布」→ 执行发布
> - 回复「取消」/「暂不发布」→ 不发布

**发布确认流程：**

```
任何场景触发发布
    ↓
AI 调用 ftp_manager.mjs publish（不带 --confirmed）
    ↓
脚本返回确认请求 JSON
    ↓
AI 向用户展示确认提示：「⚠️ 发布网站将覆盖线上版本，此操作无法撤销还原！是否确认发布？」
    ↓
┌── 用户回复「确认发布」→ AI 调用 ftp_manager.mjs publish --confirmed → 执行发布
│
└── 用户回复「取消」/「暂不发布」→ 终止发布操作
```

**⚠️ 绝对禁止的行为：**
- 禁止直接带 `--confirmed` 调用 publish（必须先不带该参数，获取确认请求后再让用户确认）
- 禁止在生成网站后自动发布
- 禁止将"用户说生成+发布"视为发布已确认

### 发布流程（确认后执行）：

**Important**: The publish command automatically checks:
1. FTP configuration is complete
2. FTP connection is successful (failure = warning, not block)
3. All required fields are filled

After successful generation, you'll be prompted to publish using:
```bash
node {baseDir}/scripts/ftp_manager.mjs publish
```

### Python version:
```bash
# Python 版本同样需要两步确认
python3 {baseDir}/scripts/ftp_manager.py publish
python3 {baseDir}/scripts/ftp_manager.py publish --confirmed
python3 {baseDir}/scripts/ftp_manager.py publish --confirmed --batch-size 50 --overwrite-mode force
```

### Node.js version:
```bash
# 第一步：请求确认（不带 --confirmed）
node {baseDir}/scripts/ftp_manager.mjs publish

# 第二步：用户确认后，带 --confirmed 执行发布
node {baseDir}/scripts/ftp_manager.mjs publish --confirmed
```

### Options:
- `--confirmed`: **必须用户明确确认后才能传入**，否则脚本只返回确认请求不执行发布
- `--batch-size`: Batch size (20|30|50)
- `--overwrite-mode`: Overwrite mode (smart|force)
- `--time-tolerance`: Time tolerance in seconds
- `--mode-detection`: FTP mode detection (auto|passive|active)
- `--clean-before-publish`: Clean remote directory before publish
- `--include-drafts`: Include draft pages
- `--generate-mode`: HTML generate mode (default|full_static)
- `--disable-streaming`: Disable streaming output

## Environment

### 修改 API Key（默认方式）

当用户提出要修改「秘钥、key、api key」时，**默认使用 `set-key` 命令**，直接修改操作系统环境变量 `AIBOX_API_KEY`：

```bash
# 查看当前秘钥
node {baseDir}/scripts/set-key.mjs
python {baseDir}/scripts/set-key.py

# 修改秘钥（写入操作系统环境变量，立即生效+持久化）
node {baseDir}/scripts/set-key.mjs "your_new_api_key"
python {baseDir}/scripts/set-key.py "your_new_api_key"
```

此方式会：
1. 将新密钥写入当前进程 `process.env.AIBOX_API_KEY`（本次会话立即生效）
2. 调用 PowerShell 写入用户级操作系统环境变量 `HKCU:\Environment`（永久生效，重启后依然有效）

> **提示**：如果其他工具（IDE、第三方脚本）需要用到 `AIBOX_API_KEY`，建议手动在系统「环境变量」设置中确认或手动添加。

### 临时环境变量（备用方式）

如果只想在当前终端会话中临时使用某个密钥（不影响系统环境变量）：

```bash
# PowerShell（当前终端有效，关闭后失效）
$env:AIBOX_API_KEY="your_api_key"

# Bash / Git Bash / WSL（当前终端有效）
export AIBOX_API_KEY="your_api_key"
```

### Base URL（通常无需修改）

```bash
# 仅当 NiceBox API 地址变更时才需设置
$env:AIBOX_BASE_URL="http://aidev.nicebox.cn/api/openclaw"
```

## API Specification

### Authorization Header
**Format**: `Authorization: <api_key>` (no Bearer prefix)

Correct:
```
Authorization: 4_455_14ed156fdba64c6ccdb7a0cf236ac712078382681f3cb237
```

Wrong (will fail):
```
Authorization: Bearer 4_455_14ed156fdba64c6ccdb7a0cf236ac712078382681f3cb237
```

### getCompanyInfo Required Fields

The `POST /ai_tools/getCompanyInfo` API requires these fields:

| Field | Required | Note |
|-------|---------|------|
| `company_name` | ✅ Yes | 公司/网站名称，必填 |
| `business_scope` | No | 业务范围 |
| `industry` | No | 所属行业 |
| `advantages` | No | 核心竞争优势 |
| `phone` | No | 联系电话 |
| `email` | No | 联系邮箱（从联系方式追问中收集）|
| `address` | No | 公司地址（从联系方式追问中收集）|
| `logo` | No | Logo（未提供则用占位图）|
| `style` | No | 视觉风格（含配色）|
| `other` | No | 其他补充 |

**Important**: The API will return `400 "公司名称/网站名称不能为空"` or `400 "业务范围不能为空"` if required fields are missing. When fields are not provided by the user, store as the string `"未填写"` (not an empty string).

**Logo placeholder** (when user has no logo):
```
https://via.placeholder.com/200x80/8B4513/FFFFFF?text=CompanyName
```
Color codes: `8B4513` (brown), `00A86B` (green), `1E3A8A` (blue), `D4AF37` (gold)

### generateWebsite SSE Events

The `POST /ai_tools/generateWebsite` API returns SSE (Server-Sent Events):

| Event Type | Description | Fields |
|-----------|-------------|--------|
| `intro_text` | Requirement confirmation | `content`, `timestamp` |
| `progress` | Generation progress | `percentage` (may be null), `message` |
| `section_generating` | Section generation started | `section` (may be undefined), `timestamp` |
| `progressive_content` | HTML content chunk | `content` (accumulates) |
| `section_complete` | Section generation done | `section` (may be undefined), `timestamp` |
| `complete` | All generation finished | - |
| `error` | Error occurred | `message` |

**Important**: The `section` field may be `undefined` in some events. Use sequential numbering as fallback.

### Error Codes

| HTTP/Code | Meaning | Action |
|-----------|---------|--------|
| 0 | Success | Continue |
| 400 | Missing required fields | Check `message`, fix payload |
| 500 | Server error | Retry 2-3 times with delay |

### Publish API Parameters

The `POST /site_publish/publish` endpoint requires:

| Field | Location | Required | Description |
|-------|----------|----------|-------------|
| `options.batch_size` | options object | Yes | Batch size: 20, 30, or 50 |
| `options.overwrite_mode` | options object | Yes | `smart` or `force` |
| `options.generate_mode` | options object | Yes | `default` or `full_static` |
| `options.batch_number` | options object | Yes | Current batch number (starts at 1) |
| `disable_streaming` | top level | No | `true` for JSON response, omit for SSE |

**Critical**: `batch_number` MUST be inside `options`. Placing it at top level causes `Undefined array key "batch_number"`.

The `POST /site_publish/preparePublish` endpoint requires:

| Field | Location | Required | Description |
|-------|----------|----------|-------------|
| `options.batch_size` | options object | Yes | Batch size |
| `options.overwrite_mode` | options object | Yes | Overwrite mode |
| `options.generate_mode` | options object | Yes | Generate mode |
| `options.batch_number` | options object | Yes | Batch number (1) |

Response fields: `has_more` (boolean), `total_batches` (number), `generated_pages` (number)

## Default endpoint assumptions

This skill assumes the following API paths (relative to the Base URL `http://aidev.nicebox.cn/api/openclaw`):

* `POST /article/publish`
* `GET /article/getCategories`
* `POST /product/publish`
* `GET /product/getCategories`
* `GET /site_pages/getLanguageList`
* `POST /template/initializeData`
* `POST /ai_tools/getCompanyInfo`
* `POST /ai_tools/generateWebsite`
* `GET /message/list`
* `GET /site/status`
* `GET /site_publish/getConfig`
* `POST /site_publish/updateFtpConfig`
* `POST /site_publish/testFtpConnection`
* `POST /site_publish/publish`
* `POST /site_publish/preparePublish`
* `GET /site_publish/getServerInfo`
* `GET /site_publish/getTaskStatus`
* `POST /site_publish/cancelTask`
* `POST /material/upload`

**Important**: The FTP publishing endpoints are under the `site_publish` controller, NOT `ftp`. Full example URLs:
- `http://aidev.nicebox.cn/api/openclaw/site_publish/getConfig`
- `http://aidev.nicebox.cn/api/openclaw/site_publish/testFtpConnection`
- `http://aidev.nicebox.cn/api/openclaw/site_publish/getServerInfo`
- `http://aidev.nicebox.cn/api/openclaw/site_publish/getTaskStatus`
- `http://aidev.nicebox.cn/api/openclaw/site_publish/cancelTask`
- `http://aidev.nicebox.cn/api/openclaw/site_publish/preparePublish`
- `http://aidev.nicebox.cn/api/openclaw/site_publish/publish`

If your actual backend uses different paths, update the `BASE_URL` constant in the scripts.

## Troubleshooting

### 任何接口返回 404：先读文档，再猜路径

遇到 404 时，立即执行以下三步，**不要凭记忆或直觉猜测路径**：

**Step 1 — 立刻回读 SKILL.md**
找到「Default endpoint assumptions」章节（通常在文档中后段），里面有本技能所有接口的完整路径列表。以 FTP 为例：文档写的是 `site_publish`，不是 `ftp`。

**Step 2 — 按文档路径重试**
用 SKILL.md 中的实际路径发起请求，确认是否真的 404。

**Step 3 — 探测可能的变体**
如果文档路径也 404，再尝试合理的变体（下划线/驼峰/复数）：
- `get_config` vs `getConfig` vs `getConfigInfo`
- `/product/categories` vs `/product/getCategories`
- `/ftp/` vs `/site_publish/` vs `/site_publish/` vs `/publish/`

**永远顺序：读文档 → 用文档路径 → 最后才尝试变体。**

### "公司名称/网站名称不能为空"
The `getCompanyInfo` API requires `company_name` fields to be non-empty. Store undefined fields as `"未填写"`.

### Logo field is empty
Use a placeholder image URL:
```
https://via.placeholder.com/200x80/8B4513/FFFFFF?text=Logo
```

### SSE streaming error
If `generateWebsite` returns `{"type":"error","content":"参数缺失，无法创建页面"}`, this is an internal `AiEditor` error, not a parameter issue. The request only needs `requirement`. Check if the site was properly initialized first.

### FTP 接口 404：路径不对

**先读 SKILL.md 再动手。**

FTP 相关接口路径是 `site_publish`，不是 `ftp`。完整路径：
- `http://aidev.nicebox.cn/api/openclaw/site_publish/getConfig`
- `http://aidev.nicebox.cn/api/openclaw/site_publish/getServerInfo`
- `http://aidev.nicebox.cn/api/openclaw/site_publish/updateFtpConfig`
- `http://aidev.nicebox.cn/api/openclaw/site_publish/testFtpConnection`
- `http://aidev.nicebox.cn/api/openclaw/site_publish/publish`

**永远不要凭记忆猜测 API 路径。**

### Python scripts not working on Windows

**Use Node.js instead of Python.** Python 3 is not available on this system. The `generate_website.mjs` script provides equivalent functionality:

```bash
node {baseDir}/scripts/generate_website.mjs <command>
```

If you need to run Python scripts for other commands (publish, list, etc.), ensure Python 3 is installed first.

### 📌 FTP 接口路径易错点（经验教训）

**FTP 相关接口路径是 `site_publish`，不是 `ftp`！**

首次测试时犯了严重错误：用户问 FTP 配置，我先入为主用了 `/ftp/getConfig` 等路径（凭空猜测），导致连续返回 404，白费了两次 API 调用。直到重新完整读完 SKILL.md，才在底部 "Default endpoint assumptions" 章节找到正确答案。

**教训：任何 API 路径问题，先读 SKILL.md 的 endpoint 列表，不要凭记忆或猜测。**

---

## Notes

* All requests use the HTTP `Authorization` header.
* The API key is sent as plain header value:
  * `Authorization: YOUR_KEY` (no Bearer prefix)
* Output is printed as formatted JSON for easier debugging and agent use.
* If your API field names differ, update the payload fields in the scripts.
* Unanswered fields are always stored as the string `"未填写"`, never as empty strings.
* State is stored in `.dialogue_state.json` in the scripts directory.

### 📌 generateWebsite API 说明

**接口路径**：`/ai_tools/generateWebsite`

**请求参数**：只需 `requirement`

```json
{ "requirement": "网站需求描述..." }
```

| 参数 | 必须 | 说明 |
|------|------|------|
| `requirement` | ✅ | 网站需求描述（通过 `getCompanyInfo` 获取企业信息后填入） |

**注意事项**：
- 网站在站点内部生成，不返回 HTML 内容
- SSE 流事件类型：`progress`、`section_generating`、`section_complete`、`complete`、`error`
- 错误事件字段：`ev.content`（不是 `ev.message`），代码需兼容两种
- 如果返回 `{"type":"error","content":"参数缺失，无法创建页面"}`，是 `AiEditor` 内部错误，与请求参数无关
- 生成前需确保站点已初始化（通过 `template/initializeData`）
- 生成成功后，状态文件会保留（不再立即删除），方便重试
- 生成成功后会输出结构化确认请求（`need_publish_confirm: true`），AI 必须询问用户是否发布，不得自动发布

## Upload material

Upload images to your site's cloud resource library, automatically detecting the file type based on recent conversation context.

### 🔍 自动判断上传类型逻辑

**AI 必须严格遵循以下判断逻辑**：

1. **30分钟内上下文检测**：
   - 检查最近 30 分钟内的对话是否涉及上传类型
   - 如果无相关上下文，询问客户："检测到您上传了图片，请问这是什么类型的图片？是否要上传到网站站点的云资源库中？"

2. **Logo 文件特殊处理**：
   - 如果 30 分钟内存在上传类型且为 `logo`：
     - 检查对话历史是否已经上传过 logo
     - 如果已上传过，则当作无上传类型处理（重新询问）
     - 如果未上传过，则直接上传为 `guide_logo` 类型

3. **自动类型检测**（文件名匹配）：
   - **Logo**：文件名包含 `logo`
   - **产品图片**：文件名包含 `product`、`产品`、`商品`
   - **新闻图片**：文件名包含 `news`、`新闻`、`资讯`
   - **其他图片**：默认 `openclaw_other`

### 📝 上传后处理

1. **记录返回路径**：上传成功后，必须记录返回的 `filePath` 和 `fileId`
2. **后续操作使用**：在后续的网站生成或内容发布中，如需使用该图片，应使用记录的路径
3. **重复文件处理**：如果上传相同文件，API 会返回已有文件的 ID（`isOld: true`），应正常处理

### Python version:
```bash
python3 {baseDir}/scripts/upload_material.py upload path/to/image.jpg
python3 {baseDir}/scripts/upload_material.py upload path/to/logo.png --source guide_logo
python3 {baseDir}/scripts/upload_material.py upload path/to/product.jpg --source openclaw_products
```

### Node.js version:
```bash
node {baseDir}/scripts/upload_material.mjs upload path/to/image.jpg
node {baseDir}/scripts/upload_material.mjs upload path/to/logo.png --source guide_logo
node {baseDir}/scripts/upload_material.mjs upload path/to/product.jpg --source openclaw_products
```

### Options:
- `upload`: Upload file
- `--source`: Manually specify file type (choices: `guide_logo`, `openclaw_products`, `openclaw_news`)

### API Specification

**Endpoint**: `POST /material/upload`

**Request form data**:

| Field | Required | Description |
|-------|----------|-------------|
| `file` | ✅ | File to upload (for non-logo files) |
| `logoFile` | ✅ | File to upload (for logo files only) |
| `source` | ✅ | File type: `guide_logo`, `openclaw_products`, `openclaw_news` |

**Response**:

```json
{
  "code": 0,
  "message": "上传成功",
  "data": {
    "fileId": 123,
    "filePath": "https://example.com/path/to/image.jpg",
    "fileType": "image/jpeg",
    "fileName": "image.jpg",
    "isOld": false
  }
}
```

**Important**:
- Maximum file size: 10MB
- Supported image formats: JPG, PNG, GIF, WebP
- Files are automatically organized into folders based on type:
  - `guide_logo` → `guideLogo` folder
  - `openclaw_products` → `OpenClawlawProducts` folder
  - `openclaw_news` → `OpenClawlawNews` folder
  - `openclaw_other` → root of "My Files"

### 🌐 完整 API 路径

- `http://aidev.nicebox.cn/api/openclaw/material/upload`

## Generate share URL

Generate a temporary share URL for your site.

### 说明

当客户要求生成【预览地址、临时地址】时，使用此功能生成临时分享地址。

**有效期提示：** 临时分享链接有效期为 **2 小时**，请提醒客户及时查看。

### ⚠️ 【强制】前置内容检查

生成分享链接前，**必须**先调用 `GET /site_pages/getLanguageList` 检查 `data.total`：

| total 值 | 含义 | 操作 |
|---------|------|------|
| `> 0` | 站点已有语言配置（已有网站内容） | ✅ 继续生成分享链接 |
| `= 0` | 站点无内容 | ❌ 终止，提示用户「站点暂无网站内容，请先生成并发布网站后再生成分享链接」 |

```
用户要求生成分享链接
    ↓
调用 GET /site_pages/getLanguageList
    ↓
检查 data.total
    ├── ✅ total > 0 → 生成分享链接 → 输出 URL
    └── ❌ total = 0 → 终止操作 → 提示用户
```

### Python version:
```bash
python3 {baseDir}/scripts/generate_share_url.py
```

### Node.js version:
```bash
node {baseDir}/scripts/generate_share_url.mjs
```

### API Specification

**Endpoint**: `GET /site/generateShareUrl`

**Response**:

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "site_id": 123,
    "share_url": "http://aidev.nicebox.cn/api/template/preview/share/token/123-1618764000-abc123"
  }
}
```

### 🌐 完整 API 路径

- `http://aidev.nicebox.cn/api/openclaw/site/generateShareUrl`
