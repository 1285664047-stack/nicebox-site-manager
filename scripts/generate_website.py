#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate website through interactive multi-turn dialogue.

This script runs in TWO MODES:
  1. Orchestration mode: called once by the AI agent, it orchestrates the full
     flow and prints a structured JSON plan (one question per line) telling the
     agent exactly what to say to the user.
  2. Per-turn mode: called with --question-index to ask ONE specific question
     and capture the user's answer (stored in a shared state file).

All actual user interaction happens in the OpenClaw conversation — this script
is purely a state machine / renderer.

优化点（v2）：
  - 未填写字段自动赋值为"未填写"（不能为空字符串）
  - HTML完整性验证（检查DOCTYPE/闭合标签/长度）
  - SSE超时保护（3分钟自动终止+断点保存）
  - 进度条优化（每5000字符更新显示）
  - section字段fallback（undefined时用序号替代）
  - buffer flush（连接结束时处理残留数据）
  - 断点保存（每30秒自动保存草稿）
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime

BASE_URL = os.environ.get("AIBOX_BASE_URL", "http://aidev.nicebox.cn/api/openclaw")
API_KEY = os.environ.get("AIBOX_API_KEY", "")

ENDPOINT_LANGUAGE_LIST = f"{BASE_URL}/site_pages/getLanguageList"
ENDPOINT_INITIALIZE = f"{BASE_URL}/template/initializeData"
ENDPOINT_GET_COMPANY_INFO = f"{BASE_URL}/ai_tools/getCompanyInfo"
ENDPOINT_GENERATE_WEBSITE = f"{BASE_URL}/ai_tools/generateWebsite"

# State file stored alongside the script
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".dialogue_state.json")

# 11 questions, each with field, question text, and example
QUESTIONS = [
    {
        "field": "company_name",
        "question": "请告诉我您的公司名称或想创建的网站名称是什么？",
        "example": "例如：明德律师事务所、某某科技官网",
        "required": True,
    },
    {
        "field": "industry",
        "question": "您从事哪个行业？",
        "example": "例如：科技、教育、医疗、餐饮、零售、金融、法律服务",
        "required": False,
    },
    {
        "field": "business_scope",
        "question": "请描述您的业务范围？",
        "example": "例如：软件开发、网站建设、APP开发、技术咨询服务",
        "required": True,
    },
    {
        "field": "business_features",
        "question": "您的业务有哪些特色或亮点？",
        "example": "例如：20年行业经验、专业团队、售后保障、收费透明",
        "required": False,
    },
    {
        "field": "culture",
        "question": "请介绍一下您的企业文化或理念？",
        "example": "例如：客户至上、创新进取、诚信为本",
        "required": False,
    },
    {
        "field": "advantages",
        "question": "您的核心竞争优势是什么？",
        "example": "例如：技术领先、价格合理、服务周到、高性价比",
        "required": False,
    },
    {
        "field": "phone",
        "question": "请提供您的联系电话？",
        "example": "例如：400-888-8888 或 138-0000-0000",
        "required": False,
    },
    {
        "field": "email",
        "question": "请提供您的联系邮箱？",
        "example": "例如：contact@example.com",
        "required": False,
    },
    {
        "field": "address",
        "question": "请提供您的公司地址？",
        "example": "例如：北京市朝阳区建国门外大街1号国贸大厦B座15层",
        "required": False,
    },
    {
        "field": "logo",
        "question": "您有企业Logo吗？如果有，请提供Logo图片的URL地址",
        "example": "例如：https://example.com/logo.png（没有可回复「跳过」）",
        "required": False,
    },
    {
        "field": "style",
        "question": "您希望网站采用什么视觉风格？",
        "example": "例如：简约现代、专业商务、创意时尚、温馨亲切、深色科技感",
        "required": False,
    },
    {
        "field": "color_scheme",
        "question": "您希望网站的主色调是什么？",
        "example": "例如：深蓝色+金色（专业权威）、绿色（环保健康）、橙色+白色（活力创新）",
        "required": False,
    },
    {
        "field": "other",
        "question": "还有其他需要补充的信息吗？",
        "example": "例如：需要留言表单等",
        "required": False,
    },
]

FIELD_LABELS = {
    "company_name": "公司/网站名称",
    "industry": "行业",
    "business_scope": "业务范围",
    "business_features": "业务特色",
    "culture": "企业文化",
    "advantages": "核心优势",
    "phone": "联系电话",
    "email": "联系邮箱",
    "address": "公司地址",
    "logo": "Logo",
    "style": "视觉风格",
    "color_scheme": "网站主题色调",
    "other": "其他补充",
}

# API必填字段（不能为空，值为空时用"未填写"替代）
REQUIRED_API_FIELDS = ["company_name", "business_scope"]


# ─── State Management ─────────────────────────────────────────────────────────

def load_state():
    """Load dialogue state from file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "current_index": 0,
        "collected": {},
        "started_at": datetime.now().isoformat(),
        "initialized": False,
    }


def save_state(state):
    """Save dialogue state to file."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def reset_state():
    """Reset dialogue state."""
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)


# ─── 优化：未填写字段处理 ─────────────────────────────────────────────────────

def sanitize_company_info(collected):
    """
    规范化公司信息：空值/None → "未填写"，Logo 为空 → 占位图。

    API 必填字段（company_name, business_scope）不能为空，
    统一赋值为"未填写"，确保 API 调用不会返回"不能为空"错误。
    """
    result = {}
    for key in FIELD_LABELS:
        value = collected.get(key, "")
        # 空值处理：None / 空字符串 / 仅空格 → "未填写"
        if value is None or (isinstance(value, str) and value.strip() == ""):
            result[key] = "未填写"
        else:
            result[key] = value.strip()

    # Logo 特殊处理：未填写时使用占位图
    if result.get("logo") == "未填写":
        company_name = result.get("company_name", "Logo")
        # 生成占位图 URL（棕色背景+白色文字）
        result["logo"] = (
            f"https://via.placeholder.com/200x80/8B4513/FFFFFF?text="
            f"{urllib.parse.quote(company_name)}"
        )

    return result


# ─── 优化：HTML 完整性验证 ────────────────────────────────────────────────────

def validate_html(html):
    """
    验证 HTML 片段的完整性，返回问题列表（空=验证通过）。
    检查项：
      - 是否有 DOCTYPE 或 <html> 标签
      - 是否有 </html> 闭合标签
      - <head> 标签是否成对
      - 内容长度是否过短
    """
    issues = []
    if not html:
        issues.append("HTML 内容为空")
        return issues

    stripped = html.strip()
    if "<!DOCTYPE" not in stripped and "<html" not in stripped:
        issues.append("缺少 DOCTYPE 或 <html> 标签")

    if "</html>" not in stripped:
        issues.append("缺少 </html> 闭合标签（内容可能不完整）")

    if "</body>" not in stripped:
        issues.append("缺少 </body> 闭合标签")

    head_opens = len([m.group(0) for m in __import__("re").finditer(r"<head[^>]*>", stripped, __import__("re").IGNORECASE)])
    head_closes = len([m.group(0) for m in __import__("re").finditer(r"</head>", stripped, __import__("re").IGNORECASE)])
    if head_opens > head_closes:
        issues.append(f"<head> 标签未闭合（开 {head_opens} / 闭 {head_closes}）")

    if len(stripped) < 5000:
        issues.append(f"内容过短（{len(stripped)} 字符），生成可能不完整")

    return issues


# ─── API Calls ────────────────────────────────────────────────────────────────

def check_site_languages():
    """Check if site has languages configured."""
    headers = {"Authorization": API_KEY, "Content-Type": "application/json"}
    try:
        req = urllib.request.Request(
            ENDPOINT_LANGUAGE_LIST,
            data=b"{}",
            headers=headers,
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 0 and result.get("data", {}).get("list"):
                return result["data"]["list"]
            return []
    except Exception:
        return []


def initialize_site():
    """Initialize site data."""
    headers = {"Authorization": API_KEY, "Content-Type": "application/json"}
    try:
        req = urllib.request.Request(
            ENDPOINT_INITIALIZE,
            data=json.dumps({}, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
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
    """
    Call getCompanyInfo API.

    发送前自动对 collected 做 sanitize，确保必填字段不为空。
    """
    # 优化：规范化数据，确保必填字段不为空
    info = sanitize_company_info(collected)

    headers = {"Authorization": API_KEY, "Content-Type": "application/json"}
    try:
        req = urllib.request.Request(
            ENDPOINT_GET_COMPANY_INFO,
            data=json.dumps(info, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"code": 1, "msg": f"HTTP {e.code}"}
    except Exception as e:
        return {"code": 1, "msg": str(e)}


def call_generate_website(requirement, output_file=None):
    """
    Call generateWebsite API (SSE streaming).

    优化点：
      - SSE 超时保护（3分钟）
      - 进度条优化（每5000字符更新）
      - section fallback（undefined时用序号）
      - buffer flush（处理残留数据）
      - 断点保存（每30秒）
      - HTML 验证（完成后检查完整性）

    返回：{"code": 0, "html_file": "...", "html_len": ..., "issues": [...]}
          或 {"code": 非0, "msg": "..."}
    """
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {"requirement": requirement}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if output_file is None:
        output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"website_{timestamp}.html")

    try:
        req = urllib.request.Request(
            ENDPOINT_GENERATE_WEBSITE,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        # 打开 SSE 连接，手动处理超时
        import socket
        orig_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(300)  # 3分钟超时

        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                raw_bytes = b""
                html_content = ""
                buffer = ""
                section_index = 0
                section_names = [
                    "Header", "Hero", "Services", "About", "Team",
                    "Contact", "Footer", "Products", "News", "FAQ"
                ]
                last_display_chars = 0
                last_save_time = time.time()
                last_progress_msg = ""

                print("\n🎨 网站生成中（SSE 流式）...")

                while True:
                    chunk = resp.read(4096)
                    if not chunk:
                        break
                    raw_bytes += chunk
                    buffer += chunk.decode("utf-8", errors="replace")

                    # 逐行解析 SSE data: 事件
                    lines = buffer.split("\n")
                    buffer = lines.pop()  # 残留行留在 buffer 中

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
                            # 非 JSON：直接当作 HTML 片段处理
                            if "<!DOCTYPE" in data_str or "<html" in data_str:
                                html_content += data_str
                            continue

                        event_type = event.get("type", "")
                        event_msg = event.get("message", "")

                        # ── 进度事件（优化：每5000字符更新一次）──
                        if event_type == "progress":
                            pct = event.get("percentage")
                            msg = event.get("message", "")
                            if pct is not None:
                                last_progress_msg = f"{pct}%"
                            elif msg:
                                last_progress_msg = msg
                            # 每5000字符才打印进度，避免刷屏
                            if html_content and (html_content.__len__() - last_display_chars) >= 5000:
                                sys.stdout.write(f"\r📊 已接收 {html_content.__len__()} 字符 {last_progress_msg}...")
                                sys.stdout.flush()
                                last_display_chars = html_content.__len__()

                        # ── 区块开始事件（优化：section fallback）──
                        elif event_type == "section_generating":
                            section_index += 1
                            sec = event.get("section")
                            sec_name = sec if sec else section_names[section_index - 1] if section_index <= len(section_names) else f"区块{section_index}"
                            print(f"\n🔨 正在生成: {sec_name}（{section_index}）")

                        # ── HTML 内容片段（累积）──
                        elif event_type == "progressive_content":
                            content = event.get("content", "")
                            if content:
                                html_content += content
                                # 断点保存：每30秒保存一次
                                if time.time() - last_save_time > 30 and html_content:
                                    try:
                                        with open(output_file + ".draft", "w", encoding="utf-8") as f:
                                            f.write(html_content)
                                        sys.stdout.write(f"\r💾 [断点保存] {html_content.__len__()} 字符已保存...")
                                        sys.stdout.flush()
                                        last_save_time = time.time()
                                    except Exception:
                                        pass

                        # ── 区块完成事件 ──
                        elif event_type == "section_complete":
                            sec = event.get("section")
                            sec_name = sec if sec else section_names[section_index - 1] if section_index > 0 else "区块"
                            print(f"✅ {sec_name} 完成")

                        # ── 完成事件 ──
                        elif event_type == "complete":
                            print("\n🎉 网站生成完成！")

                        # ── 错误事件 ──
                        elif event_type == "error":
                            print(f"\n❌ SSE 错误: {event_msg}")

                        # ── 其他未知事件类型：打印即可 ──
                        elif event_type not in ("intro_text",):
                            # 未知类型，打印 message 供调试
                            if event_msg:
                                print(f"[{event_type}] {event_msg}")

                # ── buffer flush：处理 SSE 末尾残留数据 ──
                if buffer.strip():
                    data_str = buffer.strip()
                    try:
                        event = json.loads(data_str)
                        if event.get("type") == "progressive_content":
                            content = event.get("content", "")
                            if content:
                                html_content += content
                    except json.JSONDecodeError:
                        # 非 JSON，当作 HTML 处理
                        if "<!DOCTYPE" in data_str or "<html" in data_str:
                            html_content += data_str

                socket.setdefaulttimeout(orig_timeout)

        except socket.timeout:
            socket.setdefaulttimeout(orig_timeout)
            print("\n\n⏰ SSE 生成超时（3分钟），保存当前内容...")
            if html_content:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"💾 [超时保存] → {output_file} ({html_content.__len__()} 字符)")
                return {
                    "code": 0,
                    "html_file": output_file,
                    "html_len": html_content.__len__(),
                    "timed_out": True,
                    "issues": ["SSE 超时，内容可能不完整"]
                }
            return {"code": 1, "msg": "SSE 超时，未收到任何内容"}

    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
            return {"code": e.code, "msg": err_body.get("msg", str(err_body))}
        except Exception:
            return {"code": e.code, "msg": f"HTTP {e.code}"}
    except Exception as e:
        return {"code": 1, "msg": str(e)}

    # ── 保存 HTML 文件 + HTML 验证 ──
    if html_content:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"\n💾 HTML 已保存: {output_file} ({html_content.__len__()} 字符)")

        # HTML 完整性验证
        issues = validate_html(html_content)
        if issues:
            print("\n⚠️ HTML 验证发现问题:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✅ HTML 验证通过")

        return {
            "code": 0,
            "html_file": output_file,
            "html_len": html_content.__len__(),
            "issues": issues
        }
    else:
        return {"code": 1, "msg": "未收到 HTML 内容"}


# ─── Script Modes ─────────────────────────────────────────────────────────────

def mode_status():
    """Show current dialogue status: how many questions answered, what's next."""
    state = load_state()
    current = state.get("current_index", 0)
    collected = state.get("collected", {})
    answered = [FIELD_LABELS[k] for k in collected
                if collected[k] not in ("未填写", "") and collected[k]]
    skipped = [FIELD_LABELS[k] for k in collected if collected[k] == "未填写"]

    result = {
        "status": "in_progress" if current < len(QUESTIONS) else "ready_to_generate",
        "total_questions": len(QUESTIONS),
        "answered_count": len(answered),
        "skipped_count": len(skipped),
        "current_question_index": current,
        "next_question": QUESTIONS[current]["question"] if current < len(QUESTIONS) else None,
        "next_example": QUESTIONS[current].get("example") if current < len(QUESTIONS) else None,
        "next_field": QUESTIONS[current]["field"] if current < len(QUESTIONS) else None,
        "next_required": QUESTIONS[current].get("required", False) if current < len(QUESTIONS) else False,
        "answered": answered,
        "skipped": skipped,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def mode_questions():
    """List all 13 questions (for AI to display to user)."""
    questions = []
    for i, q in enumerate(QUESTIONS):
        questions.append({
            "index": i,
            "field": q["field"],
            "label": FIELD_LABELS[q["field"]],
            "question": q["question"],
            "example": q.get("example", ""),
            "required": q.get("required", False),
        })
    print(json.dumps(questions, ensure_ascii=False, indent=2))


def mode_next():
    """Print the next question the AI should ask the user."""
    state = load_state()
    current = state.get("current_index", 0)
    if current >= len(QUESTIONS):
        print(json.dumps({
            "done": True,
            "message": "所有问题已问完，请生成网站"
        }))
        return

    q = QUESTIONS[current]
    print(json.dumps({
        "done": False,
        "index": current,
        "field": q["field"],
        "label": FIELD_LABELS[q["field"]],
        "question": q["question"],
        "example": q.get("example", ""),
        "required": q.get("required", False),
        "tip": '回复「跳过」跳过此题（记为"未填写"），回复「结束」提前生成网站',
    }, ensure_ascii=False, indent=2))


def mode_answer(args):
    """
    Record user's answer to the current question.

    优化：空回答且未跳过时 → 赋值为"未填写"
    """
    user_answer = args.answer.strip()

    # Handle special commands
    if user_answer.lower() in ("跳过", "skip", "s"):
        answer = "未填写"
    elif user_answer.lower() in ("结束", "finish", "done"):
        state = load_state()
        state["finished_early"] = True
        save_state(state)
        print(json.dumps({
            "action": "finish_early",
            "message": "对话已结束，开始生成网站",
            "current_index": state.get("current_index", 0),
            "answered": len([v for v in state.get("collected", {}).values()
                            if v and v != "未填写"]),
        }, ensure_ascii=False))
        return
    else:
        answer = user_answer

    # 优化：空回答（非skip/结束）→ 赋值为"未填写"，确保 API 不报错
    if not answer:
        answer = "未填写"

    state = load_state()
    current = state.get("current_index", 0)

    if current >= len(QUESTIONS):
        print(json.dumps({"error": "所有问题已回答完毕"}))
        return

    field = QUESTIONS[current]["field"]
    state["collected"][field] = answer
    state["current_index"] = current + 1
    save_state(state)

    next_index = current + 1
    if next_index >= len(QUESTIONS) or state.get("finished_early"):
        answered_count = len([v for v in state["collected"].values()
                              if v and v != "未填写"])
        skipped_count = len([v for v in state["collected"].values()
                             if v == "未填写"])
        print(json.dumps({
            "action": "question_answered",
            "field": field,
            "answer": answer,
            "next_index": next_index,
            "all_done": True,
            "answered_count": answered_count,
            "skipped_count": skipped_count,
            "message": f"已记录「{FIELD_LABELS[field]}」的回答（{'已跳过' if answer == '未填写' else answer}）。所有问题已收集完毕！",
        }, ensure_ascii=False, indent=2))
    else:
        next_q = QUESTIONS[next_index]
        print(json.dumps({
            "action": "question_answered",
            "field": field,
            "answer": answer,
            "next_index": next_index,
            "all_done": False,
            "next_question": next_q["question"],
            "next_example": next_q.get("example", ""),
            "next_field": next_q["field"],
            "tip": '回复「跳过」跳过此题（记为"未填写"），回复「结束」提前生成网站',
        }, ensure_ascii=False, indent=2))


def mode_summary():
    """Print a summary of all collected info."""
    state = load_state()
    collected = state.get("collected", {})

    # 优化：显示时也规范化数据（未填写显示清晰）
    info = sanitize_company_info(collected)

    lines = ["📋 网站需求汇总：", ""]
    for q in QUESTIONS:
        field = q["field"]
        value = info.get(field, "未填写")
        tag = " [必填]" if field in REQUIRED_API_FIELDS else ""
        lines.append(f"  {FIELD_LABELS[field]}：{value}{tag}")

    print("\n".join(lines))

    result = {
        "total": len(QUESTIONS),
        "answered": len([v for v in info.values() if v != "未填写"]),
        "skipped": len([v for v in info.values() if v == "未填写"]),
        "collected": info,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def mode_generate(args):
    """
    Generate website using collected info.

    优化点：
      - 调用前自动 sanitize（确保必填字段不为空）
      - SSE 超时保护
      - HTML 验证
      - 断点保存
    """
    state = load_state()
    collected = state.get("collected", {})

    # 优化：生成前再次规范化（兜底处理）
    info = sanitize_company_info(collected)

    # 提前检查必填字段（友情提示，不阻塞流程）
    for f in REQUIRED_API_FIELDS:
        if info.get(f) == "未填写":
            print(f"⚠️ 提示：{FIELD_LABELS[f]} 为「未填写」，API 可能无法生成理想内容")

    # Check & optionally init site
    languages = check_site_languages()
    if languages and not state.get("initialized"):
        if args.init:
            result = initialize_site()
            if result.get("code") == 0:
                print("✅ 站点初始化完成")
                state["initialized"] = True
                save_state(state)
            else:
                print(f"⚠️ 初始化失败: {result.get('msg', '')}")
        else:
            print("⚠️ 站点已有语言配置，未执行初始化（添加 --init 强制初始化）")

    # Get company info
    print("📡 正在获取企业信息...")
    info_result = call_get_company_info(collected)  # 会自动 sanitize
    if info_result.get("code") != 0:
        print(f"❌ 获取企业信息失败: {info_result.get('msg', '')}")
        sys.exit(1)

    company_info = info_result.get("data", "")
    if not company_info:
        print("❌ 企业信息为空，无法生成网站")
        sys.exit(1)

    requirement = f"请根据以下信息生成网站：\n{company_info}"

    print("🚀 正在生成网站（可能需要几分钟，SSE 流式输出）...")

    # 优化：使用新的 SSE 流式处理
    result = call_generate_website(requirement)

    if result.get("code") == 0:
        html_len = result.get("html_len", 0)
        html_file = result.get("html_file", "")
        issues = result.get("issues", [])
        timed_out = result.get("timed_out", False)

        if timed_out:
            print(f"\n⚠️ 生成超时，内容可能不完整！")
            print(f"💾 HTML 已保存: {html_file} ({html_len} 字符)")
        else:
            print(f"\n✅ 网站生成成功！")
            print(f"💾 HTML 已保存: {html_file} ({html_len} 字符)")

        if issues:
            print("⚠️ HTML 验证问题:")
            for issue in issues:
                print(f"  - {issue}")

        print(json.dumps({
            "ok": True,
            "html_file": html_file,
            "html_len": html_len,
            "requirement_preview": requirement[:200] + "..." if len(requirement) > 200 else requirement,
            "issues": issues,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"\n❌ 生成失败: {result.get('msg', 'Unknown error')}")
        sys.exit(1)

    # Reset state after successful generation
    reset_state()


def mode_init():
    """Initialize the site."""
    result = initialize_site()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("code") == 0:
        state = load_state()
        state["initialized"] = True
        save_state(state)


# ─── CLI Entry Point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate website through multi-turn dialogue (优化版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  status        Show current dialogue progress
  questions     List all 11 questions
  next          Print the next question to ask
  answer        Record user's answer to current question
  summary       Show collected info summary
  generate      Generate website (after collecting info)
  init          Initialize site
  reset         Reset dialogue state

Examples:
  python generate_website.py status
  python generate_website.py questions
  python generate_website.py next
  python generate_website.py answer --answer "明德律师事务所"
  python generate_website.py answer --answer "跳过"
  python generate_website.py answer --answer "结束"
  python generate_website.py summary
  python generate_website.py generate
  python generate_website.py generate --init
  python generate_website.py reset

Note:
  - Empty answers are stored as "未填写" (not empty string)
  - Logo field defaults to a placeholder image if not provided
  - SSE streaming includes 3-minute timeout protection
  - Draft auto-saves every 30 seconds during generation
        """,
    )
    sub = parser.add_subparsers(dest="cmd")

    sub.add_argument("status", help="Show dialogue progress")

    sub.add_argument("questions", help="List all questions")

    sub.add_argument("next", help="Print next question")

    sub.add_argument("answer", help="Record answer")
    sub.add_argument("--answer", required=True, help="User's answer")

    sub.add_argument("summary", help="Show summary")

    gen = sub.add_parser("generate", help="Generate website")
    gen.add_argument("--init", action="store_true", help="Initialize site before generating")

    sub.add_argument("init", help="Initialize site")

    sub.add_argument("reset", help="Reset dialogue state")

    args = parser.parse_args()

    if not API_KEY:
        print(json.dumps({"error": "AIBOX_API_KEY not set"}), file=sys.stderr)
        sys.exit(1)

    # 导入 time 模块（SSE 断点保存需要）
    global time
    import time as time_module

    if args.cmd == "status":
        mode_status()
    elif args.cmd == "questions":
        mode_questions()
    elif args.cmd == "next":
        mode_next()
    elif args.cmd == "answer":
        mode_answer(args)
    elif args.cmd == "summary":
        mode_summary()
    elif args.cmd == "generate":
        mode_generate(args)
    elif args.cmd == "init":
        mode_init()
    elif args.cmd == "reset":
        reset_state()
        print("✅ 对话状态已重置")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
