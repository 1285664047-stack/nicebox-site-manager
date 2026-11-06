---
name: page-code-validate
description: Draft and deterministically validate Nicebox page code changes without saving
metadata: {"clawdbot":{"emoji":"[EDIT]"}}
---

# 页面修改草稿与校验

本阶段由宿主 AI/WorkBuddy 在对话上下文中修改代码，Nicebox 只执行确定性校验。校验通过仍然没有保存、预览写入或发布。

## 流程

1. 按 `page_code_read.skill.md` 选定页面，读取 metadata 和 sections 定位目标区域；无论局部还是全页修改，校验前都必须再读取 full 完整原文。
2. sections 只用于取得 `target_selector`，不能单独作为 `before_html`。只修改目标区域；复杂跨区域任务才使用 `target_type=full`。
3. 在当前上下文基于完整原文生成完整 `after_html`，修改前排除共享 Header/Footer 和系统保护节点。业务样式优先使用 Tailwind class，不创建本地草稿文件。
   响应式只按 `< 768px` 手机端无前缀 class 与 `>= 768px` 电脑端 `md:*` 两档处理。未指定终端时必须同时检查两端；指定单端时必须验证另一端最终渲染语义不变。
4. 新图片先调用 `nicebox_upload_images`。工具成功并返回非空 `image_url` 后即视为上传和登记完成，把地址原样写入草稿；不得再下载、探测 CDN、验证 Referer/防盗链、查询素材列表或重复上传。随后直接继续正常页面校验和预览。
5. 生成完整 `after_html` 后，先按 `../references/page-edit-library/workflows/page-edit-review.md` 在内部 Review 当前差异。只审查用户最新要求、当前 `target_selector`、必要依赖和本次 diff；目标外既有问题、历史草稿和旧待办不进入 Review。发现本次差异内问题时修正后重新 Review。
6. Review 通过后调用 `nicebox_validate_page_change`。传入读取时的页面版本、Hash 和规则版本，不得用预览 HTML 作为 `before_html`。
7. 校验失败时先按当前 `target_selector` 和本次 diff 过滤结构化 errors/warnings。只修复和说明目标内问题；目标外既有问题不展示、不修复。若目标外问题导致整页校验被拒绝，只说明其阻止当前校验且本次不会修改无关区域。校验通过时说明“尚未保存”。
8. 用户只要求校验时到此停止；用户要求实际修改页面时，校验通过后才增量读取 `page_change_workflow.skill.md`，继续创建预览并显示“确定保存 / 继续修改 / 回退到本次修改前的版本”。

## 参数来源

- `expected_version` 使用本次读取返回的 `content_version`。
- `expected_hash` 使用本次读取返回的 `content_hash`。
- `rules_version` 使用 full 读取结果中的 `rules_version`。
- `before_html` 原样使用 full 读取结果中的 `html`。
- `after_html` 是基于完整原文只修改目标范围后的完整文档。

不得猜测参数名，不得把 `content_version/content_hash` 直接作为校验工具的参数名。

同一次修改只读取一次 metadata、一次 sections 和一次 full，只有 `VERSION_CONFLICT` 才重新读取。正常仅向用户反馈“读取定位、草稿校验、预览确认”三个阶段，不展示规则文件读取、字段探测、哈希比对、无关区域诊断、历史草稿待办或内部命令。

## 宽度专用流程

页面宽度不能通过 after_html 修改。先读取 `nicebox_get_page_width_settings`，取得用户确认的桌面端/移动端宽度后调用 `nicebox_preview_page_width_settings`。该工具也只生成预览数据，不保存。

## 强制规则

- 不修改 `tailwind.config`、全站主题、全站字体、`systemDefaultStyle260918` 或 `disableJumpScript`。
- 不直接编辑 `contentWidthSettings` 或 `contentMobileWidthSettings`。
- 非必要不新增 `<style>`、行内 `style` 或外部 CSS；确需局部 CSS 时提供原因和范围，禁止全局标签或通配选择器。
- 不删除动态组件必需的 `data-type` 链路，不把具体产品/文章预览数据固化到模板。
- 不新增危险脚本、危险 URL、外部表单提交或未知外部脚本。
- 单独修改电脑端时不得改变手机端基础 class、专属结构或交互；单独修改手机端时必须用必要的 `md:*` 覆盖锁定原电脑端结果，不得改变电脑端专属结构或交互。无法隔离时停止，不创建可保存预览。
- 图片上传成功响应是唯一的图片导入成功依据。CDN 对无 Referer 请求返回 403 不属于页面修改失败；不得添加图片可访问性或登记状态二次验证。
- 本阶段不调用页面保存、页面预览写入、回退或发布工具。

详细规则见 `../references/page-code-validation-rules.md`，提示词见 `../prompts/page-edit-draft.md`。
