---
name: mcp-tools
description: Select registered tools, temporary direct access, or equivalent API fallback without exposing transport details
metadata: {"clawdbot":{"emoji":"[MCP]"}}
---

# 内部通信选择与静默回退

> 本文件是内部执行规范。不得把其中的协议、地址、工具名、脚本名、命令、能力映射或故障切换过程输出给用户。

不得在普通业务结果中生成“MCP 执行链路”、Transport、端点、工具调用顺序或校验统计。仅当用户明确要求调试 MCP 调用链路时，才说明其明确询问的部分。

## 连接配置

- Transport：Streamable HTTP
- 主、备用服务地址只从机器配置读取，不在 Skill 文本或用户回复中展示。
- Authentication：`Authorization: Bearer <API_KEY>`
- API Key 从 `{baseDir}/scripts/config.json` 的 `api_key` 读取，不得输出给用户或写入日志。
- 新 API Key 或新连接始终先用主 URL 完成 initialize 和 `nicebox_get_site_status` 校验。只有 DNS/TLS/超时、Transport 初始化失败或 HTTP 5xx 才尝试备用 URL；401/403、无权限、业务校验或参数错误不切换。
- 通道成功后固定为当前 Key 本次连接的专属通道。换 Key、断开重连或当前通道确实不可用时才重新从主 URL 探测；不得明文保存 Key 与通道映射。
- 宿主只支持单 URL 时默认注册主 URL；主 URL 不可用后使用同一 Key 重连备用 URL。禁止同时注册两个包含同名 `nicebox_*` 工具的 Server。
- 写操作结果未知时保留原通道和原任务标识先查状态，不得跨通道重复提交。

## 调用优先级

1. 宿主存在对应 `nicebox_*` MCP 工具时，优先调用 MCP。
2. 对应工具未注册时，运行 `scripts/mcp_direct_client.py call --tool TOOL --args-json JSON` 临时直连。客户端从现有配置读取 API Key，自动初始化并短期复用会话；不得把 API Key 放入命令参数、输出或日志。
3. 临时客户端仅在返回 `allow_api_fallback=true` 时，才运行 `scripts/` 中对应 Python 脚本，通过普通 OpenClaw REST API 完成同一操作。认证、权限、参数、确认缺失、没有可优化项及其他业务错误不得回退。
4. 已注册 MCP 或临时直连返回业务错误时，不得为了绕过校验而回退 REST API。
5. 三种内部方式的选择和切换必须静默执行。不得告知用户工具未注册、正在临时连接、正在切换通道或正在改用普通接口；成功时只展示业务结果。
6. 三种方式的成功标准相同：只有结构化结果明确成功，才能告诉用户成功。

### 临时直连约束

- 仅当宿主没有注册对应工具时使用；已注册工具不可达时也可使用，但写操作结果不明确时必须先查询原操作状态，不能直接重提。
- 服务地址和超时只从 `scripts/mcp_connection.json` 或机器环境变量读取，不接受用户输入的任意地址。
- 临时文件只允许保存会话 ID、选中通道、协议版本、创建时间和不可逆 API Key 指纹，禁止保存明文 API Key。
- 更换 API Key、临时会话过期或服务端会话失效后自动重新初始化。认证失败不得尝试备用通道或普通 API。
- 只有 DNS、TLS、超时、协议初始化失败或 HTTP 5xx 等连接问题允许切换备用通道；业务错误不切换。
- 命令退出码 `0` 表示取得结构化结果；`2` 表示连接层失败且允许普通 API 回退；`3` 或 `4` 表示不得回退，必须按返回的业务提示处理。

若三种内部方式都失败，仅输出与用户行动有关的业务提示，不输出内部诊断。认证失效提示重新连接；暂时不可达提示稍后重试；不支持的能力提示更新连接器。禁止输出服务地址、接口路径、工具名、脚本名、命令、请求头、状态码或堆栈。

## 能力映射

完整的 77 项机器可检查映射位于 `scripts/fallback_manifest.json`；发布前运行
`python scripts/audit_fallback_parity.py`，任何新增 MCP 工具没有普通 API 回退时检查都会失败。

| 能力组 | MCP 工具 | 普通 API 回退 |
| --- | --- | --- |
| 版本、站点状态、来源、语言、首页验证 | `nicebox_get_release_info`、`nicebox_get_site_status`、`nicebox_get_site_source`、`nicebox_list_languages`、`nicebox_verify_homepage` | `api_tool.py TOOL` |
| 页面代码只读能力 | `nicebox_list_pages`、`nicebox_get_page_metadata`、`nicebox_get_page_sections`、`nicebox_get_page_code`、`nicebox_get_page_width_settings`、`nicebox_diagnose_page_components` | `api_tool.py TOOL --args-json JSON` |
| 页面草稿校验 | `nicebox_validate_page_change`、`nicebox_preview_page_width_settings` | `api_tool.py TOOL --args-json JSON` |
| 页面预览、保存与回退 | `nicebox_create_page_preview`、`nicebox_create_page_width_preview`、`nicebox_get_page_preview`、`nicebox_abandon_page_preview`、`nicebox_commit_page_change`、`nicebox_commit_page_width_settings`、`nicebox_get_page_change_operation`、`nicebox_list_page_backups`、`nicebox_preview_page_backup`、`nicebox_commit_page_backup` | `api_tool.py TOOL --args-json JSON` |
| SEO/GEO 报告、检测、报告优化、无报告优化、状态 | 9 个 `nicebox_*seo_geo*` / `nicebox_*direct_optimization*` 工具 | `seo_geo.py latest/report/optimizable/direct-plan/start-detect/detect-status/start-optimize/start-direct-optimize/optimize-status` |
| 文章/产品分类查询和创建 | 4 个 category 工具 | `api_tool.py TOOL --args-json JSON` |
| 文章/产品列表和搜索 | 4 个 list/search 工具 | `list_content.py article|product`，搜索增加 `--id` 或 `--keyword` |
| 文章/产品排序和永久删除 | 4 个 update/delete 工具 | `update_content_sort.py`、`delete_content.py`；必须携带快照和 `--confirmed` |
| 文章/产品正文生成 | `nicebox_generate_article_content`、`nicebox_generate_product_content` | `api_tool.py TOOL --args-json JSON` |
| 封面、Logo 和云资源库 | `nicebox_generate_content_cover`、`nicebox_generate_logo`、`nicebox_upload_images` | `api_tool.py nicebox_generate_content_cover`、`generate_logo.py`、`upload_image.py` |
| 共享 Header/Footer | `nicebox_get_shared_header/footer`、`nicebox_create/get/commit_shared_section*`、共享备份工具 | `api_tool.py` 同名工具 |
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

生成文章或产品封面前，先让用户选择图片比例，再向 `nicebox_generate_content_cover` 传 `aspect_ratio`；不得静默使用默认比例。文章封面、产品封面和 Logo 均支持 `3:2`、`4:3`、`3:4`、`2:3`。网站 Logo 缺失时提示用户选择提供 URL、AI 生成或暂不设置；选择 AI 后让用户选择比例并调用 `nicebox_generate_logo`。候选图被用户接受后必须调用 `nicebox_upload_images`：Logo 用 `logo`，产品封面用 `product_cover`，文章封面用 `article_cover`，其他图片用 `image`；图片 URL 放入 `image_urls` 数组，用户指定 `folder_name` 时使用自定义目录。上传成功后只把返回的 `image_url` 原样写入业务数据，并立即继续草稿或预览流程；禁止对回调 URL 做 CDN 下载、可访问性、Referer、防盗链、时间戳、素材列表或登记状态二次验证，也不得重复上传。

## 网站生成进度

`nicebox_start_website_generation` 返回 `operation_id` 只表示任务已受理。随后每 15-30 秒调用一次
`nicebox_get_website_generation_status`，向用户展示 `status`、`progress`、`elapsed_seconds` 和 `message`。
`progress_estimated=true` 表示百分比是等待时间估算，只提供进度感知；只有 `status=succeeded` 且首页验证通过才算真正完成。
不得频繁轮询，也不得因等待较久重复启动生成任务。

调用 `nicebox_start_website_generation` 时，`requirement` 必须包含完整的导航与 section 映射约束：一级导航使用 `data-type="nav"`，英文锚点去掉 `#` 后与首页对应 `section id` 完全相同；产品区/项使用 `products`/`product`，新闻区/项使用 `newslist`/`news`。不能只传公司资料或“生成完整网站”，否则后端可能只创建内页记录而无法截取内页正文。
