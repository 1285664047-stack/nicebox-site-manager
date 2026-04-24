---
name: list-messages
description: List messages, inquiries, or leads from your NiceBox site
metadata: {"clawdbot":{"emoji":"[MSG]","requires":{"env":["AIBOX_API_KEY"]},"primaryEnv":"AIBOX_API_KEY"}}
---

# List Messages

List messages, inquiries, or leads from your site.

## Usage

```bash
# List all messages
python3 {baseDir}/scripts/list_messages.py

# List messages on page 1 with 20 items per page
python3 {baseDir}/scripts/list_messages.py --page 1 --page-size 20

# List only unread messages
python3 {baseDir}/scripts/list_messages.py --is-read 0

# List only read messages
python3 {baseDir}/scripts/list_messages.py --is-read 1
```

## Options

| Option | Description | Required |
|---------|-------------|-----------|
| `--page` | Page number (default: `1`) | No |
| `--page-size` | Number of items per page (default: `20`) | No |
| `--is-read` | Filter by read status, `0` unread / `1` read | No |

## Example

```bash
# List all messages
python3 {baseDir}/scripts/list_messages.py

# List messages on page 2 with 30 items per page
python3 {baseDir}/scripts/list_messages.py --page 2 --page-size 30

# List only unread messages
python3 {baseDir}/scripts/list_messages.py --is-read 0
```

## Response Format

Returns a paginated list of messages:
```json
{
  "code": 0,
  "data": {
    "list": [
      {
        "id": 1,
        "name": "张三",
        "email": "zhangsan@example.com",
        "phone": "13800138000",
        "content": "我想咨询产品价格",
        "is_read": 0,
        "created_at": "2024-01-01 12:00:00"
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20
  }
}
```

## Notes

- Messages include customer inquiries and leads
- Use `--is-read 0` to find unread messages
- Supports pagination for large datasets
