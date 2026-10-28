---
name: mcp-tools
description: Prefer Nicebox MCP tools and use local OpenClaw API scripts only as fallback
metadata: {"clawdbot":{"emoji":"[MCP]"}}
---

# MCP 优先、普通 API 回退

## MCP Server 连接

- Transport：Streamable HTTP
- URL：`https://aidev.nicebox.cn/mcp`
- Authentication：`Authorization: Bearer <API_KEY>`
- API Key 从 `{baseDir}/scripts/config.json` 的 `api_key` 读取，不得输出给用户或写入日志。
- 宿主没有发现 `nicebox_*` 工具时，先使用技能依赖中声明的上述端点注册或连接；不要询问用户提供 MCP Server 地址。
- 只有默认端点连接失败且宿主无法使用 REST API 回退，或用户明确要求自定义端点时，才向用户询问其他地址。

## 调用优先级

1. 宿主存在对应 `nicebox_*` MCP 工具时，优先调用 MCP。
2. MCP 工具不存在、MCP Server 不可达或宿主不支持 MCP 时，才运行 `scripts/` 中对应 Python 脚本，通过普通 OpenClaw REST API 完成同一操作。
3. MCP 返回业务错误（参数错误、没有权限、没有可优化项、用户未确认）时，不得为了绕过校验而回退 REST API。
4. 回退前向用户简要说明连接器工具暂不可用，将使用同一账号 API Key 调用 Nicebox API；不得显示 API Key。
5. MCP 与 API 的成功标准相同：只有结构化结果明确成功，才能告诉用户成功。

## 能力映射

完整的 46 项机器可检查映射位于 `scripts/fallback_manifest.json`；发布前运行
`python scripts/audit_fallback_parity.py`，任何新增 MCP 工具没有普通 API 回退时检查都会失败。

| 能力组 | MCP 工具 | 普通 API 回退 |
| --- | --- | --- |
| 站点状态、来源、语言、首页验证 | `nicebox_get_site_status`、`nicebox_get_site_source`、`nicebox_list_languages`、`nicebox_verify_homepage` | `api_tool.py TOOL` |
| SEO/GEO 报告、检测、报告优化、无报告优化、状态 | 9 个 `nicebox_*seo_geo*` / `nicebox_*direct_optimization*` 工具 | `seo_geo.py latest/report/optimizable/direct-plan/start-detect/detect-status/start-optimize/start-direct-optimize/optimize-status` |
| 文章/产品分类查询和创建 | 4 个 category 工具 | `api_tool.py TOOL --args-json JSON` |
| 文章/产品列表和搜索 | 4 个 list/search 工具 | `list_content.py article|product`，搜索增加 `--id` 或 `--keyword` |
| 文章/产品排序和永久删除 | 4 个 update/delete 工具 | `update_content_sort.py`、`delete_content.py`；必须携带快照和 `--confirmed` |
| 文章/产品正文生成 | `nicebox_generate_article_content`、`nicebox_generate_product_content` | `api_tool.py TOOL --args-json JSON` |
| 封面、Logo 和云资源库 | `nicebox_generate_content_cover`、`nicebox_generate_logo`、`nicebox_upload_images` | `api_tool.py nicebox_generate_content_cover`、`generate_logo.py`、`upload_image.py` |
| 草稿、内容预览和正式显示 | 6 个 article/product draft/publish/preview 工具 | `publish_article.py`、`publish_product.py`；草稿后自动预览，确认后才正式显示 |
| 留言和整站预览 | `nicebox_list_messages`、`nicebox_generate_preview` | `api_tool.py TOOL --args-json JSON` |
| FTP 配置、测试、准备、上传、状态和取消 | 6 个 FTP/publish 工具 | `ftp_manager.py get-config/test-connection/prepare/start/get-task-status/cancel-task` |
| 初始化和企业资料 | `nicebox_initialize_site`、`nicebox_save_company_info` | `initialize_site.py`、`api_tool.py nicebox_save_company_info` |
| 整站生成和进度 | `nicebox_start_website_generation`、`nicebox_get_website_generation_status` | `python -u _full_gen.py` 前台 SSE 流程，持续显示进度并返回最终结果 |

`api_tool.py` 的 `--args-json` 使用与对应 MCP 工具相同的字段。例如：
`python api_tool.py nicebox_get_site_source`，或
`python api_tool.py nicebox_create_article_category --args-json '{"name":"新闻","parent_id":0}'`。

状态查询、检测和优化重试必须继续使用原 `operation_id` 或 `request_id`，不得因为切换通道重复创建任务。

发布意图必须按对象分流：带 `article_id` 的发布只调用 `nicebox_publish_article`，带 `product_id` 的发布只调用 `nicebox_publish_product`；它们仅改变内容显示状态，不得检查或调用 FTP。只有用户明确要求发布整个网站/站点上线/FTP 发布时才使用站点发布工具。

生成文章或产品封面前，先让用户选择图片比例，再向 `nicebox_generate_content_cover` 传 `aspect_ratio`；不得静默使用默认比例。文章封面、产品封面和 Logo 均支持 `3:2`、`4:3`、`3:4`、`2:3`。网站 Logo 缺失时提示用户选择提供 URL、AI 生成或暂不设置；选择 AI 后让用户选择比例并调用 `nicebox_generate_logo`。候选图被用户接受后必须调用 `nicebox_upload_images`：Logo 用 `logo`，产品封面用 `product_cover`，文章封面用 `article_cover`，其他图片用 `image`；图片 URL 放入 `image_urls` 数组，用户指定 `folder_name` 时使用自定义目录。只把上传返回的稳定 `image_url` 写入业务数据。

## 网站生成进度

`nicebox_start_website_generation` 返回 `operation_id` 只表示任务已受理。随后每 15-30 秒调用一次
`nicebox_get_website_generation_status`，向用户展示 `status`、`progress`、`elapsed_seconds` 和 `message`。
`progress_estimated=true` 表示百分比是等待时间估算，只提供进度感知；只有 `status=succeeded` 且首页验证通过才算真正完成。
不得频繁轮询，也不得因等待较久重复启动生成任务。

调用 `nicebox_start_website_generation` 时，`requirement` 必须包含完整的导航与 section 映射约束：一级导航使用 `data-type="nav"`，英文锚点去掉 `#` 后与首页对应 `section id` 完全相同；产品区/项使用 `products`/`product`，新闻区/项使用 `newslist`/`news`。不能只传公司资料或“生成完整网站”，否则后端可能只创建内页记录而无法截取内页正文。
