---
name: upload-image
description: Upload images to the Nicebox cloud asset library
metadata: {"clawdbot":{"emoji":"[UPLOAD]","requires":{"file":["scripts/config.json"]}}}
---

# Upload Image

上传本地图片或导入公开图片 URL 到当前账号的云资源库。目录不存在时由服务端自动创建。

## Usage

```bash
python3 {baseDir}/scripts/upload_image.py --file /path/to/image.jpg --purpose image
python3 {baseDir}/scripts/upload_image.py --image-url https://example.com/logo.png --purpose logo
python3 {baseDir}/scripts/upload_image.py --image-url https://example.com/1.jpg --image-url https://example.com/2.jpg --purpose product_cover
python3 {baseDir}/scripts/upload_image.py --image-url https://example.com/a.jpg --folder-name 自定义目录
```

## Options

| Option | Description | Required |
|---------|-------------|-----------|
| `--file` | 本地图片路径，与 `--image-url` 二选一 | Yes |
| `--image-url` | 公开图片 URL，与 `--file` 二选一；可重复传入 | Yes |
| `--purpose` | `logo`、`product_cover`、`article_cover`、`image` | No |
| `--folder-name` | 自定义文件夹，覆盖默认目录 | No |

## Rules

- 仅支持 JPEG、PNG、WebP，源文件最大 10MB。
- 图片大于约 2MB 时由服务端先压缩再上传。
- 默认目录：Logo `s_logo`、产品封面 `s_products`、文章封面 `s_news`、其他图片 `s_image`。
- 批量 URL 上传没有业务数量上限；每张图片独立执行 10MB 与压缩规则。
- 使用返回的 `image_url` 写入文章、产品或网站资料。
