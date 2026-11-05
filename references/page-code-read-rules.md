# 页面代码只读规则

规则版本：`1.0.0`

| 规则 | 内容 |
| --- | --- |
| READ-001 | 修改分析只能基于 `site_pages.html` 原始模板 |
| READ-002 | metadata 不返回完整 HTML |
| READ-003 | sections 返回稳定选择器、原始区域 HTML 和 Hash |
| READ-004 | full 仅用于复杂全页分析 |
| READ-005 | 外链页没有可编辑页面代码 |
| READ-006 | 页面必须按 API Key 绑定账号、站点和 locale 隔离 |
| SYS-001 | `tailwind.config` 完全只读 |
| SYS-002 | `systemDefaultStyle260918` 完全只读 |
| SYS-003 | `disableJumpScript` 完全只读 |
| WIDTH-001 | 两个宽度 Style 为 `controlled_width_only` |
| SHARED-001 | Header/Footer 本阶段只读，按站点和语言共享 |

页面读取返回的 `rules_version` 与本文件不一致时，停止后续分析并重新加载最新版 Skill。
