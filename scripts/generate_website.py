#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import argparse
import urllib.request

BASE_URL = os.environ.get("AIBOX_BASE_URL", "http://aidev.nicebox.cn/api/openclaw")
API_KEY = os.environ.get("AIBOX_API_KEY")

ENDPOINT_GENERATE = "/ai_tools/generateWebsite"


def request_generate(session_id):
    url = BASE_URL + ENDPOINT_GENERATE

    payload = {
        "session": session_id
    }

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": API_KEY,
            "Content-Type": "application/json"
        }
    )

    with urllib.request.urlopen(req) as resp:
        raw = resp.read().decode()
        return json.loads(raw)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", required=True)
    args = parser.parse_args()

    res = request_generate(args.session_id)

    print(json.dumps({
        "result": res
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
