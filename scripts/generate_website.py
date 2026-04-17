#!/usr/bin/env python3
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
        "required": True,
    },
    {
        "field": "business_scope",
        "question": "请描述您的业务范围？",
        "example": "例如：软件开发、网站建设、APP开发、技术咨询服务",
        "required": False,
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
}


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
    except Exception as e:
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
    """Call getCompanyInfo API."""
    headers = {"Authorization": API_KEY, "Content-Type": "application/json"}
    payload = {k: collected.get(k, "") for k in FIELD_LABELS}
    try:
        req = urllib.request.Request(
            ENDPOINT_GET_COMPANY_INFO,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
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


def call_generate_website(requirement):
    """Call generateWebsite API (SSE). Returns first JSON line."""
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {"requirement": requirement}
    try:
        req = urllib.request.Request(
            ENDPOINT_GENERATE_WEBSITE,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            # Read all response (SSE may contain multiple lines)
            raw = resp.read().decode("utf-8", errors="replace")
            # Return the first JSON object found
            for line in raw.split("\n"):
                line = line.strip()
                if line.startswith("data:") or line.startswith("{"):
                    try:
                        text = line.lstrip("data: ").strip()
                        if text.startswith("{"):
                            return json.loads(text)
                    except Exception:
                        pass
            return {"code": 500, "msg": "No valid JSON in response", "raw": raw[:500]}
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"code": 1, "msg": f"HTTP {e.code}"}
    except Exception as e:
        return {"code": 1, "msg": str(e)}


# ─── Script Modes ─────────────────────────────────────────────────────────────

def mode_status():
    """Show current dialogue status: how many questions answered, what's next."""
    state = load_state()
    current = state.get("current_index", 0)
    collected = state.get("collected", {})
    answered = [FIELD_LABELS[k] for k in collected if collected[k] not in ("未填写", "")]
    unanswered = [QUESTIONS[i]["field"] for i in range(current, len(QUESTIONS))
                  if FIELD_LABELS[QUESTIONS[i]["field"]] not in answered]

    result = {
        "status": "in_progress" if current < len(QUESTIONS) else "ready_to_generate",
        "total_questions": len(QUESTIONS),
        "answered_count": len(answered),
        "current_question_index": current,
        "next_question": QUESTIONS[current]["question"] if current < len(QUESTIONS) else None,
        "next_example": QUESTIONS[current].get("example") if current < len(QUESTIONS) else None,
        "next_field": QUESTIONS[current]["field"] if current < len(QUESTIONS) else None,
        "answered": answered,
        "unanswered": [FIELD_LABELS[f] for f in unanswered],
        "skipped": [FIELD_LABELS[k] for k in collected if collected[k] == "未填写"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def mode_questions():
    """List all 11 questions (for AI to display to user)."""
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
        print(json.dumps({"done": True, "message": "所有问题已问完，请生成网站"}))
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
        "tip": "回复「跳过」跳过此题，回复「结束」提前生成网站",
    }, ensure_ascii=False, indent=2))


def mode_answer(args):
    """
    Record user's answer to the current question.
    Called with: --answer "user's answer"
    Advances current_index and saves state.
    """
    user_answer = args.answer.strip()

    # Handle special commands
    if user_answer.lower() in ("跳过", "skip", "s"):
        answer = "未填写"
    elif user_answer.lower() in ("结束", "finish", "done"):
        # Signal early finish
        state = load_state()
        state["finished_early"] = True
        save_state(state)
        print(json.dumps({
            "action": "finish_early",
            "message": "对话已结束，开始生成网站",
            "current_index": state.get("current_index", 0),
            "answered": len([v for v in state.get("collected", {}).values() if v and v != "未填写"]),
        }, ensure_ascii=False))
        return
    elif not user_answer:
        print(json.dumps({"error": "回答不能为空，请输入内容或回复「跳过」/「结束」"}))
        return
    else:
        answer = user_answer

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
        print(json.dumps({
            "action": "question_answered",
            "field": field,
            "answer": answer,
            "next_index": next_index,
            "all_done": True,
            "message": f"已记录「{FIELD_LABELS[field]}」的回答。所有问题已收集完毕！",
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
            "tip": "回复「跳过」跳过此题，回复「结束」提前生成网站",
        }, ensure_ascii=False, indent=2))


def mode_summary():
    """Print a summary of all collected info."""
    state = load_state()
    collected = state.get("collected", {})

    lines = ["📋 网站需求汇总：", ""]
    for q in QUESTIONS:
        field = q["field"]
        value = collected.get(field, "未填写")
        lines.append(f"  {FIELD_LABELS[field]}：{value}")

    print("\n".join(lines))

    # Also output JSON for structured use
    result = {
        "total": len(QUESTIONS),
        "answered": len([v for v in collected.values() if v and v != "未填写"]),
        "skipped": len([v for v in collected.values() if v == "未填写"]),
        "collected": collected,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def mode_generate(args):
    """Generate website using collected info (and optionally init site first)."""
    state = load_state()
    collected = state.get("collected", {})

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
    info_result = call_get_company_info(collected)
    if info_result.get("code") != 0:
        print(f"❌ 获取企业信息失败: {info_result.get('msg', '')}")
        sys.exit(1)

    company_info = info_result.get("data", "")
    requirement = f"请根据以下信息生成网站：\n{company_info}"

    print("🚀 正在生成网站（可能需要几分钟）...")

    # For streaming output, just print the result
    result = call_generate_website(requirement)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result.get("code") == 0 and result.get("data", {}).get("html"):
        html_len = len(result["data"]["html"])
        tokens = result["data"].get("total_tokens", 0)
        print(f"\n✅ 网站生成成功！HTML长度：{html_len} 字符，Token消耗：{tokens}")
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
        description="Generate website through multi-turn dialogue",
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
  python generate_website.py next
  python generate_website.py answer --answer "明德律师事务所"
  python generate_website.py answer --answer "跳过"
  python generate_website.py answer --answer "结束"
  python generate_website.py summary
  python generate_website.py generate
  python generate_website.py generate --init
  python generate_website.py reset
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
