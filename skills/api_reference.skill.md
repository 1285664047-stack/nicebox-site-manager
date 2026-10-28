---
name: api-reference
description: API specification and endpoint reference for AiWebSite OpenClaw
metadata: {"clawdbot":{"emoji":"[API-REF]","requires":{"file":["scripts/config.json"]}}}
---

# API Reference

Complete API specification for AiWebSite OpenClaw.

## Base URL

```
从 config.json 中的 base_url 字段动态读取
所有脚本通过 config_reader.py 读取 base_url
```

> **注意**：所有脚本通过 `config_reader.py` 读取 base_url，文档中的 URL 仅供参考。

## Authentication

**Format**: `Authorization: <api_key>` (no Bearer prefix)

Correct:
```
Authorization: 456_478_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Wrong (will fail):
```
Authorization: Bearer YOUR_API_KEY
```

## All Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/article/save` | Create or update article draft |
| POST | `/article/publishSaved` | Publish a saved article by article_id |
| GET | `/article/getCategories` | List article categories |
| POST | `/article/createCategory` | Create an article category |
| POST | `/product/save` | Create or update product draft |
| POST | `/product/publishSaved` | Publish a saved product by product_id |
| GET | `/product/getCategories` | List product categories |
| POST | `/product/createCategory` | Create a product category |
| POST | `/ai_tools/generateContentCover` | Generate article/product cover or Logo candidate with `aspect_ratio` |
| GET | `/site_pages/getLanguageList` | List site languages |
| GET | `/site_pages/readIndexHtml` | Read index HTML |
| POST | `/template/initializeData` | Initialize site data |
| POST | `/ai_tools/getCompanyInfo` | Register company info |
| POST | `/ai_tools/generateWebsite` | Generate website (SSE) |
| GET | `/message/list` | List messages |
| GET | `/site/status` | Check site status |
| GET | `/site/generateShareUrl` | Generate share URL |
| GET | `/site/generateContentShareUrl` | Generate article/product draft preview URL |
| GET | `/seo_geo/getLatest` | Get latest SEO/GEO report |
| GET | `/seo_geo/getReport` | Get full SEO/GEO report |
| GET | `/seo_geo/getOptimizableItems` | Get actual optimizable items |
| POST | `/seo_geo/startDetection` | Start confirmed detection |
| GET | `/seo_geo/getDetectionStatus` | Query detection status |
| POST | `/seo_geo/startOptimization` | Start confirmed one-click optimization |
| GET | `/seo_geo/getOptimizationStatus` | Query and advance optimization status |
| GET | `/site_publish/getConfig` | Get FTP config |
| POST | `/site_publish/updateFtpConfig` | Update FTP config |
| POST | `/site_publish/testFtpConnection` | Test FTP connection |
| POST | `/site_publish/publish` | Publish website |
| POST | `/site_publish/preparePublish` | Prepare publish |
| GET | `/site_publish/getServerInfo` | Get server info |
| GET | `/site_publish/getTaskStatus` | Get task status |
| POST | `/site_publish/cancelTask` | Cancel task |
| POST | `/image/upload` | Upload/import an image to cloud assets |

## Category Creation APIs

文章分类：`POST /article/createCategory`  
产品分类：`POST /product/createCategory`

请求 JSON：

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | 分类名称；同一父分类下不能重名 |
| `parent_id` | No | 父分类 ID，顶级分类传 `0`，默认 `0` |
| `sort_order` | No | 非负排序值；不传时由服务端自动追加 |
| `locale` | No | 语言代码，默认 `zh-CN` |

普通 REST 认证仍使用裸 API Key：`Authorization: <api_key>`，不加 `Bearer`。

调用示例：

```bash
python3 {baseDir}/scripts/create_category.py article --name "公司新闻" --locale zh-CN
python3 {baseDir}/scripts/create_category.py product --name "智能设备" --parent-id 0 --sort-order 10 --locale zh-CN
```

也可以使用通用回退入口：

```bash
python3 {baseDir}/scripts/api_tool.py nicebox_create_article_category --args-json '{"name":"公司新闻","parent_id":0,"locale":"zh-CN"}'
python3 {baseDir}/scripts/api_tool.py nicebox_create_product_category --args-json '{"name":"智能设备","parent_id":0,"locale":"zh-CN"}'
```

## getCompanyInfo Required Fields

| Field | Required | Note |
|-------|---------|------|
| `company_name` | [OK] Yes | Company/website name, required |
| `business_scope` | No | Business scope |
| `industry` | No | Industry |
| `advantages` | No | Core competitive advantages |
| `phone` | No | Contact phone |
| `email` | No | Contact email |
| `address` | No | Company address |
| `logo` | No | Public Logo URL, accepted AI Logo URL, or `未填写` |
| `style` | No | Visual style (including colors) |
| `other` | No | Other information |

**Important**: The API returns `400 "公司名称/网站名称不能为空"` if required fields are missing. When fields are not provided, store as `"未填写"` (not empty string).

**Logo handling** (when user has no logo):

Ask the user to choose a public URL, AI generation, or no Logo. For AI generation call `/ai_tools/generateContentCover` with `content_type=logo` and a user-selected `aspect_ratio` from `1:1`, `5:2`, `3:2`, `4:3`, `3:4`, or `2:3`; show the candidate before saving it. Do not silently create a placeholder.

## generateWebsite SSE Events

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

## generateShareUrl Response

**Endpoint**: `GET /site/generateShareUrl` (no parameters needed)

**Response**:
```json
{
  "code": 0,
  "data": {
    "site_id": 478,
    "share_url": "/api/template/preview/share/token/xxx"
  }
}
```

**Important**: `share_url` is a **relative path** (e.g., `/api/template/preview/share/token/xxx`), NOT a full URL. Scripts must extract the **origin** from `base_url` and prepend it — do **NOT** use the full `base_url` (which includes `/api/openclaw`) to avoid path duplication:
```
# Correct: extract origin from base_url
origin = urlparse(base_url).scheme + '://' + urlparse(base_url).netloc
full_url = origin + share_url  # https://<dynamic_domain>/api/template/preview/share/token/xxx

# Wrong: direct concatenation
full_url = base_url + share_url  # https://<domain>/api/openclaw/api/template/preview/share/token/xxx (WRONG!)
```

## Error Codes

| HTTP/Code | Meaning | Action |
|-----------|---------|--------|
| 0 | Success | Continue |
| 400 | Missing required fields | Check `message`, fix payload |
| 500 | Server error | Retry 2-3 times with delay |

## Publish API Parameters

The `POST /site_publish/publish` endpoint requires:

| Field | Location | Required | Description |
|-------|----------|----------|-------------|
| `options.batch_size` | options object | Yes | Batch size: 20, 30, or 50 |
| `options.overwrite_mode` | options object | Yes | `smart` or `force` |
| `options.generate_mode` | options object | Yes | `default` or `full_static` |
| `batch_number` | top level | Yes | Current upload batch number (starts at 1) |
| `disable_streaming` | top level | No | `true` for JSON response, omit for SSE |

**Current contract**: `batch_number` is a top-level field. The API normalizes it into internal options and still accepts the old `options.batch_number` form for compatibility.

The `POST /site_publish/preparePublish` endpoint requires:

| Field | Location | Required | Description |
|-------|----------|----------|-------------|
| `options.batch_size` | options object | Yes | Batch size |
| `options.overwrite_mode` | options object | Yes | Overwrite mode |
| `options.generate_mode` | options object | Yes | Generate mode |
| `batch_number` | top level | Yes | Current preparation batch number (starts at 1) |

Response fields: `has_more` (boolean), `total_batches` (number), `generated_pages` (number)

## Image Upload API

**Endpoint**: `POST /image/upload`

**Request form data**:

| Field | Required | Description |
|-------|----------|-------------|
| `file` | 二选一 | 本地 JPEG、PNG 或 WebP 图片 |
| `image_url` | 二选一 | 公开可访问的 HTTP/HTTPS 图片地址 |
| `image_urls` | 二选一 | MCP 批量公开图片地址数组，不设业务数量上限；不能与 `file`/`image_url` 同传 |
| `purpose` | No | `logo`、`product_cover`、`article_cover`、`image`，默认 `image` |
| `folder_name` | No | 自定义云资源库文件夹；不存在时自动创建，并覆盖默认目录 |
| `original_name` | No | 素材库显示文件名 |

**Response**:

```json
{
  "code": 0,
  "message": "上传成功",
  "data": {
    "material_id": 123,
    "image_url": "https://example.com/path/to/image.jpg",
    "folder_name": "s_image",
    "purpose": "image",
    "source_bytes": 2500000,
    "uploaded_bytes": 800000,
    "compressed": true,
    "reused": false
  }
}
```

每张源文件最大 10MB；大于约 2MB 时服务端先压缩。默认目录为：Logo `s_logo`、产品封面 `s_products`、文章封面 `s_news`、其他图片 `s_image`。`image_urls` 批量模式没有业务数量上限。

## generateWebsite API

**Endpoint**: `POST /ai_tools/generateWebsite`

**Request**: Only `requirement` is needed

```json
{ "requirement": "网站需求描述..." }
```

**Notes**:
- Website is generated internally, no HTML content returned
- SSE event types: `progress`, `section_generating`, `section_complete`, `complete`, `error`
- Error event field: `ev.content` (not `ev.message`), code must handle both
- If returns `{"type":"error","content":"参数缺失，无法创建页面"}`, it's an `AiEditor` internal error, not related to request parameters
- Site must be initialized first (via `template/initializeData`)
- After successful generation, state file is preserved (not immediately deleted) for retry
- After successful generation, structured confirmation request is output (`need_publish_confirm: true`), AI must ask user whether to publish, must not auto-publish
- **Generation verification**: SSE stream returning `ok: true` does not guarantee website was actually generated. Script auto-calls `/site_pages/readIndexHtml` to verify index HTML exists. Verification failure prompts user to retry, does not enter publish flow
