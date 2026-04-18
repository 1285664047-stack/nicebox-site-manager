#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成网站 - 交互式多轮对话脚本（Python 版）

双重确认机制：
  - 第1次 ask-init  — 收集问题前检查站点数据，有数据则弹出确认
  - 第2次 generate  — 生成网站前再次检查站点数据，有数据则弹出确认
  - 两次确认提示内容完全一致

SSE progressive_content 使用整体赋值（覆盖）而非累积追加
"""
import argparse
import json
import os
import re
import socket
import sys
import time as time_module
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

BASE_URL = os.environ.get("AIBOX_BASE_URL", "http://aidev.nicebox.cn/api/openclaw")
API_KEY = os.environ.get("AIBOX_API_KEY", "")

ENDPOINT_LANGUAGE_LIST = f"{BASE_URL}/site_pages/getLanguageList"
ENDPOINT_INITIALIZE = f"{BASE_URL}/template/initializeData"
ENDPOINT_GET_COMPANY_INFO = f"{BASE_URL}/ai_tools/getCompanyInfo"
ENDPOINT_GENERATE_WEBSITE = f"{BASE_URL}/ai_tools/generateWebsite"

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".dialogue_state.json")

# ── 统一确认提示（两次确认使用完全相同的文案） ─────────────────────────────
CONFIRM_MESSAGE = "检测到站点已有数据，生成网站将初始化站点，清空已有的所有网站信息，包括页面、产品、文章、留言等。是否确认继续？"
CONFIRM_OPTIONS = ["确认", "取消"]

# ═══════════════════════════════════════════════════════════════════════════════
# 7 个核心问题（精简版）
# ═══════════════════════════════════════════════════════════════════════════════
# field：对应 API 字段名（一个 question 可能对应多个 API 字段）
# followups：回答后需要追问的子字段（为空时自动跳过追问）
QUESTIONS = [
    {
        "field": "company_name",
        "question": "请问您的公司名称或想创建的网站名称是什么？",
        "placeholder": "例如：明德律师事务所、某某科技官网",
        "required": True,
        "followups": [],          # 公司名称无追问
    },
    {
        "field": "logo",
        "question": "请问您是否有公司logo地址？没有请直接跳过。",
        "placeholder": "例如：https://example.com/logo.png",
        "required": False,
        "followups": [],          # 公司logo无追问
    },
    {
        "field": "industry",
        "question": "您从事哪个行业？",
        "placeholder": "例如：科技、医疗、教育、餐饮、金融、法律",
        "required": False,
        "followups": [],
    },
    {
        "field": "business_scope",
        "question": "您的业务范围是什么？提供哪些产品或服务？",
        "placeholder": "例如：软件开发与定制、技术咨询服务",
        "required": True,
        "followups": [],
    },
    {
        "field": "advantages",
        "question": "您的核心竞争优势是什么？",
        "placeholder": "例如：技术领先、价格合理、服务周到、高性价比",
        "required": False,
        "followups": [],
    },
    {
        "field": "phone",
        "question": "请提供您的联系方式（电话、邮箱、地址）？",
        "placeholder": "例如：400-888-8888 / contact@example.com / 北京市朝阳区",
        "required": False,
        "followups": ["email", "address"],
    },
    {
        "field": "style",
        "question": "您希望网站呈现什么样的视觉风格？",
        "placeholder": "例如：简约现代风、专业商务风、活力创意风、温馨亲切风",
        "required": False,
        "followups": [],
    },
    {
        "field": "other",
        "question": "还有其他需要补充的内容吗？例如：配色方案、公司介绍、公司口号、企业文化、业务特色等。",
        "placeholder": "没有可跳过",
        "required": False,
        "followups": [],
    },
]

# API 字段中文标签
FIELD_LABELS = {
    "company_name": "公司名称",
    "industry": "行业",
    "business_scope": "业务范围",
    "advantages": "核心优势",
    "phone": "联系电话",
    "email": "联系邮箱",
    "address": "公司地址",
    "logo": "Logo",
    "style": "视觉风格",
    "other": "其他补充",
}

# API 必填字段（getCompanyInfo 要求）
REQUIRED_API_FIELDS = ["company_name", "business_scope"]

# ═══════════════════════════════════════════════════════════════════════════════
# 状态管理
# ═══════════════════════════════════════════════════════════════════════════════

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "current_index": 0,
        "collected": {},       # field -> answer string
        "pending_followups": [],  # 待追问的子字段列表
        "started_at": datetime.now().isoformat(),
        "initialized": False,
        # 第1次确认（ask-init 阶段）: None=未询问 | "pending"=等待回复 | True=已确认 | False=已取消
        "init_confirmed": None,
        # 第2次确认（generate 阶段）: None=未询问 | True=已确认 | False=已取消
        "generate_confirmed": None,
        "finished_early": False,
    }


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, ensure_ascii=False, indent=2)


def reset_state():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    # 清除草稿文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for f in os.listdir(script_dir):
        if f.endswith(".draft"):
            try:
                os.remove(os.path.join(script_dir, f))
            except Exception:
                pass
    print("对话状态已重置，所有草稿已清除")


# ═══════════════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════════════

def is_phone(text):
    return bool(re.search(r"[\d\-\(\)\s]{7,}", text))


def is_email(text):
    return bool(re.search(r"[\w.\-]+@[\w.\-]+\.\w+", text))


def is_address(text):
    # 地址特征：含省/市/区/县/路/号等关键词
    return bool(re.search(
        r"[\u4e00-\u9fa5]{2,}[\省市县区镇路街号楼单元层座]",
        text
    ))


def parse_contact(text):
    """
    从一段文本中提取电话、邮箱、地址。
    返回 {phone, email, address}，字段可能为空字符串。
    """
    phone = ""
    email = ""
    address = ""

    # 提取邮箱
    emails = re.findall(r"[\w.\-]+@[\w.\-]+\.\w+", text)
    if emails:
        email = emails[0]

    # 提取电话号码
    phones = re.findall(r"[\d\-\(\)\s]{7,}", text)
    # 过滤掉太短的（可能是年份、邮编等）
    phones = [p for p in phones if len(re.sub(r"\D", "", p)) >= 7]
    if phones:
        phone = re.sub(r"\s+", "", phones[0])

    # 提取地址（中文地址特征词）
    addr_match = re.search(
        r"[\u4e00-\u9fa5]{2,}[\u4e00-\u9fa5\s\d\-省市区县镇路街号楼单元层座]",
        text
    )
    if addr_match:
        address = addr_match.group().strip()

    # 如果以上都没找到，整个文本作为地址
    if not phone and not email and not address and len(text) >= 8:
        address = text.strip()

    return phone, email, address


def sanitize_company_info(collected):
    """
    规范化公司信息：
      - 空值 → "未填写"
      - Logo 未填写 → 占位图
    """
    result = {}
    for key in FIELD_LABELS:
        value = collected.get(key, "")
        if value is None or (isinstance(value, str) and value.strip() == ""):
            result[key] = "未填写"
        else:
            result[key] = value.strip()

    if result.get("logo") == "未填写" or not result.get("logo"):
        name = result.get("company_name", "Logo")
        result["logo"] = f"https://via.placeholder.com/200x80/8B4513/FFFFFF?text={urllib.parse.quote(name[:6])}"

    return result


def validate_html(html):
    """验证 HTML 完整性，返回问题列表（空 = 通过）。"""
    issues = []
    if not html:
        issues.append("HTML 内容为空")
        return issues
    s = html.strip()
    if "<!DOCTYPE" not in s and "<html" not in s:
        issues.append("缺少 DOCTYPE 或 <html> 标签")
    if "</html>" not in s:
        issues.append("缺少 </html> 闭合标签（内容可能不完整）")
    if len(s) < 5000:
        issues.append(f"内容过短（{len(s)} 字符），生成可能不完整")
    return issues


# ── 统一确认提示输出 ──────────────────────────────────────────────────────────

def output_confirm_prompt(stage):
    """输出确认提示
    stage: "ask-init" 或 "generate"，两次提示内容完全一致
    """
    print(json.dumps({
        "need_confirm": True,
        "stage": stage,
        "message": CONFIRM_MESSAGE,
        "options": CONFIRM_OPTIONS,
        "tip": "回复「确认」继续，回复「取消」终止操作",
    }, ensure_ascii=False))


# ── 辅助：下一题或结束 ────────────────────────────────────────────────────────

def advance(state):
    """推进到下一个问题或结束"""
    if state.get("pending_followups"):
        sub = state["pending_followups"][0]
        prompt = build_followup_question(None, sub)
        print(json.dumps({
            "type": "followup",
            "field": sub,
            "label": FIELD_LABELS.get(sub, sub),
            "question": prompt["question"],
            "placeholder": prompt.get("placeholder", ""),
            "hint": "可回复「跳过」跳过此项",
        }, ensure_ascii=False))
        return
    
    if state.get("current_index", 0) >= len(QUESTIONS) or state.get("finished_early"):
        print_summary(state.get("collected", {}))
        print("\n如需生成网站，请输入：python generate_website.py generate")
    else:
        q = QUESTIONS[state["current_index"]]
        print(json.dumps({
            "index": state["current_index"],
            "total": len(QUESTIONS),
            "field": q["field"],
            "label": FIELD_LABELS.get(q["field"], q["field"]),
            "question": q["question"],
            "placeholder": q.get("placeholder", ""),
            "required": q.get("required", False),
            "hint": "可回复「跳过」跳过此题，回复「完成」提前结束所有问答",
        }, ensure_ascii=False))


# ── 辅助：执行初始化并继续 ────────────────────────────────────────────────────

def do_initialize(state, label):
    """执行初始化并继续"""
    print(f"{label}，正在初始化站点数据...")
    result = initialize_site()
    if result.get("code") == 0:
        print("初始化完成！")
        state["initialized"] = True
    else:
        print(f"[警告] 初始化返回: {result.get('msg', '')}，继续流程。")
        state["initialized"] = True
    save_state(state)


# ── 辅助：执行网站生成 ────────────────────────────────────────────────────────

def do_generate(state):
    """执行网站生成"""
    collected = state.get("collected", {})
    info = sanitize_company_info(collected)
    
    for f in REQUIRED_API_FIELDS:
        if info.get(f) == "未填写":
            print(f"[警告] {FIELD_LABELS.get(f, f)} 为空，可能影响生成效果")
    
    print("正在获取企业信息...")
    info_result = call_get_company_info(collected)
    if info_result.get("code") != 0:
        print(f"获取企业信息失败: {info_result.get('msg', '')}")
        return
    
    company_info = info_result.get("data", "")
    if not company_info:
        print("企业信息为空，无法生成")
        return
    
    requirement = f"请根据以下信息生成网站：\n{company_info}"
    print("企业信息获取成功，正在生成网站（预计 1-3 分钟）...\n")
    
    result = call_generate_website(requirement)
    
    if result.get("code") == 0:
        print("\n网站已成功生成到站点！")
        # 🔒 不自动发布，输出结构化确认请求让 AI 询问用户
        print(json.dumps({
            "need_publish_confirm": True,
            "stage": "post_generate",
            "message": "网站生成成功！是否需要发布到线上？⚠️ 发布网站将覆盖线上版本，此操作无法撤销还原！",
            "options": ["确认发布", "暂不发布"],
            "tip": "回复「确认发布」发布到线上，回复「暂不发布」保留当前状态"
        }, ensure_ascii=False))
        # 保留状态文件以便重试，10 分钟后自动过期
        state["generated_at"] = datetime.now().isoformat()
        state["generate_result"] = "success"
        save_state(state)
    else:
        print(f"\n生成失败: {result.get('msg', '未知错误')}")
        print("💡 可重新执行 generate 命令重试")
        # 保留状态文件以便重试
        state["generate_result"] = "failed"
        state["generate_error"] = result.get("msg", "未知错误")
        save_state(state)


# ═══════════════════════════════════════════════════════════════════════════════
# API 调用
# ═══════════════════════════════════════════════════════════════════════════════

def check_site_languages():
    headers = {"Authorization": API_KEY, "Content-Type": "application/json",
               "User-Agent": "nicebox-openclaw-skill/1.0"}
    try:
        req = urllib.request.Request(ENDPOINT_LANGUAGE_LIST, data=b"{}",
                                      headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 0:
                return result.get("data", {}).get("list", [])
    except Exception:
        pass
    return []


def initialize_site():
    headers = {"Authorization": API_KEY, "Content-Type": "application/json",
               "User-Agent": "nicebox-openclaw-skill/1.0"}
    try:
        req = urllib.request.Request(
            ENDPOINT_INITIALIZE,
            data=json.dumps({}, ensure_ascii=False).encode("utf-8"),
            headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"code": 1, "msg": f"HTTP {e.code}"}
    except Exception as e:
        return {"code": 1, "msg": str(e)}


def call_get_company_info(collected):
    info = sanitize_company_info(collected)
    headers = {"Authorization": API_KEY, "Content-Type": "application/json",
               "User-Agent": "nicebox-openclaw-skill/1.0"}
    try:
        req = urllib.request.Request(
            ENDPOINT_GET_COMPANY_INFO,
            data=json.dumps(info, ensure_ascii=False).encode("utf-8"),
            headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"code": 1, "msg": f"HTTP {e.code}"}
    except Exception as e:
        return {"code": 1, "msg": str(e)}


def call_generate_website(requirement):
    """
    SSE 流式生成网站。
    返回：{"code": 0, "html_file": ..., "html_len": N, "issues": [...], "timed_out": bool}
          或 {"code": 非0, "msg": "..."}
    """
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "User-Agent": "nicebox-openclaw-skill/1.0",
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"website_{timestamp}.html"
    )

    try:
        req = urllib.request.Request(
            ENDPOINT_GENERATE_WEBSITE,
            data=json.dumps({"requirement": requirement}, ensure_ascii=False).encode("utf-8"),
            headers=headers, method="POST")

        orig_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(300)

        html_content = ""
        buffer = ""
        section_index = 0
        section_names = ["Header", "Hero", "Services", "About", "Team",
                         "Contact", "Footer", "Products", "News", "FAQ"]
        last_display_chars = 0
        last_save_time = time_module.time()
        last_progress = ""

        print("\n🎨 网站生成中（SSE 流式）...")

        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                while True:
                    chunk = resp.read(4096)
                    if not chunk:
                        break
                    buffer += chunk.decode("utf-8", errors="replace")
                    lines = buffer.split("\n")
                    buffer = lines.pop()

                    for line in lines:
                        line = line.strip()
                        if not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if not data_str:
                            continue

                        try:
                            event = json.loads(data_str)
                        except json.JSONDecodeError:
                            if "<!DOCTYPE" in data_str or "<html" in data_str:
                                html_content += data_str
                            continue

                        etype = event.get("type", "")
                        emsg = event.get("message", "")

                        if etype == "progress":
                            pct = event.get("percentage")
                            msg = event.get("message", "")
                            if pct is not None:
                                last_progress = f"{pct}%"
                            elif msg:
                                last_progress = msg
                            if html_content and (len(html_content) - last_display_chars) >= 5000:
                                sys.stdout.write(f"\r📊 已接收 {len(html_content)} 字符 {last_progress}    ")
                                sys.stdout.flush()
                                last_display_chars = len(html_content)

                        elif etype == "section_generating":
                            section_index += 1
                            sec = event.get("section")
                            sec_name = sec if sec else (
                                section_names[section_index - 1]
                                if section_index <= len(section_names)
                                else f"区块{section_index}"
                            )
                            print(f"\n🔨 正在生成: {sec_name}（{section_index}）")

                        elif etype == "progressive_content":
                            content = event.get("content", "")
                            if content:
                                html_content += content
                                if time_module.time() - last_save_time > 30:
                                    try:
                                        with open(output_file + ".draft", "w", encoding="utf-8") as f:
                                            f.write(html_content)
                                        sys.stdout.write(f"\r💾 [断点] {len(html_content)} 字符已保存     ")
                                        sys.stdout.flush()
                                        last_save_time = time_module.time()
                                    except Exception:
                                        pass

                        elif etype == "section_complete":
                            sec = event.get("section")
                            sec_name = sec if sec else (
                                section_names[section_index - 1]
                                if section_index > 0 else "区块"
                            )
                            print(f"  ✅ {sec_name} 完成")

                        elif etype == "complete":
                            print("\n🎉 网站生成完成！")

                        elif etype == "error":
                            print(f"\n❌ SSE 错误: {emsg}")

        finally:
            socket.setdefaulttimeout(orig_timeout)

    except socket.timeout:
        print("\n\n⏰ SSE 生成超时（3 分钟），正在保存当前内容...")
        if html_content:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            return {"code": 0, "html_file": output_file,
                    "html_len": len(html_content), "timed_out": True,
                    "issues": ["SSE 超时，内容可能不完整"]}
        return {"code": 1, "msg": "SSE 超时，未收到任何内容"}

    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"code": e.code, "msg": f"HTTP {e.code}"}
    except Exception as e:
        return {"code": 1, "msg": str(e)}

    # 处理残留 buffer
    if buffer.strip():
        try:
            ev = json.loads(buffer.strip())
            if ev.get("type") == "progressive_content":
                c = ev.get("content", "")
                if c:
                    html_content += c
        except json.JSONDecodeError:
            if "<!DOCTYPE" in buffer or "<html" in buffer:
                html_content += buffer

    # 保存并验证
    if html_content:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"\n💾 HTML 已保存: {output_file}（{len(html_content)} 字符）")
        issues = validate_html(html_content)
        if issues:
            print("\n⚠️ HTML 验证发现问题:")
            for iss in issues:
                print(f"  - {iss}")
        else:
            print("✅ HTML 验证通过")
        return {"code": 0, "html_file": output_file,
                "html_len": len(html_content), "issues": issues, "timed_out": False}

    return {"code": 1, "msg": "未收到 HTML 内容"}


# ═══════════════════════════════════════════════════════════════════════════════
# 追问：从已回答中提取子字段
# ═══════════════════════════════════════════════════════════════════════════════

def build_followup_question(parent_field, sub_field):
    """根据父字段的回答构建追问问题。"""
    prompts = {
        "email": {
            "question": "请提供您的联系邮箱？",
            "placeholder": "例如：contact@example.com",
        },
        "address": {
            "question": "请提供您的公司地址？",
            "placeholder": "例如：北京市朝阳区建国门外大街1号国贸大厦B座15层",
        },
    }
    return prompts.get(sub_field, {"question": f"请提供{FIELD_LABELS.get(sub_field, sub_field)}？",
                                     "placeholder": ""})


def auto_extract_from_parent(parent_field, sub_field, parent_answer):
    """
    尝试从父字段的回答中自动提取子字段信息。
    返回提取到的内容，或 None（无法提取，需要追问）。
    """
    if sub_field == "email":
        # 从 parent_answer 中提取邮箱
        phones, emails = [], []
        # 简单邮箱提取
        found = re.findall(r"[\w.\-]+@[\w.\-]+\.\w+", parent_answer)
        if found:
            return found[0]
    elif sub_field == "address":
        # 地址特征词
        match = re.search(
            r"[\u4e00-\u9fa5]{2,}[\u4e00-\u9fa5\s\d\-省市区县镇路街号楼单元层座]",
            parent_answer
        )
        if match:
            return match.group().strip()
    # 其他字段暂不自动提取
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# CLI 模式
# ═══════════════════════════════════════════════════════════════════════════════

def mode_status():
    """查看当前进度。"""
    state = load_state()
    current = state.get("current_index", 0)
    collected = state.get("collected", {})
    pending = state.get("pending_followups", [])
    answered = [v for v in collected.values() if v and v != "未填写"]

    result = {
        "status": "in_progress" if current < len(QUESTIONS) or pending else "ready_to_generate",
        "total_questions": len(QUESTIONS),
        "answered_count": len(answered),
        "pending_followups": pending,
        "current_question_index": current,
        "next_question": (
            {"field": pending[0], **build_followup_question(None, pending[0])}
            if pending else (
                QUESTIONS[current] if current < len(QUESTIONS) else None
            )
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def mode_questions():
    """列出全部 7 个问题。"""
    out = [{
        "index": i,
        "field": q["field"],
        "label": FIELD_LABELS.get(q["field"], q["field"]),
        "question": q["question"],
        "placeholder": q.get("placeholder", ""),
        "required": q.get("required", False),
        "followups": q.get("followups", []),
    } for i, q in enumerate(QUESTIONS)]
    print(json.dumps(out, ensure_ascii=False, indent=2))


def mode_next():
    """打印下一个要问的问题（含追问）。"""
    state = load_state()
    pending = state.get("pending_followups", [])
    current = state.get("current_index", 0)

    if pending:
        sub = pending[0]
        prompt = build_followup_question(None, sub)
        print(json.dumps({
            "done": False,
            "type": "followup",
            "field": sub,
            "label": FIELD_LABELS.get(sub, sub),
            "question": prompt["question"],
            "placeholder": prompt.get("placeholder", ""),
            "tip": "回复「跳过」跳过此项",
        }, ensure_ascii=False, indent=2))
        return

    if current >= len(QUESTIONS):
        print(json.dumps({"done": True, "message": "所有问题已收集完毕，请生成网站"}))
        return

    q = QUESTIONS[current]
    print(json.dumps({
        "done": False,
        "type": "main",
        "index": current,
        "field": q["field"],
        "label": FIELD_LABELS.get(q["field"], q["field"]),
        "question": q["question"],
        "placeholder": q.get("placeholder", ""),
        "required": q.get("required", False),
        "followups": q.get("followups", []),
        "tip": "回复「跳过」跳过此题（记为未填写），回复「完成」提前结束",
    }, ensure_ascii=False, indent=2))


def mode_answer(args):
    """记录用户回答，支持追问流程。"""
    raw = args.answer.strip()

    # 特殊命令
    if raw == "跳过":
        answer = "未填写"
    elif raw == "完成":
        state = load_state()
        state["finished_early"] = True
        save_state(state)
        print_summary(state.get("collected", {}))
        return
    else:
        answer = raw if raw else "未填写"

    state = load_state()
    pending = state.get("pending_followups", [])

    # ── 追问模式：处理子字段回答 ──
    if pending:
        sub_field = pending[0]
        if raw == "跳过":
            state["pending_followups"] = pending[1:]
            save_state(state)
            if state["pending_followups"]:
                next_sub = state["pending_followups"][0]
                prompt = build_followup_question(None, next_sub)
                print(json.dumps({
                    "type": "followup",
                    "field": next_sub,
                    "label": FIELD_LABELS.get(next_sub, next_sub),
                    "question": prompt["question"],
                    "placeholder": prompt.get("placeholder", ""),
                    "hint": "可回复「跳过」跳过此项",
                }, ensure_ascii=False))
            else:
                advance(state)
            return
        
        state["collected"][sub_field] = answer
        state["pending_followups"] = pending[1:]
        save_state(state)
        
        if state["pending_followups"]:
            next_sub = state["pending_followups"][0]
            prompt = build_followup_question(None, next_sub)
            print(json.dumps({
                "type": "followup",
                "field": next_sub,
                "label": FIELD_LABELS.get(next_sub, next_sub),
                "question": prompt["question"],
                "placeholder": prompt.get("placeholder", ""),
                "hint": "可回复「跳过」跳过此项",
            }, ensure_ascii=False))
        else:
            advance(state)
        return

    # ── 主问题模式 ──
    if raw == "跳过":
        state = load_state()
        if state.get("current_index", 0) < len(QUESTIONS):
            state["collected"][QUESTIONS[state["current_index"]]["field"]] = "未填写"
            state["current_index"] += 1
            save_state(state)
        advance(state)
        return

    if raw == "完成":
        state = load_state()
        state["finished_early"] = True
        save_state(state)
        print_summary(state.get("collected", {}))
        return

    state = load_state()
    current = state.get("current_index", 0)
    if current >= len(QUESTIONS) or state.get("finished_early"):
        print(json.dumps({"error": "所有问题已收集完毕"}))
        return

    q = QUESTIONS[current]
    field = q["field"]
    followups = q.get("followups", [])

    # 联系方式字段：智能解析
    if field == "phone":
        phone_val, email_val, address_val = parse_contact(answer)
        state["collected"]["phone"] = phone_val if phone_val else answer
        # 自动提取 email/address 并加入追问
        new_followups = []
        if email_val:
            state["collected"]["email"] = email_val
        else:
            new_followups.append("email")
        if address_val:
            state["collected"]["address"] = address_val
        else:
            new_followups.append("address")

        state["pending_followups"] = new_followups
        state["current_index"] = current + 1
        save_state(state)

        if new_followups:
            next_sub = new_followups[0]
            prompt = build_followup_question(field, next_sub)
            print(json.dumps({
                "collected": {
                    "phone": state["collected"].get("phone", ""),
                    "email": state["collected"].get("email", ""),
                    "address": state["collected"].get("address", ""),
                },
                "type": "followup",
                "field": next_sub,
                "label": FIELD_LABELS.get(next_sub, next_sub),
                "question": prompt["question"],
                "placeholder": prompt.get("placeholder", ""),
                "hint": "可回复「跳过」跳过此项",
            }, ensure_ascii=False))
        else:
            state["collected"]["phone"] = raw
            print(json.dumps({
                "collected": {
                    "phone": state["collected"].get("phone", ""),
                    "email": None,
                    "address": None,
                },
                "next": None,
                "all_contact_collected": True,
            }, ensure_ascii=False))
            advance(state)

    # 其他普通字段
    else:
        state["collected"][field] = answer
        state["current_index"] += 1
        save_state(state)
        advance(state)


def _advance_to_next(state, next_index):
    """推进到下一个问题，处理追问队列和提前结束。"""
    pending = state.get("pending_followups", [])

    if pending:
        next_sub = pending[0]
        prompt = build_followup_question(None, next_sub)
        print(json.dumps({
            "action": "next",
            "all_done": False,
            "next_type": "followup",
            "next_field": next_sub,
            "next_label": FIELD_LABELS.get(next_sub, next_sub),
            "next_question": prompt["question"],
            "next_placeholder": prompt.get("placeholder", ""),
        }, ensure_ascii=False, indent=2))
        return

    if next_index >= len(QUESTIONS) or state.get("finished_early"):
        answered = len([v for v in state["collected"].values()
                       if v and v != "未填写"])
        skipped = len([v for v in state["collected"].values()
                       if v == "未填写"])
        print(json.dumps({
            "action": "all_done",
            "answered_count": answered,
            "skipped_count": skipped,
            "message": f"所有问题收集完毕！共 {answered} 项已填，{skipped} 项跳过。请生成网站。",
        }, ensure_ascii=False, indent=2))
    else:
        q = QUESTIONS[next_index]
        print(json.dumps({
            "action": "next",
            "all_done": False,
            "next_type": "main",
            "next_index": next_index,
            "next_field": q["field"],
            "next_label": FIELD_LABELS.get(q["field"], q["field"]),
            "next_question": q["question"],
            "next_placeholder": q.get("placeholder", ""),
            "required": q.get("required", False),
            "followups": q.get("followups", []),
            "tip": "回复「跳过」跳过此题，回复「完成」提前结束",
        }, ensure_ascii=False, indent=2))


def mode_summary():
    """显示汇总（生成前确认）。"""
    state = load_state()
    collected = state.get("collected", {})
    info = sanitize_company_info(collected)

    lines = ["=" * 50, "📋 网站需求汇总", "=" * 50, ""]
    for q in QUESTIONS:
        f = q["field"]
        v = info.get(f, "未填写")
        tag = " ⭐必填" if f in REQUIRED_API_FIELDS else ""
        lines.append(f"  {FIELD_LABELS.get(f, f)}：{v}{tag}")
    # 追问字段也显示
    for f in ["email", "address"]:
        if f in collected and collected[f] and collected[f] != "未填写":
            lines.append(f"  {FIELD_LABELS.get(f, f)}：{collected[f]}")

    lines += ["", "=" * 50]
    print("\n".join(lines))

    answered = len([v for v in info.values() if v != "未填写"])
    skipped = len([v for v in info.values() if v == "未填写"])
    print(json.dumps({
        "answered_count": answered,
        "skipped_count": skipped,
        "collected": info,
    }, ensure_ascii=False, indent=2))


def mode_generate(args):
    """
    生成网站主流程：
      1. 检查是否有语言数据 → 需要用户确认
      2. 用户回复「确认」→ 初始化 → 生成
      3. 用户回复「取消」→ 退出
      4. 其他回复 → 重新询问
    """
    state = load_state()
    init_confirmed = state.get("init_confirmed")
    languages = check_site_languages()

    # ── 尚未确认初始化 ──
    if init_confirmed is None:
        if languages:
            print(json.dumps({
                "action": "confirm_init",
                "message": (
                    "⚠️ 检测到站点已有语言配置，继续生成将清空所有页面、产品、文章和留言。\n\n"
                    "请回复「确认」继续初始化并生成网站\n"
                    "请回复「取消」取消操作"
                ),
                "options": ["确认", "取消"],
            }, ensure_ascii=False, indent=2))
        else:
            # 无数据，自动初始化
            state["init_confirmed"] = True
            state["initialized"] = True
            save_state(state)
            result = initialize_site()
            if result.get("code") == 0:
                print(json.dumps({"action": "auto_init_ok", "message": "✅ 站点为空，已自动初始化"}))
            else:
                print(json.dumps({"action": "auto_init_warn",
                                  "message": f"⚠️ 自动初始化失败: {result.get('msg', '')}，继续尝试生成..."}))
            _do_generate(state)
        return

    # ── 用户已回复「取消」─
    if init_confirmed is False:
        print(json.dumps({
            "action": "cancelled",
            "message": "已取消操作，不生成网站。如需重新生成，请先重置状态。",
        }, ensure_ascii=False))
        return

    # ── 用户已回复「确认」─
    if init_confirmed is True and not state.get("initialized"):
        result = initialize_site()
        if result.get("code") == 0:
            state["initialized"] = True
            save_state(state)
            print(json.dumps({"action": "init_ok", "message": "✅ 确认初始化完成，正在生成网站..."}))
            _do_generate(state)
        else:
            print(json.dumps({"action": "init_failed",
                              "message": f"❌ 初始化失败: {result.get('msg', '')}，无法生成网站"}))
        return

    # ── 已初始化，继续生成 ──
    _do_generate(state)


def mode_init_confirm(args):
    """处理用户对初始化确认的回复。"""
    raw = args.answer.strip()
    state = load_state()

    if raw in ("确认", "是", "确认初始化", "确认"):
        state["init_confirmed"] = True
        save_state(state)
        result = initialize_site()
        if result.get("code") == 0:
            state["initialized"] = True
            save_state(state)
            print(json.dumps({"action": "init_ok", "message": "✅ 确认初始化完成，正在生成网站..."}))
            _do_generate(state)
        else:
            print(json.dumps({"action": "init_failed",
                              "message": f"❌ 初始化失败: {result.get('msg', '')}，无法生成网站"}))
        return

    if raw in ("取消", "取消操作", "否", "不生成"):
        state["init_confirmed"] = False
        save_state(state)
        print(json.dumps({
            "action": "cancelled",
            "message": "已取消操作，不生成网站。如需重新生成，请先重置状态。",
        }, ensure_ascii=False))
        return

    # 其他回复：重新询问
    print(json.dumps({
        "action": "confirm_again",
        "message": (
            "请明确回复「确认」继续初始化并生成网站\n"
            "或回复「取消」取消操作"
        ),
        "options": ["确认", "取消"],
    }, ensure_ascii=False))


def _do_generate(state):
    """执行实际生成流程。"""
    collected = state.get("collected", {})
    info = sanitize_company_info(collected)

    for f in REQUIRED_API_FIELDS:
        if info.get(f) == "未填写":
            print(f"⚠️ 提示：{FIELD_LABELS.get(f, f)} 为「未填写」，可能影响生成效果")

    print("📡 正在获取企业信息...")
    info_result = call_get_company_info(collected)
    if info_result.get("code") != 0:
        print(f"❌ 获取企业信息失败: {info_result.get('msg', '')}")
        sys.exit(1)

    company_info = info_result.get("data", "")
    if not company_info:
        print("❌ 企业信息为空，无法生成网站")
        sys.exit(1)

    requirement = f"请根据以下信息生成网站：\n{company_info}"
    print("🚀 正在生成网站（预计 1-3 分钟）...")

    result = call_generate_website(requirement)

    if result.get("code") == 0:
        html_len = result.get("html_len", 0)
        html_file = result.get("html_file", "")
        issues = result.get("issues", [])
        timed_out = result.get("timed_out", False)

        if timed_out:
            print(f"\n⚠️ 生成超时，内容可能不完整")
        else:
            print(f"\n✅ 网站生成成功！")
        print(f"💾 文件已保存: {html_file}（{html_len} 字符）")
        if issues:
            for iss in issues:
                print(f"  ⚠️ {iss}")
        print(json.dumps({
            "ok": True, "html_file": html_file, "html_len": html_len,
            "timed_out": timed_out, "issues": issues,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"\n❌ 生成失败: {result.get('msg', 'Unknown error')}")
        sys.exit(1)

    reset_state()


# ═══════════════════════════════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════════════════════════════

def mode_ask_init():
    """第1次确认，收集问题前"""
    state = load_state()
    
    # 已取消
    if state.get("init_confirmed") is False:
        print("您之前已取消操作，请先 reset 后重新开始。")
        return
    
    # 已确认且已初始化 → 直接显示下一题
    if state.get("init_confirmed") is True and state.get("initialized"):
        print("已确认并初始化完成，请直接回答以下问题：")
        next_q = QUESTIONS[state.get("current_index", 0)] if state.get("current_index", 0) < len(QUESTIONS) else None
        if next_q:
            print(json.dumps({
                "index": state.get("current_index", 0),
                "total": len(QUESTIONS),
                "field": next_q["field"],
                "label": FIELD_LABELS.get(next_q["field"], next_q["field"]),
                "question": next_q["question"],
                "placeholder": next_q.get("placeholder", ""),
                "required": next_q.get("required", False),
                "hint": "可回复「跳过」跳过此题，回复「完成」提前结束所有问答",
            }, ensure_ascii=False))
        return
    
    # 等待回复中 → 再次弹出提示
    if state.get("init_confirmed") == "pending":
        output_confirm_prompt("ask-init")
        return
    
    # 首次检查
    languages = check_site_languages()
    if languages:
        # 有数据 → 弹出确认
        state["init_confirmed"] = "pending"
        save_state(state)
        output_confirm_prompt("ask-init")
    else:
        # 无数据 → 自动初始化，直接进入收集问题
        state["init_confirmed"] = True
        print("站点为空，正在自动初始化...")
        do_initialize(state, "自动初始化")
        print("请直接回答以下问题：")
        next_q = QUESTIONS[state.get("current_index", 0)] if state.get("current_index", 0) < len(QUESTIONS) else None
        if next_q:
            print(json.dumps({
                "index": state.get("current_index", 0),
                "total": len(QUESTIONS),
                "field": next_q["field"],
                "label": FIELD_LABELS.get(next_q["field"], next_q["field"]),
                "question": next_q["question"],
                "placeholder": next_q.get("placeholder", ""),
                "required": next_q.get("required", False),
                "hint": "可回复「跳过」跳过此题，回复「完成」提前结束所有问答",
            }, ensure_ascii=False))


def mode_confirm(args):
    """统一确认命令，两个阶段共用"""
    raw = args.answer.strip()
    state = load_state()
    
    # 第1次确认待回复（ask-init 阶段）
    if state.get("init_confirmed") == "pending":
        if raw == "确认":
            state["init_confirmed"] = True
            save_state(state)
            do_initialize(state, "收到确认")
            # 显示下一题
            answered = len([v for v in state.get("collected", {}).values() if v and v != "未填写"])
            print(f"\n当前进度：已回答 {answered}/{len(QUESTIONS)} 题")
            if state.get("current_index", 0) < len(QUESTIONS):
                q = QUESTIONS[state.get("current_index", 0)]
                print(json.dumps({
                    "index": state.get("current_index", 0),
                    "total": len(QUESTIONS),
                    "field": q["field"],
                    "label": FIELD_LABELS.get(q["field"], q["field"]),
                    "question": q["question"],
                    "placeholder": q.get("placeholder", ""),
                    "required": q.get("required", False),
                    "hint": "可回复「跳过」跳过此题，回复「完成」提前结束所有问答",
                }, ensure_ascii=False))
            else:
                print("所有问题已收集完毕，请输入：python generate_website.py generate")
        elif raw == "取消":
            state["init_confirmed"] = False
            save_state(state)
            print("已取消，后续操作已终止。\n如需重新开始，请输入：python generate_website.py reset")
        else:
            output_confirm_prompt("ask-init")
        return
    
    # 第2次确认待回复（generate 阶段）
    if state.get("generate_confirmed") == "pending":
        if raw == "确认":
            state["generate_confirmed"] = True
            save_state(state)
            # 确认后初始化并生成
            if not state.get("initialized"):
                do_initialize(state, "收到确认")
            do_generate(state)
        elif raw == "取消":
            state["generate_confirmed"] = False
            save_state(state)
            print("已取消，后续操作已终止。\n如需重新开始，请输入：python generate_website.py reset")
        else:
            output_confirm_prompt("generate")
        return
    
    # 没有待确认的
    print("当前没有待确认的操作。")


def mode_generate(args):
    """第2次确认，生成网站前"""
    state = load_state()
    
    # 任一阶段已取消
    if state.get("init_confirmed") is False or state.get("generate_confirmed") is False:
        print("操作已取消，无法生成网站。如需重新开始，请先 reset。")
        return
    
    # 第1次确认还在等待
    if state.get("init_confirmed") == "pending":
        print("请先完成初始化确认（ask-init 阶段）。")
        output_confirm_prompt("ask-init")
        return
    
    # 第2次确认等待回复中
    if state.get("generate_confirmed") == "pending":
        output_confirm_prompt("generate")
        return
    
    # 第2次已确认 → 直接生成
    if state.get("generate_confirmed") is True:
        if not state.get("initialized"):
            do_initialize(state, "正在初始化站点")
        do_generate(state)
        return
    
    # ── 首次进入 generate，检查站点数据（第2次确认） ──
    languages = check_site_languages()
    if languages:
        # 有数据 → 弹出第2次确认
        state["generate_confirmed"] = "pending"
        save_state(state)
        output_confirm_prompt("generate")
    else:
        # 无数据 → 直接生成
        state["generate_confirmed"] = True
        save_state(state)
        if not state.get("initialized"):
            do_initialize(state, "站点为空，自动初始化")
        do_generate(state)


def main():
    parser = argparse.ArgumentParser(
        description="生成网站 - 交互式多轮对话（Python 版 · 双重确认机制）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
推荐工作流程：
  1. ask-init          ← 【必须第一步】检查站点数据（第1次确认）
  2. answer "内容"     ← 逐题收集信息（可随时「跳过」或「完成」）
  3. summary           ← 查看汇总确认
  4. generate          ← 生成网站（第2次确认）

双重确认说明：
  ask-init 和 generate 都会检查站点数据
  如果站点有数据，两次都会弹出相同的确认提示
  确认 → 初始化站点并继续  |  取消 → 终止所有操作

命令列表：
  python generate_website.py reset              # 重置对话状态
  python generate_website.py status             # 查看当前进度
  python generate_website.py ask-init           # 【第1步】检查站点（第1次确认）
  python generate_website.py confirm "确认"     # 确认（两个阶段通用）
  python generate_website.py confirm "取消"     # 取消（两个阶段通用）
  python generate_website.py questions          # 列出全部 8 个问题
  python generate_website.py next               # 打印下一题
  python generate_website.py answer "内容"      # 记录回答
  python generate_website.py summary            # 显示需求汇总
  python generate_website.py generate           # 【第4步】生成网站（第2次确认）
        """,
    )
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("status", help="查看进度")
    sub.add_parser("questions", help="列出所有问题")
    sub.add_parser("next", help="打印下一个问题")
    
    answer_parser = sub.add_parser("answer", help="记录回答")
    answer_parser.add_argument("answer", help="用户回复内容")
    
    confirm_parser = sub.add_parser("confirm", help="确认（两个阶段通用）")
    confirm_parser.add_argument("answer", help="确认回复（确认/取消）")
    
    sub.add_parser("ask-init", help="【第1步】检查站点（第1次确认）")
    sub.add_parser("summary", help="显示汇总")
    sub.add_parser("generate", help="【第4步】生成网站（第2次确认）")
    sub.add_parser("reset", help="重置状态")

    args = parser.parse_args()

    if not API_KEY:
        print(json.dumps({"error": "AIBOX_API_KEY not set"}))
        sys.exit(2)

    if args.cmd == "status":
        mode_status()
    elif args.cmd == "questions":
        mode_questions()
    elif args.cmd == "next":
        mode_next()
    elif args.cmd == "answer":
        mode_answer(args)
    elif args.cmd == "confirm":
        mode_confirm(args)
    elif args.cmd == "ask-init":
        mode_ask_init()
    elif args.cmd == "summary":
        mode_summary()
    elif args.cmd == "generate":
        mode_generate(args)
    elif args.cmd == "reset":
        reset_state()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
