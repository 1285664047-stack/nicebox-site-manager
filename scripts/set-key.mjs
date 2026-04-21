/**
 * 设置 API 秘钥 - 写入操作系统环境变量 AIBOX_API_KEY
 *
 * 用法：
 *   node set-key.mjs <新密钥>          设置并持久化
 *   node set-key.mjs                   查看当前密钥
 */
import { execSync } from 'child_process';

const newKey = process.argv[2] || '';

if (!newKey) {
  const current = process.env.AIBOX_API_KEY || '';
  console.log(current ? `当前：${current.slice(0, 8)}****` : '当前：未设置');
  console.log('用法：node set-key.mjs <新密钥>');
  process.exit(0);
}

// 写入当前进程（本次会话立即生效）
process.env.AIBOX_API_KEY = newKey;

// 持久化到用户级环境变量（重启后依然有效）
execSync(
  `[Environment]::SetEnvironmentVariable('AIBOX_API_KEY', '${newKey}', 'User')`,
  { shell: 'powershell' }
);

console.log(`✅ 已更新为：${newKey.slice(0, 8)}****（已持久化到系统环境变量）`);