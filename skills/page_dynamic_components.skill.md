# 动态组件与复杂页面修改

本流程只处理产品、文章、FAQ、分类、搜索、分页、详情模板或表单的页面结构、展示配置和样式修改，不处理业务记录。已有文章内容修改转入 `edit_article.skill.md`，已有产品内容修改转入 `edit_product.skill.md`，已有独立 FAQ 内容修改转入 `edit_faq.skill.md`。不得把业务记录修改分流到页面诊断或创建新草稿。确认属于页面模板修改后，必须先调用 `nicebox_diagnose_page_components`，并始终传入当前目标的精确 `target_selector`。Legacy 普通接口等价命令仅供内部执行：

```bash
python scripts/api_tool.py nicebox_diagnose_page_components --args-json '{"page_id":123,"target_selector":"#target"}'
```

## 诊断结果

- 先按 `target_selector` 和当前任务过滤诊断结果。只处理目标区域本身及其必要依赖；其他区域的 `errors/warnings/components/scripts` 属于旁路信息，不展示、不修复、不写入草稿摘要。
- `errors`：仅当前目标或其必要依赖中的错误必须修复后才能校验草稿，不能删除动态字段来规避。其他区域的既有错误不能阻止本次无关修改；若服务端因此拒绝校验，只提示“存在目标范围外的既有校验问题，当前修改未保存”，不得展开无关问题详情或顺手修复。
- `components`：只展示当前目标组件的类型、选择器、模板项数量和有效性。
- `scripts[].ownership=local`：仅当属于当前目标区域时才可随区域修改。
- `shared`：同时服务多个区域，提供上下文但原样保留。
- `unknown`：无法可靠确认归属，原样保留。
- `other`：明确属于其他区域，不纳入当前修改。

## 组件硬规则

- 产品：`products -> product -> link + img + name/title`，单项只能有一个链接，不能写死产品 ID。
- 文章：`newslist -> news -> link + title`；图片卡片保留 `img`，纯文字紧凑列表允许无图，并保留已有日期、摘要和分页结构。
- FAQ：`faq -> faq-item -> question + answer`，保留展开收起交互。
- 分类导航只支持对应特殊列表页：产品页必须为 `page_type=list + element_type=product_list`，使用 `category-list[data-category=product] -> category-item[itemid]` 和 `pgid`；文章页必须为 `page_type=list + element_type=news_list`，使用 `data-category=news` 和 `gid`。必须先读取 metadata 确认页面身份，普通页、首页、详情页、FAQ 页及类型不匹配页面禁止新增；FAQ 分类导航暂不支持。
- 每个特殊列表页只保留一个同类型分类导航。保留根节点 `data-type/data-category/data-typeid`、分类项 `data-type/data-typeid/itemid`、系统链接及已有 `data-section-type`。分类名称、ID、链接、数量、排序、层级、箭头和选中态会动态重建，只能修改根容器和首个模板项的布局样式。
- 平铺模式保留首个分类项作为克隆原型；树形模式额外保留 `div.category-item`、`.category-list-style-shu`、`.next-child`、`.all-category` 和 `toggleSubmenuStyleShu()`。不得仅凭 class 切换依赖数据库 `style_id` 的模式。
- 搜索：保留合法 `data-config`、`search-input`、`search-btn`；multi 模式必须有 `search-select`，不能用 form 包裹或新增搜索 JS。
- 表单：`data-type=form` 只能在 form 标签；内部必须有 `data-type=title` 的非空标题、至少一个带 `data-itemid/date-element` 的 `form-item`，控件必须有唯一 name，并且只能有一个 `type=submit data-type=submit data-href=form-submit` 按钮。新增表单不自行生成 `data-sign`，已有表单必须原样保留 `data-sign`，不新增表单 JS。
- 产品详情：读取规则库中的正式字段，保留 `product_detail` 根节点以及已有的 `cover/thumbnail/thumbnail-item/title/categoryname/price/description/content/parameters` 和附件链路。允许多个顶层兄弟 `product_detail` 区域，禁止相互嵌套。
- 文章详情：保留第一个 `news_detail` 根节点内已有的 `title/publish/author/source_container/source/views/cover/description/content`。当前后端只填充第一个根节点，不得把标题和正文拆成多个顶层 `news_detail` 区域。
- 详情正文和参数是运行时富文本槽位，FAQ 会由后端追加；不能把某条预览数据、内容 ID 或预览地址固化进模板。关联列表必须留在 `content` 外并继续使用标准产品/文章列表链路。
- `data-config` 必须设置在实际被配置的动态列表元素自身：产品为 `[data-type="products"]`，文章为 `[data-type="newslist"]`，FAQ 为 `[data-type="faq"]`。旧 `faqlist` 只兼容读取，新增统一使用 `faq`；不得把配置写到外层普通容器、目标 selector 根节点或读取片段根节点。
- 修改 `limit/showpage/category_id` 时先定位唯一目标动态列表，只合并更新该元素自身的 `data-config` 并保留未知字段。存在多个候选且用户未指明时必须让用户选择。
- 禁止动态列表根节点嵌套：`products`、`newslist`、`faq/faqlist` 不得嵌套同类列表，不同类型的独立动态列表也不得彼此包裹；多个列表使用顶层兄弟区域。

表单确认保存时服务端扫描完整页面表单，提取标题、字段、按钮和验证规则，按 `data-sign` 创建或更新 `forms`，并把新签名回填页面 HTML。草稿与临时预览不创建表单。组件草稿通过后仍执行 `validate -> preview -> 用户确认 -> commit`，保存不等于发布；保存后以服务端最终页面版本为准。

分类准入失败时不生成代码或预览，直接使用规则库中的“不支持页面 / 类型不匹配 / FAQ 分类不支持”提示。用户要求改真实分类名称、链接、数量、顺序或层级时，改走分类管理能力；不得通过页面模板修改伪装完成。
