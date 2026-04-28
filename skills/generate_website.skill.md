---
name: generate-website
description: Generate websites using AiWebSite AI with interactive dialogue or direct API call
metadata: {"clawdbot":{"emoji":"[GEN]","requires":{"file":["scripts/config.json"]}}}
---

# Generate Website

Generate a complete website for your business using AiWebSite AI.

## [CONFIG] 配置持久化（自动）

**在调用 API 生成网站之前，脚本会自动将用户提供的企业信息保存到 `config.json` 的 `site_info` 字段中。**

保存的字段包括：`company_name`、`industry`、`business_scope`、`logo`、`advantages`、`phone`、`email`、`address`、`style`、`other`。

**好处：**
- 生成完成后，可通过 `python config_manager.py` 查看历史生成记录
- 下次重新生成时，可从 `config.json` 恢复之前的信息
- 信息进入配置体系，后续操作（发布、编辑等）可复用

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

## 执行流程

```
Step 0: 保存站点信息到 config.json（自动，无需手动操作）
Step 1: 初始化站点（清空已有数据）
Step 2: 注册公司信息（调用 getCompanyInfo API）
Step 3: 生成网站（SSE 流式输出，5-10 分钟）
Step 4: 验证结果（检查首页 HTML 是否存在）
Step 5: 获取分享链接（2 小时有效）
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
- Site info is automatically saved to `config.json` before API calls
