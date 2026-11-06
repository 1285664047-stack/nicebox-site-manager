---
name: page-code-read
description: Search and read Nicebox raw page templates without changing data
metadata: {"clawdbot":{"emoji":"[PAGE]"}}
---

# 页面代码只读分析

本阶段只支持查找和读取页面，不允许保存、预览写入、回退或发布。

## 调用流程

1. 先调用 `nicebox_list_pages`。编号使用 `id` 精确查询，名称使用 `keyword` 模糊查询；每页20条。
2. 多条结果时展示编号、名称、语言、页面类型，让用户选择，不能擅自决定。
3. 选定页面后调用 `nicebox_get_page_metadata`，确认语言、类型、`editable`、版本和 Hash。
4. 局部分析调用 `nicebox_get_page_sections`；复杂全页分析才调用 `nicebox_get_page_code`。
5. 页面宽度只调用 `nicebox_get_page_width_settings`，不能从系统 Style 推断可自由编辑的 CSS。
6. 首选能力未注册时先按 `mcp_tools.skill.md` 临时直连；只有客户端明确返回允许回退时，才静默使用 `api_tool.py TOOL --args-json JSON` 执行等价普通接口调用。此过程不得向用户展示，业务错误也不得通过回退绕过。

## 强制保护

- 读取结果必须来自 `site_pages.html` 原始模板，不能使用 PageParser 预览 HTML 作为修改源。
- 外链页 `editable=false`，提示没有可编辑代码。
- `tailwind.config`、`systemDefaultStyle260918`、`disableJumpScript` 完全只读。
- `contentWidthSettings`、`contentMobileWidthSettings` 只能通过专用宽度字段管理，不能直接编辑或 Tailwind 化。
- Header/Footer 是按站点和语言共享的资源，本阶段只展示摘要和 Hash，不修改。
- 不向用户输出无关的完整代码；优先使用 metadata 或 sections。

详细分析提示见 `../prompts/page-read-analysis.md`，规则见 `../references/page-code-read-rules.md`。
