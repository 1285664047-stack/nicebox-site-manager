---
name: manage-pages
description: Query and manage existing pages without editing page HTML
metadata: {"clawdbot":{"emoji":"[PAGE]"}}
---

# 页面管理

本流程只处理现有页面的列表、筛选、排序、设置上级页面、复制、删除、显示隐藏、语言归属、文件名、页面名称和 TDK。页面正文或布局修改转入页面代码修改流程；新增页面转入新增页面流程。

## 定位

1. 使用 `nicebox_list_pages`：编号用 `id` 精确查询，名称用 `keyword` 模糊查询；可用 `locale`、`element_type`、`status` 筛选，每页20条。
2. 多条候选时只展示“编号、名称、语言、类型、文件名、状态、排序”让用户选择；唯一后复用页面编号。
3. 需要读取完整管理字段或能力限制时调用 `nicebox_get_page_management_detail`。外链页面不能修改文件名或 TDK。

## 无需二次确认

目标和新值明确后直接执行，不再询问确认：

- 排序：先读取管理详情取得最新同级顺序摘要，再调用 `nicebox_update_page_sort`；只调整同级位置，不改变父级。若同级顺序已变化，只刷新后重试，不要求用户重复确认。
- 设置上级页面：调用 `nicebox_update_page_parent`，固定参数为 `{"page_id":待移动页面编号,"parent_id":上级页面编号}`；设为顶级页面时传 `parent_id=0`。目标页面和上级页面名称都必须先定位到唯一编号；多条候选时只让用户选择，选择后直接执行，不再二次确认。
- 复制：`nicebox_copy_pages`，使用本次操作唯一的内部 `operation_id`；只复制明确页面，不递归复制子页面，不发布网站。超时重试必须复用同一个值，不能重复复制。
- 显示/隐藏：`nicebox_update_page_status`，同步共享导航，但不发布网站。
- 文件名：`nicebox_update_page_filename`，只允许字母、数字、下划线和横杠；冲突时提示更换。
- 页面名称和 TDK：`nicebox_update_page_settings`，参数固定为 `{"page_id":页面编号,"changes":{"page_name":"新名称"}}`；TDK 同样只能放在 `changes` 内，字段为 `seo_title`、`seo_keywords`、`seo_description`。只传用户要求修改的字段，未传字段保持不变；禁止猜测 `name`、`title`、`pageName`、`settings` 或 `fields` 等别名。

## AI 一键设置页面 TDK

1. 用户要求 AI 设置或生成页面标题、关键词、描述时，先定位唯一页面，再调用 `nicebox_generate_page_seo`。外链页面不支持。
2. 生成结果只是待保存草稿。展示标题、关键词和描述，并提供三个选择项：`确定保存`、`重新生成`、`取消`。不要提示 Token 消耗。
3. 用户选择 `确定保存` 后，调用 `nicebox_update_page_settings`，把本次返回的 `generated` 三个字段完整放入 `changes` 保存；不得重新生成或改写。
4. 用户选择 `重新生成` 时重新调用生成能力并替换待保存草稿；选择 `取消` 时不写入。
5. 只报告当前页面结果，不顺带检查或提示其他页面的 TDK。AI 生成和保存均不等于发布网站。

页面名称和文件名是两个独立操作。用户同时修改时，分别调用页面设置和文件名工具；页面名称成功必须以返回的 `changed_fields` 包含 `page_name` 且页面详情中的 `page_name` 已更新为准，不能因为文件名成功就推断名称成功。

不得为了统一流程给以上操作增加“是否确认”。缺少新位置、新状态或新值时，只补问缺失参数。

设置上级页面时不得通过重建页面、复制后删除、修改页面代码或手工修改共享导航实现。上级页面必须与目标页面语言一致；不能选择目标自身或其子孙页面，产品详情和新闻详情不能作为上级，移动后的整棵页面分支不能超过三级。服务端会同步更新全部后代层级并标记共享导航刷新。

## 删除，必须二次提醒

1. 调用 `nicebox_check_page_deletion`。
2. 展示将删除的页面及全部子孙页面、首页保护、详情模板关联内容和替代模板；不展示 `impact_hash`。
3. 等待用户明确确认。取消或目标改变时不写入。
4. 确认后把原 `impact_hash` 作为 `expected_impact_hash`，生成本次操作唯一的内部 `operation_id`，调用 `nicebox_delete_pages(confirmed=true)`；超时重试复用同一个值。
5. 返回影响已变化时重新检查、展示并确认，不能沿用旧确认。

## 更改语言，必须二次提醒

1. 调用 `nicebox_check_page_locale_change`。
2. 目标语言只需是系统支持的有效语言，无需预先存在于当前站点；不得要求用户先去后台启用或创建该语言页面。
3. 展示必须一起迁移的完整父子树、当前语言和目标语言，并明确说明页面名称、HTML、链接文本和 TDK不会自动翻译。
4. 用户实际要求“翻译”时转入翻译流程，不能用更改语言代替。
5. 明确确认后携带原 `impact_hash` 和本次操作唯一的内部 `operation_id` 调用 `nicebox_update_page_locale(confirmed=true)`；超时重试复用同一个值。迁移成功后站点语言列表由系统自动同步。
6. 影响变化时重新检查和确认。

## 结果

只报告页面业务结果和必要提醒。文件名变化提示重新发布后线上地址更新；所有页面管理保存均不得表述为网站已经发布。不要输出工具名、接口、Hash、参数或通信方式。
