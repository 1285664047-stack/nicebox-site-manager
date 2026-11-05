# 表单、搜索、链接与资源规则

## 表单

- 只有真实 `<form>` 标签可标记 `data-type="form"`，并必须包含当前页面唯一的 `data-itemid`，例如 `form-1`。
- 表单内部必须有一个非空标题并标记 `data-type="title"`。标题用于创建后台表单名称，不能只把标题放在 form 外部；否则后台提取时可能使用兜底名称或无法正确识别。
- 表单至少包含一个 `data-type="form-item"`。表单项容器必须有唯一 `data-itemid` 和正确的 `date-element`；其中的 `input`、`select` 或 `textarea` 必须有非空且在当前表单内唯一的 `name`。
- 常用字段标记：`label`、`input`、`text`、`radio`、`checkbox`、`date`、`select`、`option`、`textarea`、`file-upload`、`help-text`、`validation`、`hidden`。
- 每个表单必须且只能有一个提交按钮，并保留 `type="submit" data-type="submit" data-href="form-submit"`；重置按钮使用 `type="reset" data-type="reset" data-href="form-reset"`。
- 不新增表单提交 JS、外部 action 或自定义网络请求；系统运行时会接管提交。修改字段后检查 label、name、选项组和验证提示仍一一对应。

### data-sign 与保存生命周期

- 新增表单草稿时不要猜测或自行生成 `data-sign`。允许新表单只带 `data-type="form"` 和 `data-itemid`。
- 修改已有表单时必须原样保留其 `data-sign`。`data-sign` 是页面 HTML 与后台 `forms.unique_code` 的关联键，删除或改写会导致创建新表单、关联错位或历史留言脱离。
- 草稿校验和临时预览不会创建或更新后台表单。只有用户查看当前预览并明确确认保存后，服务端才执行：扫描完整页面 `<form>` → 提取标题、字段、按钮和验证规则 → 按 `data-sign` 创建或更新 `forms` → 为新表单生成唯一编码 → 把 `data-sign` 回填到最终页面 HTML。
- 保存成功后必须以服务端返回的最终页面版本为准，不继续使用保存前没有 `data-sign` 的草稿。不得让 WorkBuddy、MCP 客户端或普通 API 客户端自行写入 `forms` 表。
- 同一页面已有 `data-sign` 的表单按唯一编码更新，不重复创建；复制到其他页面时由服务端处理签名冲突并生成新签名。
- 删除某个表单后，保存时服务端同步清理该页面不再存在的表单定义；已有访客提交记录的表单按后台保留策略处理。删除页面全部表单也必须通过页面确认保存流程，不能只在对话里宣称已删除。
- 页面保存成功只代表表单定义与 HTML 已同步，尚未发布网站。访客正式填写后，数据才写入 `form_submissions`；预览提交会标记为预览数据。

新增表单最低结构：

```html
<form data-type="form" data-itemid="form-1">
  <h2 data-type="title">联系我们</h2>
  <div data-type="form-item" data-itemid="form-item-field-1" date-element="text">
    <label data-type="label" for="contact-name">姓名</label>
    <input id="contact-name" type="text" data-type="text" name="name">
  </div>
  <button type="submit" data-type="submit" data-href="form-submit">提交</button>
</form>
```

## 站内搜索

- 搜索根节点使用 `data-type="searchbox"`、唯一 `data-typeid` 和可解析的 `data-config` JSON。
- 输入框：`input[type="text"][data-type="search-input"]`，不设置 `name`。
- 按钮：`button[type="button"][data-type="search-btn"]`。多类型搜索可使用 `select[data-type="search-select"]`，option 下标与 `data-config.items` 顺序一致。
- 搜索框不得用 `<form>` 包裹，不添加 action/method/onsubmit，不新增搜索跳转 JS。
- `data-config` 的 `type` 只使用运行时支持的 `products` 或 `newslist`；页面 ID 和目标参数沿用系统返回值，不猜测。

## 链接占位符

- 保留系统占位链接及 `href`/`data-href` 配对，例如 `[PAGE_URL@...@PAGE_URL]`；不要提前转换为当前预览 URL 或线上绝对地址。
- 保留 `data-link-type`（如 `productCategory`）和运行时所需的页面/分类/内容标识。
- 新增内部链接时先通过页面或内容查询取得真实 ID，再按现有同类链接格式生成；不能猜测页面 ID。
- 禁止 `javascript:` 等危险协议、未知外部脚本链接和会绕过系统路由的 onclick 跳转。
- “查看更多”按钮继续使用组件规定的 `data-type="link"` 与 `data-href`，不能抢占单项卡片的整卡链接。

## 图片与二维码

- 新图片先调用图片上传能力。工具返回成功和非空 `image_url` 后直接使用该回调地址，不再检测 CDN 可访问性、Referer、防盗链或登记状态，也不重复上传。
- 可从 alt、title、data-description、周边文字或区块语义判断为二维码的现有图片，默认完整保留原始 `src`；只有用户明确要求修改二维码本身时才处理。
- 不能用 CSS 滤镜、遮罩或背景色假装修改位图像素。需要去底、重绘或生成图片时应走图片能力，再由用户确认替换。
