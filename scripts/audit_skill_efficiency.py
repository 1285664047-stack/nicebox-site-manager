#!/usr/bin/env python3
"""Audit skill routing efficiency without executing any business operation."""

from __future__ import print_function

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEGACY = ROOT / "nicebox-site-manager-main"
WORKBUDDY = ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager"


def read(path):
    return path.read_text(encoding="utf-8")


def require(condition, message, errors):
    if not condition:
        errors.append(message)


def require_any(text, markers, message, errors):
    require(any(marker in text for marker in markers), message, errors)


def referenced_markdown(text):
    return re.findall(r"\[[^\]]+\]\(([^)]+\.md)\)", text)


def main():
    errors = []
    legacy_entry_path = LEGACY / "SKILL.md"
    workbuddy_entry_path = WORKBUDDY / "SKILL.md"
    legacy_entry = read(legacy_entry_path)
    workbuddy_entry = read(workbuddy_entry_path)

    require(len(legacy_entry.splitlines()) <= 120,
            "Legacy SKILL.md exceeds 120 lines; default context has expanded.", errors)
    require(len(workbuddy_entry.splitlines()) <= 100,
            "WorkBuddy SKILL.md exceeds 100 lines; default context has expanded.", errors)

    for relative in referenced_markdown(legacy_entry):
        require((LEGACY / relative).exists(),
                "Legacy route target is missing: {}".format(relative), errors)

    workbuddy_routes = re.findall(r"@references/([^\s]+\.md)", workbuddy_entry)
    for relative in workbuddy_routes:
        require((WORKBUDDY / "references" / relative).exists(),
                "WorkBuddy route target is missing: {}".format(relative), errors)

    require("普通业务请求不得预读" in workbuddy_entry,
            "WorkBuddy no longer forbids preloading the tool/risk catalog.", errors)
    require("只有实际发现所需能力未注册时" in legacy_entry,
            "Legacy entry no longer defers transport mapping until needed.", errors)

    duplicate_transport_refs = []
    for path in (LEGACY / "skills").glob("*.skill.md"):
        if path.name == "mcp_tools.skill.md":
            continue
        if "mcp_tools.skill.md" in read(path):
            duplicate_transport_refs.append(path.name)
    require(not duplicate_transport_refs,
            "Legacy child skills duplicate transport loading: {}".format(
                ", ".join(sorted(duplicate_transport_refs))), errors)

    legacy_all = "\n".join(read(path) for path in [legacy_entry_path] + sorted((LEGACY / "skills").glob("*.skill.md")))
    workbuddy_all = "\n".join(read(path) for path in [workbuddy_entry_path] + sorted((WORKBUDDY / "references").glob("*.md")))

    capabilities = {
        "website_generation": [["重新生成"], ["初始化"], ["生成进度"]],
        "content_draft_preview": [["草稿"], ["预览"], ["正式发布"]],
        "article_edit": [["修改已有文章"], ["重新生成 SEO"], ["FAQ"]],
        "content_listing": [["模糊搜索"], ["排序"], ["删除"]],
        "page_edit": [["页面代码"], ["Review"], ["当前目标"]],
        "page_continuation": [["继续修改"], ["回退到本次修改前的版本"], ["未保存"]],
        "shared_sections": [["Header/Footer"], ["所有页面", "所有 {locale} 页面", "所有 {locale} 页面"], ["回退"]],
        "seo_geo": [["SEO/GEO"], ["当前检测域名"], ["一键优化"]],
        "site_publish": [["HTML 静态发布"], ["增量上传"], ["分批"]],
        "image_upload": [["image_url"], ["Referer"], ["不重复上传"]],
    }
    for capability, marker_groups in capabilities.items():
        for markers in marker_groups:
            require_any(legacy_all, markers,
                        "Legacy capability {} lost marker group: {}".format(capability, markers), errors)
            require_any(workbuddy_all, markers,
                        "WorkBuddy capability {} lost marker group: {}".format(capability, markers), errors)

    safety_marker_groups = [
        ["不得替用户确认"],
        ["内容发布不等于"],
        ["不得检查或修复用户未要求", "不检查或修复用户未要求"],
        ["写入结果未知"],
    ]
    for markers in safety_marker_groups:
        require_any(legacy_all, markers, "Legacy safety rule missing: {}".format(markers), errors)
        require_any(workbuddy_all, markers, "WorkBuddy safety rule missing: {}".format(markers), errors)

    workflow_invariants = [
        ("version_check", legacy_entry, workbuddy_entry,
         ["24 小时", "版本检查"], ["24小时", "版本检测时间"]),
        ("page_edit_chain",
         read(LEGACY / "skills" / "page_code_validate.skill.md"),
         read(WORKBUDDY / "references" / "页面修改草稿与校验流程.md"),
         ["page_change_workflow.skill.md", "继续创建预览"],
         ["页面预览保存与回退流程.md", "继续创建预览"]),
        ("website_rebuild",
         read(LEGACY / "skills" / "interactive_generate.skill.md"),
         read(WORKBUDDY / "references" / "建站与预览流程.md"),
         ["沿用", "初始化", "生成首页、内页"],
         ["沿用", "初始化", "operation_id"]),
        ("article_draft_publish",
         read(LEGACY / "skills" / "publish_article.skill.md"),
         read(WORKBUDDY / "references" / "内容管理流程.md"),
         ["先调用", "预览地址", "再次明确确认"],
         ["先调用", "预览地址", "再次明确确认"]),
        ("article_edit_followup",
         read(LEGACY / "skills" / "edit_article.skill.md"),
         read(WORKBUDDY / "references" / "文章修改流程.md"),
         ["文件名", "重新生成 SEO", "修改前已经存在 FAQ", "确认保存", "调整修改内容", "follow_up.choices"],
         ["文件名", "重新生成 SEO", "修改前已经有 FAQ", "确认保存", "调整修改内容", "follow_up.choices"]),
        ("product_edit_followup",
         read(LEGACY / "skills" / "edit_product.skill.md"),
         read(WORKBUDDY / "references" / "产品修改流程.md"),
         ["currency", "attachments", "parameters", "重新生成 SEO", "修改前已经存在 FAQ", "先 FAQ", "预览", "单独确认", "确认保存", "调整修改内容", "follow_up.choices"],
         ["currency", "attachments", "parameters", "重新生成 SEO", "修改前已经有 FAQ", "先 FAQ", "预览", "单独确认", "确认保存", "调整修改内容", "follow_up.choices"]),
        ("faq_create",
         read(LEGACY / "skills" / "create_faq.skill.md"),
         read(WORKBUDDY / "references" / "内容管理流程.md"),
         ["FAQ 分类", "精确搜索", "模糊搜索", "创建该分类并继续", "确认创建", "faq_items"],
         ["FAQ 分类", "精确查找", "模糊查找", "创建该分类并继续", "确认创建", "faq_items"]),
        ("page_continuation",
         read(LEGACY / "skills" / "page_change_workflow.skill.md"),
         read(WORKBUDDY / "references" / "页面预览保存与回退流程.md"),
         ["base_preview_token", "继续修改", "回退到本次修改前的版本"],
         ["base_preview_token", "继续修改", "回退到本次修改前的版本"]),
        ("shared_scope",
         read(LEGACY / "skills" / "shared_sections.skill.md"),
         read(WORKBUDDY / "references" / "共享头尾修改与回退流程.md"),
         ["所有页面", "preview_pages", "明确确认"],
         ["所有 {locale} 页面", "preview_pages", "单独确认"]),
        ("seo_detection",
         read(LEGACY / "skills" / "seo_geo.skill.md"),
         read(WORKBUDDY / "references" / "SEO-GEO检测与优化流程.md"),
         ["当前检测域名", "SITE_NOT_PUBLISHED", "二次确认"],
         ["当前检测域名", "SITE_NOT_PUBLISHED", "二次确认"]),
        ("ftp_publish",
         read(LEGACY / "skills" / "ftp_publish.skill.md"),
         read(WORKBUDDY / "references" / "FTP发布流程.md"),
         ["HTML 静态发布", "增量上传", "no_changes", "batch_number"],
         ["HTML 静态发布", "增量上传", "no_changes", "batch_number"]),
        ("page_review_scope",
         read(LEGACY / "skills" / "page_code_validate.skill.md"),
         read(WORKBUDDY / "references" / "页面修改草稿与校验流程.md"),
         ["本次 diff", "目标外既有问题", "不展示、不修复"],
         ["本次 diff", "目标外既有问题", "不展示、不修复"]),
    ]
    for name, legacy_text, workbuddy_text, legacy_markers, workbuddy_markers in workflow_invariants:
        for marker in legacy_markers:
            require(marker in legacy_text,
                    "Legacy workflow {} lost marker: {}".format(name, marker), errors)
        for marker in workbuddy_markers:
            require(marker in workbuddy_text,
                    "WorkBuddy workflow {} lost marker: {}".format(name, marker), errors)

    legacy_version = re.search(r"^version:\s*(\S+)", legacy_entry, re.MULTILINE)
    workbuddy_version = re.search(r"^version:\s*(\S+)", workbuddy_entry, re.MULTILINE)
    require(bool(legacy_version and workbuddy_version), "Skill version is missing.", errors)
    if legacy_version and workbuddy_version:
        require(legacy_version.group(1) == workbuddy_version.group(1),
                "Legacy and WorkBuddy skill versions differ.", errors)
        installed = json.loads(read(LEGACY / "scripts" / "installed_versions.json"))
        require(installed.get("skill_version") == legacy_version.group(1),
                "installed_versions.json does not match SKILL.md.", errors)

    manifest_path = WORKBUDDY / "references" / "page-edit-library" / "manifest.json"
    manifest = json.loads(read(manifest_path))
    manifest_files = manifest.get("files", [])
    require(len(manifest_files) == len(set(manifest_files)),
            "Page edit manifest contains duplicate modules.", errors)
    for relative in manifest_files:
        require((manifest_path.parent / relative).exists(),
                "Page edit module is missing: {}".format(relative), errors)

    if errors:
        print("Skill efficiency audit failed ({} issue(s)):".format(len(errors)))
        for error in errors:
            print("- {}".format(error))
        return 1

    print("Skill efficiency audit passed.")
    print("Legacy entry: {} lines".format(len(legacy_entry.splitlines())))
    print("WorkBuddy entry: {} lines".format(len(workbuddy_entry.splitlines())))
    print("Legacy child transport preload references: 0")
    print("Checked capability groups: {}".format(len(capabilities)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
