---
name: ftp-publish
description: Test FTP connection and publish your AiWebSite website to FTP server
metadata: {"clawdbot":{"emoji":"[FTP]","requires":{"file":["scripts/config.json"]}}}
---

# FTP Publish

Test FTP connection and publish your website to FTP server with pre-checks.

本流程只用于用户明确要求“发布网站、发布站点、整站上线、FTP 发布”。如果用户要求发布文章或产品，尤其上下文包含 `article_id` 或 `product_id`，禁止读取 FTP 配置、测试 FTP 或调用整站发布；应返回文章/产品流程，只修改内容显示状态。

FTP 密码由 API 服务端直接从账号级 `account_ftp_config` 表读取，只向技能返回 `password_configured` 或脱敏占位符。`password_configured=true`（或旧接口返回 `ftp_password=******`）表示密码已经保存：不得要求用户重新输入、不得把掩码当密码传回，也不得调用更新配置接口覆盖密码。此时直接调用测试连接；若仍返回“配置不完整”，应报告服务端读取异常，不向用户索取秘密。只有 `password_configured=false` 且密码确实未保存时，才引导用户到 Nicebox 后台安全配置，不能在对话中索取或展示 FTP 密码。

`preparePublish` 是分批生成状态机，不是一次调用必定创建任务。返回 `has_more=true` 时没有 `task_id` 是正常的中间状态：使用 `next_batch` 继续，并原样携带 `next_batch_type`、`total_generated`、`total_estimated`、`standard_pages_num`；静态批次从 1 开始递增 `static_batch_number`。必须继续到 `task_created=true`。只有同时满足 `task_ready=true` 且存在 `task_id` 才能开始上传；`no_changes=true` 表示无需上传并直接完成。不得把中间批次误报为任务表缺字段，不得绕过 MCP 改调完整发布接口。

`batch_number` 只能作为 `nicebox_prepare_publish` 的顶层参数，禁止放入 `options`。每次响应都核对 `requested_batch_number` 和 `batch_number` 等于请求批次；如果请求第 2 批却返回第 1 批，应停止并报告版本/参数错误，不能继续覆盖第 1 批状态。

发布任务保存在 `publish_tasks` 数据库表，不依赖 PHP Session、Cookie 或 MCP 会话。取得真实 `task_id` 后，上传和后续状态查询都必须显式传同一个 ID；不能按“当前任务”猜测。第一批返回 `phase=generating_files`、`task_id=null` 是正常状态，不得诊断为 Session 丢失。

上传阶段 `nicebox_start_publish` 的 `task_id` 和 `batch_number` 也都必须放在工具顶层。首次上传使用 `batch_number=1`；返回 `has_more=true` 时把 `next_batch` 作为下一次顶层批次号并复用同一个任务 ID。不得只传 `options`，否则旧服务会出现 `Undefined array key "batch_number"`。

最后一批上传后，按同一个 `task_id` 查询发布状态。只有任务为 `completed`、`site_publish_status=published`，且再次调用站点状态也得到 `publish_status=published`，才能说整站发布成功或进入 SEO/GEO 检测。任务完成但站点状态未同步时先查询任务触发服务端修复，再复查站点，不能根据上传文件数自行判断。

增量准备返回 `no_changes=true` 或 `total_files=0` 时，明确提示“本次增量发布没有发现需要上传的内容，因此未执行 FTP 上传”。这只代表生成文件与上次成功清单的哈希一致，不足以证明公网内容必然最新。若用户确认线上仍旧，先检查预览和生成结果，再展示全量/force 覆盖影响并取得新的发布确认。

`clean_before_publish=true` 会清空远端目录，必须同时使用 `upload_mode=full`；禁止与增量模式组合。任务创建前生成清单必须包含 `index.html`、`index.htm` 或 `index.php` 首页入口。若只有 sitemap、robots、JS/CSS 等辅助文件，停止发布并要求先重新生成、验证首页和内页；不得通过新增文章等无关修改故意触发增量哈希。

## [WARN] 【强制】发布确认机制（三重保障）

**AI 在发布网站时，必须严格遵守以下 3 条规则，不得违反：**

1. **客户主动要求发布时**：必须先询问确认，提示"发布后无法还原"，用户明确确认后才执行
2. **生成网站后**：不得自动发布，必须询问客户是否需要发布，提示"发布后无法还原"
3. **即使客户要求"生成后自动发布"**：生成完成后仍需再次询问确认，不得跳过

**确认提示文案（统一使用）：**

> [WARN] 发布网站将覆盖线上版本，此操作无法撤销还原！确认发布请回复「确认发布」。

## Usage

```bash
# Get FTP configuration
python3 {baseDir}/scripts/ftp_manager.py get-config

# Test FTP connection
python3 {baseDir}/scripts/ftp_manager.py test-connection

# Get publish task status
python3 {baseDir}/scripts/ftp_manager.py get-task-status --task-id TASK_ID

# Cancel publish task
python3 {baseDir}/scripts/ftp_manager.py cancel-task --confirmed

# Prepare files (repeat with next_batch until task_ready=true)
python3 {baseDir}/scripts/ftp_manager.py prepare --batch-number 1 --confirmed

# Upload the prepared task (repeat with next_batch while has_more=true)
python3 {baseDir}/scripts/ftp_manager.py start --task-id TASK_ID --batch-number 1 --confirmed
```

## Publish Options

| Option | Description | Default |
|---------|-------------|---------|
| `--options-json` | MCP-compatible publish options JSON | `{}` |
| `--batch-number` | Current prepare/upload batch | `1` |
| `--task-id` | Task returned by prepare | required for upload |

## Example

```bash
# Step 1: Get FTP configuration
python3 {baseDir}/scripts/ftp_manager.py get-config

# Step 2: Test FTP connection
python3 {baseDir}/scripts/ftp_manager.py test-connection

# Step 3: Prepare then upload the returned task
python3 {baseDir}/scripts/ftp_manager.py prepare --batch-number 1 --confirmed
python3 {baseDir}/scripts/ftp_manager.py start --task-id TASK_ID --batch-number 1 --confirmed

# Check publish task status
python3 {baseDir}/scripts/ftp_manager.py get-task-status --task-id TASK_ID

# Cancel publish task
python3 {baseDir}/scripts/ftp_manager.py cancel-task --confirmed
```

## Notes

- Always test FTP connection before publishing
- Publishing overwrites the online version
- Supports multi-batch publishing for large sites
- Use `get-task-status` to monitor publish progress
- Use `cancel-task` to cancel an ongoing publish
