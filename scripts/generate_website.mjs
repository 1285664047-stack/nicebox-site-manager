/**
 * 生成网站 - 交互式多轮对话脚本（Node.js 版）
 *
 * 双重确认机制：
 *   第1次 ask-init  — 收集问题前检查站点数据，有数据则弹出确认
 *   第2次 generate  — 生成网站前再次检查站点数据，有数据则弹出确认
 *   两次确认提示内容完全一致
 *
 * SSE progressive_content 使用整体赋值（覆盖）而非累积追加
 */
import { createRequire } from "module";
import http from "http";
import https from "https";
import { URL } from "url";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";
const require = createRequire(import.meta.url);

// 读取 API 配置（环境变量优先）
const BASE_URL = process.env.AIBOX_BASE_URL || "https://ai.nicebox.cn/api/openclaw";
const API_KEY  = process.env.AIBOX_API_KEY  || "";
const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const STATE_FILE = path.join(SCRIPT_DIR, ".dialogue_state.json");

// 检查 API_KEY 是否设置
if (!API_KEY) {
  console.error('错误：缺少 API 配置，请设置 AIBOX_API_KEY 环境变量');
  process.exit(1);
}

// ── 统一确认提示（两次确认使用完全相同的文案） ─────────────────────────────
const CONFIRM_MESSAGE = "检测到站点已有数据，生成网站将初始化站点，清空已有的所有网站信息，包括页面、产品、文章、留言等。是否确认继续？";
const CONFIRM_OPTIONS = ["确认", "取消"];

// ── HTTP 工具 ────────────────────────────────────────────────────────────────

function httpRequest(urlStr, options = {}) {
  return new Promise((resolve, reject) => {
    const url = new URL(urlStr);
    const mod = url.protocol === "https:" ? https : http;
    const opt = {
      hostname: url.hostname,
      port:     url.port || (mod === https ? 443 : 80),
      path:     url.pathname + url.search,
      method:   options.method || "GET",
      headers:  {
        "Authorization": API_KEY,
        "Content-Type":  "application/json",
        "User-Agent":    "nicebox-openclaw-skill/1.0",
        ...options.headers,
      },
    };
    const req = mod.request(opt, (res) => {
      if (options.stream) { resolve(res); return; }
      let data = "";
      res.on("data", c => data += c);
      res.on("end", () => {
        try { resolve({ status: res.statusCode, data: JSON.parse(data) }); }
        catch { resolve({ status: res.statusCode, data }); }
      });
    });
    req.on("error", reject);
    // 移除超时设置，让连接保持开放直到完成
    // req.setTimeout(60000, () => { req.destroy(); reject(new Error("Request timeout")); });
    if (options.body) req.write(options.body);
    req.end();
  });
}

const httpPost = (u, b) => httpRequest(u, { method: "POST", body: JSON.stringify(b) });
const httpGet  = u => httpRequest(u, { method: "GET" });

// ── 状态管理 ─────────────────────────────────────────────────────────────────

function loadState() {
  if (fs.existsSync(STATE_FILE)) {
    try {
      const raw = fs.readFileSync(STATE_FILE, "utf-8");
      const state = JSON.parse(raw);
      // 检测乱码：如果包含常见的 GBK->UTF-8 乱码特征，重置状态
      const sample = JSON.stringify(state.collected || {});
      if (/[\x00-\x1f]/.test(sample) || /缁?壊|鏈?潵|鐜?繚/.test(sample)) {
        console.log("[警告] 检测到乱码状态文件，自动重置...");
        resetState();
        return getDefaultState();
      }
      return state;
    } catch (_) {}
  }
  return getDefaultState();
}

function saveState(state) {
  // 确保所有字符串值都是有效的 UTF-8
  const sanitized = JSON.parse(JSON.stringify(state, (key, value) => {
    if (typeof value === 'string') {
      // 移除无效的 UTF-8 字符
      return value.replace(/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]/g, '');
    }
    return value;
  }));
  fs.writeFileSync(STATE_FILE, JSON.stringify(sanitized, null, 2), { encoding: "utf-8" });
}

function getDefaultState() {
  return {
    current_index:      0,
    collected:          {},
    pending_followups:  [],
    started_at:         new Date().toISOString(),
    initialized:        false,
    init_confirmed:     null,
    generate_confirmed: null,
    summary_confirmed:  null,  // summary 阶段的确认状态
    finished_early:     false,
  };
}

function resetState() {
  if (fs.existsSync(STATE_FILE)) fs.unlinkSync(STATE_FILE);
  fs.readdirSync(SCRIPT_DIR)
    .filter(f => f.endsWith(".draft"))
    .forEach(f => { try { fs.unlinkSync(path.join(SCRIPT_DIR, f)); } catch (_) {} });
  console.log("对话状态已重置，所有草稿已清除");
}

// ── 8 个核心问题（每个问题都包含跳过/完成提示 + 行业案例） ─────────────────────

const INDUSTRY_EXAMPLES = {
  // 餐饮行业
  "餐饮": "川菜馆、火锅店、日本料理、西餐厅、咖啡厅、茶餐厅、快餐店、面馆、烧烤店、烘焙坊",
  "食品": "鲜然食品加工厂、光明乳业、康师傅方便面、五粮液酒业、茅台酱香白酒",
  "农业": "果园飘香水果农场、绿色有机蔬菜基地、生态养殖农场、农产品专业合作社",
  // 法律/金融
  "法律": "明德律师事务所、星辰法律咨询、知识产权代理、法务咨询中心",
  "金融": "华夏基金、平安保险、招商银行、证券投资咨询",
  "医疗": "仁和医院、口腔诊所、体检中心、康复理疗馆、药店",
  // 教育/服务
  "教育": "新东方培训、英孚教育、幼儿园、职业技能学校、在线教育平台",
  "科技": "阿里云、腾讯科技、软件开发公司、人工智能企业",
  "商贸": "某某商贸公司、进出口贸易、批发市场、便利店、超市",
  "制造": "鼎盛帽业有限公司、某某电子厂、服装加工厂、五金制品厂",
  // 通用
  "default": "请根据您的实际业务填写"
};

function getIndustryExample(industryText) {
  if (!industryText) return INDUSTRY_EXAMPLES.default;
  const lower = industryText.toLowerCase();
  for (const key of Object.keys(INDUSTRY_EXAMPLES)) {
    if (lower.includes(key)) return INDUSTRY_EXAMPLES[key];
  }
  return INDUSTRY_EXAMPLES.default;
}

const QUESTIONS = [
  { field: "company_name",   question: "请问您的公司名称或想创建的网站名称是什么？",
    placeholder: "例如：鲜然食品加工厂、明德律师事务所、果园飘香水果农场",
    hint: "【必填项】请填写公司名称或网站名称。", required: true },

  { field: "logo",           question: "请问您是否有公司 logo 图片地址？",
    placeholder: "例如：https://example.com/logo.png（没有则使用默认占位图）",
    hint: "可回复「跳过」跳过此题，或「完成」提前结束问答", required: false },

  { field: "industry",       question: "您从事哪个行业？",
    placeholder: "例如：食品加工、餐饮服务、农业种植、法律咨询、医疗健康、教育培训、科技研发",
    hint: "可回复「跳过」跳过此题，或「完成」提前结束问答。", required: false },

  { field: "business_scope", question: "您的业务范围是什么？提供哪些产品或服务？",
    placeholder: "例如：果蔬罐头加工、软件开发与定制、餐饮服务、法律咨询服务",
    hint: "可回复「跳过」或「完成」提前结束问答。请尽量描述详细，有助于生成更精准的网站内容", required: false },

  { field: "advantages",     question: "您的核心竞争优势是什么？（客户为什么选择您？）",
    placeholder: "例如：原料直供、品质保证、出口认证、技术领先、服务周到、价格优惠",
    hint: "可回复「跳过」或「完成」提前结束问答。这是网站宣传的重点内容，建议填写", required: false },

  { field: "phone",          question: "请提供您的联系方式，包括联系电话、联系邮箱、公司地址等",
    placeholder: "例如：400-888-8888 / contact@example.com / 北京市朝阳区建国路88号",
    hint: "可回复「跳过」或「完成」提前结束问答。", required: false, followups: ["email", "address"] },

  { field: "style",          question: "您希望网站呈现什么样的视觉风格？",
    placeholder: "例如：简约现代风、健康自然风、专业商务风、活力创意风、复古中式、时尚潮流",
    hint: "可回复「跳过」或「完成」提前结束问答。", required: false },

  { field: "other",          question: "还有其他需要补充的吗？例如：配色方案、公司介绍、企业口号、核心价值观、业务特色等",
    placeholder: "例如：我们的使命是让每个家庭吃上健康水果；主打产品是红富士苹果和赣南脐橙",
    hint: "可回复「跳过」或「完成」提前结束问答。补充信息可让网站内容更丰富", required: false },
];

const FIELD_LABELS = {
  company_name:  "公司名称", industry:      "行业",
  business_scope:"业务范围", advantages:    "核心优势",
  phone:         "联系电话", email:         "联系邮箱",
  address:       "公司地址", logo:          "Logo",
  style:         "视觉风格", other:         "其他补充",
};

const REQUIRED_API_FIELDS = ["company_name"];

// ── 工具函数 ──────────────────────────────────────────────────────────────────

function parseContact(text) {
  let phone = "", email = "", address = "";
  const emails = text.match(/[\w.\-]+@[\w.\-]+\.\w+/g);
  if (emails) email = emails[0];
  const phones = (text.match(/[\d\-\(\)\s]{7,}/g) || []).filter(p => p.replace(/\D/g, "").length >= 7);
  if (phones.length) phone = phones[0].replace(/\s+/g, "");
  const addrMatch = text.match(/[\u4e00-\u9fa5]{2,}[\u4e00-\u9fa5\s\d\-省市县区镇路街号楼单元层座号A-Za-z]+/);
  if (addrMatch) address = addrMatch[0].trim();
  if (!phone && !email && !address && text.trim().length >= 8) address = text.trim();
  return { phone, email, address };
}

function buildFollowup(subField) {
  const prompts = {
    email:   { question: "请提供您的联系邮箱？",   placeholder: "例如：contact@example.com" },
    address: { question: "请提供您的公司地址？",   placeholder: "例如：浙江省杭州市余杭区良渚工业园A座" },
  };
  return prompts[subField] || { question: "请提供" + (FIELD_LABELS[subField] || subField) + "？", placeholder: "" };
}

function formatQuestion(q, index, total) {
  // 使用问题自带的 hint，如果没有则用默认提示
  const hintText = q.hint || "可回复「跳过」跳过此题，回复「完成」提前结束所有问答";
  return {
    index, total,
    field:       q.field,
    label:       FIELD_LABELS[q.field] || q.field,
    question:    q.question,
    placeholder: q.placeholder || "",
    required:    q.required || false,
    hint:        hintText,
  };
}

function formatFollowup(subField, label) {
  const p = buildFollowup(subField);
  return { type: "followup", field: subField, label, question: p.question, placeholder: p.placeholder || "", hint: "可回复「跳过」跳过此项" };
}

function sanitize(collected) {
  const result = {};
  for (const key of Object.keys(FIELD_LABELS)) {
    const v = collected[key];
    result[key] = (!v || !v.trim() || v === "未填写") ? "未填写" : v.trim();
  }
  const name = result.company_name || "Logo";
  if (!result.logo || result.logo === "未填写") {
    result.logo = "https://via.placeholder.com/200x80/8B4513/FFFFFF?text=" + encodeURIComponent(name.slice(0, 6));
  }
  return result;
}

function printSummary(collected) {
  const info = sanitize(collected);
  console.log("\n" + "=".repeat(52));
  console.log("网站需求汇总");
  console.log("=".repeat(52));
  for (const q of QUESTIONS) {
    const v = info[q.field] || "未填写";
    const tag = REQUIRED_API_FIELDS.includes(q.field) ? " [必填]" : "";
    console.log("  " + (FIELD_LABELS[q.field] || q.field) + tag + "：" + v);
  }
  for (const f of ["email", "address"]) {
    if (collected[f] && collected[f] !== "未填写") {
      console.log("  " + FIELD_LABELS[f] + "：" + collected[f]);
    }
  }
  console.log("=".repeat(52));
}

// ── 统一确认提示输出 ──────────────────────────────────────────────────────────

function outputConfirmPrompt(stage) {
  // stage: "ask-init" 或 "generate"，两次提示内容完全一致
  console.log(JSON.stringify({
    need_confirm: true,
    stage,
    message: CONFIRM_MESSAGE,
    options: CONFIRM_OPTIONS,
    tip: "回复「确认」继续，回复「取消」终止操作",
  }));
}

// ── API 调用 ──────────────────────────────────────────────────────────────────

async function checkSiteLanguages() {
  try {
    const { status, data } = await httpGet(BASE_URL + "/site_pages/getLanguageList");
    if (status === 200 && data.code === 0) return data.data?.list || [];
  } catch (_) {}
  return [];
}

async function initializeSite() {
  return httpPost(BASE_URL + "/template/initializeData", {});
}

async function getCompanyInfo(collected) {
  return httpPost(BASE_URL + "/ai_tools/getCompanyInfo", sanitize(collected));
}

// ── SSE 网站生成 ──────────────────────────────────────────────────────────────

async function generateWebsiteStream(requirement) {
  return new Promise((resolve) => {
    let completed = false, error = null, buf = "", secIdx = 0;

    // API 只需要 requirement 参数，网站在站点内部生成
    const body = JSON.stringify({ requirement });
    const url = new URL(BASE_URL + "/ai_tools/generateWebsite");
    const mod = url.protocol === "https:" ? https : http;

    const req = mod.request({
      hostname: url.hostname,
      port:     url.port || (mod === https ? 443 : 80),
      path:     url.pathname,
      method:   "POST",
      headers:  {
        "Authorization":  API_KEY,
        "Content-Type":   "application/json",
        "Accept":         "text/event-stream",
        "User-Agent":     "nicebox-openclaw-skill/1.0",
        "Content-Length": Buffer.byteLength(body),
      },
    }, (res) => {
      res.on("data", (chunk) => {
        buf += chunk.toString("utf-8");
        const lines = buf.split("\n");
        buf = lines.pop();
        for (const raw of lines) {
          const ln = raw.trim();
          if (!ln.startsWith("data:")) continue;
          const str = ln.slice(5).trim();
          if (!str) continue;
          try {
            const ev = JSON.parse(str);
            const t = ev.type || "";
            if (t === "progress") {
              const pct = ev.percentage;
              if (pct != null) process.stdout.write("\r进度: " + pct + "%");
              else if (ev.message) process.stdout.write("\r" + ev.message);
            } else if (t === "section_generating") {
              secIdx++;
              console.log("\n正在生成: " + (ev.section || "区块" + secIdx));
            } else if (t === "section_complete") {
              console.log("  完成: " + (ev.section || "区块" + secIdx));
            } else if (t === "complete") {
              completed = true;
              console.log("\n网站生成完成！");
            } else if (t === "error") {
              error = ev.message || ev.content || "未知错误";
              console.log("\n错误: " + error);
            }
          } catch { /* 忽略无效行 */ }
        }
      });

      res.on("end", () => {
        // 检查缓冲区尾部
        if (buf.trim()) {
          try {
            const ev = JSON.parse(buf.trim());
            if (ev.type === "complete") completed = true;
            if (ev.type === "error") error = ev.message || ev.content || "未知错误";
          } catch { /* 忽略尾数据 */ }
        }
        // 处理非 SSE 的 JSON 响应（如错误响应）
        // 专门捕获 500 "参数缺失" 错误（A iEditor 初始化不完整）
        if (!completed && !error) {
          try {
            const json = JSON.parse(buf.trim());
            if (json.code === 500 || json.code === 400) {
              error = json.message || "生成失败";
            }
          } catch { /* 不是 JSON，忽略 */ }
        }
        if (completed) {
          resolve({ ok: true });
        } else if (error) {
          resolve({ ok: false, error });
        } else {
          resolve({ ok: false, error: "SSE 流结束但未收到完成信号" });
        }
      });
      res.on("error", e => resolve({ ok: false, error: e.message }));
    });

    req.on("error", err => resolve({ ok: false, error: err.message }));
    // 移除超时设置，让连接保持开放直到完成
    // req.setTimeout(300000, () => {
    //   req.destroy();
    //   resolve({ ok: false, error: "SSE 超时（5 分钟），未收到完成信号" });
    // });

    req.write(body);
    req.end();
  });
}

// ── 辅助：下一题或结束 ────────────────────────────────────────────────────────

async function advance(state) {
  if (state.pending_followups.length) {
    const sub = state.pending_followups[0];
    console.log(JSON.stringify(formatFollowup(sub, FIELD_LABELS[sub] || sub)));
    return;
  }
  if (state.current_index >= QUESTIONS.length || state.finished_early) {
    printSummary(state.collected);
    console.log("\n如需生成网站，请输入：node generate_website.mjs generate");
  } else {
    console.log(JSON.stringify(formatQuestion(QUESTIONS[state.current_index], state.current_index, QUESTIONS.length)));
  }
}

// ── 辅助：执行初始化并继续 ────────────────────────────────────────────────────

async function doInitialize(state, label) {
  console.log(label + "，正在初始化站点数据...");
  const { data } = await initializeSite();
  // 检查 initializeSuccess === true 才确认成功（后端返回：return $this->success(['initializeSuccess' => true], '数据初始化完成')）
  if (data.code === 0 && data.data?.initializeSuccess === true) {
    console.log("初始化完成！");
    state.initialized = true;
  } else {
    // 未返回 initializeSuccess，视为失败，终止流程等待后端修复
    const msg = data.msg || JSON.stringify(data);
    console.log("[错误] 初始化失败：" + msg);
    console.log("请检查后端是否正常运行，或稍后重试。如需帮助，请联系技术支持。");
    process.exit(1);
  }
  saveState(state);
}

// ── 辅助：执行网站生成 ────────────────────────────────────────────────────────



// ── 辅助：提示重新初始化（用于两个错误场景） ─────────────────────────────────

function outputReInitPrompt(reason) {
  console.log(JSON.stringify({
    need_reinit:  true,
    reason,
    message:
      "网站生成失败，需要重新进行初始化。请按以下步骤操作：\n" +
      "\n" +
      "1. node generate_website.mjs reset\n" +
      "2. node generate_website.mjs generate\n" +
      "（generate 命令内部会先检测并引导完成初始化确认）\n" +
      "\n" +
      "如需帮助，请输入：node generate_website.mjs --help",
  }));
  // 重置状态以便重新走完整流程
  resetState();
}

// 生成成功后自动获取临时分享链接
async function getShareUrl() {
  const url = BASE_URL + '/site/generateShareUrl';
  const isHttps = url.startsWith('https');
  const mod = isHttps ? https : http;
  return new Promise((resolve) => {
    const u = new URL(url);
    const req = mod.request({
      hostname: u.hostname, path: u.pathname,
      method: 'GET',
      headers: { 'Authorization': API_KEY }
    }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => { try { resolve(JSON.parse(d)); } catch { resolve(null); } });
    });
    req.on('error', () => resolve(null));
    req.end();
  });
}

async function doGenerate(state) {
  for (const f of REQUIRED_API_FIELDS) {
    if (!state.collected[f] || state.collected[f] === "未填写") {
      console.log("[警告] " + FIELD_LABELS[f] + " 为空，可能影响生成效果");
    }
  }
  console.log("正在获取企业信息...");
  const { data: infoData } = await getCompanyInfo(state.collected);
  if (infoData.code !== 0) { console.log("获取企业信息失败: " + infoData.msg); return; }
  const companyInfo = infoData.data || "";
  if (!companyInfo) { console.log("企业信息为空，无法生成"); return; }
  console.log("企业信息获取成功，正在生成网站（预计 1-3 分钟）...\n");
  const result = await generateWebsiteStream("请根据以下信息生成网站：\n" + companyInfo);
  if (result.ok) {
    // 移除网站内容验证，直接认为生成成功
    console.log("\n网站已成功生成到站点！");
    // 生成成功后自动获取临时分享链接
    const shareResult = await getShareUrl();
    if (shareResult && shareResult.code === 0 && shareResult.data) {
      console.log('\n✅ 临时分享链接（有效期 2 小时）：');
      console.log('   ' + shareResult.data.share_url);
      console.log('');
    }
    // 🔒 不自动发布，输出结构化确认请求让 AI 询问用户
    console.log(JSON.stringify({
      need_publish_confirm: true,
      stage: "post_generate",
      message: "网站生成成功！是否需要发布到线上？⚠️ 发布网站将覆盖线上版本，此操作无法撤销还原！",
      options: ["确认发布", "暂不发布"],
      tip: "回复「确认发布」发布到线上，回复「暂不发布」保留当前状态"
    }));
    state.generated_at = new Date().toISOString();
    state.generate_result = "success";
    saveState(state);
  } else {
    const errMsg = result.error || "";

    // 判断是否为「参数缺失」错误（A iEditor 初始化不完整）
    if (errMsg.includes("参数缺失") || errMsg.includes("无法创建页面")) {
      console.log("\n生成失败：「" + errMsg + "」");
      // ⚠️ 不再 resetState() 清空数据，保留已收集的问题答案
      // 仅回退到 generate 阶段（初始化确认 + 生成），不回到 ask-init 阶段
      state.generate_confirmed = "pending";  // 回到第2次确认等待状态
      saveState(state);
      console.log(JSON.stringify({
        need_reinit: true,
        stage: "generate",
        reason: "generateWebsite 返回「" + errMsg + "」，网站未正确初始化。",
        message:
          "网站生成失败，需要重新进行初始化。\n" +
          "已收集的问题答案已保留，将返回到【生成网站前】的确认步骤重新进行。\n" +
          "请回复「确认」重新初始化站点并生成网站。\n" +
          "回复「取消」终止操作（可执行 reset 重新收集信息）。",
        options: ["确认", "取消"],
        tip: "回复「确认」继续，回复「取消」终止（数据已保留，可随时重新 generate）",
      }));
    } else {
      console.log("\n生成失败: " + errMsg);
      console.log("💡 可重新执行 generate 命令重试");
      state.generate_result = "failed";
      state.generate_error = errMsg;
      saveState(state);
    }
  }
}

// ── 主流程 ────────────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);
  const cmd  = args[0] || "";

  // 支持 --input-file 选项，从文件读取输入（解决 PowerShell 中文编码问题）
  let raw = "";
  const inputFileIdx = args.indexOf("--input-file");
  if (inputFileIdx !== -1 && args[inputFileIdx + 1]) {
    try {
      raw = fs.readFileSync(args[inputFileIdx + 1], "utf-8").trim();
    } catch (e) {
      console.error("无法读取输入文件:", e.message);
      process.exit(1);
    }
  } else {
    raw = (args.slice(1).join(" ") || "").trim();
  }

  const state = loadState();

  // ── reset ────────────────────────────────────────────────────────────────
  if (cmd === "reset") {
    resetState();
    return;
  }

  // ── status ───────────────────────────────────────────────────────────────
  if (cmd === "status") {
    const answered = Object.values(state.collected).filter(v => v && v !== "未填写").length;
    const isDone   = state.current_index >= QUESTIONS.length || state.finished_early;
    console.log(JSON.stringify({
      answered,
      total:              QUESTIONS.length,
      pending_followups:  state.pending_followups.length,
      next_field:         isDone ? null : (QUESTIONS[state.current_index]?.field || null),
      next_label:         isDone ? null : (FIELD_LABELS[QUESTIONS[state.current_index]?.field] || null),
      init_confirmed:     state.init_confirmed,
      generate_confirmed: state.generate_confirmed,
      initialized:        state.initialized,
      finished_early:     state.finished_early,
    }, null, 2));
    return;
  }

  // ── questions ─────────────────────────────────────────────────────────────
  if (cmd === "questions") {
    console.log(JSON.stringify(QUESTIONS.map((q, i) => formatQuestion(q, i, QUESTIONS.length)), null, 2));
    return;
  }

  // ── next ──────────────────────────────────────────────────────────────────
  if (cmd === "next") {
    const pending = state.pending_followups;
    if (pending.length) {
      console.log(JSON.stringify(formatFollowup(pending[0], FIELD_LABELS[pending[0]] || pending[0]), null, 2));
      return;
    }
    if (state.current_index >= QUESTIONS.length || state.finished_early) {
      console.log(JSON.stringify({ done: true, message: "所有问题已收集完毕，请输入 answer 完成 或 summary 查看汇总" }));
      return;
    }
    console.log(JSON.stringify(formatQuestion(QUESTIONS[state.current_index], state.current_index, QUESTIONS.length), null, 2));
    return;
  }

  // ── answer ────────────────────────────────────────────────────────────────
  if (cmd === "answer") {
    // 追问模式
    if (state.pending_followups.length) {
      const sub = state.pending_followups[0];
      if (raw === "跳过") {
        state.pending_followups = state.pending_followups.slice(1);
        saveState(state);
        if (state.pending_followups.length) {
          console.log(JSON.stringify(formatFollowup(state.pending_followups[0], FIELD_LABELS[state.pending_followups[0]] || state.pending_followups[0])));
        } else {
          await advance(state);
        }
        return;
      }
      state.collected[sub] = raw;
      state.pending_followups = state.pending_followups.slice(1);
      saveState(state);
      if (state.pending_followups.length) {
        console.log(JSON.stringify(formatFollowup(state.pending_followups[0], FIELD_LABELS[state.pending_followups[0]] || state.pending_followups[0])));
      } else {
        await advance(state);
      }
      return;
    }

    if (raw === "跳过") {
      if (state.current_index < QUESTIONS.length) {
        state.collected[QUESTIONS[state.current_index].field] = "未填写";
        state.current_index++;
        saveState(state);
      }
      await advance(state);
      return;
    }

    if (raw === "完成") {
      state.finished_early = true;
      saveState(state);
      printSummary(state.collected);
      return;
    }

    if (state.current_index >= QUESTIONS.length || state.finished_early) {
      console.log(JSON.stringify({ error: "所有问题已收集完毕" }));
      return;
    }

    const q = QUESTIONS[state.current_index];

    if (q.field === "phone") {
      const { phone, email, address } = parseContact(raw);
      state.collected.phone = phone || raw;
      const newF = [];
      if (email)   state.collected.email   = email;
      else         newF.push("email");
      if (address) state.collected.address = address;
      else         newF.push("address");
      state.pending_followups = newF;
      state.current_index++;
      saveState(state);
      if (newF.length) {
        console.log(JSON.stringify({
          collected: { phone: state.collected.phone, email: state.collected.email || null, address: state.collected.address || null },
          ...formatFollowup(newF[0], FIELD_LABELS[newF[0]]),
        }));
      } else {
        state.collected.phone = raw;
        console.log(JSON.stringify({ collected: { phone: state.collected.phone, email: null, address: null }, next: null, all_contact_collected: true }));
        await advance(state);
      }
      return;
    }

    state.collected[q.field] = raw;
    state.current_index++;
    saveState(state);
    await advance(state);
    return;
  }

  // ── summary（展示汇总 + 询问是否补充 + 询问是否生成） ──────────────────────
  if (cmd === "summary") {
    // 先展示汇总
    printSummary(state.collected);
    // 标记等待确认状态
    state.summary_confirmed = "pending";
    saveState(state);
    // 然后输出确认选项
    console.log(JSON.stringify({
      need_summary_confirm: true,
      stage: "summary",
      message: "以上是您填写的信息汇总，请确认是否需要补充？",
      options: ["补充信息", "确认无误，生成网站"],
      tip: "回复「补充信息」继续填写或修改，回复「确认无误，生成网站」直接进入生成流程"
    }));
    return;
  }

  // ── 补充信息命令 ──────────────────────────────────────────────────────────
  if (cmd === "supplement") {
    // 用户选择补充信息，回到下一个问题继续收集
    const isDone = state.current_index >= QUESTIONS.length || state.finished_early;
    if (isDone) {
      // 已完成所有问题，回到第一题重新填写
      state.current_index = 0;
      state.finished_early = false;
      saveState(state);
    }
    // 显示下一题
    if (state.current_index < QUESTIONS.length) {
      console.log(JSON.stringify(formatQuestion(QUESTIONS[state.current_index], state.current_index, QUESTIONS.length)));
    }
    return;
  }

  // ── confirm（统一确认命令，两个阶段共用） ─────────────────────────────────
  // 用法: confirm "确认" / confirm "取消" / confirm "补充信息" / confirm "确认无误，生成网站"
  if (cmd === "confirm") {
    const ans = raw || "";

    // ── summary 阶段的确认 ───────────────────────────────────────────────
    if (state.summary_confirmed === "pending") {
      if (ans === "补充信息") {
        // 用户选择补充信息，回到问题继续收集
        state.summary_confirmed = null;
        const isDone = state.current_index >= QUESTIONS.length || state.finished_early;
        if (isDone) {
          // 已完成所有问题，回到第一题重新填写
          state.current_index = 0;
          state.finished_early = false;
        }
        saveState(state);
        console.log("好的，请继续补充信息：");
        if (state.current_index < QUESTIONS.length) {
          console.log(JSON.stringify(formatQuestion(QUESTIONS[state.current_index], state.current_index, QUESTIONS.length)));
        }
      } else if (ans === "确认无误，生成网站" || ans === "确认生成" || ans === "生成") {
        // 用户确认无误，进入生成流程
        state.summary_confirmed = true;
        saveState(state);
        console.log("\n信息已确认，正在进入生成流程...");
        console.log("请输入：node generate_website.mjs generate");
      } else {
        // 重新显示 summary 确认选项
        console.log(JSON.stringify({
          need_summary_confirm: true,
          stage: "summary",
          message: "请选择：补充信息 or 生成网站？",
          options: ["补充信息", "确认无误，生成网站"],
          tip: "回复「补充信息」继续填写，回复「确认无误，生成网站」进入生成"
        }));
      }
      return;
    }

    // 第1次确认待回复（ask-init 阶段）
    if (state.init_confirmed === "pending") {
      if (ans === "确认") {
        state.init_confirmed = true;
        saveState(state);
        await doInitialize(state, "收到确认");
        // 显示下一题
        const answered = Object.values(state.collected).filter(v => v && v !== "未填写").length;
        console.log("\n当前进度：已回答 " + answered + "/" + QUESTIONS.length + " 题");
        if (state.current_index < QUESTIONS.length) {
          console.log(JSON.stringify(formatQuestion(QUESTIONS[state.current_index], state.current_index, QUESTIONS.length)));
        } else {
          console.log("所有问题已收集完毕，请输入：node generate_website.mjs generate");
        }
      } else if (ans === "取消") {
        state.init_confirmed = false;
        saveState(state);
        console.log("已取消，后续操作已终止。\n如需重新开始，请输入：node generate_website.mjs reset");
      } else {
        outputConfirmPrompt("ask-init");
      }
      return;
    }

    // 第2次确认待回复（generate 阶段）
    if (state.generate_confirmed === "pending") {
      if (ans === "确认") {
        state.generate_confirmed = true;
        saveState(state);
        // 确认后初始化并生成
        if (!state.initialized) {
          await doInitialize(state, "收到确认");
        }
        await doGenerate(state);
      } else if (ans === "取消") {
        state.generate_confirmed = false;
        saveState(state);
        console.log("已取消，后续操作已终止。\n如需重新开始，请输入：node generate_website.mjs reset");
      } else {
        outputConfirmPrompt("generate");
      }
      return;
    }

    // 没有待确认的
    console.log("当前没有待确认的操作。");
    return;
  }

  // ── ask-init（第1次确认，收集问题前） ─────────────────────────────────────
  if (cmd === "ask-init") {
    // 已取消
    if (state.init_confirmed === false) {
      console.log("您之前已取消操作，请先 reset 后重新开始。");
      return;
    }
    // 已确认且已初始化 → 直接显示下一题
    if (state.init_confirmed === true && state.initialized) {
      console.log("已确认并初始化完成，请直接回答以下问题：");
      const next = QUESTIONS[state.current_index];
      if (next) console.log(JSON.stringify(formatQuestion(next, state.current_index, QUESTIONS.length)));
      return;
    }
    // 等待回复中 → 再次弹出提示
    if (state.init_confirmed === "pending") {
      outputConfirmPrompt("ask-init");
      return;
    }
    // 首次检查
    const langs = await checkSiteLanguages();
    if (langs.length > 0) {
      // 有数据 → 弹出确认
      state.init_confirmed = "pending";
      saveState(state);
      outputConfirmPrompt("ask-init");
    } else {
      // 无数据 → 自动初始化，直接进入收集问题
      state.init_confirmed = true;
      console.log("站点为空，正在自动初始化...");
      await doInitialize(state, "自动初始化");
      console.log("请直接回答以下问题：");
      const next = QUESTIONS[state.current_index];
      if (next) console.log(JSON.stringify(formatQuestion(next, state.current_index, QUESTIONS.length)));
    }
    return;
  }

  // ── generate（第2次确认，生成网站前） ─────────────────────────────────────
  if (cmd === "generate") {
    // 检查是否已完成信息汇总确认
    if (!state.summary_confirmed && state.current_index >= QUESTIONS.length) {
      // 用户还没做 summary 确认，引导先做 summary
      printSummary(state.collected);
      console.log(JSON.stringify({
        need_summary_confirm: true,
        stage: "summary",
        message: "请先确认信息汇总后再生成网站。是否需要补充信息？",
        options: ["补充信息", "确认无误，生成网站"],
        tip: "回复「补充信息」继续填写，回复「确认无误，生成网站」进入生成"
      }));
      return;
    }

    // 任一阶段已取消
    if (state.init_confirmed === false || state.generate_confirmed === false) {
      console.log("操作已取消，无法生成网站。如需重新开始，请先 reset。");
      return;
    }
    // 第1次确认还在等待
    if (state.init_confirmed === "pending") {
      console.log("请先完成初始化确认（ask-init 阶段）。");
      outputConfirmPrompt("ask-init");
      return;
    }
    // 第2次确认等待回复中
    if (state.generate_confirmed === "pending") {
      outputConfirmPrompt("generate");
      return;
    }
    // 第2次已确认 → 直接生成
    if (state.generate_confirmed === true) {
      if (!state.initialized) {
        await doInitialize(state, "正在初始化站点");
      }
      await doGenerate(state);
      return;
    }

    // ── 首次进入 generate，检查站点数据（第2次确认） ──
    const langs = await checkSiteLanguages();
    if (langs.length > 0) {
      // 有数据 → 弹出第2次确认
      state.generate_confirmed = "pending";
      saveState(state);
      outputConfirmPrompt("generate");
    } else {
      // 无数据 → 直接生成
      state.generate_confirmed = true;
      saveState(state);
      if (!state.initialized) {
        await doInitialize(state, "站点为空，自动初始化");
      }
      await doGenerate(state);
    }
    return;
  }

  // ── 帮助 ──────────────────────────────────────────────────────────────────
  console.log([
    "",
    " 生成网站脚本用法（Node.js 版 · 双重确认机制）",
    "",
    " 推荐工作流程：",
    "   1. ask-init          ← 【必须第一步】检查站点数据（第1次确认）",
    "   2. answer \"内容\"    ← 逐题收集信息（可随时「跳过」或「完成」）",
    "   3. summary           ← 查看信息汇总，确认是否需要补充",
    "   4. confirm \"补充信息\"        ← 如需补充，继续填写",
    "   5. confirm \"确认无误，生成网站\" ← 确认后生成网站",
    "   6. generate          ← 生成网站（第2次确认，如需重新确认）",
    "",
    " 双重确认说明：",
    "   ask-init 和 generate 都会检查站点数据",
    "   如果站点有数据，两次都会弹出相同的确认提示",
    "   确认 → 初始化站点并继续  |  取消 → 终止所有操作",
    "",
    " 信息汇总确认：",
    "   summary 后可选择「补充信息」继续填写或「确认无误，生成网站」直接生成",
    "   使用 confirm \"补充信息\" 或 confirm \"确认无误，生成网站\" 回复",
    "",
    " 命令列表：",
    "   node generate_website.mjs reset                            # 重置对话状态",
    "   node generate_website.mjs status                           # 查看当前进度",
    "   node generate_website.mjs ask-init                         # 【第1步】检查站点（第1次确认）",
    "   node generate_website.mjs confirm \"确认\"                    # 确认（初始化/生成阶段通用）",
    "   node generate_website.mjs confirm \"取消\"                    # 取消（初始化/生成阶段通用）",
    "   node generate_website.mjs questions                        # 列出全部 8 个问题",
    "   node generate_website.mjs next                             # 打印下一题",
    "   node generate_website.mjs answer \"内容\"                    # 记录回答",
    "   node generate_website.mjs summary                          # 【第3步】显示需求汇总",
    "   node generate_website.mjs confirm \"补充信息\"                # 补充信息（summary 后使用）",
    "   node generate_website.mjs confirm \"确认无误，生成网站\"     # 确认生成（summary 后使用）",
    "   node generate_website.mjs generate                         # 【第5步】生成网站（第2次确认）",
    "",
  ].join("\n"));
}

main().catch(console.error);
