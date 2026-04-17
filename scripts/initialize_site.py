#!/usr/bin/env python3
"""
Initialize site data - clears existing pages, products, articles, messages
"""
import argparse
import json
import os
import sys

BASE_URL = os.environ.get("AIBOX_BASE_URL", "http://aidev.nicebox.cn/api/openclaw")
API_KEY = os.environ.get("AIBOX_API_KEY", "")

ENDPOINT_INITIALIZE = f"{BASE_URL}/template/initializeData"


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
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return result

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_body)
            print(json.dumps(error_json, ensure_ascii=False, indent=2), file=sys.stderr)
        except:
            print(json.dumps({"error": f"HTTP {e.code}", "message": error_body}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize site data")
    args = parser.parse_args()

    initialize_site()
