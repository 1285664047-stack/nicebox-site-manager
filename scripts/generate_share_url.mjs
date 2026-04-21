#!/usr/bin/env node

import fetch from 'node-fetch';

const BASE_URL        = process.env.AIBOX_BASE_URL || "https://ai.nicebox.cn/api/openclaw";
const ENDPOINT_LANG  = "/site_pages/getLanguageList";
const ENDPOINT_SHARE = "/site/generateShareUrl";

function loadConfig() {
  const apiKey = process.env.AIBOX_API_KEY || "";
  if (!apiKey) {
    console.error('错误：缺少 API 配置，请设置 AIBOX_API_KEY 环境变量');
    process.exit(1);
  }
  return { api_url: BASE_URL, api_key: apiKey };
}

/**
 * 检查站点语言配置
 * total > 0 → 有内容 → 继续生成
 * total = 0 → 无内容 → 终止操作
 */
async function checkSiteHasContent(config) {
  const resp = await fetch(config.api_url + ENDPOINT_LANG, {
    method: 'GET',
    headers: { "Authorization": config.api_key }
  });
  const result = await resp.json();

  if (result.code !== 0 || !result.data) {
    console.error(`错误：无法获取站点语言配置 — ${result.message || '未知错误'}`);
    process.exit(1);
  }

  const total = result.data.total ?? 0;
  const list  = result.data.list   ?? [];

  if (total === 0) {
    console.error('\n[操作终止] 站点暂无网站内容，请先生成并发布网站后再生成分享链接。');
    process.exit(1);
  }

  console.log(`✓ 站点内容检测通过（语言配置 ${total} 项）`);
  return total;
}

async function generateShareUrl(config) {
  const resp = await fetch(config.api_url + ENDPOINT_SHARE, {
    method: 'GET',
    headers: { "Authorization": config.api_key }
  });
  const result = await resp.json();

  if (result.code === 0 && result.data) {
    console.log('\n✅ 临时分享链接生成成功：');
    console.log('   分享链接: ' + result.data.share_url);
    console.log('   有效期:   2 小时\n');
  } else {
    console.error(`错误：${result.message || '生成分享地址失败'}`);
    process.exit(1);
  }
}

async function main() {
  const config = loadConfig();
  await checkSiteHasContent(config);
  await generateShareUrl(config);
}

main();
