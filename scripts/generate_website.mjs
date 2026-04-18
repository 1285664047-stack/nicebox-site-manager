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

const BASE_URL = process.env.AIBOX_BASE_URL || "http://aidev.nicebox.cn/api/openclaw";
const API_KEY  = process.env.AIBOX_API_KEY  || "4_455_14ed156fdba64c6ccdb7a0cf236ac712078382681f3cb237";
const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const STATE_FILE = path.join(SCRIPT_DIR, ".dialogue_state.json");

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
    req.setTimeout(60000, () => { req.destroy(); reject(new Error("Request timeout")); });
    if (options.body) req.write(options.body);
    req.end();
  });
}

const httpPost = (u, b) => httpRequest(u, { method: "POST", body: JSON.stringify(b) });
const httpGet  = u => httpRequest(u, { method: "GET" });

// ── 状态管理 ─────────────────────────────────────────────────────────────────

function loadState() {
  if (fs.existsSync(STATE_FILE)) {
    try { return JSON.parse(fs.readFileSync(STATE_FILE, "utf-8")); } catch (_) {}
  }
  return {
    current_index:      0,
    collected:          {},
    pending_followups:  [],
    started_at:         new Date().toISOString(),
    initialized:        false,
    // 第1次确认（ask-init 阶段）: null=未询问 | "pending"=等待回复 | true=已确认 | false=已取消
    init_confirmed:     null,
    // 第2次确认（generate 阶段）: null=未询问 | true=已确认 | false=已取消
    generate_confirmed: null,
    finished_early:     false,
  };
}

function saveState(state) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2), "utf-8");
}

function resetState() {
  if (fs.existsSync(STATE_FILE)) fs.unlinkSync(STATE_FILE);
  fs.readdirSync(SCRIPT_DIR)
    .filter(f => f.endsWith(".draft"))
    .forEach(f => { try { fs.unlinkSync(path.join(SCRIPT_DIR, f)); } catch (_) {} });
  console.log("对话状态已重置，所有草稿已清除");
}

// ── 8 个核心问题 ──────────────────────────────────────────────────────────────

const QUESTIONS = [
  { field: "company_name",   question: "请问您的公司名称或想创建的网站名称是什么？",                placeholder: "例如：鲜然食品加工厂、明德律师事务所", required: true,  followups: [] },
  { field: "logo",           question: "请问您是否有公司 logo 地址？",                           placeholder: "例如：https://example.com/logo.png（没有请跳过）", required: false, followups: [] },
  { field: "industry",       question: "您从事哪个行业？",                                       placeholder: "例如：食品加工、科技、医疗、教育、餐饮、金融", required: false, followups: [] },
  { field: "business_scope", question: "您的业务范围是什么？提供哪些产品或服务？",                 placeholder: "例如：果蔬罐头加工、软件开发与定制、技术咨询服务", required: true,  followups: [] },
  { field: "advantages",     question: "您的核心竞争优势是什么？",                               placeholder: "例如：原料直供、品质保证、出口认证、技术领先", required: false, followups: [] },
  { field: "phone",          question: "请提供您的联系方式, 包括联系电话、联系邮箱、公司地址等？",                                   placeholder: "例如：400-888-8888 / contact@example.com / 北京市朝阳区", required: false, followups: ["email", "address"] },
  { field: "style",          question: "您希望网站呈现什么样的视觉风格？",                placeholder: "例如：简约现代风、健康自然风，专业商务风、活力创意风", required: false, followups: [] },
  { field: "other",          question: "还有其他需要补充的吗？例如：配色方案、公司介绍、公司口号、企业文化、业务特色等。", placeholder: "没有可跳过", required: false, followups: [] },
];

const FIELD_LABELS = {
  company_name:  "公司名称", industry:      "行业",
  business_scope:"业务范围", advantages:    "核心优势",
  phone:         "联系电话", email:         "联系邮箱",
  address:       "公司地址", logo:          "Logo",
  style:         "视觉风格", other:         "其他补充",
};

const REQUIRED_API_FIELDS = ["company_name", "business_scope"];

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
  return {
    index, total,
    field:       q.field,
    label:       FIELD_LABELS[q.field] || q.field,
    question:    q.question,
    placeholder: q.placeholder || "",
    required:    q.required || false,
    hint:        "可回复「跳过」跳过此题，回复「完成」提前结束所有问答",
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
    req.setTimeout(300000, () => {
      req.destroy();
      resolve({ ok: false, error: "SSE 超时（5 分钟），未收到完成信号" });
    });

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
  if (data.code === 0) {
    console.log("初始化完成！");
    state.initialized = true;
  } else {
    console.log("[警告] 初始化返回: " + data.msg + "，继续流程。");
    state.initialized = true;
  }
  saveState(state);
}

// ── 辅助：执行网站生成 ────────────────────────────────────────────────────────

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
    console.log("\n网站已成功生成到站点！");
    // 🔒 不自动发布，输出结构化确认请求让 AI 询问用户
    console.log(JSON.stringify({
      need_publish_confirm: true,
      stage: "post_generate",
      message: "网站生成成功！是否需要发布到线上？⚠️ 发布网站将覆盖线上版本，此操作无法撤销还原！",
      options: ["确认发布", "暂不发布"],
      tip: "回复「确认发布」发布到线上，回复「暂不发布」保留当前状态"
    }));
    // 保留状态文件以便重试，10 分钟后自动过期
    state.generated_at = new Date().toISOString();
    state.generate_result = "success";
    saveState(state);
  } else {
    console.log("\n生成失败: " + result.error);
    console.log("💡 可重新执行 generate 命令重试");
    // 保留状态文件以便重试
    state.generate_result = "failed";
    state.generate_error = result.error;
    saveState(state);
  }
}

// ── 主流程 ────────────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);
  const cmd  = args[0] || "";
  const raw  = (args.slice(1).join(" ") || "").trim();
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

  // ── summary ───────────────────────────────────────────────────────────────
  if (cmd === "summary") {
    printSummary(state.collected);
    return;
  }

  // ── confirm（统一确认命令，两个阶段共用） ─────────────────────────────────
  // 用法: confirm "确认" / confirm "取消"
  if (cmd === "confirm") {
    const ans = raw || "";

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
    "   2. answer \"内容\"     ← 逐题收集信息（可随时「跳过」或「完成」）",
    "   3. summary           ← 查看汇总确认",
    "   4. generate          ← 生成网站（第2次确认）",
    "",
    " 双重确认说明：",
    "   ask-init 和 generate 都会检查站点数据",
    "   如果站点有数据，两次都会弹出相同的确认提示",
    "   确认 → 初始化站点并继续  |  取消 → 终止所有操作",
    "",
    " 命令列表：",
    "   node generate_website.mjs reset              # 重置对话状态",
    "   node generate_website.mjs status             # 查看当前进度",
    "   node generate_website.mjs ask-init           # 【第1步】检查站点（第1次确认）",
    "   node generate_website.mjs confirm \"确认\"     # 确认（两个阶段通用）",
    "   node generate_website.mjs confirm \"取消\"     # 取消（两个阶段通用）",
    "   node generate_website.mjs questions          # 列出全部 8 个问题",
    "   node generate_website.mjs next               # 打印下一题",
    "   node generate_website.mjs answer \"内容\"      # 记录回答",
    "   node generate_website.mjs summary            # 显示需求汇总",
    "   node generate_website.mjs generate           # 【第4步】生成网站（第2次确认）",
    "",
  ].join("\n"));
}

main().catch(console.error);
