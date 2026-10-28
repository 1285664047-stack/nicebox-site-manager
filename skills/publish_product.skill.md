---
name: publish-product
description: Create a product draft, show its preview, and publish the saved draft after confirmation
metadata: {"clawdbot":{"emoji":"[PRODUCT]","requires":{"file":["scripts/config.json"]}}}
---

# 添加和发布产品

优先调用 MCP 工具；MCP 不可用时才运行 `publish_product.py`。

## 发布边界

发布产品只把指定 `product_id` 的草稿状态改为显示。不得检查 FTP、站点域名或整站发布状态，不得调用任何 FTP/站点发布工具，也不得把结果说成“网站已发布”。已有 `product_id` 时直接沿用该 ID；不要重新创建产品。

## 固定流程

1. 检查站点连接，收集名称、正文、价格、币种、简介、参数、语言和分类。
2. 不得虚构价格、型号、库存、规格、认证或功效。
3. 分类 ID 必须来自分类查询结果。
4. 没有产品图片时停下来询问：提供/上传可访问的图片 URL，还是 AI 生成封面。
5. 用户选择 AI 后必须继续询问比例：`1:1`、`4:3`、`3:2`、`16:9`、`2:3`、`3:4` 或 `9:16`，不得替用户默认选择。
6. MCP 调用 `nicebox_generate_content_cover` 时传 `aspect_ratio`；展示候选图并得到接受后，调用 `nicebox_upload_images(purpose=product_cover)` 导入 `s_products`，只把返回的稳定 `image_url` 作为产品图片。API 回退使用 `--ai-cover --cover-ratio 比例`，脚本会自动完成导入。
   - 返回 `COVER_NOT_GENERATED`/HTTP 422 表示本次没有生成合适图片，不要描述成系统崩溃；提示用户选择重试、上传图片或提供可访问 URL。
   - 上传返回 `IMAGE_UPLOAD_FAILED` 时保留已经生成的产品资料，待服务恢复后只重试上传与保存草稿。
7. 无论用户要求草稿、直接发布还是“发布一个新的产品”，都先调用 `nicebox_create_product_draft`。最初的“发布”指令只表示创建意图，不是正式发布确认。
8. 取得 `product_id` 后调用 `nicebox_generate_content_preview`，展示包含 `id` 和 `prodId` 的完整预览地址。
9. 展示预览地址后必须停下来询问是否正式发布。只有用户在看到本次预览后再次明确确认，才能按该 `product_id` 调用 `nicebox_publish_product`；不得复用最初的发布要求、生成确认或历史确认，不得重新创建产品。
10. 用户暂不发布时保留草稿。
11. 预览失败或预览地址尚未展示时只能保留草稿并重试同一 `product_id` 的预览，绝不能调用 `nicebox_publish_product`。

## API 回退

```bash
python3 {baseDir}/scripts/publish_product.py \
  --name "产品名称" \
  --price 2999 \
  --content-file "product.html" \
  --images "https://example.com/product.jpg" \
  --category-id 1
```

AI 生成封面：

```bash
python3 {baseDir}/scripts/publish_product.py \
  --name "产品名称" \
  --price 2999 \
  --content-file "product.html" \
  --ai-cover \
  --cover-ratio "1:1"
```

用户看过预览并确认后正式发布：

```bash
python3 {baseDir}/scripts/publish_product.py --publish-saved 123 --confirmed
```

旧命令中的 `--status publish` 仅为参数兼容，不再跳过草稿和预览。
