#!/usr/bin/env node
/**
 * generate_website.mjs - 网站生成脚本（Node.js 版本）
 * 
 * 使用 Node.js 原生 https 模块处理 SSE 流，避免 Python 内存累积导致的 SIGKILL
 * 
 * 用法：
 *   node generate_website.mjs ask-init          # 检查站点数据
 *   node generate_website.mjs answer "内容"     # 记录回答
 *   node generate_website.mjs summary           # 显示汇总
 *   node generate_website.mjs generate          # 生成网站
 *   node generate_website.mjs direct-generate   # 直接生成（跳过确认）
 *   node generate_website.mjs reset             # 重置状态
 */

import { spawn } from 'child_process';
import { createWriteStream, existsSync, mkdirSync, readFileSync, writeFileSync, unlinkSync, readdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

import { getApiKey, getBaseUrl } from './config_reader.mjs';

const BASE_URL = getBaseUrl();
const API_KEY = getApiKey();
const STATE_FILE = join(__dirname, '.dialogue_state.json');

// API 端点
const ENDPOINTS = {
  languageList: `${BASE_URL}/site_pages/getLanguageList`,
  initialize: `${BASE_URL}/template/initializeData`,
  getCompanyInfo: `${BASE_URL}/ai_tools/getCompanyInfo`,
  generateWebsite: `${BASE_URL}/ai_tools/generateWebsite`,
  generateShareUrl: `${BASE_URL}/site/generateShareUrl`,
  readIndexHtml: `${BASE_URL}/site_pages/readIndexHtml`,
};

// 8 个核心问题
const QUESTIONS = [
  { field: 'company_name', question: '请问您的公司名称或想创建的网站名称是什么？', placeholder: '例如：明德律师事务所', required: true },
  { field: 'logo', question: '请问您是否有公司logo地址？没有请直接跳过。', placeholder: 'https://example.com/logo.png', required: false },
  { field: 'industry', question: '您从事哪个行业？', placeholder: '例如：科技、医疗、教育', required: false },
  { field: 'business_scope', question: '您的业务范围是什么？提供哪些产品或服务？', placeholder: '例如：软件开发与定制', required: false },
  { field: 'advantages', question: '您的核心竞争优势是什么？', placeholder: '例如：技术领先、价格合理', required: false },
  { field: 'phone', question: '请提供您的联系方式（电话、邮箱、地址）？', placeholder: '400-888-8888', required: false },
  { field: 'style', question: '您希望网站呈现什么样的视觉风格？', placeholder: '例如：简约现代风', required: false },
  { field: 'other', question: '还有其他需要补充的内容吗？', placeholder: '没有可跳过', required: false },
];

const FIELD_LABELS = {
  company_name: '公司名称',
  logo: 'Logo',
  industry: '行业',
  business_scope: '业务范围',
  advantages: '核心优势',
  phone: '联系电话',
  email: '联系邮箱',
  address: '公司地址',
  style: '视觉风格',
  other: '其他补充',
};

// 统一确认提示
const CONFIRM_MESSAGE = '检测到站点已有数据，生成网站将初始化站点，清空已有的所有网站信息，包括页面、产品、文章、留言等。是否确认继续？';

// ============ 工具函数 ============

function loadState() {
  if (existsSync(STATE_FILE)) {
    try {
      return JSON.parse(readFileSync(STATE_FILE, 'utf-8'));
    } catch (e) {}
  }
  return {
    current_index: 0,
    collected: {},
    pending_followups: [],
    started_at: new Date().toISOString(),
    initialized: false,
    init_confirmed: null,
    generate_confirmed: null,
    finished_early: false,
  };
}

function saveState(state) {
  writeFileSync(STATE_FILE, JSON.stringify(state, null, 2), 'utf-8');
}

function resetState() {
  if (existsSync(STATE_FILE)) {
    unlinkSync(STATE_FILE);
  }
  // 清除草稿文件
  const draftFiles = readdirSync(__dirname).filter(f => f.endsWith('.draft'));
  draftFiles.forEach(f => { try { unlinkSync(join(__dirname, f)); } catch (e) {} });
  output({ action: 'reset', message: '对话状态已重置，所有草稿已清除' });
}

function output(data) {
  console.log(JSON.stringify(data, null, 2));
}

function sanitizeInfo(collected) {
  const result = {};
  Object.keys(FIELD_LABELS).forEach(key => {
    const value = collected[key];
    if (!value || value.trim() === '') {
      result[key] = '未填写';
    } else {
      result[key] = value.trim();
    }
  });
  
  // Logo 占位图
  if (!result.logo || result.logo === '未填写') {
    const name = result.company_name || 'Logo';
    result.logo = `https://via.placeholder.com/200x80/8B4513/FFFFFF?text=${encodeURIComponent(name.substring(0, 6))}`;
  }
  
  return result;
}

// ============ API 调用（使用 curl） ============

function curlAPI(url, method, data, headers = {}) {
  return new Promise((resolve, reject) => {
    const args = ['-s', '-X', method, url];
    
    args.push('-H', 'Content-Type: application/json');
    args.push('-H', `Authorization: ${API_KEY}`);
    args.push('-H', 'User-Agent: qidc-nodejs-skill/2.0');
    
    Object.entries(headers).forEach(([k, v]) => {
      args.push('-H', `${k}: ${v}`);
    });
    
    if (data && method !== 'GET') {
      args.push('-d', JSON.stringify(data));
    }
    
    const proc = spawn('curl.exe', args, { shell: false });
    let stdout = '';
    let stderr = '';
    
    proc.stdout.on('data', chunk => { stdout += chunk; });
    proc.stderr.on('data', chunk => { stderr += chunk; });
    
    proc.on('close', code => {
      if (code !== 0) {
        reject(new Error(`curl exited with code ${code}: ${stderr}`));
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (e) {
        resolve({ raw: stdout });
      }
    });
    
    proc.on('error', reject);
  });
}

/**
 * SSE 流处理 - 使用 curl --no-buffer 处理 Server-Sent Events
 * 这是关键改进：curl 流式读取，Node.js 逐行解析，避免内存累积
 */
function curlSSE(url, data, onEvent) {
  return new Promise((resolve, reject) => {
    const args = [
      '-s', '--no-buffer',  // 关键：禁用缓冲，流式输出
      '-X', 'POST',
      url,
      '-H', 'Content-Type: application/json',
      '-H', `Authorization: ${API_KEY}`,
      '-H', 'Accept: text/event-stream',
      '-H', 'User-Agent: qidc-nodejs-skill/2.0',
      '-d', JSON.stringify(data),
    ];
    
    const proc = spawn('curl.exe', args, { shell: false });
    let buffer = '';
    let lastEvent = null;
    let htmlContent = '';
    let sectionIndex = 0;
    
    proc.stdout.on('data', chunk => {
      buffer += chunk.toString('utf-8');
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (!line.trim()) continue;
        
        if (line.startsWith('data:')) {
          const dataStr = line.substring(5).trim();
          if (!dataStr) continue;
          
          try {
            const event = JSON.parse(dataStr);
            lastEvent = event;
            
            // 处理不同事件类型
            if (event.type === 'progress') {
              onEvent && onEvent('progress', event);
            } else if (event.type === 'section_generating') {
              sectionIndex++;
              onEvent && onEvent('section', { index: sectionIndex, section: event.section });
            } else if (event.type === 'progressive_content') {
              if (event.content) {
                htmlContent += event.content;
                // 每 5000 字符报告一次
                if (htmlContent.length % 5000 < event.content.length) {
                  onEvent && onEvent('content', { length: htmlContent.length });
                }
              }
            } else if (event.type === 'section_complete') {
              onEvent && onEvent('complete', { section: event.section });
            } else if (event.type === 'complete') {
              onEvent && onEvent('done', { htmlContent });
            } else if (event.type === 'error') {
              onEvent && onEvent('error', { message: event.content || event.message });
            }
          } catch (e) {
            // 可能是纯 HTML 片段
            if (dataStr.includes('<!DOCTYPE') || dataStr.includes('<html')) {
              htmlContent += dataStr;
            }
          }
        }
      }
    });
    
    proc.stderr.on('data', chunk => {
      console.error('curl stderr:', chunk.toString());
    });
    
    proc.on('close', code => {
      if (code !== 0) {
        reject(new Error(`curl SSE exited with code ${code}`));
        return;
      }
      
      // 处理剩余 buffer
      if (buffer.trim()) {
        try {
          const event = JSON.parse(buffer.trim());
          if (event.type === 'progressive_content' && event.content) {
            htmlContent += event.content;
          }
        } catch (e) {}
      }
      
      resolve({ htmlContent, lastEvent });
    });
    
    proc.on('error', reject);
  });
}

// ============ 核心功能 ============

async function checkSiteLanguages() {
  try {
    const result = await curlAPI(ENDPOINTS.languageList, 'GET', null);
    if (result.code === 0) {
      return result.data?.list || [];
    }
  } catch (e) {}
  return [];
}

async function initializeSite() {
  return curlAPI(ENDPOINTS.initialize, 'POST', {});
}

async function getCompanyInfo(collected) {
  const info = sanitizeInfo(collected);
  return curlAPI(ENDPOINTS.getCompanyInfo, 'POST', info);
}

async function generateShareUrl() {
  return curlAPI(ENDPOINTS.generateShareUrl, 'GET', null);
}

async function readIndexHtml() {
  return curlAPI(ENDPOINTS.readIndexHtml, 'GET', null);
}

async function generateWebsite(requirement) {
  console.log('\n[GENERATING] 网站生成中（SSE 流式，curl + Node.js）...\n');
  
  let htmlContent = '';
  let lastProgress = '';
  
  try {
    await curlSSE(ENDPOINTS.generateWebsite, { requirement }, (type, data) => {
      if (type === 'progress') {
        const pct = data.percentage;
        const msg = data.message || '';
        lastProgress = pct ? `${pct}%` : msg;
        if (lastProgress && process.stdout.isTTY) {
          process.stdout.write(`\r[PROGRESS] ${lastProgress.padEnd(30)}`);
        }
      } else if (type === 'section') {
        console.log(`\n[GENERATING] 正在生成: ${data.section || `区块${data.index}`}（${data.index}）`);
      } else if (type === 'content') {
        if (process.stdout.isTTY) {
          process.stdout.write(`\r[RECEIVED] 已接收 ${data.length} 字符`.padEnd(30));
        }
      } else if (type === 'complete') {
        console.log(`  [DONE] ${(data.section || '区块')} 完成`);
      } else if (type === 'done') {
        htmlContent = data.htmlContent;
        console.log('\n[COMPLETE] 网站生成完成！');
      } else if (type === 'error') {
        console.log(`\n[ERROR] SSE 错误: ${data.message}`);
      }
    });
    
    return { code: 0, htmlContent, html_len: htmlContent.length };
  } catch (e) {
    return { code: 1, msg: e.message };
  }
}

// ============ 命令处理 ============

async function cmdAskInit() {
  const state = loadState();
  
  if (state.init_confirmed === false) {
    output({ error: '已取消操作，请先 reset 后重新开始' });
    return;
  }
  
  if (state.init_confirmed === true && state.initialized) {
    // 已确认且已初始化，显示下一题
    const q = QUESTIONS[state.current_index];
    if (q) {
      output({
        index: state.current_index,
        total: QUESTIONS.length,
        field: q.field,
        label: FIELD_LABELS[q.field],
        question: q.question,
        placeholder: q.placeholder,
        required: q.required,
        hint: '可回复「跳过」跳过此题，回复「完成」提前结束',
        _ai_instruction: '【AI 注意】展示问题后停下来等待用户回复',
      });
    }
    return;
  }
  
  if (state.init_confirmed === 'pending') {
    output({
      need_confirm: true,
      stage: 'ask-init',
      message: CONFIRM_MESSAGE,
      options: ['确认', '取消'],
      _ai_instruction: '【AI 注意】展示确认提示后停下来等待用户回复',
    });
    return;
  }
  
  // 首次检查
  const languages = await checkSiteLanguages();
  if (languages.length > 0) {
    state.init_confirmed = 'pending';
    saveState(state);
    output({
      need_confirm: true,
      stage: 'ask-init',
      message: CONFIRM_MESSAGE,
      options: ['确认', '取消'],
      _ai_instruction: '【AI 注意】展示确认提示后停下来等待用户回复',
    });
  } else {
    // 无数据，自动初始化
    console.log('站点为空，正在自动初始化...');
    const result = await initializeSite();
    if (result.code === 0 && result.data?.initializeSuccess) {
      state.init_confirmed = true;
      state.initialized = true;
      saveState(state);
      
      const q = QUESTIONS[0];
      output({
        index: 0,
        total: QUESTIONS.length,
        field: q.field,
        label: FIELD_LABELS[q.field],
        question: q.question,
        placeholder: q.placeholder,
        required: q.required,
        hint: '可回复「跳过」跳过此题，回复「完成」提前结束',
        _ai_instruction: '【AI 注意】展示问题后停下来等待用户回复',
      });
    } else {
      output({ error: `初始化失败: ${result.msg || JSON.stringify(result)}` });
    }
  }
}

async function cmdConfirm(answer) {
  const state = loadState();
  const raw = answer.trim();
  
  // summary 阶段确认
  if (state.summary_confirmed === 'pending') {
    if (raw === '补充信息') {
      state.summary_confirmed = null;
      state.current_index = Math.min(state.current_index, QUESTIONS.length - 1);
      state.finished_early = false;
      saveState(state);
      
      const q = QUESTIONS[state.current_index];
      output({
        index: state.current_index,
        total: QUESTIONS.length,
        field: q.field,
        question: q.question,
        placeholder: q.placeholder,
        hint: '可回复「跳过」或「完成」',
      });
    } else if (raw.includes('确认') || raw.includes('生成')) {
      state.summary_confirmed = true;
      saveState(state);
      console.log('\n信息已确认，正在生成网站...');
      await cmdGenerate();
    }
    return;
  }
  
  // ask-init 阶段确认
  if (state.init_confirmed === 'pending') {
    if (raw === '确认') {
      state.init_confirmed = true;
      console.log('正在初始化站点...');
      const result = await initializeSite();
      if (result.code === 0 && result.data?.initializeSuccess) {
        state.initialized = true;
        saveState(state);
        
        const q = QUESTIONS[state.current_index];
        output({
        action: 'init_ok',
        message: '[OK] 初始化完成',
        next: {
          index: state.current_index,
          field: q.field,
          question: q.question,
          placeholder: q.placeholder,
        },
      });
      } else {
        output({ error: `初始化失败: ${result.msg}` });
      }
    } else if (raw === '取消') {
      state.init_confirmed = false;
      saveState(state);
      output({ action: 'cancelled', message: '已取消操作' });
    }
    return;
  }
  
  // generate 阶段确认
  if (state.generate_confirmed === 'pending') {
    if (raw === '确认') {
      state.generate_confirmed = true;
      saveState(state);
      await doGenerate(state);
    } else if (raw === '取消') {
      state.generate_confirmed = false;
      saveState(state);
      output({ action: 'cancelled', message: '已取消操作' });
    }
    return;
  }
  
  output({ message: '当前没有待确认的操作' });
}

async function cmdAnswer(answer) {
  const state = loadState();
  const raw = answer.trim();
  
  if (raw === '跳过') {
    state.collected[QUESTIONS[state.current_index].field] = '未填写';
  } else if (raw === '完成') {
    state.finished_early = true;
    saveState(state);
    await cmdSummary();
    return;
  } else {
    state.collected[QUESTIONS[state.current_index].field] = raw;
  }
  
  state.current_index++;
  saveState(state);
  
  if (state.current_index >= QUESTIONS.length || state.finished_early) {
    await cmdSummary();
  } else {
    const q = QUESTIONS[state.current_index];
    output({
      index: state.current_index,
      total: QUESTIONS.length,
      field: q.field,
      label: FIELD_LABELS[q.field],
      question: q.question,
      placeholder: q.placeholder,
      required: q.required,
      hint: '可回复「跳过」或「完成」',
      _ai_instruction: '【AI 注意】展示问题后停下来等待用户回复',
    });
  }
}

async function cmdSummary() {
  const state = loadState();
  const info = sanitizeInfo(state.collected);
  
  console.log('\n[SUMMARY] 网站需求汇总');
  console.log('='.repeat(50));
  QUESTIONS.forEach(q => {
    const v = info[q.field] || '未填写';
    console.log(`  ${FIELD_LABELS[q.field]}：${v}${q.required ? ' [REQ]' : ''}`);
  });
  console.log('='.repeat(50));
  
  state.summary_confirmed = 'pending';
  saveState(state);
  
  output({
    action: 'show_summary',
    collected: info,
    need_summary_confirm: true,
    options: ['补充信息', '确认无误，生成网站'],
    _ai_instruction: '【AI 注意】展示汇总后停下来等待用户确认',
  });
}

async function doGenerate(state) {
  const info = sanitizeInfo(state.collected);
  
  // 构建需求字符串
  const parts = [];
  Object.entries(info).forEach(([k, v]) => {
    if (v && v !== '未填写') {
      parts.push(`${FIELD_LABELS[k] || k}：${v}`);
    }
  });
  const requirement = parts.join('\n');
  
  // 获取企业信息
  console.log('正在获取企业信息...');
  const infoResult = await getCompanyInfo(state.collected);
  if (infoResult.code !== 0) {
    output({ error: `获取企业信息失败: ${infoResult.msg}` });
    return;
  }
  
  // 生成网站
  const result = await generateWebsite(requirement);
  
  if (result.code === 0) {
    // 验证
    console.log('\n正在验证网站是否生成成功...');
    const verify = await readIndexHtml();
    
    if (verify.code === 0 && verify.data?.status === true) {
      console.log('[OK] 验证通过：首页 HTML 内容已存在');
      
      // 获取分享链接
      const shareResult = await generateShareUrl();
      let shareUrl = '';
      if (shareResult.code === 0 && shareResult.data?.share_url) {
        const urlPath = shareResult.data.share_url;
        // API 返回相对路径，需提取 origin 拼接（避免 base_url 中的 /api/openclaw 重复）
        shareUrl = urlPath.startsWith('http') ? urlPath : new URL(ENDPOINTS.generateShareUrl).origin + urlPath;
        console.log(`\n[LINK] 临时分享链接（2 小时有效）：\n   ${shareUrl}\n`);
      }
      
      output({
        need_publish_confirm: true,
        message: '网站生成成功！是否需要发布到线上？',
        options: ['确认发布', '暂不发布'],
        share_url: shareUrl,
        html_len: result.html_len,
      });
      
      state.generate_result = 'success';
      state.generated_at = new Date().toISOString();
      saveState(state);
    } else {
      output({
        need_reinit: true,
        message: '验证失败：首页 HTML 不存在，可能需要重新初始化',
      });
      state.generate_result = 'verify_failed';
      saveState(state);
    }
  } else {
    output({ error: `生成失败: ${result.msg}` });
    state.generate_result = 'failed';
    state.generate_error = result.msg;
    saveState(state);
  }
}

async function cmdGenerate() {
  const state = loadState();
  
  // 检查是否需要重新确认
  if (state.generate_confirmed === 'pending') {
    output({
      need_confirm: true,
      stage: 'generate',
      message: CONFIRM_MESSAGE,
      options: ['确认', '取消'],
    });
    return;
  }
  
  if (state.generate_confirmed === false || state.init_confirmed === false) {
    output({ error: '操作已取消，请先 reset' });
    return;
  }
  
  // 首次进入 generate，检查站点
  if (!state.generate_confirmed) {
    const languages = await checkSiteLanguages();
    if (languages.length > 0) {
      state.generate_confirmed = 'pending';
      saveState(state);
      output({
        need_confirm: true,
        stage: 'generate',
        message: CONFIRM_MESSAGE,
        options: ['确认', '取消'],
      });
      return;
    }
  }
  
  // 直接生成
  state.generate_confirmed = true;
  saveState(state);
  
  if (!state.initialized) {
    console.log('正在初始化站点...');
    const result = await initializeSite();
    if (result.code !== 0) {
      output({ error: `初始化失败: ${result.msg}` });
      return;
    }
    state.initialized = true;
    saveState(state);
  }
  
  await doGenerate(state);
}

async function cmdDirectGenerate() {
  const state = loadState();
  
  if (!state.collected.company_name || state.collected.company_name === '未填写') {
    output({ error: '缺少公司名称，请先完成问答流程' });
    return;
  }
  
  // 强制初始化并生成
  console.log('Step 1: 初始化站点...');
  const initResult = await initializeSite();
  if (initResult.code !== 0) {
    output({ error: `初始化失败: ${initResult.msg}` });
    return;
  }
  
  console.log('Step 2: 生成网站...');
  const info = sanitizeInfo(state.collected);
  const parts = [];
  Object.entries(info).forEach(([k, v]) => {
    if (v && v !== '未填写') {
      parts.push(`${FIELD_LABELS[k] || k}：${v}`);
    }
  });
  
  await doGenerate(state);
}

async function cmdStatus() {
  const state = loadState();
  output({
    status: state.current_index < QUESTIONS.length ? 'in_progress' : 'ready',
    current_index: state.current_index,
    total: QUESTIONS.length,
    collected: state.collected,
    initialized: state.initialized,
    init_confirmed: state.init_confirmed,
    generate_result: state.generate_result,
  });
}

// ============ CLI 入口 ============

async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0];
  
  if (!API_KEY) {
    output({ error: 'API key not set. Please run: python config_manager.py --key <your_api_key>' });
    process.exit(2);
  }
  
  switch (cmd) {
    case 'ask-init':
      await cmdAskInit();
      break;
    case 'confirm':
      await cmdConfirm(args[1] || '');
      break;
    case 'answer':
      await cmdAnswer(args[1] || '');
      break;
    case 'summary':
      await cmdSummary();
      break;
    case 'generate':
      await cmdGenerate();
      break;
    case 'direct-generate':
      await cmdDirectGenerate();
      break;
    case 'reset':
      resetState();
      break;
    case 'status':
      await cmdStatus();
      break;
    case 'questions':
      output(QUESTIONS.map((q, i) => ({
        index: i,
        field: q.field,
        question: q.question,
        required: q.required,
      })));
      break;
    default:
      console.log(`
用法:
  node generate_website.mjs ask-init          # 检查站点（第1次确认）
  node generate_website.mjs answer "内容"     # 回答问题
  node generate_website.mjs summary           # 显示汇总
  node generate_website.mjs generate          # 生成网站
  node generate_website.mjs direct-generate   # 直接生成
  node generate_website.mjs reset             # 重置状态
  node generate_website.mjs status            # 查看进度
`);
  }
}

main().catch(e => {
  output({ error: e.message });
  process.exit(1);
});
