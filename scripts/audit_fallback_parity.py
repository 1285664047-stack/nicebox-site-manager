#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail when an MCP tool has no checked-in ordinary API fallback."""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOLS_FILE = ROOT / "mcp-server" / "src" / "tools.ts"
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
MANIFEST_FILE = SCRIPT_DIR / "fallback_manifest.json"
API_TOOL_FILE = SCRIPT_DIR / "api_tool.py"
PROMPT_SYNC_SCRIPT = SCRIPT_DIR / "sync_page_prompt_library.py"
PAGE_READ_SERVICE = ROOT / "api" / "app" / "openclaw" / "service" / "PageCodeReadService.php"
PAGE_DIAGNOSTIC_SERVICE = ROOT / "api" / "app" / "openclaw" / "service" / "PageComponentDiagnosticService.php"
MCP_INSTRUCTIONS_FILE = ROOT / "mcp-server" / "src" / "instructions.ts"

PAGE_TOOLS = {
    "nicebox_analyze_page_creation": "analyzePageCreation",
    "nicebox_create_page_draft": "createPageDraft",
    "nicebox_get_page_creation_draft": "getPageCreationDraft",
    "nicebox_abandon_page_creation_draft": "abandonPageCreationDraft",
    "nicebox_commit_page_creation": "commitPageCreation",
    "nicebox_get_page_creation_operation": "getPageCreationOperation",
    "nicebox_list_pages": "listPages",
    "nicebox_get_page_metadata": "getPageMetadata",
    "nicebox_get_page_sections": "getPageSections",
    "nicebox_get_page_code": "getPageCode",
    "nicebox_get_page_width_settings": "getPageWidthSettings",
    "nicebox_diagnose_page_components": "diagnosePageComponents",
    "nicebox_validate_page_change": "validatePageChange",
    "nicebox_preview_page_width_settings": "previewPageWidthSettings",
    "nicebox_create_page_preview": "createPagePreview",
    "nicebox_create_page_width_preview": "createPageWidthPreview",
    "nicebox_get_page_preview": "getPagePreview",
    "nicebox_abandon_page_preview": "abandonPagePreview",
    "nicebox_rollback_page_preview_step": "rollbackPagePreviewStep",
    "nicebox_commit_page_change": "commitPageChange",
    "nicebox_commit_page_width_settings": "commitPageWidthSettings",
    "nicebox_get_page_change_operation": "getPageChangeOperation",
    "nicebox_list_page_backups": "listPageBackups",
    "nicebox_preview_page_backup": "previewPageBackup",
    "nicebox_commit_page_backup": "commitPageBackup",
}

PAGE_MANAGEMENT_TOOLS = {
    "nicebox_get_page_management_detail": "getPageManagementDetail",
    "nicebox_update_page_sort": "updatePageSort",
    "nicebox_update_page_parent": "updatePageParent",
    "nicebox_copy_pages": "copyPages",
    "nicebox_check_page_deletion": "checkPageDeletion",
    "nicebox_delete_pages": "deletePages",
    "nicebox_update_page_status": "updatePageStatus",
    "nicebox_check_page_locale_change": "checkPageLocaleChange",
    "nicebox_update_page_locale": "updatePageLocale",
    "nicebox_update_page_filename": "updatePageFilename",
    "nicebox_generate_page_seo": "generatePageSeo",
    "nicebox_update_page_settings": "updatePageSettings",
}

ARTICLE_EDIT_TOOLS = {
    "nicebox_get_article_detail": "getDetail",
    "nicebox_check_article_filename": "checkFilename",
    "nicebox_update_article": "update",
    "nicebox_regenerate_article_seo": "regenerateSeo",
    "nicebox_regenerate_article_faq": "regenerateFaq",
    "nicebox_sync_article_schema": "syncSchemaFromFaq",
}

PRODUCT_EDIT_TOOLS = {
    "nicebox_get_product_detail": "getDetail",
    "nicebox_check_product_filename": "checkFilename",
    "nicebox_update_product": "update",
    "nicebox_regenerate_product_seo": "regenerateSeo",
    "nicebox_regenerate_product_faq": "regenerateFaq",
    "nicebox_sync_product_schema": "syncSchemaFromFaq",
}

FAQ_EDIT_TOOLS = {
    "nicebox_list_faq_categories": "getCategories",
    "nicebox_search_faq_categories": "getCategories",
    "nicebox_create_faq_category": "createCategory",
    "nicebox_create_faq": "create",
    "nicebox_list_faqs": "list",
    "nicebox_search_faqs": "list",
    "nicebox_get_faq_detail": "getDetail",
    "nicebox_update_faq": "update",
    "nicebox_delete_faq": "delete",
    "nicebox_get_faq_category_impact": "getCategoryImpact",
    "nicebox_update_faq_category": "updateCategory",
    "nicebox_delete_faq_category": "deleteCategory",
}

CATEGORY_MANAGEMENT_TOOLS = {
    "nicebox_get_product_category_impact": "getCategoryImpact",
    "nicebox_update_product_category": "updateCategory",
    "nicebox_delete_product_category": "deleteCategory",
    "nicebox_get_article_category_impact": "getCategoryImpact",
    "nicebox_update_article_category": "updateCategory",
    "nicebox_delete_article_category": "deleteCategory",
}

KNOWLEDGE_TOOLS = {
    "nicebox_get_knowledge_profile": "getProfile",
    "nicebox_update_knowledge_profile": "updateProfile",
}

LANGUAGE_MANAGEMENT_TOOLS = {
    "nicebox_update_language_config": "updateConfig",
    "nicebox_preview_language_migration": "previewMigration",
    "nicebox_execute_language_migration": "executeMigration",
    "nicebox_get_language_delete_impact": "getDeleteImpact",
    "nicebox_delete_language": "delete",
    "nicebox_get_default_language_impact": "getDefaultImpact",
    "nicebox_set_default_language": "setDefault",
    "nicebox_get_language_operation": "getOperation",
}

REMOVED_QUALIFICATION_TOOLS = {
    "nicebox_list_qualifications": "listQualifications",
    "nicebox_create_qualification": "createQualification",
    "nicebox_update_qualification": "updateQualification",
    "nicebox_get_qualification_delete_impact": "getQualificationDeleteImpact",
    "nicebox_delete_qualification": "deleteQualification",
    "nicebox_extract_qualifications": "extractQualifications",
    "nicebox_import_qualifications": "importQualifications",
}

LEGACY_PAGE_FLOW_FILES = [
    ROOT / "nicebox-site-manager-main" / "skills" / "create_page.skill.md",
    ROOT / "nicebox-site-manager-main" / "skills" / "page_code_read.skill.md",
    ROOT / "nicebox-site-manager-main" / "skills" / "page_code_validate.skill.md",
    ROOT / "nicebox-site-manager-main" / "skills" / "page_change_workflow.skill.md",
    ROOT / "nicebox-site-manager-main" / "skills" / "page_dynamic_components.skill.md",
]

WORKBUDDY_PAGE_FLOW_FILES = [
    ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "references" / "新增页面流程.md",
    ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "references" / "页面代码读取流程.md",
    ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "references" / "页面修改草稿与校验流程.md",
    ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "references" / "页面预览保存与回退流程.md",
    ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "references" / "动态组件与复杂页面流程.md",
]

def joined_text(files):
    return "\n".join(path.read_text(encoding="utf-8") for path in files)

def main():
    source = TOOLS_FILE.read_text(encoding="utf-8")
    tools = set(re.findall(r"(?:registerApiTool\(|registerTool\()\s*(?:server,\s*client,\s*)?['\"](nicebox_[a-z0-9_]+)['\"]", source))
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    missing = sorted(tools - set(manifest))
    stale = sorted(set(manifest) - tools)
    missing_scripts = []
    for tool, command in manifest.items():
        script = command.split()[0]
        if script.endswith((".py", ".mjs")) and not (SCRIPT_DIR / script).is_file():
            missing_scripts.append("%s -> %s" % (tool, script))
    api_tool_source = API_TOOL_FILE.read_text(encoding="utf-8")
    controller_source = (ROOT / "api" / "app" / "openclaw" / "controller" / "SitePages.php").read_text(encoding="utf-8")
    legacy_flow = joined_text(LEGACY_PAGE_FLOW_FILES)
    workbuddy_flow = joined_text(WORKBUDDY_PAGE_FLOW_FILES)
    page_contract_errors = []
    for tool, controller_method in PAGE_TOOLS.items():
        checks = {
            "mcp": tool in tools,
            "fallback_manifest": tool in manifest,
            "ordinary_api_script": ('"%s"' % tool) in api_tool_source,
            "ordinary_api_controller": ("function %s(" % controller_method) in controller_source,
            "legacy_skill": tool in legacy_flow,
            "workbuddy_skill": tool in workbuddy_flow,
        }
        absent = [name for name, present in checks.items() if not present]
        if absent:
            page_contract_errors.append({"tool": tool, "missing": absent})
    page_management_sources = {
        "legacy_skill": joined_text([
            ROOT / "nicebox-site-manager-main" / "SKILL.md",
            ROOT / "nicebox-site-manager-main" / "skills" / "manage_pages.skill.md",
            ROOT / "nicebox-site-manager-main" / "skills" / "mcp_tools.skill.md",
        ]),
        "workbuddy_skill": joined_text([
            ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "SKILL.md",
            ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "references" / "页面管理流程.md",
        ]),
    }
    for tool, controller_method in PAGE_MANAGEMENT_TOOLS.items():
        checks = {
            "mcp": tool in tools,
            "fallback_manifest": tool in manifest,
            "ordinary_api_script": ('"%s"' % tool) in api_tool_source,
            "ordinary_api_controller": ("function %s(" % controller_method) in controller_source,
            "legacy_skill": tool in page_management_sources["legacy_skill"],
            "workbuddy_skill": tool in page_management_sources["workbuddy_skill"],
        }
        absent = [name for name, present in checks.items() if not present]
        if absent:
            page_contract_errors.append({"tool": tool, "missing": absent})
    ordered_tool_positions = sorted((max(source.find('"%s"' % tool), source.find("'%s'" % tool)), tool) for tool in PAGE_MANAGEMENT_TOOLS)
    if ordered_tool_positions and ordered_tool_positions[0][0] < 0:
        page_contract_errors.append({"tool": "page_management", "missing": ["tool registration source"]})
    else:
        for index, (position, tool) in enumerate(ordered_tool_positions):
            end = ordered_tool_positions[index + 1][0] if index + 1 < len(ordered_tool_positions) else source.find("nicebox_get_page_metadata", position)
            snippet = source[position:end if end > position else position + 2000]
            should_confirm = tool in {"nicebox_delete_pages", "nicebox_update_page_locale"}
            has_confirmed_schema = re.search(r"\bconfirmed\b", snippet) is not None
            if should_confirm != has_confirmed_schema:
                page_contract_errors.append({
                    "tool": tool,
                    "missing": ["confirmed schema" if should_confirm else "unexpected confirmed schema"],
                })
            should_be_idempotent = tool in {"nicebox_copy_pages", "nicebox_delete_pages", "nicebox_update_page_locale"}
            has_operation_id = re.search(r"\boperation_id\s*:", snippet) is not None
            if should_be_idempotent != has_operation_id:
                page_contract_errors.append({
                    "tool": tool,
                    "missing": ["operation_id schema" if should_be_idempotent else "unexpected operation_id schema"],
                })
            if tool == "nicebox_update_page_sort" and "expected_scope_hash" not in snippet:
                page_contract_errors.append({"tool": tool, "missing": ["expected_scope_hash schema"]})
    page_settings_contracts = {
        "mcp_nested_changes": 'changes: z.object({' in source and 'page_name: z.string().trim()' in source,
        "fallback_normalizer": 'def normalize_payload(tool, payload):' in api_tool_source
            and 'nicebox_update_page_settings' in api_tool_source and 'normalized["changes"] = changes' in api_tool_source,
        "controller_legacy_compatibility": "foreach (['page_name', 'seo_title', 'seo_keywords', 'seo_description'] as $field)" in controller_source,
        "legacy_skill_exact_contract": '"changes":{"page_name":"新名称"}' in page_management_sources["legacy_skill"],
        "workbuddy_skill_exact_contract": '"changes":{"page_name":"新名称"}' in page_management_sources["workbuddy_skill"],
    }
    missing_page_settings_contracts = [name for name, present in page_settings_contracts.items() if not present]
    if missing_page_settings_contracts:
        page_contract_errors.append({"tool": "nicebox_update_page_settings", "missing": missing_page_settings_contracts})

    page_management_service_source = (ROOT / "api" / "app" / "openclaw" / "service" / "PageManagementService.php").read_text(encoding="utf-8")
    generate_seo_body = page_management_service_source.split("public function generateSeo", 1)[-1].split("public function updateSettings", 1)[0]
    skill_capability_source = (ROOT / "api" / "config" / "skill_capabilities.php").read_text(encoding="utf-8")
    page_seo_contracts = {
        "shared_generator": "SeoTdkGeneratorService" in generate_seo_body and "generateBundle(" in generate_seo_body,
        "generate_only": "'saved' => false" in generate_seo_body
            and "->save(" not in generate_seo_body and "->update(" not in generate_seo_body and "->insert(" not in generate_seo_body,
        "operation_log_capability": "sitepages/generatepageseo" in skill_capability_source and "page.seo.generate" in skill_capability_source,
        "legacy_review_choices": all(token in page_management_sources["legacy_skill"] for token in ["确定保存", "重新生成", "取消"]),
        "workbuddy_review_choices": all(token in page_management_sources["workbuddy_skill"] for token in ["确定保存", "重新生成", "取消"]),
    }
    missing_page_seo_contracts = [name for name, present in page_seo_contracts.items() if not present]
    if missing_page_seo_contracts:
        page_contract_errors.append({"tool": "nicebox_generate_page_seo", "missing": missing_page_seo_contracts})

    locale_body = page_management_service_source.split("public function localeImpact", 1)[-1].split("public function updateLocale", 1)[0]
    update_locale_body = page_management_service_source.split("public function updateLocale", 1)[-1].split("public function updateFilename", 1)[0]
    page_locale_contracts = {
        "supported_locale_validation": "LocaleConfig::isValidLocale" in locale_body,
        "no_existing_locale_requirement": "PAGE_LOCALE_NOT_ENABLED" not in page_management_service_source
            and "目标语言尚未在当前站点启用" not in page_management_service_source,
        "site_language_sync": "SiteLangService::SCENE_ADD_NEW" in update_locale_body and "syncSiteLangs(" in update_locale_body,
        "legacy_skill_allows_new_locale": "无需预先存在于当前站点" in page_management_sources["legacy_skill"],
        "workbuddy_skill_allows_new_locale": "不要求当前站点已经存在该语言" in page_management_sources["workbuddy_skill"],
    }
    missing_page_locale_contracts = [name for name, present in page_locale_contracts.items() if not present]
    if missing_page_locale_contracts:
        page_contract_errors.append({"tool": "nicebox_update_page_locale", "missing": missing_page_locale_contracts})

    article_contract_errors = []
    article_controller_source = (ROOT / "api" / "app" / "openclaw" / "controller" / "Article.php").read_text(encoding="utf-8")
    article_skill_sources = {
        "legacy_skill": joined_text([
            ROOT / "nicebox-site-manager-main" / "SKILL.md",
            ROOT / "nicebox-site-manager-main" / "skills" / "edit_article.skill.md",
            ROOT / "nicebox-site-manager-main" / "skills" / "mcp_tools.skill.md",
        ]),
        "workbuddy_skill": joined_text([
            ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "SKILL.md",
            ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "references" / "文章修改流程.md",
        ]),
    }
    for tool, controller_method in ARTICLE_EDIT_TOOLS.items():
        checks = {
            "mcp": tool in tools,
            "fallback_manifest": tool in manifest,
            "ordinary_api_script": ('"%s"' % tool) in api_tool_source,
            "ordinary_api_controller": ("function %s(" % controller_method) in article_controller_source,
            "legacy_skill": tool in article_skill_sources["legacy_skill"] or "edit_article.skill.md" in article_skill_sources["legacy_skill"],
            "workbuddy_skill": "文章修改流程" in article_skill_sources["workbuddy_skill"],
        }
        absent = [name for name, present in checks.items() if not present]
        if absent:
            article_contract_errors.append({"tool": tool, "missing": absent})

    product_contract_errors = []
    product_controller_source = (ROOT / "api" / "app" / "openclaw" / "controller" / "Product.php").read_text(encoding="utf-8")
    product_skill_sources = {
        "legacy_skill": joined_text([
            ROOT / "nicebox-site-manager-main" / "SKILL.md",
            ROOT / "nicebox-site-manager-main" / "skills" / "edit_product.skill.md",
            ROOT / "nicebox-site-manager-main" / "skills" / "mcp_tools.skill.md",
        ]),
        "workbuddy_skill": joined_text([
            ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "SKILL.md",
            ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "references" / "产品修改流程.md",
        ]),
    }
    for tool, controller_method in PRODUCT_EDIT_TOOLS.items():
        checks = {
            "mcp": tool in tools,
            "fallback_manifest": tool in manifest,
            "ordinary_api_script": ('"%s"' % tool) in api_tool_source,
            "ordinary_api_controller": ("function %s(" % controller_method) in product_controller_source,
            "legacy_skill": tool in product_skill_sources["legacy_skill"] or "edit_product.skill.md" in product_skill_sources["legacy_skill"],
            "workbuddy_skill": "产品修改流程" in product_skill_sources["workbuddy_skill"],
        }
        absent = [name for name, present in checks.items() if not present]
        if absent:
            product_contract_errors.append({"tool": tool, "missing": absent})

    faq_contract_errors = []
    faq_controller_source = (ROOT / "api" / "app" / "openclaw" / "controller" / "Faq.php").read_text(encoding="utf-8")
    faq_skill_sources = {
        "legacy_skill": joined_text([
            ROOT / "nicebox-site-manager-main" / "SKILL.md",
            ROOT / "nicebox-site-manager-main" / "skills" / "edit_faq.skill.md",
            ROOT / "nicebox-site-manager-main" / "skills" / "create_faq.skill.md",
            ROOT / "nicebox-site-manager-main" / "skills" / "mcp_tools.skill.md",
        ]),
        "workbuddy_skill": joined_text([
            ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "SKILL.md",
            ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "references" / "FAQ修改流程.md",
            ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "references" / "内容管理流程.md",
        ]),
    }
    for tool, controller_method in FAQ_EDIT_TOOLS.items():
        checks = {
            "mcp": tool in tools,
            "fallback_manifest": tool in manifest,
            "ordinary_api_script": ('"%s"' % tool) in api_tool_source,
            "ordinary_api_controller": ("function %s(" % controller_method) in faq_controller_source,
            "legacy_skill": "create_faq.skill.md" in faq_skill_sources["legacy_skill"] or "edit_faq.skill.md" in faq_skill_sources["legacy_skill"],
            "workbuddy_skill": "独立 FAQ" in faq_skill_sources["workbuddy_skill"] or "FAQ修改流程" in faq_skill_sources["workbuddy_skill"],
        }
        absent = [name for name, present in checks.items() if not present]
        if absent:
            faq_contract_errors.append({"tool": tool, "missing": absent})

    category_contract_errors = []
    category_skill_sources = joined_text([
        ROOT / "nicebox-site-manager-main" / "skills" / "list_categories.skill.md",
        ROOT / "nicebox-site-manager-main" / "skills" / "mcp_tools.skill.md",
        ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "references" / "分类修改与删除流程.md",
    ])
    controller_sources = {
        "product": product_controller_source,
        "article": article_controller_source,
    }
    for tool, controller_method in CATEGORY_MANAGEMENT_TOOLS.items():
        category_type = "product" if "_product_" in tool else "article"
        checks = {
            "mcp": tool in tools,
            "fallback_manifest": tool in manifest,
            "ordinary_api_script": ('"%s"' % tool) in api_tool_source,
            "ordinary_api_controller": ("function %s(" % controller_method) in controller_sources[category_type],
            "skills": "expected_impact_hash" in category_skill_sources and "删除分类不会删除" in category_skill_sources,
        }
        absent = [name for name, present in checks.items() if not present]
        if absent:
            category_contract_errors.append({"tool": tool, "missing": absent})

    knowledge_contract_errors = []
    knowledge_controller_source = (ROOT / "api" / "app" / "openclaw" / "controller" / "Knowledge.php").read_text(encoding="utf-8")
    knowledge_skill_sources = joined_text([
        ROOT / "nicebox-site-manager-main" / "SKILL.md",
        ROOT / "nicebox-site-manager-main" / "skills" / "knowledge_base.skill.md",
        ROOT / "nicebox-site-manager-main" / "skills" / "mcp_tools.skill.md",
        ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "SKILL.md",
        ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "references" / "AI知识库管理流程.md",
    ])
    for tool, controller_method in KNOWLEDGE_TOOLS.items():
        checks = {
            "mcp": tool in tools,
            "fallback_manifest": tool in manifest,
            "ordinary_api_script": ('"%s"' % tool) in api_tool_source,
            "ordinary_api_controller": ("function %s(" % controller_method) in knowledge_controller_source,
            "skills": tool in knowledge_skill_sources,
        }
        absent = [name for name, present in checks.items() if not present]
        if absent:
            knowledge_contract_errors.append({"tool": tool, "missing": absent})
    profile_aliases = ["公司资料", "公司基本资料", "企业资料", "企业基本资料", "网站基本资料"]
    for alias in profile_aliases:
        if alias not in knowledge_skill_sources:
            knowledge_contract_errors.append({"profile_alias_missing_from_skills": alias})
        if alias not in source:
            knowledge_contract_errors.append({"profile_alias_missing_from_mcp": alias})

    language_contract_errors = []
    language_controller_source = (ROOT / "api" / "app" / "openclaw" / "controller" / "SiteLanguages.php").read_text(encoding="utf-8")
    language_skill_sources = joined_text([
        ROOT / "nicebox-site-manager-main" / "SKILL.md",
        ROOT / "nicebox-site-manager-main" / "skills" / "list_languages.skill.md",
        ROOT / "nicebox-site-manager-main" / "skills" / "mcp_tools.skill.md",
        ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "SKILL.md",
        ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "references" / "多语言管理流程.md",
    ])
    for tool, controller_method in LANGUAGE_MANAGEMENT_TOOLS.items():
        checks = {
            "mcp": tool in tools,
            "fallback_manifest": tool in manifest,
            "ordinary_api_script": ('"%s"' % tool) in api_tool_source,
            "ordinary_api_controller": ("function %s(" % controller_method) in language_controller_source,
            "skills": tool in language_skill_sources,
        }
        absent = [name for name, present in checks.items() if not present]
        if absent:
            language_contract_errors.append({"tool": tool, "missing": absent})
    for required_text in ["只更改内容归属语言，不翻译", "目标语言已有内容", "二次提醒", "页面入口"]:
        if required_text not in language_skill_sources:
            language_contract_errors.append({"language_flow_missing": required_text})

    qualification_boundary_errors = []
    for tool, controller_method in REMOVED_QUALIFICATION_TOOLS.items():
        leaks = []
        if tool in tools: leaks.append("mcp")
        if tool in manifest: leaks.append("fallback_manifest")
        if ('"%s"' % tool) in api_tool_source: leaks.append("ordinary_api_script")
        if ("function %s(" % controller_method) in knowledge_controller_source: leaks.append("openclaw_controller")
        if tool in knowledge_skill_sources: leaks.append("skills")
        if leaks:
            qualification_boundary_errors.append({"tool": tool, "unexpected": leaks})

    admin_qualification_controller = ROOT / "api" / "app" / "admin" / "controller" / "SiteQualifications.php"
    admin_qualification_model = ROOT / "api" / "app" / "common" / "model" / "SiteQualification.php"
    admin_qualification_extract = ROOT / "api" / "app" / "common" / "service" / "SiteQualificationExtractService.php"
    admin_qualification_sync = ROOT / "api" / "app" / "common" / "service" / "SiteQualificationMaterialSyncService.php"
    admin_source = admin_qualification_controller.read_text(encoding="utf-8") if admin_qualification_controller.is_file() else ""
    for required_file in [admin_qualification_controller, admin_qualification_model, admin_qualification_extract, admin_qualification_sync]:
        if not required_file.is_file():
            qualification_boundary_errors.append({"backend_missing": str(required_file)})
    for method in ["index", "save", "updateName", "delete", "extract", "import"]:
        if ("function %s(" % method) not in admin_source:
            qualification_boundary_errors.append({"backend_method_missing": method})

    prompt_library_errors = []
    canonical_prompt_dir = ROOT / "doc" / "workbuddy" / "页面修改能力" / "page-edit-prompts"
    prompt_manifest_file = canonical_prompt_dir / "manifest.json"
    prompt_manifest = {}
    if not PROMPT_SYNC_SCRIPT.is_file() or not prompt_manifest_file.is_file():
        prompt_library_errors.append("canonical prompt library or synchronization script is missing")
    else:
        prompt_manifest = json.loads(prompt_manifest_file.read_text(encoding="utf-8"))
        prompt_files = ["manifest.json", *prompt_manifest.get("files", [])]
        prompt_targets = [
            ROOT / "nicebox-site-manager-main" / "references" / "page-edit-library",
            ROOT / "workbuddy-connector" / "skills" / "nicebox-site-manager" / "references" / "page-edit-library",
        ]
        for relative in prompt_files:
            source_file = canonical_prompt_dir / relative
            if not source_file.is_file():
                prompt_library_errors.append("missing canonical prompt file: %s" % relative)
                continue
            source_content = source_file.read_bytes()
            for target in prompt_targets:
                target_file = target / relative
                if not target_file.is_file() or target_file.read_bytes() != source_content:
                    prompt_library_errors.append("prompt library out of sync: %s" % target_file)

        page_read_source = PAGE_READ_SERVICE.read_text(encoding="utf-8")
        for constant, manifest_key in [("RULES_VERSION", "rules_version"), ("PROMPT_VERSION", "prompt_version")]:
            match = re.search(r"public const %s\s*=\s*['\"]([^'\"]+)['\"]" % constant, page_read_source)
            expected = str(prompt_manifest.get(manifest_key, ""))
            if not match or match.group(1) != expected:
                actual = match.group(1) if match else "missing"
                prompt_library_errors.append("%s mismatch: backend=%s manifest=%s" % (constant, actual, expected))

        diagnostic_source = PAGE_DIAGNOSTIC_SERVICE.read_text(encoding="utf-8")
        mcp_instruction_source = MCP_INSTRUCTIONS_FILE.read_text(encoding="utf-8")
        required_detail_contracts = [
            ("PRODUCT_DETAIL_NESTED_ROOT_FORBIDDEN", diagnostic_source, "backend product detail nesting rule"),
            ("NEWS_DETAIL_MULTIPLE_ROOTS_FORBIDDEN", diagnostic_source, "backend news detail single-root rule"),
            ("多个顶层兄弟 product_detail", mcp_instruction_source, "MCP product detail sibling-root instruction"),
            ("只填充第一个根节点", mcp_instruction_source, "MCP news detail first-root instruction"),
        ]
        for token, source_text, label in required_detail_contracts:
            if token not in source_text:
                prompt_library_errors.append("missing detail contract: %s" % label)

    if missing or stale or missing_scripts or page_contract_errors or article_contract_errors or product_contract_errors or faq_contract_errors or category_contract_errors or knowledge_contract_errors or language_contract_errors or qualification_boundary_errors or prompt_library_errors:
        print(json.dumps({"ok": False, "mcp_tool_count": len(tools), "fallback_count": len(manifest), "missing": missing, "stale": stale, "missing_scripts": missing_scripts, "page_contract_errors": page_contract_errors, "article_contract_errors": article_contract_errors, "product_contract_errors": product_contract_errors, "faq_contract_errors": faq_contract_errors, "category_contract_errors": category_contract_errors, "knowledge_contract_errors": knowledge_contract_errors, "language_contract_errors": language_contract_errors, "qualification_boundary_errors": qualification_boundary_errors, "prompt_library_errors": prompt_library_errors}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"ok": True, "mcp_tool_count": len(tools), "fallback_count": len(manifest), "page_tool_count": len(PAGE_TOOLS), "page_management_tool_count": len(PAGE_MANAGEMENT_TOOLS), "article_edit_tool_count": len(ARTICLE_EDIT_TOOLS), "product_edit_tool_count": len(PRODUCT_EDIT_TOOLS), "faq_edit_tool_count": len(FAQ_EDIT_TOOLS), "category_management_tool_count": len(CATEGORY_MANAGEMENT_TOOLS) + 3, "knowledge_tool_count": len(KNOWLEDGE_TOOLS), "language_management_tool_count": len(LANGUAGE_MANAGEMENT_TOOLS), "prompt_library_version": prompt_manifest["library_version"], "message": "所有 MCP 工具均已登记普通 API 回退，多语言与页面管理能力已同步到普通 API 和两个 Skill"}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__": sys.exit(main())
