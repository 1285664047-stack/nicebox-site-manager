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

重新生成时第一次回应必须提醒：初始化会删除页面、产品、文章、留言等所有站点内容，并先创建普通备份。若当前对话或 `config.json` 已有网站资料，同时展示旧资料并询问用户选择“沿用旧资料”或“修改资料”；修改后重新展示摘要。只有资料定稿后才能继续正式初始化确认和生成确认。

## [API] Direct API Call (Recommended)

Use the one-shot Python script to avoid SIGKILL issues:

### Method 1: Command Line Arguments (Recommended)

```bash
python3 -u {baseDir}/scripts/_full_gen.py \
  --company-name "帽饰工坊" \
  --industry "帽子设计" \
  --business-scope "帽子设计、帽子定制、帽饰批发" \
  --advantages "原创设计、品质保证" \
  --phone "400-888-8888" \
  --style "时尚简约风"
```

### Method 2: Interactive Input

```bash
python3 -u {baseDir}/scripts/_full_gen.py
# Then follow the prompts to enter information
```

## 执行流程

```
Step 0: 保存站点信息到 config.json（自动，无需手动操作）
Step 1: 初始化站点（清空已有数据）
Step 2: 注册公司信息（调用 getCompanyInfo API）
Step 3: 生成网站（SSE 流式输出，5-10 分钟）
Step 4: 验证结果（首页、内页、产品和文章数量）
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
| `--ai-logo` | 使用 AI 生成 Logo | No；与 `--logo-ratio` 同时使用 |
| `--logo-ratio` | AI Logo 比例：`1:1`、`5:2`、`3:2`、`4:3`、`3:4` 或 `2:3` | 使用 `--ai-logo` 时必填 |
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

必须直接以前台、无缓冲方式运行脚本。禁止在命令后添加 `| tail`、`| head`、输出捕获或其他管道；这些操作会缓存输出，导致 WorkBuddy 在生成结束前看不到任何进度。不要把脚本包在等待其结束后才返回输出的二次 Python `subprocess` 中。

正确：

```bash
python3 -u {baseDir}/scripts/_full_gen.py --company-name "公司名称" ...
```

错误：

```bash
python3 ... -c "subprocess.call(...)" 2>&1 | tail -40
```

Website generation shows real-time progress:

| Indicator | Meaning | Example |
|-----------|-----------|----------|
| [PROGRESS] Progress | Progress percentage or status | `[PROGRESS] 进度: 50%` or `[PROGRESS] 正在处理生成的内容...` |
| [GENERATING] Generating | Current section being generated | `[GENERATING] 正在生成: Header（1）` |
| [DONE] Complete | Section completed | `[DONE] Header 完成` |
| [RECEIVED] Received | Characters/bytes received | `[RECEIVED] 已接收 15000 字符` |
| [COMPLETE] Complete | Generation finished | `[COMPLETE] 网站生成完成！共接收 50000 字符` |
| [ERROR] Error | Error message | `[ERROR] SSE 错误: 网络连接失败` |
| [WAIT] Waiting | 后端暂无 SSE 时每 20 秒输出心跳 | `[WAIT] 网站仍在生成：已等待 2分0秒...` |

## 完整站点要求

生成需求必须明确包含页面计划和初始化内容。用户未指定时默认：首页、关于我们、产品或服务、新闻资讯、联系我们，并生成 6-8 条业务相关的示例产品/服务和 6-8 条行业文章。示例内容不得虚构价格、认证、客户案例、联系方式或功效。

调用生成接口时，必须把以下结构约束放进 `requirement`，不能只写“生成完整网站”：

- 一级导航必须使用 `data-type="nav"`、`data-nav-level="1"`、唯一 `data-typeid`，并同时提供相同的 `href` 与 `data-href` 英文锚点。
- 导航 `#home/#about/#products/#news/#contact` 必须分别对应首页中的 `<section id="home/about/products/news/contact">`；锚点去掉 `#` 后必须与 section id 完全一致。
- 产品区使用 `data-type="products"`，产品项使用 `data-type="product"`；新闻区使用 `data-type="newslist"`，文章项使用 `data-type="news"`。
- 所有栏目正文必须完整存在于首页相应 section，不能创建空 section，也不能只生成导航。后端正是从这些 section 截取并保存内页内容。
- 禁止使用 `href="#"`、`javascript:`、中文路径、页面占位符或指向不存在 section 的导航。

生成接口完成后依次检查首页和站点状态中的 `pages_count`、`generated_pages_count`、`products_count`、`articles_count`。只有首页有效但没有内页或内容数据时，应报告“整站生成不完整”，不能进入整站成功提示。

## 8 Core Questions

| # | Question | Field | Required |
|---|----------|---------|----------|
| 1 | Company name | company_name | [REQ] Yes |
| 2 | Logo | logo | No；提供 URL、AI 生成或暂不设置 |
| 3 | Industry | industry | No |
| 4 | Business scope | business_scope | No |
| 5 | Core advantages | advantages | No |
| 6 | Contact info | phone, email, address | No |
| 7 | Visual style | style | No |
| 8 | Other info | other | No |

## Notes

- Generation typically takes 5-10 minutes
- 单次生成最长按 10 分钟处理；超时后先查询或验证现有任务，不要直接重复生成
- Progress is shown in real-time with text indicators
- MCP 模式每 15-30 秒查询一次原 `operation_id`；估算百分比只用于等待感知，不代表已经完成
- Share URL is automatically generated after successful completion
- Site info is automatically saved to `config.json` before API calls
