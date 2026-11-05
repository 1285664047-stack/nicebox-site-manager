# 页面结构、样式与系统保护规则

修改页面代码时读取本文件。它只约束页面修改，不用于从零生成整站。

## 修改边界

- 代码由 WorkBuddy/当前宿主在对话上下文中修改；Nicebox MCP 或普通 API 只负责读取、诊断、校验、预览和保存。
- `sections` 只用于定位，提交校验的 `before_html` 必须是本次 `full` 返回的完整原文，`after_html` 必须是只替换目标范围后的完整文档。
- 只修改用户指定范围。保留未点名的标签层级、文本、属性、图片、链接、交互和响应式行为。
- 删除 `data-*` 属性不等于删除元素。仅删除指定属性，并保持修改前后的标签名称和顺序一致。
- 普通页面修改不得改共享 Header/Footer；共享头尾必须走专用流程。不能修改 `tailwind.config`、全站主题色、全站字体或站点级 `html_config`。

## Section 与容器

- 每个业务 `section` 保留或补充准确的 `data-section-type`。标题区域单独使用 `title`，内容区域使用实际类型；不要把标题与内容强行合并到一个 section。
- Header/Footer 不拆成标题区与内容区。常用类型包括 `banner`、`image_text`、`about`、`company_culture`、`develop_course`、`group_show`、`contact_us`、`common_problem`、`counter`、`param_table`、`option_switch`、`prod_list`、`news_list`、`product_detail`、`news_detail`、`message_form`。
- 内容宽度沿用 `max-header-container`、`max-content-container`、`max-footer-container`。桌面/移动宽度只能通过专用宽度工具修改，不能直接改写宽度 Style。

## 样式与响应式

- 优先使用现有 Tailwind CSS class。非必要不新增 `<style>`、行内 `style` 或外部 CSS。
- 如 Tailwind 无法合理表达且确有必要，新增样式必须限制在目标区域，说明原因和选择器，不得使用污染全站的标签级或通配选择器。
- 保留现有旧 CSS；不要顺手清理、格式化或改写与需求无关的样式。
- 页面修改默认只使用两个响应式范围：无前缀 class 表示 `< 768px` 手机端基础样式，`md:*` 表示 `>= 768px` 电脑端覆盖样式。除非用户明确要求保留既有断点，否则不得新增或依赖 `xs:`、`sm:`、`lg:`、`xl:`、`2xl:`、`3xl:` 等其他断点。
- 用户未限定终端时，每次新增或修改内容都必须同时设计并检查手机端和电脑端，确保两端的排列、宽度、间距、字号、图片比例、显示隐藏和交互均正常；不能只让当前预览端好看。
- 用户明确只修改电脑端时，只调整 `md:*` 规则或仅电脑端容器，保留无前缀手机端基础样式和手机端专属 DOM/交互不变，并检查 `< 768px` 的渲染语义未变化。
- 用户明确只修改手机端时，只调整无前缀基础规则或仅手机端容器；如果原有无前缀 class 同时作为电脑端基础值，必须保留或补齐对应 `md:*` 覆盖，使 `>= 768px` 的最终渲染语义不变。不得修改电脑端专属 DOM/交互。
- 单端修改不能仅凭 class 文本变化判断隔离成功，必须按最终级联结果检查另一端。无法安全隔离时停止生成可保存预览，并说明需要先拆分响应式 class 或终端专属容器。
- 保持现有页面的响应式语义，不要把生成阶段的严格布局偏好机械用于旧页面重构。
- 图片和视频保持 `object-cover` 等既有适配规则。修改图片容器背景不等于替换图片；只有用户明确要求并提供或生成新图片时才能更换 `src`。

## 不可修改的系统节点

以下节点内容、顺序和语义必须原样保护，不得格式化、替换或 Tailwind 化：

- `<script>` 中的 `tailwind.config`
- `<style id="systemDefaultStyle260918">`
- `<script id="disableJumpScript">`

以下节点不能删除或转换为 Tailwind，只能由专用宽度流程根据宽度字段受控重建：

- `<style id="contentWidthSettings">`
- `<style id="contentMobileWidthSettings">`

新增图片必须先使用上传图片能力进入当前账号云素材库。上传工具返回 `success=true` 且包含非空 `image_url` 后，即视为上传和登记成功；把回调中的 `image_url` 原样写入草稿，不修改协议、域名、路径、查询参数或编码。禁止本地路径、`blob:`、Base64、临时附件地址和短期签名地址。

上传成功后禁止再对回调 URL 执行 HEAD/GET、下载、curl、浏览器可访问性、状态码、Referer、防盗链、时间戳、素材列表、登记状态或重复上传验证。CDN 对无 Referer 请求返回 403 不代表图片无效。替换 HTML 后直接进入一次正常页面校验并创建预览，不增加图片专项验证步骤，也不因外部探测失败循环重试。
