---
name: api-reference
description: API specification and endpoint reference for NiceBox OpenClaw
metadata: {"clawdbot":{"emoji":"[API-REF]","requires":{"env":["AIBOX_API_KEY"]},"primaryEnv":"AIBOX_API_KEY"}}
---

# API Reference

Complete API specification for NiceBox OpenClaw.

## Base URL

```
https://ai.nicebox.cn/api/openclaw
```

## Authentication

**Format**: `Authorization: <api_key>` (no Bearer prefix)

Correct:
```
Authorization: 4_455_14ed156fdba64c6ccdb7a0cf236ac712078382681f3cb237
```

Wrong (will fail):
```
Authorization: Bearer 4_455_14ed156fdba64c6ccdb7a0cf236ac712078382681f3cb237
```

## All Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/article/publish` | Publish article |
| GET | `/article/getCategories` | List article categories |
| POST | `/product/publish` | Publish product |
| GET | `/product/getCategories` | List product categories |
| GET | `/site_pages/getLanguageList` | List site languages |
| GET | `/site_pages/readIndexHtml` | Read index HTML |
| POST | `/template/initializeData` | Initialize site data |
| POST | `/ai_tools/getCompanyInfo` | Register company info |
| POST | `/ai_tools/generateWebsite` | Generate website (SSE) |
| GET | `/message/list` | List messages |
| GET | `/site/status` | Check site status |
| GET | `/site/generateShareUrl` | Generate share URL |
| GET | `/site_publish/getConfig` | Get FTP config |
| POST | `/site_publish/updateFtpConfig` | Update FTP config |
| POST | `/site_publish/testFtpConnection` | Test FTP connection |
| POST | `/site_publish/publish` | Publish website |
| POST | `/site_publish/preparePublish` | Prepare publish |
| GET | `/site_publish/getServerInfo` | Get server info |
| GET | `/site_publish/getTaskStatus` | Get task status |
| POST | `/site_publish/cancelTask` | Cancel task |
| POST | `/material/upload` | Upload material |

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
| `logo` | No | Logo (use placeholder if not provided) |
| `style` | No | Visual style (including colors) |
| `other` | No | Other information |

**Important**: The API returns `400 "公司名称/网站名称不能为空"` if required fields are missing. When fields are not provided, store as `"未填写"` (not empty string).

**Logo placeholder** (when user has no logo):
```
https://via.placeholder.com/200x80/8B4513/FFFFFF?text=CompanyName
```

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

## Material Upload API

**Endpoint**: `POST /material/upload`

**Request form data**:

| Field | Required | Description |
|-------|----------|-------------|
| `file` | [OK] | File to upload (for non-logo files) |
| `logoFile` | [OK] | File to upload (for logo files only) |
| `source` | [OK] | File type: `guide_logo`, `openclaw_products`, `openclaw_news` |

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
