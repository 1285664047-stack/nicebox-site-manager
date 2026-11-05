---
name: shared-sections
description: Safely preview, save and roll back shared Nicebox Header/Footer without publishing
metadata: {"clawdbot":{"emoji":"[SHARED]"}}
---

# 共享 Header/Footer 修改

共享头尾按站点和语言存储，修改会影响该语言的所有页面。它不能通过普通页面保存流程写入。

## 流程

1. 调用 `nicebox_get_site_status` 确认站点，再调用 `nicebox_get_shared_header(locale)` 或 `nicebox_get_shared_footer(locale)` 读取原始 HTML 和 `content_hash`。
2. 明确提示影响范围是“当前站点、当前语言的所有页面”。Header/Footer 的保存确认不能复用普通页面确认、历史确认或发布确认。
3. 在宿主上下文只修改目标共享区域。Header 保留 PC/移动容器、Logo、导航模板、`menu-toggle`、唯一 `mobile-menu` 和相关局部 JS；Footer 保留动态链接和 `.max-footer-container`。
4. 新图片先上传，只使用回调 `image_url`。不得修改全站主题、字体、`tailwind.config` 或系统宽度节点。
5. 调用 `nicebox_create_shared_section_preview`。必须向用户展示返回的全部 `preview_pages`，至少检查首页和普通内页（站点存在时）；此时尚未保存、尚未发布。
6. 用户针对本次共享预览明确确认后，用新的 `operation_id` 调用 `nicebox_commit_shared_section(confirmed=true)`。响应不明确时先查 `nicebox_get_shared_section_operation`，禁止重复写入或直接换通道。
7. 保存成功只说明“已保存并创建独立回退记录，尚未发布”。用户明确要求发布网站时重新进入 FTP 发布流程并重新确认。

## 回退

先调用 `nicebox_list_shared_section_backups`，选择后调用 `nicebox_preview_shared_section_backup`。展示全部样本预览并确认后调用 `nicebox_commit_shared_section_backup`。共享区域回退不会修改页面正文，也不会自动发布。

MCP 不可用时普通 API 使用相同工具名通过 `api_tool.py` 回退；写入状态不明确时仍必须先查询操作结果。
