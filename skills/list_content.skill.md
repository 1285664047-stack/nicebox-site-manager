---
name: list-content
description: List or fuzzy-search Nicebox articles and products with pagination and preview links
metadata: {"clawdbot":{"emoji":"[LIST]","requires":{"file":["scripts/config.json"]}}}
---

# 文章和产品列表/模糊搜索

优先使用 MCP：

- 文章列表：`nicebox_list_articles`
- 文章标题模糊搜索：`nicebox_search_articles`
- 产品列表：`nicebox_list_products`
- 产品名称模糊搜索：`nicebox_search_products`

MCP 不可用时使用同一 OpenClaw API 回退：

```bash
python3 {baseDir}/scripts/list_content.py article --page 1
python3 {baseDir}/scripts/list_content.py article --keyword "关键词" --page 1
python3 {baseDir}/scripts/list_content.py article --id 16817
python3 {baseDir}/scripts/list_content.py product --page 1
python3 {baseDir}/scripts/list_content.py product --keyword "关键词" --page 1
python3 {baseDir}/scripts/list_content.py product --id 12345
```

可追加 `--locale zh-CN` 或 `--category-id 123`。每页固定 20 条，不接受自定义页大小。

## 展示规则

结果必须按以下 Markdown 表格展示，列顺序不得调整：

```markdown
| 编号 | 名称 | 语言 | 分类 | 预览 | 排序 |
| ---: | --- | --- | --- | --- | ---: |
| 16817 | 示例 | 简体中文 | 新闻 | [点击预览](https://...) | 10 |
```

- `preview_url` 有值：显示 `[点击预览](preview_url)`，不要展示冗长裸链接。
- `编号` 必须使用返回记录的 `id`，即真实产品 ID 或文章 ID；不得使用 1、2、3 等页内行号代替。
- `preview_url` 为空：显示 `不可预览`，说明对应语言缺少详情页。
- 表格之后显示 `第 X/Y 页，共 N 条`。
- `has_next=true` 时提示用户可查看下一页；用户说“下一页”时沿用当前内容类型、关键词、语言和分类，只增加页码。
- 没有结果时明确提示未找到，不输出空表格。
- 列表和搜索都是只读操作，无需确认。

## 修改排序

1. 用户提供编号时按真实 ID 精确搜索；提供名称时进行模糊搜索。
2. 用六列表格展示候选，同时展示准备修改的新排序并说明“排序值越大展示越靠前”。
3. 只有一条时询问一次是否确认修改；用户确认后立即调用修改工具，不再追加确认。
4. 存在多条时提示：“请选择具体编号；选择后将直接修改为排序 N。”不得自行选择相似项。用户选择编号即视为本次确认，立即调用修改工具，不再重复展示或二次确认。
5. MCP 调用传 `confirmed=true`；REST 回退命令带 `--confirmed`。该参数表示用户刚刚完成了上述一次确认或候选选择，不能在没有用户回复时预填。
6. 修改成功后展示接口返回的 `previous_sort_order` 和 `sort_order`；相同则提示排序未发生变化。目标或新排序变化时重新执行一次确认。

```bash
python3 {baseDir}/scripts/update_content_sort.py article --id 16817 --current-sort-order 10 --sort-order 20 --confirmed
python3 {baseDir}/scripts/update_content_sort.py product --id 12345 --current-sort-order 10 --sort-order 20 --confirmed
```

## 删除文章/产品

1. 用户提供编号时按真实 ID 精确搜索；提供名称时模糊搜索。
2. 必须先展示六列候选表格，并明确警告：“确认或选择后将直接永久删除，删除后无法恢复”。
3. 只有一条时询问一次是否确认删除；用户确认后立即调用删除工具，不再追加确认。
4. 存在多条时提示：“请选择要删除的具体编号；选择后将直接永久删除。”不得自动选择。用户选择编号即视为本次确认，立即删除，不再重复展示或二次确认。
5. MCP 调用传 `confirmed=true`；REST 回退命令带 `--confirmed`。一次只删除一条，不批量删除。
6. 如果内容快照在确认期间变化，停止删除并重新查询；必须重新进行一次确认或选择。

REST 回退命令必须携带刚刚展示的完整快照和 `--confirmed`：

```bash
python3 {baseDir}/scripts/delete_content.py article --id 16817 --expected-name "示例文章" --expected-locale zh-CN --expected-category-id 12 --expected-sort-order 10 --confirmed
python3 {baseDir}/scripts/delete_content.py product --id 12345 --expected-name "示例产品" --expected-locale zh-CN --expected-category-id 15 --expected-sort-order 10 --confirmed
```
