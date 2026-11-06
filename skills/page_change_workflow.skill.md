---
name: page-change-workflow
description: Preview, confirm, save and roll back Nicebox page changes safely
metadata: {"clawdbot":{"emoji":"[SAVE]"}}
---

# 页面预览、保存与回退

必须遵守“草稿校验 -> 临时预览 -> 用户查看 -> 当次确认 -> 保存”的顺序。保存页面不等于发布网站。

## 修改保存

1. 草稿通过 `nicebox_validate_page_change` 后调用 `nicebox_create_page_preview`，不能把校验成功当作保存成功。
2. 展示 `preview_url`、修改摘要、影响范围和服务端返回的 `expires_at`，并说明尚未保存、尚未发布。不得根据本地时间自行换算剩余分钟；会话恢复、用户询问当前预览或需要核对令牌状态时，调用 `nicebox_get_page_preview`，不能使用旧缓存猜测。
3. 用户继续修改同一页面时，调用 `nicebox_get_page_preview` 取得旧预览 `after_html`，以此为基础继续修改，并把旧令牌作为 `base_preview_token` 创建新预览。新预览自动取代旧预览，只保存最新合并版本。仅当用户明确要求放弃上次修改时才调用 `nicebox_abandon_page_preview`。
4. 每次预览后优先使用宿主原生结构化提问能力，显示“请选择下一步操作”和三个可点击单选项：确定保存、继续修改、回退到本次修改前的版本。原生能力可用时不得重复输出编号 Markdown 选项；宿主不支持时才使用文本回退。MCP 使用响应 `choices` 的 action，普通 API 回退必须提供相同语义。
5. 用户选择回退时调用 `nicebox_rollback_page_preview_step`，把 `reverted_change` 和 `remaining_changes` 转换成“本次已撤回”和“当前仍保留”的自然语言摘要，不显示原始字段名；恢复后的预览仍提供三个选项，不得让用户选择冲突版本。
6. 用户针对当前预览明确确认保存后，生成唯一 `operation_id` 并调用 `nicebox_commit_page_change(confirmed=true)`。
7. 成功后只提示页面已保存为新版本、已创建可回退记录且网站尚未发布；新版本号和 `backup_id` 保留在内部，不向用户展示。
8. MCP 写入超时或结果不明时，先用同一 operation_id 调用 `nicebox_get_page_change_operation`；禁止直接 API 重试。只有状态明确为未执行时才可回退普通 API。

## 宽度保存

使用 `nicebox_create_page_width_preview` 生成预览；用户查看并确认后调用 `nicebox_commit_page_width_settings`。不得通过 HTML 草稿修改系统宽度 Style。

## 页面回退

1. 调用 `nicebox_list_page_backups`，按时间倒序向用户展示“时间 + 修改摘要”，不展示原始版本号、来源代码和 `backup_id`；内部维护选项与真实编号的映射。
2. 用户选择对应的时间/摘要选项后，在内部使用绑定的 `backup_id` 调用 `nicebox_preview_page_backup`。回退预览保留当前共享头尾和系统节点，不会立即写库。
3. 展示预览并提醒“确认后会按新版本保存，不会发布网站”。
4. 用户明确确认后调用 `nicebox_commit_page_backup`。回退保存也会生成新的 backup_id。

## 强制边界

- 预览令牌过期、放弃、已提交或版本冲突时，重新读取页面，不能强制保存。
- 保存确认只对当前 preview_token、版本和操作有效，不能复用历史确认。
- 保存和发布必须分开确认；本阶段不自动调用整站发布。
- 重复写入使用同一 operation_id；目标或预览改变后必须生成新的 operation_id。
