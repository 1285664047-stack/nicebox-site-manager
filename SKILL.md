---
name: website-manager
description: Manage Nicebox AI websites, content drafts and previews, publishing, messages, and SEO/GEO workflows without exposing internal transport details.
version: 0.4.19
metadata: {"clawdbot":{"emoji":"[TOOL]","requires":{"file":["scripts/config.json"]}}}
---

# Website Manager

本入口只负责任务路由、全局安全边界和结果表达。每轮只加载当前任务所需的一个主流程；详细业务规则、参数和工具映射按需渐进读取。

## 内部执行策略

以下内容只用于内部执行，不得向用户解释或复述：

1. 优先使用宿主已注册的 Nicebox 能力。只有实际发现所需能力未注册时，才读取 [mcp_tools.skill.md](skills/mcp_tools.skill.md) 使用临时直连；仅连接层明确失败且写入未执行时，静默使用等价普通接口回退。
2. 参数错误、权限不足、确认缺失和业务校验失败不得通过换通道绕过。写入结果未知时查询原任务状态，禁止重复提交。
3. WorkBuddy 环境只使用连接器能力，不运行 Legacy 脚本；Legacy 宿主按专用工具映射回退。不得使用其他建站服务或自行生成本地 HTML 代替 Nicebox 建站。
4. 已知能力和参数时直接调用，不枚举工具、不搜索命令、不预读 API 参考。仅在开发审计、字段未知或故障定位时读取 [api_reference.skill.md](skills/api_reference.skill.md) 或 [troubleshooting.skill.md](skills/troubleshooting.skill.md)。
5. 每次使用时静默执行 24 小时缓存的版本检查；检查失败不得延迟或污染当前任务。仅 `notify=true` 时在业务结果后追加简短更新提醒。

## 最短执行原则

1. 每轮只处理用户最新消息中的当前任务和目标对象；无关诊断、旧草稿、历史待办和其他页面问题保持休眠。
2. 只加载下方命中的一个主流程。主流程明确要求且任务确实命中时，才增量加载一个专项规则。
3. 复用对话中仍有效的站点、对象 ID、版本、Hash、预览和任务状态；仅在缺失、变化、冲突或流程强制要求时重新读取。
4. 只保留下一步需要的结果字段；完整 HTML、正文、Schema 或 FAQ 仅在当前任务确需时进入上下文，不重复转述。
5. 参数校验失败最多按明确错误修正一次；同一已确认任务的只读步骤和状态轮询连续执行。
6. 一个确认覆盖同一参数快照；参数未变时不重复确认，不得省略专项流程规定的风险确认。

## 任务路由

只读取当前任务对应的主流程：

| 当前任务 | 主流程 |
| --- | --- |
| 新建、重新生成网站或生成进度 | [interactive_generate.skill.md](skills/interactive_generate.skill.md)；仅 Legacy 直接生成回退再读 [generate_website.skill.md](skills/generate_website.skill.md) |
| 新增文章 | [publish_article.skill.md](skills/publish_article.skill.md) |
| 修改已有文章 | [edit_article.skill.md](skills/edit_article.skill.md) |
| 新增产品 | [publish_product.skill.md](skills/publish_product.skill.md) |
| 内容列表、搜索、排序或删除 | [list_content.skill.md](skills/list_content.skill.md) |
| 分类、语言、留言或站点状态 | [list_categories.skill.md](skills/list_categories.skill.md)、[list_languages.skill.md](skills/list_languages.skill.md)、[list_messages.skill.md](skills/list_messages.skill.md) 或 [site_status.skill.md](skills/site_status.skill.md) 中命中的一个 |
| 页面代码读取或分析 | [page_code_read.skill.md](skills/page_code_read.skill.md) |
| 页面代码修改和校验 | [page_code_validate.skill.md](skills/page_code_validate.skill.md) |
| 页面预览、连续修改、保存或回退 | [page_change_workflow.skill.md](skills/page_change_workflow.skill.md) |
| 动态组件、表单、分类组件或局部 JS | [page_dynamic_components.skill.md](skills/page_dynamic_components.skill.md) |
| 共享 Header/Footer | [shared_sections.skill.md](skills/shared_sections.skill.md) |
| SEO/GEO 报告、检测或优化 | [seo_geo.skill.md](skills/seo_geo.skill.md) |
| 整站发布 | [ftp_publish.skill.md](skills/ftp_publish.skill.md) |
| 分享预览或上传图片 | [generate_share_url.skill.md](skills/generate_share_url.skill.md) 或 [upload_image.skill.md](skills/upload_image.skill.md) |
| 设置连接 | [set_key.skill.md](skills/set_key.skill.md) |

页面修改时先读取 `prompts/page-edit-draft.md`，再按任务从 `references/page-edit-library/manifest.json` 只加载命中的模块；完成草稿后读取 `workflows/page-edit-review.md`，Review 只覆盖当前目标和本次差异，不得一次加载整个规则库。

## 全局业务边界

- 用户更换 Key、重新连接或切换站点后，废弃旧站点和任务上下文；下一次写操作前重新确认实际站点。
- 高风险操作必须展示真实影响并等待确认，不得替用户确认。已有确认只对参数未变化的同一阶段有效。
- 新文章/产品无论用户要求草稿还是直接发布，都先创建草稿并展示预览；只有用户看到本次预览后再次确认，才把该内容设为显示。内容发布不等于整站发布。
- 已有文章按文章修改流程处理；已有产品和独立 FAQ 内容暂不支持修改。页面模板的布局、样式、数量和分页不属于业务内容修改。
- 初始化、重新生成、页面保存/回退、共享头尾、检测、优化和整站发布的顺序及确认文案以对应主流程为准，不得合并跨风险阶段确认。
- 未保存页面预览上的后续修改继续叠加；每次预览提供“确定保存 / 继续修改 / 回退到本次修改前的版本”。
- 页面修改只处理当前目标和必要依赖，不检查或修复用户未要求的其他区域。
- 图片上传成功并返回非空地址后直接用于业务数据和预览，不再检查 CDN、Referer、防盗链、素材登记或可访问性，不重复上传。
- 响应式默认只使用手机端 `< 768px` 无前缀 class 与电脑端 `>= 768px` 的 `md:*`；只改一端时不得改变另一端最终效果。

## 对话与输出边界

- 只补问会阻止当前任务的必要信息，不虚构企业资料、价格、联系方式、资质、产品参数或用户确认。
- 不展示协议、服务地址、工具名、脚本、命令、凭据、内部 ID、Hash、原始参数、状态枚举、错误码、执行链路、诊断过程或校验统计。
- 文章/产品编号等用于用户查询、选择、排序或删除的业务编号可以展示。只有用户明确要求代码、属性、参数或实现原理时，才展示与当前问题直接相关的技术内容。
- 长任务只反馈用户可理解的业务阶段、等待时间和进度，不播报内部轮询、读取、重试或回退。
- 最终回复只给业务结果、实际变化、预览/访问地址、保存/发布状态和必要下一步。普通结果用一句状态和 1 至 3 条变化，不主动增加技术细节。
- 认证失效提示重新连接；暂时不可达提示稍后重试；写入结果未知时先查询同一任务状态。

## 配置约束

- 连接配置从 `scripts/config.json` 读取；不得硬编码地址或向用户展示凭据。
- 安装或设置连接时记录安装时间和版本；版本检查不阻止正常业务。
- 详细 AI 确认规则仅在流程出现确认歧义时读取 [ai_rules.skill.md](skills/ai_rules.skill.md)，普通任务不得预读。
