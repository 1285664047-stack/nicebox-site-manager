#!/usr/bin/env python3
"""
Generate website through AI-guided multi-turn dialogue
AI asks questions, user answers
"""
import argparse
import json
import os
import sys

BASE_URL = os.environ.get("AIBOX_BASE_URL", "http://aidev.nicebox.cn/api/openclaw")
API_KEY = os.environ.get("AIBOX_API_KEY", "")

ENDPOINT_LANGUAGE_LIST = f"{BASE_URL}/site_pages/getLanguageList"
ENDPOINT_INITIALIZE = f"{BASE_URL}/template/initializeData"
ENDPOINT_GET_COMPANY_INFO = f"{BASE_URL}/ai_tools/getCompanyInfo"
ENDPOINT_GENERATE_WEBSITE = f"{BASE_URL}/ai_tools/generateWebsite"

QUESTIONS = [
    {"field": "company_name", "question": "请告诉我您的公司名称或想创建的网站名称是什么？", "example": "某某科技有限公司 或 某某律师事务所官网"},
    {"field": "industry", "question": "您从事哪个行业？", "example": "科技、教育、医疗、餐饮、零售、金融、法律等"},
    {"field": "business_scope", "question": "请描述您的业务范围？", "example": "提供软件开发、网站建设APP开发等技术服务"},
    {"field": "business_features", "question": "您的业务有哪些特色或亮点？", "example": "20年行业经验、专业团队、售后保障等"},
    {"field": "culture", "question": "请介绍一下您的企业文化或理念？", "example": "客户至上、创新进取、诚信为本"},
    {"field": "advantages", "question": "您的核心竞争优势是什么？", "example": "技术领先、价格合理、服务周到"},
    {"field": "phone", "question": "请提供您的联系电话？", "example": "400-888-8888 或 138-0000-0000"},
    {"field": "email", "question": "请提供您的联系邮箱？", "example": "contact@example.com"},
    {"field": "address", "question": "请提供您的公司地址？", "example": "北京市朝阳区某某大厦10层"},
    {"field": "logo", "question": "您有logo吗？如果有，请提供logo图片的URL地址？", "example": "https://example.com/logo.png (如果没有可跳过)"},
    {"field": "style", "question": "您希望网站采用什么视觉风格？", "example": "简约现代、专业商务、创意时尚、温馨亲切等"},
]


def check_site_languages(api_key=None):
    """Check if site has languages configured"""
    if api_key is None:
        api_key = API_KEY

    if not api_key:
        return None

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(
            ENDPOINT_LANGUAGE_LIST,
            data=json.dumps({}).encode("utf-8"),
            headers=headers,
            method="GET"
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            if result.get("code") == 0 and result.get("data"):
                return result.get("data", [])
            return []

    except Exception as e:
        print(f"Error checking languages: {e}", file=sys.stderr)
        return []


def initialize_site(api_key=None):
    """Initialize site data"""
    if api_key is None:
        api_key = API_KEY

    if not api_key:
        print(json.dumps({"error": "API key is required"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(
            ENDPOINT_INITIALIZE,
            data=json.dumps({}).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_body)
            return error_json
        except:
            return {"code": 1, "msg": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"code": 1, "msg": str(e)}


def get_company_info(collected, api_key=None):
    """Call getCompanyInfo API to get company info text"""
    if api_key is None:
        api_key = API_KEY

    if not api_key:
        print(json.dumps({"error": "API key is required"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "company_name": collected.get("company_name", ""),
        "industry": collected.get("industry", ""),
        "business_scope": collected.get("business_scope", ""),
        "business_features": collected.get("business_features", ""),
        "culture": collected.get("culture", ""),
        "advantages": collected.get("advantages", ""),
        "phone": collected.get("phone", ""),
        "email": collected.get("email", ""),
        "address": collected.get("address", ""),
        "logo": collected.get("logo", ""),
        "style": collected.get("style", ""),
    }

    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(
            ENDPOINT_GET_COMPANY_INFO,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_body)
            return error_json
        except:
            return {"code": 1, "msg": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"code": 1, "msg": str(e)}


def generate_website(requirement, api_key=None):
    """Call generateWebsite API"""
    if api_key is None:
        api_key = API_KEY

    if not api_key:
        print(json.dumps({"error": "API key is required"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "requirement": requirement
    }

    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(
            ENDPOINT_GENERATE_WEBSITE,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_body)
            return error_json
        except:
            return {"code": 1, "msg": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"code": 1, "msg": str(e)}


def print_welcome():
    """Print welcome message"""
    print("\n" + "=" * 60)
    print("🌐  AI Website Generator - Multi-turn Dialogue")
    print("=" * 60)
    print("\nThis tool will help you generate a website through dialogue.")
    print("IMPORTANT: All answers must be manually entered by you!")
    print("AI will ask questions, but will NEVER auto-answer.")
    print("You can:")
    print("  - Type your answer manually for each question")
    print("  - Type 'skip' to skip a question")
    print("  - Type 'finish' to end dialogue and generate summary")
    print("  - Type 'exit' to quit at any time")
    print("=" * 60 + "\n")


def ask_initialize():
    """Ask user if they want to initialize site"""
    print("\n⚠️  Your site already has languages configured.")
    print("    Initializing will CLEAR all existing:")
    print("    - Pages, Products, Articles, Messages")
    print("")
    while True:
        response = input("Do you want to initialize the site? (yes/no): ").strip().lower()
        if response in ["yes", "y", "是", "确认"]:
            return True
        elif response in ["no", "n", "否", "不"]:
            return False
        print("Please answer 'yes' or 'no'")


def ask_single_question(question_data, index, total):
    """Ask a single question and get user's answer"""
    field = question_data["field"]
    question = question_data["question"]
    example = question_data.get("example", "")

    while True:
        print(f"\n💬 AI (问题 {index + 1}/{total}): {question}")
        if example:
            print(f"   例如: {example}")
        print("   (输入 'skip' 跳过此题, 输入 'finish' 结束对话)")

        user_input = input("\n👤 Your answer: ").strip()

        if user_input.lower() in ["exit", "quit", "退出"]:
            return None, True

        if user_input.lower() in ["finish", "end", "完成", "结束"]:
            return "", True

        if user_input.lower() in ["skip", "s", "跳过"]:
            return "未填写", False

        if user_input:
            return user_input, False

        print("   ⚠️  您没有输入内容，请回答问题、输入 'skip' 跳过或 'finish' 结束")


def collect_website_info():
    """Collect website information through multi-turn dialogue"""
    collected = {}
    total = len(QUESTIONS)

    for i, q in enumerate(QUESTIONS):
        answer, should_exit = ask_single_question(q, i, total)

        if should_exit:
            if answer is None:
                return None
            break

        collected[q["field"]] = answer

    return collected


def generate_summary(collected):
    """Generate summary text from collected info"""
    field_labels = {
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

    summary_parts = ["📋 网站需求汇总："]
    for field, label in field_labels.items():
        value = collected.get(field, "未填写")
        summary_parts.append(f"- {label}: {value}")

    return "\n".join(summary_parts)


def main():
    parser = argparse.ArgumentParser(
        description="Generate website through AI-guided multi-turn dialogue"
    )
    args = parser.parse_args()

    api_key = API_KEY

    if not api_key:
        print(json.dumps({"error": "API key is required. Set AIBOX_API_KEY environment variable."}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    print_welcome()

    print("🔍 Checking site languages...")
    languages = check_site_languages(api_key)

    if languages and len(languages) > 0:
        if ask_initialize():
            print("\n🔄 Initializing site...")
            result = initialize_site(api_key)
            if result.get("code") == 0:
                print("✅ Site initialized successfully!")
            else:
                print(f"⚠️  Initialization warning: {result.get('msg', 'Unknown error')}")
    else:
        print("✅ No existing languages found, skipping initialization")

    print("\n🚀 Starting dialogue...")
    print("-" * 60)

    collected = collect_website_info()

    if collected is None:
        print("\n👋 Goodbye!")
        sys.exit(0)

    summary = generate_summary(collected)

    print("\n" + "=" * 60)
    print("📋 Website Design Summary")
    print("=" * 60)
    print(summary)
    print("=" * 60)

    while True:
        print("\n请确认以上信息是否正确？")
        print("输入 'yes' 或 '确认' 表示确认生成网站")
        print("输入 'no' 或 '否' 表示取消")

        response = input("\n👤 Your choice: ").strip().lower()

        if response in ["yes", "y", "是", "确认"]:
            print("\n📡 正在获取企业信息...")
            info_result = get_company_info(collected, api_key)

            if info_result.get("code") != 0:
                print(f"\n❌ 获取企业信息失败: {info_result.get('msg', 'Unknown error')}")
                sys.exit(1)

            company_info = info_result.get("data", "")
            requirement = f"请根据以下信息生成网站：\n{company_info}"

            print("\n🚀 正在生成网站...(这可能需要几分钟时间)")
            result = generate_website(requirement, api_key)

            if result.get("code") == 0:
                print("\n✅ 网站生成成功!")
                print(f"   {result.get('msg', '')}")
                if result.get("data"):
                    print(f"   Data: {json.dumps(result.get('data', {}), ensure_ascii=False, indent=2)}")
            else:
                print(f"\n❌ 网站生成失败: {result.get('msg', 'Unknown error')}")
            break

        elif response in ["no", "n", "否", "不"]:
            print("\n👋 网站生成已取消。")
            break
        else:
            print("请输入 'yes' 或 'no'")

    print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
