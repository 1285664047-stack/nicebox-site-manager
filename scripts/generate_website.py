#!/usr/bin/env python3
"""
Generate website through AI-guided multi-turn dialogue
"""
import argparse
import json
import os
import sys
import time

BASE_URL = os.environ.get("AIBOX_BASE_URL", "http://aidev.nicebox.cn/api/openclaw")
API_KEY = os.environ.get("AIBOX_API_KEY", "")

ENDPOINT_LANGUAGE_LIST = f"{BASE_URL}/site_pages/getLanguageList"
ENDPOINT_INITIALIZE = f"{BASE_URL}/template/initializeData"
ENDPOINT_GUIDE_DIALOGUE = f"{BASE_URL}/ai_tools/guideDialogue"
ENDPOINT_GUIDE_COLLECT = f"{BASE_URL}/ai_tools/guideCollect"
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
            if result.get("code") == 1 and result.get("data"):
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
            return {"code": 0, "msg": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"code": 0, "msg": str(e)}


def guide_dialogue(message, session_id="", api_key=None):
    """Call guideDialogue API"""
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
        "message": message
    }

    if session_id:
        payload["session_id"] = session_id

    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(
            ENDPOINT_GUIDE_DIALOGUE,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_body)
            return error_json
        except:
            return {"code": 0, "msg": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"code": 0, "msg": str(e)}


def guide_collect(session_id, api_key=None):
    """Call guideCollect API to summarize collected information"""
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
        "session": session_id
    }

    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(
            ENDPOINT_GUIDE_COLLECT,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_body)
            return error_json
        except:
            return {"code": 0, "msg": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"code": 0, "msg": str(e)}


def generate_website(session_id, api_key=None):
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
        "session": session_id
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
            return {"code": 0, "msg": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"code": 0, "msg": str(e)}


def print_welcome():
    """Print welcome message"""
    print("\n" + "=" * 60)
    print("🌐  AI Website Generator - Multi-turn Dialogue")
    print("=" * 60)
    print("\nThis tool will help you generate a website through dialogue.")
    print("I'll ask you questions about your website requirements.")
    print("You can:")
    print("  - Answer each question")
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


def print_collection_status(collected):
    """Print current collection status"""
    fields = {
        "company_name": "Company/Website Name",
        "industry": "Industry",
        "business_scope": "Business Scope",
        "business_features": "Business Features",
        "culture": "Culture & Philosophy",
        "advantages": "Core Advantages",
        "phone": "Contact Phone",
        "email": "Contact Email",
        "address": "Company Address",
        "logo": "Logo",
        "style": "Visual Style"
    }

    print("\n📋 Current Collection Status:")
    print("-" * 40)
    for key, label in fields.items():
        value = collected.get(key, "")
        status = "✅" if value else "⭕"
        display_value = value if value else "Not provided"
        print(f"  {status} {label}: {display_value}")
    print("-" * 40)


def main():
    parser = argparse.ArgumentParser(
        description="Generate website through AI-guided multi-turn dialogue"
    )
    parser.add_argument(
        "--session-id",
        type=str,
        default="",
        help="Session ID for continuing previous dialogue"
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

    needs_initialize = False
    if languages and len(languages) > 0:
        # Ask user if they want to initialize
        needs_initialize = ask_initialize()
        if needs_initialize:
            print("\n🔄 Initializing site...")
            result = initialize_site(api_key)
            if result.get("code") == 1:
                print("✅ Site initialized successfully!")
            else:
                print(f"⚠️  Initialization warning: {result.get('msg', 'Unknown error')}")
    else:
        print("✅ No existing languages found, skipping initialization")

    # Step 2: Start multi-turn dialogue
    print("\n🚀 Starting dialogue to collect website information...")
    print("-" * 60)

    session_id = args.session_id
    collected = {}
    is_complete = False

    # First call to start dialogue
    print("\n💬 AI: Welcome! I'll help you create a website. Let me ask you a few questions.")
    print("    (You can type 'skip' to skip any question, 'finish' to end dialogue)\n")

    while not is_complete:
        # Call guideDialogue with empty message to get next question
        result = guide_dialogue("", session_id, api_key)

        if result.get("code") != 1:
            print(f"\n❌ Error: {result.get('msg', 'Unknown error')}")
            break

        data = result.get("data", {})
        session_id = data.get("session", session_id)
        message = data.get("message", "")
        is_complete = data.get("is_complete", False)

        if is_complete:
            print("\n✅ Dialogue completed!")
            break

        # Print AI question
        print(f"\n💬 AI: {message}")

        # Get user input
        user_input = input("\n👤 You: ").strip()

        # Handle commands
        if user_input.lower() in ["exit", "quit", "退出"]:
            print("\n👋 Goodbye!")
            sys.exit(0)

        if user_input.lower() in ["finish", "end", "完成"]:
            is_complete = True
            break

        # Check if user wants to skip
        is_skip = user_input.lower() in ["skip", "跳过", "s"]

        # Send user response to AI
        result = guide_dialogue(user_input, session_id, api_key)

        if result.get("code") != 1:
            print(f"\n❌ Error: {result.get('msg', 'Unknown error')}")
            break

        data = result.get("data", {})
        session_id = data.get("session", session_id)
        is_complete = data.get("is_complete", False)

        # Print AI response
        ai_message = data.get("message", "")
        if ai_message:
            print(f"\n💬 AI: {ai_message}")

    # Step 3: Get summary
    if session_id:
        print("\n📝 Generating summary...")
        result = guide_collect(session_id, api_key)

        if result.get("code") == 1:
            data = result.get("data", {})
            summary = data.get("summary", "")

            print("\n" + "=" * 60)
            print("📋 Website Design Summary")
            print("=" * 60)
            print(summary)
            print("=" * 60)

            # Confirm with user
            print("\n❓ Do you want to proceed with generating the website?")
            while True:
                response = input("Type 'yes' to generate, 'no' to cancel: ").strip().lower()
                if response in ["yes", "y", "是", "确认"]:
                    # Step 4: Generate website
                    print("\n🚀 Generating website... (this may take a few minutes)")
                    result = generate_website(session_id, api_key)

                    if result.get("code") == 1:
                        print("\n✅ Website generated successfully!")
                        print(f"   {result.get('msg', '')}")
                        if result.get("data"):
                            print(f"   Data: {json.dumps(result.get('data', {}), ensure_ascii=False, indent=2)}")
                    else:
                        print(f"\n❌ Failed to generate website: {result.get('msg', 'Unknown error')}")
                    break
                elif response in ["no", "n", "否", "不"]:
                    print("\n👋 Website generation cancelled.")
                    break
                print("Please answer 'yes' or 'no'")
        else:
            print(f"\n❌ Failed to generate summary: {result.get('msg', 'Unknown error')}")
    else:
        print("\n❌ No session ID available")

    print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
