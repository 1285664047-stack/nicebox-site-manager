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
ENDPOINT_ASK_QUESTION = f"{BASE_URL}/ai_tools/askQuestion"
ENDPOINT_GENERATE_WEBSITE = f"{BASE_URL}/ai_tools/generateWebsite"


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


def ask_question(question_index, collected, user_answer="", action="get_question", api_key=None):
    """Call askQuestion API - AI asks, user answers"""
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
        "question_index": question_index,
        "collected": json.dumps(collected, ensure_ascii=False),
        "user_answer": user_answer,
        "action": action
    }

    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(
            ENDPOINT_ASK_QUESTION,
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
    print("I'll ask you questions about your website requirements.")
    print("You can:")
    print("  - Answer each question in detail")
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


def start_dialogue(api_key=None):
    """Start the dialogue - get first question from AI"""
    collected = {}

    # Get first question (question_index = 0, no user answer yet)
    result = ask_question(0, collected, "", "get_question", api_key)

    if result.get("code") != 0:
        print(f"\n❌ Error: {result.get('msg', 'Unknown error')}")
        return None

    data = result.get("data", {})
    return data


def continue_dialogue(question_index, collected, user_answer, api_key=None):
    """Continue dialogue - send user answer and get next question"""
    result = ask_question(question_index, collected, user_answer, "get_question", api_key)

    if result.get("code") != 0:
        print(f"\n❌ Error: {result.get('msg', 'Unknown error')}")
        return None

    data = result.get("data", {})
    return data


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

    # Step 1: Check site languages
    print("🔍 Checking site languages...")
    languages = check_site_languages(api_key)

    if languages and len(languages) > 0:
        # Ask user if they want to initialize
        if ask_initialize():
            print("\n🔄 Initializing site...")
            result = initialize_site(api_key)
            if result.get("code") == 0:
                print("✅ Site initialized successfully!")
            else:
                print(f"⚠️  Initialization warning: {result.get('msg', 'Unknown error')}")
    else:
        print("✅ No existing languages found, skipping initialization")

    # Step 2: Start multi-turn dialogue with AI
    print("\n🚀 Starting dialogue with AI...")
    print("-" * 60)

    # Get first question from AI
    data = start_dialogue(api_key)

    if data is None:
        print("\n❌ Failed to start dialogue")
        sys.exit(1)

    collected = data.get("collected", {})
    question_index = data.get("question_index", 0)
    is_complete = data.get("is_complete", False)

    # Dialogue loop
    while not is_complete:
        question = data.get("question", "")
        example = data.get("example", "")
        total = data.get("total_questions", 11)

        # Print AI question
        print(f"\n💬 AI (问题 {question_index + 1}/{total}): {question}")
        if example:
            print(f"   例如: {example}")
        print("   (输入 'skip' 跳过此题, 输入 'finish' 结束对话)")

        # Get user input
        user_input = input("\n👤 Your answer: ").strip()

        # Handle commands
        if user_input.lower() in ["exit", "quit", "退出"]:
            print("\n👋 Goodbye!")
            sys.exit(0)

        # Continue dialogue with user answer
        data = continue_dialogue(question_index, collected, user_input, api_key)

        if data is None:
            print("\n❌ Failed to continue dialogue")
            break

        # Update collected info
        collected = data.get("collected", {})
        question_index = data.get("question_index", 0)
        is_complete = data.get("is_complete", False)

        if is_complete:
            break

    # Check if dialogue completed
    if not is_complete:
        print("\n👋 Dialogue ended by user.")
        sys.exit(0)

    # Get summary
    summary = data.get("summary", "")

    print("\n" + "=" * 60)
    print("📋 Website Design Summary")
    print("=" * 60)
    print(summary)
    print("=" * 60)

    # Confirm with user
    while True:
        print("\n请确认以上信息是否正确？")
        print("输入 'yes' 或 '确认' 表示确认生成网站")
        print("输入 'no' 或 '否' 表示取消")

        response = input("\n👤 Your choice: ").strip().lower()

        if response in ["yes", "y", "是", "确认"]:
            # User confirmed, generate requirement string and call API
            requirement = f"请根据以下信息生成网站：\n"
            for field, value in collected.items():
                if value and value != "未填写":
                    requirement += f"{field}: {value}\n"

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
