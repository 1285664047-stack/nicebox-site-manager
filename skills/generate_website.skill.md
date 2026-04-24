---
name: generate-website
description: Generate websites using NiceBox AI with interactive dialogue or direct API call
metadata: {"clawdbot":{"emoji":"[GEN]","requires":{"env":["AIBOX_API_KEY"]},"primaryEnv":"AIBOX_API_KEY"}}
---

# Generate Website

Generate a complete website for your business using NiceBox AI.

## [API] Direct API Call (Recommended)

Use the one-shot Python script to avoid SIGKILL issues:

### Method 1: Command Line Arguments (Recommended)

```bash
python3 {baseDir}/scripts/_full_gen.py \
  --company-name "帽饰工坊" \
  --industry "帽子设计" \
  --business-scope "帽子设计、帽子定制、帽饰批发" \
  --advantages "原创设计、品质保证" \
  --phone "400-888-8888" \
  --style "时尚简约风"
```

### Method 2: Interactive Input

```bash
python3 {baseDir}/scripts/_full_gen.py
# Then follow the prompts to enter information
```

## Command Line Options

| Option | Description | Required |
|---------|-------------|-----------|
| `--company-name` | Company name | Yes |
| `--industry` | Industry | No |
| `--business-scope` | Business scope | No |
| `--advantages` | Core advantages | No |
| `--logo` | Logo URL | No |
| `--phone` | Contact phone | No |
| `--email` | Contact email | No |
| `--address` | Company address | No |
| `--style` | Visual style | No |
| `--other` | Other information | No |

## Interactive Input

- Run without parameters for interactive mode
- Company name is required
- Other fields can be left blank
- Each field provides helpful examples

## Progress Indicators

Website generation shows real-time progress:

| Indicator | Meaning | Example |
|-----------|-----------|----------|
| [PROGRESS] Progress | Progress percentage or status | `[PROGRESS] 进度: 50%` or `[PROGRESS] 正在处理生成的内容...` |
| [GENERATING] Generating | Current section being generated | `[GENERATING] 正在生成: Header（1）` |
| [DONE] Complete | Section completed | `[DONE] Header 完成` |
| [RECEIVED] Received | Characters/bytes received | `[RECEIVED] 已接收 15000 字符` |
| [COMPLETE] Complete | Generation finished | `[COMPLETE] 网站生成完成！共接收 50000 字符` |
| [ERROR] Error | Error message | `[ERROR] SSE 错误: 网络连接失败` |

## 8 Core Questions

| # | Question | Field | Required |
|---|----------|---------|----------|
| 1 | Company name | company_name | [REQ] Yes |
| 2 | Logo | logo | No |
| 3 | Industry | industry | No |
| 4 | Business scope | business_scope | No |
| 5 | Core advantages | advantages | No |
| 6 | Contact info | phone, email, address | No |
| 7 | Visual style | style | No |
| 8 | Other info | other | No |

## Notes

- Generation typically takes 5-10 minutes
- No timeout should be set
- Progress is shown in real-time with text indicators
- Share URL is automatically generated after successful completion
