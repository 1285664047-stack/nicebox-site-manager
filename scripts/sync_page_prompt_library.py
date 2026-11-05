#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Synchronize the canonical page-edit prompt library into both skills."""
import argparse
import filecmp
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "doc" / "workbuddy" / "页面修改能力" / "page-edit-prompts"
TARGETS = [
    ROOT / "nicebox-site-manager-main" / "references" / "page-edit-library",
    ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "references" / "page-edit-library",
]


def declared_files():
    manifest = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    return ["manifest.json", *manifest["files"]]


def check(files):
    errors = []
    for relative in files:
        source = SOURCE / relative
        if not source.is_file():
            errors.append(f"missing source: {source}")
            continue
        for target in TARGETS:
            destination = target / relative
            if not destination.is_file() or not filecmp.cmp(source, destination, shallow=False):
                errors.append(f"out of sync: {destination}")
    return errors


def sync(files):
    for target in TARGETS:
        target.mkdir(parents=True, exist_ok=True)
        for relative in files:
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SOURCE / relative, destination)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if either skill differs from the canonical library")
    args = parser.parse_args()
    files = declared_files()
    if not args.check:
        sync(files)
    errors = check(files)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"ok": True, "file_count": len(files), "targets": [str(p) for p in TARGETS]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
