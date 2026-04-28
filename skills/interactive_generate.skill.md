---
name: interactive-generate
description: Interactive multi-turn dialogue for website generation with AI-guided questions
metadata: {"clawdbot":{"emoji":"[DIALOG]","requires":{"file":["scripts/config.json"]}}}
---

# Interactive Website Generation

AI-guided multi-turn dialogue to generate a website. **All answers are manually entered by the customer** — AI only asks questions, never auto-answers.

## [CONFIG] 配置持久化

**在执行 generate 生成网站之前，脚本会自动将收集到的企业信息保存到 `config.json` 的 `site_info` 字段中。**

保存的字段包括：`company_name`、`industry`、`business_scope`、`logo`、`advantages`、`phone`、`email`、`address`、`style`、`other`。

**好处：**
- 生成完成后，可通过 `python config_manager.py` 查看历史生成记录
- 下次重新生成时，可从 `config.json` 恢复之前的信息
- 信息进入配置体系，后续操作（发布、编辑等）可复用

## [WARN] 【强制】AI 操作流程（必须严格按此顺序执行）

```
第 1 步：ask-init       ← 【必须首先执行】检查站点数据（第1次确认）
第 2 步：answer "内容"  ← 逐题收集企业信息（8 个问题）
第 3 步：summary        ← 显示汇总确认
第 4 步：generate       ← 保存信息到 config.json → 生成网站（第2次确认）
```

**每一步执行后，必须停下来等待用户响应！**

## Commands

### Python Version

```bash
python3 {baseDir}/scripts/generate_website.py ask-init          # 【第1步】检查站点（第1次确认）
python3 {baseDir}/scripts/generate_website.py confirm "确认"    # 确认（两个阶段通用）
python3 {baseDir}/scripts/generate_website.py confirm "取消"    # 取消（两个阶段通用）
python3 {baseDir}/scripts/generate_website.py status            # 查看进度
python3 {baseDir}/scripts/generate_website.py questions         # 列出全部8问
python3 {baseDir}/scripts/generate_website.py next              # 打印下一题
python3 {baseDir}/scripts/generate_website.py answer "内容"     # 记录回答
python3 {baseDir}/scripts/generate_website.py summary           # 汇总确认
python3 {baseDir}/scripts/generate_website.py generate          # 【第4步】生成网站（第2次确认）
python3 {baseDir}/scripts/generate_website.py reset             # 重置对话
```

### Node.js Version (Backup)

```bash
node {baseDir}/scripts/generate_website.mjs ask-init
node {baseDir}/scripts/generate_website.mjs answer "内容"
node {baseDir}/scripts/generate_website.mjs answer --input-file /path/to/input.txt  # 中文编码 workaround
node {baseDir}/scripts/generate_website.mjs summary
node {baseDir}/scripts/generate_website.mjs generate
```

## Double Confirmation Mechanism

> [WARN] **检测到站点已有数据，生成网站将初始化站点，清空已有的所有网站信息，包括页面、产品、文章、留言等。是否确认继续？**

| Confirmation Stage | Command | Logic |
|-------------------|---------|-------|
| **1st** Before collecting questions | `ask-init` | Empty → proceed; Has data → confirm; Cancel → abort |
| **2nd** Before generating website | `generate` | Empty → generate; Has data → confirm; Cancel → abort |

## 8 Core Questions

| # | Question | Field | Required |
|---|----------|---------|----------|
| 1 | 公司名称 | company_name [REQ] | Yes |
| 2 | Logo | logo | No |
| 3 | 行业 | industry | No |
| 4 | 业务范围 | business_scope | No |
| 5 | 核心优势 | advantages | No |
| 6 | 联系方式 | phone → email → address | No |
| 7 | 视觉风格 | style | No |
| 8 | 其他补充 | other | No |

## User Reply Conventions

| Reply | Meaning |
|-------|---------|
| Normal content | Record as answer |
| **「跳过」** | Mark as "未填写", continue |
| **「完成」** | End all questions early, go to summary |
| **「确认」** | Confirm initialization (both stages) |
| **「取消」** | Abort all operations |
| Empty | Mark as "未填写" |

## Correct Interaction Flow Examples

### Example 1: ask-init (with data confirmation)

```
用户：帮我生成一个网站

[OK] 正确 AI 行为：
AI: 好的，我来帮您生成网站。首先执行初始化检查...
[执行] python3 generate_website.py ask-init
[输出] {"need_confirm": true, "message": "检测到站点已有数据..."}

AI: [WARN] 检测到站点已有数据，生成网站将初始化站点，清空已有的所有网站信息。
   请回复「确认」继续，或回复「取消」终止操作。
   [停止，等待用户回复]
```

### Example 2: Question collection

```
用户：帽饰工坊

[OK] 正确 AI 行为：
AI: [执行] python3 generate_website.py answer "帽饰工坊"
[输出] Q2 Logo 问题...

AI: 请问您是否有公司logo地址？没有请直接跳过。
   [停止，等待用户回复]
```

### Example 3: Summary confirmation

```
用户：（回答完所有问题后）

[OK] 正确 AI 行为：
AI: [执行] python3 generate_website.py summary
[输出] 汇总信息...

AI: 以下是您的网站需求汇总：
   公司名称：帽饰工坊
   行业：帽饰设计与定制服务
   ...
   
   如需生成网站，请回复「确认」继续。
   [停止，等待用户回复]
```

### Example 4: Generate

```
用户：确认生成

[OK] 正确 AI 行为：
AI: [执行] python3 generate_website.py generate
[输出] 网站生成中...

AI: [WAIT] 网站正在生成中，预计需要 5-10 分钟，请耐心等待...
[等待生成完成，不设置超时]
[输出] [OK] 验证通过：首页 HTML 内容已存在，网站生成成功！

AI: [OK] 网站生成成功！
   预览地址：https://...
   
   是否需要发布到线上？请回复「确认发布」或「暂不发布」。
   [停止，等待用户回复]
```

## [WARN] Generation Time Notice

**Website generation typically takes 5-10 minutes.** When executing `generate`:
1. **Do not set exec timeout**, or set timeout ≥ 600 seconds
2. **Notify user about long wait time**:
   > [WAIT] 网站正在生成中，预计需要 5-10 分钟，请耐心等待...

## [WARN] Chinese Encoding

**Python**: Native UTF-8 support, can pass Chinese parameters directly.

**Node.js**: Windows PowerShell defaults to GBK encoding. Use `--input-file` option:
```bash
node {baseDir}/scripts/generate_website.mjs answer --input-file /tmp/user_input.txt
```

## Node.js Version Notes

- [OK] Q&A flow (ask-init / answer / summary / confirm / status / reset) works normally
- [X] `generate` and `direct-generate` commands may encounter SIGKILL on Windows
- **For generate, use Python one-shot script** (`_full_gen.py`)
