---
name: upload-material
description: Upload materials (images, files) to your NiceBox site
metadata: {"clawdbot":{"emoji":"[UPLOAD]","requires":{"env":["AIBOX_API_KEY"]},"primaryEnv":"AIBOX_API_KEY"}}
---

# Upload Material

Upload materials (images, files) to your NiceBox site.

## Usage

```bash
# Python version
python3 {baseDir}/scripts/upload_material.py --file /path/to/image.jpg

# Node.js version
node {baseDir}/scripts/upload_material.mjs --file /path/to/image.jpg
```

## Options

| Option | Description | Required |
|---------|-------------|-----------|
| `--file` | File path to upload | Yes |
| `--type` | Material type (e.g., `image`, `document`) | No |

## Example

```bash
# Upload an image
python3 {baseDir}/scripts/upload_material.py --file /path/to/logo.png

# Upload using Node.js
node {baseDir}/scripts/upload_material.mjs --file /path/to/logo.png
```

## Response Format

Returns the uploaded material URL:
```json
{
  "code": 0,
  "data": {
    "url": "https://cdn.nicebox.cn/uploads/2024/01/logo.png",
    "filename": "logo.png",
    "size": 102400
  }
}
```

## Notes

- Supports common image formats (JPG, PNG, GIF, WebP)
- Supports document formats (PDF, DOC, DOCX)
- Maximum file size depends on server configuration
- Returned URL can be used in articles, products, and website content
