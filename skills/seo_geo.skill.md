---
name: seo-geo
description: View SEO/GEO reports, run confirmed detection, and perform confirmed one-click optimization
metadata: {"clawdbot":{"emoji":"[SEO]","requires":{"file":["scripts/config.json"]}}}
---

# SEO/GEO 检测与一键优化

优先使用 MCP；不可用时调用 `python3 {baseDir}/scripts/seo_geo.py ...`。

## 查看报告

- 用户要求查看报告时直接查询已有报告，不启动检测。
- 没有报告时说明情况，并在用户选择检测后执行检测确认流程。
- 有报告或检测刚完成时展示总分，并从 `main_deduction_items` 展示主要扣分项的名称、得分、权重、加权扣分、问题摘要和问题数，最多展示接口返回的前 8 项。
- 将 `optimizable=true` 的项目单独列为“可一键优化的内容”，其余列为“需人工处理”。`can_optimize=true` 时提示可以一键优化，并说明执行前会先展示拟修改摘要、再次确认；为 false 时提示暂无可自动优化内容。不得自动启动优化。

## 启动或重新检测

每一次首次检测、重新检测、优化后复检或发布后复检，都必须先提示：

1. 先调用站点状态工具读取当前 `domain` 和 `publish_status`。
2. 提醒用户 SEO/GEO 检测应在网站发布后进行；若尚未发布，停止检测并引导用户先预览、确认和发布。
3. 网站已发布时展示当前检测域名，并提示：

> 请确保网站已经发布后再检测。当前检测域名：`{domain}`。本次检测会消耗 Token 额度，通常需要等待几分钟；检测只生成报告，不会修改或发布网站。确认对这个域名开始检测吗？

用户看到域名并明确二次确认后才能启动。用户说“检测”或“重新检测”只是表达意图，不等于确认。MCP 启动时传 `target_domain={domain}`；API 回退传 `--target-domain "{domain}"`。启动前域名变化时必须重新展示并确认。启动后保存 `operation_id` 并查询状态，禁止重复启动。

`target_domain` 必须原样采用站点状态工具返回并展示给用户的当前域名，不要自行切换 `http/https` 或增删 `www` 反复试探。工具返回 `CONFIRMATION_REQUIRED` 时展示新的 `current_domain` 并重新确认；返回 `SITE_NOT_PUBLISHED` 时引导先发布网站。若返回 PHP 类型错误或 HTTP 500，应明确报告服务端错误，不要通过修改域名规避。

## 一键优化

用户说“网站优化”“SEO 优化”“GEO 优化”“一键优化”“修复这些问题”或其他明确要求执行优化的表达时，统一进入本流程，不要只给通用建议，也不要误判为启动新检测。

最新报告工具返回 `found=false` 时，直接视为“未找到检测报告”，不要向用户展示 `data`、返回结构、解析错误或账号验证过程；立即读取无报告全量优化计划并继续确认流程。

1. 先查询最新完成报告和真实可优化项。没有报告时不强制检测，改为读取“无报告全量一键优化计划”，展示页面标题、页面描述、页面关键词、标题层级、图片 Alt、绝对化用语六项及页面范围。
2. 没有可优化项时直接提醒，不创建任务。
3. 有项目时以“可一键优化的内容”为标题，展示项目、问题数、预计页面数和人工问题数，说明只修改后台、不发布公网，并询问是否确认执行一键优化。
4. 用户明确确认后，有报告时启动报告优化；没有报告时启动无报告全量优化。保存 `operation_id` 并用同一个优化状态接口查询到结束；不要再要求用户重复发送“一键优化”。
5. 展示完成、跳过、未解决和失败结果，建议生成预览；发布必须独立确认。

## API 回退命令

```bash
python3 {baseDir}/scripts/seo_geo.py latest
python3 {baseDir}/scripts/seo_geo.py report --report-id 123
python3 {baseDir}/scripts/seo_geo.py optimizable --report-id 123
python3 {baseDir}/scripts/seo_geo.py start-detect
python3 {baseDir}/scripts/seo_geo.py start-detect --confirmed --target-domain "https://example.com" --request-id stable-id
python3 {baseDir}/scripts/seo_geo.py detect-status --operation-id operation-id
python3 {baseDir}/scripts/seo_geo.py start-optimize --report-id 123 --items 15 16 19
python3 {baseDir}/scripts/seo_geo.py start-optimize --report-id 123 --items 15 16 19 --confirmed --request-id stable-id
python3 {baseDir}/scripts/seo_geo.py optimize-status --operation-id operation-id
```
