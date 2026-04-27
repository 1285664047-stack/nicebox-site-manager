#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成网站 - 交互式多轮对话脚本（Python 版）

双重确认机制：
  - 第1次 ask-init  — 收集问题前检查站点数据，有数据则弹出确认
  - 第2次 generate  — 生成网站前再次检查站点数据，有数据则弹出确认
  - 两次确认提示内容完全一致

SSE progressive_content 使用整体赋值（覆盖）而非累积追加
"""
import argparse
import json
import os
import re
import sys
import time as time_module
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

# Windows GBK 编码修复
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_URL = os.environ.get("AIBOX_BASE_URL", "https://ai.nicebox.cn/api/openclaw")
API_KEY = os.environ.get("AIBOX_API_KEY", "")

ENDPOINT_LANGUAGE_LIST = f"{BASE_URL}/site_pages/getLanguageList"
ENDPOINT_INITIALIZE = f"{BASE_URL}/template/initializeData"
ENDPOINT_GET_COMPANY_INFO = f"{BASE_URL}/ai_tools/getCompanyInfo"
ENDPOINT_GENERATE_WEBSITE = f"{BASE_URL}/ai_tools/generateWebsite"
ENDPOINT_GENERATE_SHARE_URL = f"{BASE_URL}/site/generateShareUrl"
ENDPOINT_READ_INDEX_HTML = f"{BASE_URL}/site_pages/readIndexHtml"

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".dialogue_state.json")

# ── 统一确认提示（两次确认使用完全相同的文案） ─────────────────────────────
CONFIRM_MESSAGE = "检测到站点已有数据，生成网站将初始化站点，清空已有的所有网站信息，包括页面、产品、文章、留言等。是否确认继续？"
CONFIRM_OPTIONS = ["确认", "取消"]

# ═══════════════════════════════════════════════════════════════════════════════
# 7 个核心问题（精简版）
# ═══════════════════════════════════════════════════════════════════════════════
# field：对应 API 字段名（一个 question 可能对应多个 API 字段）
# followups：回答后需要追问的子字段（为空时自动跳过追问）
QUESTIONS = [
    {
        "field": "company_name",
        "question": "请问您的公司名称或想创建的网站名称是什么？",
        "placeholder": "例如：明德律师事务所、某某科技官网",
        "required": True,
        "followups": [],          # 公司名称无追问
    },
    {
        "field": "logo",
        "question": "请问您是否有公司logo地址？没有请直接跳过。",
        "placeholder": "例如：https://example.com/logo.png",
        "required": False,
        "followups": [],          # 公司logo无追问
    },
    {
        "field": "industry",
        "question": "您从事哪个行业？",
        "placeholder": "例如：科技、医疗、教育、餐饮、金融、法律",
        "required": False,
        "followups": [],
    },
    {
        "field": "business_scope",
        "question": "您的业务范围是什么？提供哪些产品或服务？",
        "placeholder": "例如：软件开发与定制、技术咨询服务",
        "required": False,
        "followups": [],
    },
    {
        "field": "advantages",
        "question": "您的核心竞争优势是什么？",
        "placeholder": "例如：技术领先、价格合理、服务周到、高性价比",
        "required": False,
        "followups": [],
    },
    {
        "field": "phone",
        "question": "请提供您的联系方式（电话、邮箱、地址）？",
        "placeholder": "例如：400-888-8888 / contact@example.com / 北京市朝阳区",
        "required": False,
        "followups": ["email", "address"],
    },
    {
        "field": "style",
        "question": "您希望网站呈现什么样的视觉风格？",
        "placeholder": "例如：简约现代风、专业商务风、活力创意风、温馨亲切风",
        "required": False,
        "followups": [],
    },
    {
        "field": "other",
        "question": "还有其他需要补充的内容吗？例如：配色方案、公司介绍、公司口号、企业文化、业务特色等。",
        "placeholder": "没有可跳过",
        "required": False,
        "followups": [],
    },
]

# API 字段中文标签
FIELD_LABELS = {
    "company_name": "公司名称",
    "industry": "行业",
    "business_scope": "业务范围",
    "advantages": "核心优势",
    "phone": "联系电话",
    "email": "联系邮箱",
    "address": "公司地址",
    "logo": "Logo",
    "style": "视觉风格",
    "other": "其他补充",
}

# ═══════════════════════════════════════════════════════════════════════════════
# 智能提示生成（根据已填写内容动态生成相关提示）
# ═══════════════════════════════════════════════════════════════════════════════

# 公司名称关键词 -> 行业推断
COMPANY_KEYWORDS_TO_INDUSTRY = {
    "帽": "帽子设计",
    "宠物": "宠物服务",
    "律师": "法律服务",
    "科技": "科技",
    "网络": "科技",
    "软件": "科技",
    "医疗": "医疗健康",
    "医院": "医疗健康",
    "诊所": "医疗健康",
    "教育": "教育",
    "培训": "教育",
    "学校": "教育",
    "餐饮": "餐饮",
    "餐厅": "餐饮",
    "酒店": "餐饮",
    "金融": "金融服务",
    "投资": "金融服务",
    "房产": "房产",
    "地产": "房产",
    "美容": "美容美发",
    "美发": "美容美发",
    "健身": "健身运动",
    "装修": "装修设计",
    "装饰": "装修设计",
    "物流": "物流运输",
    "电商": "电子商务",
}

# 行业关键词 -> 相关业务范围示例
INDUSTRY_BUSINESS_SCOPE_HINTS = {
    "帽子": ["帽子设计、帽子定制、帽饰批发", "帽业生产、帽饰零售、品牌帽子"],
    "宠物": ["宠物医疗、宠物美容、宠物寄养", "宠物诊疗、宠物疫苗、宠物用品销售"],
    "律师": ["民事诉讼、刑事辩护、企业法务", "合同纠纷、知识产权、法律咨询"],
    "科技": ["软件开发、系统集成、技术支持", "智能硬件、数据分析、云服务"],
    "医疗": ["诊疗服务、健康管理、康复护理", "医疗器械、药品销售、健康体检"],
    "教育": ["课程培训、在线教育、教育咨询", "职业技能、语言培训、K12辅导"],
    "餐饮": ["餐饮服务、外卖配送、食材供应", "连锁经营、品牌加盟、宴会承办"],
    "金融": ["贷款服务、投资理财、保险代理", "财富管理、风险评估、金融咨询"],
    "房产": ["房产中介、房屋租赁、物业管理", "新房销售、二手房交易、装修服务"],
    "美容": ["美容护肤、美发造型、美甲美睫", "SPA护理、皮肤管理、形象设计"],
    "健身": ["健身培训、私教课程、运动康复", "健身器材、营养指导、体测服务"],
    "装修": ["室内设计、装修施工、软装搭配", "家装服务、工装设计、建材销售"],
    "物流": ["货物运输、仓储服务、配送服务", "供应链管理、国际物流、冷链运输"],
    "电商": ["网上零售、电商运营、品牌代理", "跨境贸易、直播带货、供应链服务"],
}

# 行业 -> 视觉风格推荐
INDUSTRY_STYLE_HINTS = {
    "帽子": ["时尚简约风，突出帽饰设计感", "活力创意风，展现品牌个性"],
    "宠物": ["温馨亲切风，传递关爱感", "清新可爱风，吸引宠物主人"],
    "律师": ["专业严谨风，蓝色或深灰色调", "稳重商务风，体现专业可信"],
    "科技": ["现代科技风，蓝色/深色系", "简约未来风，渐变色彩"],
    "医疗": ["清新专业风，蓝绿色调", "温馨治愈风，浅色系"],
    "教育": ["活力青春风，明亮色彩", "专业学术风，稳重大气"],
    "餐饮": ["温馨食欲风，暖色调", "时尚简约风，突出菜品"],
    "金融": ["专业稳重风，深蓝色调", "现代商务风，简洁大气"],
    "房产": ["现代简约风，突出房源", "高端大气风，金色/深色"],
    "美容": ["时尚优雅风，粉紫色系", "清新自然风，浅色调"],
    "健身": ["活力运动风，橙红色系", "现代简约风，黑白灰"],
    "装修": ["现代简约风，突出设计案例", "高端品质风，灰色/金色"],
    "物流": ["现代高效风，蓝绿色系", "简约商务风，橙色点缀"],
    "电商": ["时尚简约风，突出商品", "活力创意风，多彩配色"],
}

# 行业 -> 核心优势推荐
INDUSTRY_ADVANTAGES_HINTS = {
    "帽子": ["原创设计、品质保证、款式多样", "快速交付、定制服务、价格实惠"],
    "宠物": ["专业医疗团队、先进设备、贴心服务", "24小时急诊、价格透明、会员优惠"],
    "律师": ["资深律师团队、成功案例丰富、收费透明", "专业领域深耕、高效响应、客户至上"],
    "科技": ["技术领先、经验丰富、服务周到", "自主研发、安全可靠、性价比高"],
    "医疗": ["专家团队、先进设备、环境舒适", "预约便捷、服务贴心、医保定点"],
    "教育": ["师资优秀、课程体系完善、通过率高", "小班教学、个性化辅导、口碑良好"],
    "餐饮": ["食材新鲜、口味地道、环境优雅", "价格实惠、服务周到、特色菜品"],
    "金融": ["资质齐全、经验丰富、服务专业", "利率优惠、审批快速、隐私保护"],
    "房产": ["房源真实、专业团队、交易安全", "服务周到、价格透明、售后保障"],
    "美容": ["技术专业、产品优质、环境舒适", "效果显著、价格合理、会员特权"],
    "健身": ["设备先进、教练专业、环境舒适", "课程丰富、交通便利、会员福利多"],
    "装修": ["设计优秀、施工规范、材料环保", "价格透明、售后保障、工期准时"],
    "物流": ["网络覆盖广、时效快、价格优", "全程追踪、保险保障、服务贴心"],
    "电商": ["正品保证、价格优惠、物流快", "品类齐全、售后完善、会员福利"],
}


def infer_industry_from_name(company_name):
    """从公司名称推断行业"""
    if not company_name or company_name == "未填写":
        return None
    for keyword, industry in COMPANY_KEYWORDS_TO_INDUSTRY.items():
        if keyword in company_name:
            return industry
    return None


def get_smart_placeholder(field, collected):
    """
    根据已收集的信息，生成智能占位提示
    
    Args:
        field: 当前问题字段名
        collected: 已收集的信息字典
        
    Returns:
        智能 placeholder 字符串
    """
    company_name = collected.get("company_name", "")
    industry = collected.get("industry", "")
    
    # 如果没有填写行业，尝试从公司名推断
    if not industry or industry == "未填写":
        industry = infer_industry_from_name(company_name)
    
    # 根据字段类型生成智能提示
    if field == "industry":
        inferred = infer_industry_from_name(company_name)
        if inferred:
            return f"例如：{inferred}"
        return "例如：科技、医疗、教育、餐饮、金融、法律"
    
    elif field == "business_scope":
        # 查找匹配的行业提示
        for keyword, hints in INDUSTRY_BUSINESS_SCOPE_HINTS.items():
            if keyword in company_name or (industry and keyword in industry):
                return f"例如：{hints[0]}"
        # 默认提示
        if company_name and company_name != "未填写":
            return f"例如：{company_name}的核心业务、相关产品或服务"
        return "例如：软件开发与定制、技术咨询服务"
    
    elif field == "advantages":
        # 查找匹配的行业提示
        for keyword, hints in INDUSTRY_ADVANTAGES_HINTS.items():
            if keyword in company_name or (industry and keyword in industry):
                return f"例如：{hints[0]}"
        return "例如：技术领先、价格合理、服务周到、高性价比"
    
    elif field == "style":
        # 查找匹配的行业提示
        for keyword, hints in INDUSTRY_STYLE_HINTS.items():
            if keyword in company_name or (industry and keyword in industry):
                return f"例如：{hints[0]}"
        return "例如：简约现代风、专业商务风、活力创意风、温馨亲切风"
    
    elif field == "other":
        if company_name and company_name != "未填写":
            return f"例如：{company_name}的配色方案、公司口号、企业文化等"
        return "没有可跳过"
    
    # 默认返回原占位符
    return None


def build_smart_question(q, collected):
    """
    构建包含智能提示的问题输出
    
    Args:
        q: 问题字典
        collected: 已收集的信息字典
        
    Returns:
        包含智能提示的问题字典
    """
    field = q["field"]
    
    # 获取智能占位符
    smart_placeholder = get_smart_placeholder(field, collected)
    original_placeholder = q.get("placeholder", "")
    
    # 优先使用智能占位符，如果没有则使用原始占位符
    placeholder = smart_placeholder if smart_placeholder else original_placeholder
    
    # 构建智能问题文本
    company_name = collected.get("company_name", "")
    question = q["question"]
    
    # 为特定字段定制问题
    if field == "business_scope" and company_name and company_name != "未填写":
        question = f"{company_name}的业务范围是什么？提供哪些产品或服务？"
    elif field == "advantages" and company_name and company_name != "未填写":
        question = f"{company_name}的核心竞争优势是什么？"
    elif field == "style" and company_name and company_name != "未填写":
        question = f"您希望{company_name}的网站呈现什么样的视觉风格？"
    
    return {
        "field": field,
        "question": question,
        "placeholder": placeholder,
        "required": q.get("required", False),
        "followups": q.get("followups", []),
    }

# API 必填字段（getCompanyInfo 要求）
REQUIRED_API_FIELDS = ["company_name"]

# ═══════════════════════════════════════════════════════════════════════════════
# 状态管理
# ═══════════════════════════════════════════════════════════════════════════════

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "current_index": 0,
        "collected": {},       # field -> answer string
        "pending_followups": [],  # 待追问的子字段列表
        "started_at": datetime.now().isoformat(),
        "initialized": False,
        # 第1次确认（ask-init 阶段）: None=未询问 | "pending"=等待回复 | True=已确认 | False=已取消
        "init_confirmed": None,
        # 第2次确认（generate 阶段）: None=未询问 | True=已确认 | False=已取消
        "generate_confirmed": None,
        "finished_early": False,
    }


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def reset_state():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    # 清除草稿文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for f in os.listdir(script_dir):
        if f.endswith(".draft"):
            try:
                os.remove(os.path.join(script_dir, f))
            except Exception:
                pass
    print("对话状态已重置，所有草稿已清除")


# ═══════════════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════════════

def is_phone(text):
    return bool(re.search(r"[\d\-\(\)\s]{7,}", text))


def is_email(text):
    return bool(re.search(r"[\w.\-]+@[\w.\-]+\.\w+", text))


def is_address(text):
    # 地址特征：含省/市/区/县/路/号等关键词
    return bool(re.search(
        r"[\u4e00-\u9fa5]{2,}[\省市县区镇路街号楼单元层座]",
        text
    ))


def parse_contact(text):
    """
    从一段文本中提取电话、邮箱、地址。
    返回 {phone, email, address}，字段可能为空字符串。
    """
    phone = ""
    email = ""
    address = ""

    # 提取邮箱
    emails = re.findall(r"[\w.\-]+@[\w.\-]+\.\w+", text)
    if emails:
        email = emails[0]

    # 提取电话号码
    phones = re.findall(r"[\d\-\(\)\s]{7,}", text)
    # 过滤掉太短的（可能是年份、邮编等）
    phones = [p for p in phones if len(re.sub(r"\D", "", p)) >= 7]
    if phones:
        phone = re.sub(r"\s+", "", phones[0])

    # 提取地址（中文地址特征词）
    addr_match = re.search(
        r"[\u4e00-\u9fa5]{2,}[\u4e00-\u9fa5\s\d\-省市区县镇路街号楼单元层座]",
        text
    )
    if addr_match:
        address = addr_match.group().strip()

    # 如果以上都没找到，整个文本作为地址
    if not phone and not email and not address and len(text) >= 8:
        address = text.strip()

    return phone, email, address


def sanitize_company_info(collected):
    """
    规范化公司信息：
      - 空值 → "未填写"
      - Logo 未填写 → 占位图
    """
    result = {}
    for key in FIELD_LABELS:
        value = collected.get(key, "")
        if value is None or (isinstance(value, str) and value.strip() == ""):
            result[key] = "未填写"
        else:
            result[key] = value.strip()

    if result.get("logo") == "未填写" or not result.get("logo"):
        name = result.get("company_name", "Logo")
        result["logo"] = f"https://via.placeholder.com/200x80/8B4513/FFFFFF?text={urllib.parse.quote(name[:6])}"

    return result


# ── 统一确认提示输出 ──────────────────────────────────────────────────────────

def output_confirm_prompt(stage):
    """输出确认提示
    stage: "ask-init" 或 "generate"，两次提示内容完全一致
    
    [WARN] 重要：此函数输出后，AI 必须停下来等待用户回复！
    """
    print(json.dumps({
        "need_confirm": True,
        "stage": stage,
        "message": CONFIRM_MESSAGE,
        "options": CONFIRM_OPTIONS,
        "tip": "回复「确认」继续，回复「取消」终止操作",
        # [CRITICAL] 新增：明确告诉 AI 不要自动回复
        "_ai_instruction": "【AI 注意】请将此确认提示展示给用户，然后停下来等待用户回复。不要自动回复「确认」或「取消」！",
    }, ensure_ascii=False))


# ── 辅助：输出汇总 ──────────────────────────────────────────────────────────

def print_summary(collected):
    """输出需求汇总
    
    [WARN] 重要：此函数输出后，AI 必须停下来等待用户确认！
    """
    info = sanitize_company_info(collected)
    lines = ["=" * 50, "[SUMMARY] 网站需求汇总", "=" * 50, ""]
    for q in QUESTIONS:
        f = q["field"]
        v = info.get(f, "未填写")
        tag = " [REQ]必填" if f in REQUIRED_API_FIELDS else ""
        lines.append(f"  {FIELD_LABELS.get(f, f)}：{v}{tag}")
    for f in ["email", "address"]:
        if f in collected and collected.get(f) and collected[f] != "未填写":
            lines.append(f"  {FIELD_LABELS.get(f, f)}：{collected[f]}")
    lines += ["", "=" * 50]
    print("\n".join(lines))

    answered = len([v for v in info.values() if v != "未填写"])
    skipped = len([v for v in info.values() if v == "未填写"])
    print(json.dumps({
        "answered_count": answered,
        "skipped_count": skipped,
        "collected": info,
        "_ai_instruction": "【AI 注意】请将此汇总展示给用户，然后停下来等待用户确认是否生成。不要自动执行 generate 命令！",
    }, ensure_ascii=False, indent=2))


# ── 辅助：下一题或结束 ────────────────────────────────────────────────────────

def advance(state):
    """推进到下一个问题或结束
    
    [WARN] 重要：此函数输出问题后，AI 必须停下来等待用户回复！
    """
    if state.get("pending_followups"):
        sub = state["pending_followups"][0]
        prompt = build_followup_question(None, sub)
        print(json.dumps({
            "type": "followup",
            "field": sub,
            "label": FIELD_LABELS.get(sub, sub),
            "question": prompt["question"],
            "placeholder": prompt.get("placeholder", ""),
            "hint": "可回复「跳过」跳过此项",
            # [CRITICAL] 新增：明确告诉 AI 不要自动回答
            "_ai_instruction": "【AI 注意】请将此问题展示给用户，然后停下来等待用户回复。不要自动生成答案！",
        }, ensure_ascii=False))
        return
    
    if state.get("current_index", 0) >= len(QUESTIONS) or state.get("finished_early"):
        print_summary(state.get("collected", {}))
        print(json.dumps({
            "action": "show_summary",
            "message": "所有问题已收集完毕，请确认以上信息是否正确。",
            "next_step": "如需生成网站，请回复「确认生成」；如需修改，请告诉我具体修改内容。",
            "_ai_instruction": "【AI 注意】请将汇总信息展示给用户，然后停下来等待用户确认。不要自动执行 generate 命令！",
        }, ensure_ascii=False))
    else:
        q = QUESTIONS[state["current_index"]]
        collected = state.get("collected", {})
        
        # 使用智能提示生成问题
        smart_q = build_smart_question(q, collected)
        
        print(json.dumps({
            "index": state["current_index"],
            "total": len(QUESTIONS),
            "field": q["field"],
            "label": FIELD_LABELS.get(q["field"], q["field"]),
            "question": smart_q["question"],
            "placeholder": smart_q["placeholder"],
            "required": q.get("required", False),
            "hint": "可回复「跳过」跳过此题，回复「完成」提前结束所有问答",
            # [CRITICAL] 新增：明确告诉 AI 不要自动回答
            "_ai_instruction": "【AI 注意】请将此问题展示给用户，然后停下来等待用户回复。不要自动生成答案！",
        }, ensure_ascii=False))


# ── 辅助：执行初始化并继续 ────────────────────────────────────────────────────

def do_initialize(state, label):
    """执行初始化并继续"""
    print(f"{label}，正在初始化站点数据...")
    result = initialize_site()
    if result.get("code") == 0 and result.get("data", {}).get("initializeSuccess") is True:
        print("初始化完成！")
        state["initialized"] = True
    else:
        msg = result.get("msg") or str(result)
        print("[错误] 初始化失败：" + msg)
        print("请检查后端是否正常运行，或稍后重试。如需帮助，请联系技术支持。")
        sys.exit(1)
    save_state(state)


# ── 辅助：执行网站生成 ────────────────────────────────────────────────────────

def do_generate(state):
    """执行网站生成"""
    collected = state.get("collected", {})
    info = sanitize_company_info(collected)
    
    for f in REQUIRED_API_FIELDS:
        if info.get(f) == "未填写":
            print(f"[警告] {FIELD_LABELS.get(f, f)} 为空，可能影响生成效果")
    
    print("正在获取企业信息...")
    info_result = call_get_company_info(collected)
    if info_result.get("code") != 0:
        print(f"获取企业信息失败: {info_result.get('msg', '')}")
        return
    
    company_info = info_result.get("data", "")
    if not company_info:
        print("企业信息为空，无法生成")
        return
    
    requirement = f"请根据以下信息生成网站：\n{company_info}"
    print("企业信息获取成功，正在生成网站（预计 5-10 分钟，请耐心等待）...\n")
    
    result = call_generate_website(requirement)
    
    if result.get("code") == 0:
        # [WARN] SSE 流返回 ok 不代表网站真正生成成功，需通过 readIndexHtml 验证
        print("\n正在验证网站是否生成成功...")
        verify_result = call_read_index_html()
        if verify_result.get("status") is True:
            print("[OK] 验证通过：首页 HTML 内容已存在，网站生成成功！")
        else:
            print("[WARN] 验证未通过：首页 HTML 内容不存在，网站可能未正确生成。")
            print("[INFO] 建议：请尝试重新执行 generate 命令，或检查后端服务是否正常。")
            state["generate_result"] = "verify_failed"
            state["generate_error"] = verify_result.get("message", "首页HTML内容不存在")
            save_state(state)
            return

        print("\n网站已成功生成到站点！")
        # 生成成功后自动获取临时分享链接
        share_result = call_generate_share_url()
        if share_result and share_result.get("code") == 0 and share_result.get("data"):
            share_url = share_result.get("data", {}).get("share_url", "")
            if share_url:
                print("\n[OK] 临时分享链接（有效期 2 小时）：")
                print(f"   {share_url}")
                print("")
        # [LOCK] 不自动发布，输出结构化确认请求让 AI 询问用户
        print(json.dumps({
            "need_publish_confirm": True,
            "stage": "post_generate",
            "message": "网站生成成功！是否需要发布到线上？[WARN] 发布网站将覆盖线上版本，此操作无法撤销还原！",
            "options": ["确认发布", "暂不发布"],
            "tip": "回复「确认发布」发布到线上，回复「暂不发布」保留当前状态"
        }, ensure_ascii=False))
        # 保留状态文件以便重试，10 分钟后自动过期
        state["generated_at"] = datetime.now().isoformat()
        state["generate_result"] = "success"
        save_state(state)
    else:
        err_msg = result.get("msg", "未知错误")
        # 判断是否为「参数缺失」错误（A iEditor 初始化不完整）
        if "参数缺失" in err_msg or "无法创建页面" in err_msg:
            print(f"\n生成失败：「{err_msg}」")
            # [WARN] 不清空数据，保留已收集的问题答案
            # 仅回退到 generate 阶段（初始化确认 + 生成），不回到 ask-init 阶段
            state["generate_confirmed"] = "pending"
            save_state(state)
            print(json.dumps({
                "need_reinit": True,
                "stage": "generate",
                "reason": f"generateWebsite 返回「{err_msg}」，网站未正确初始化。",
                "message": (
                    "网站生成失败，需要重新进行初始化。\n"
                    "已收集的问题答案已保留，将返回到【生成网站前】的确认步骤重新进行。\n"
                    "请回复「确认」重新初始化站点并生成网站。\n"
                    "回复「取消」终止操作（可执行 reset 重新收集信息）。"
                ),
                "options": ["确认", "取消"],
                "tip": "回复「确认」继续，回复「取消」终止（数据已保留，可随时重新 generate）",
            }, ensure_ascii=False))
        else:
            print(f"\n生成失败: {err_msg}")
            print("[INFO] 可重新执行 generate 命令重试")
            # 保留状态文件以便重试
            state["generate_result"] = "failed"
            state["generate_error"] = err_msg
            save_state(state)


# ═══════════════════════════════════════════════════════════════════════════════
# API 调用
# ═══════════════════════════════════════════════════════════════════════════════

def check_site_languages():
    headers = {"Authorization": API_KEY, "Content-Type": "application/json",
               "User-Agent": "nicebox-openclaw-skill/1.0"}
    try:
        req = urllib.request.Request(ENDPOINT_LANGUAGE_LIST, data=b"{}",
                                      headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 0:
                return result.get("data", {}).get("list", [])
    except Exception:
        pass
    return []


def initialize_site():
    headers = {"Authorization": API_KEY, "Content-Type": "application/json",
               "User-Agent": "nicebox-openclaw-skill/1.0"}
    try:
        req = urllib.request.Request(
            ENDPOINT_INITIALIZE,
            data=json.dumps({}, ensure_ascii=False).encode("utf-8"),
            headers=headers, method="POST")
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
    info = sanitize_company_info(collected)
    headers = {"Authorization": API_KEY, "Content-Type": "application/json",
               "User-Agent": "nicebox-openclaw-skill/1.0"}
    try:
        req = urllib.request.Request(
            ENDPOINT_GET_COMPANY_INFO,
            data=json.dumps(info, ensure_ascii=False).encode("utf-8"),
            headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"code": 1, "msg": f"HTTP {e.code}"}
    except Exception as e:
        return {"code": 1, "msg": str(e)}


def call_generate_share_url():
    """获取临时分享链接"""
    headers = {"Authorization": API_KEY, "Content-Type": "application/json",
               "User-Agent": "nicebox-openclaw-skill/1.0"}
    try:
        req = urllib.request.Request(ENDPOINT_GENERATE_SHARE_URL,
                                     headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"code": 1, "msg": f"HTTP {e.code}"}
    except Exception as e:
        return {"code": 1, "msg": str(e)}


def call_read_index_html():
    """
    通过 /site_pages/readIndexHtml 验证网站是否真正生成成功。
    返回 {"status": True/False, "message": "..."}
    """
    headers = {"Authorization": API_KEY, "Content-Type": "application/json",
               "User-Agent": "nicebox-openclaw-skill/1.0"}
    try:
        req = urllib.request.Request(ENDPOINT_READ_INDEX_HTML,
                                     headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 0 and result.get("data", {}).get("status") is True:
                return {"status": True, "message": result.get("msg", "首页HTML内容存在")}
            else:
                return {"status": False, "message": result.get("msg", "首页HTML内容不存在")}
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
            return {"status": False, "message": err_body.get("msg", f"HTTP {e.code}")}
        except Exception:
            return {"status": False, "message": f"HTTP {e.code}"}
    except Exception as e:
        return {"status": False, "message": str(e)}


def call_generate_website(requirement):
    """
    SSE 流式生成网站。
    返回：{"code": 0, "html_len": N, "issues": [...], "timed_out": bool}
          或 {"code": 非0, "msg": "..."}
    """
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "User-Agent": "nicebox-openclaw-skill/1.0",
    }

    # 初始化 html_content 避免 UnboundLocalError
    html_content = ""

    try:
        req = urllib.request.Request(
            ENDPOINT_GENERATE_WEBSITE,
            data=json.dumps({"requirement": requirement}, ensure_ascii=False).encode("utf-8"),
            headers=headers, method="POST")

        html_chunks = []
        buffer = ""
        section_index = 0
        section_names = ["Header", "Hero", "Services", "About", "Team",
                         "Contact", "Footer", "Products", "News", "FAQ"]
        last_display_chars = 0
        last_progress = ""

        # 移除 emoji，使用纯文字输出避免 Windows GBK 编码问题
        print("\n[1/4] 网站生成中（SSE 流式）...")

        with urllib.request.urlopen(req) as resp:
                while True:
                    chunk = resp.read(4096)
                    if not chunk:
                        break
                    buffer += chunk.decode("utf-8", errors="replace")
                    lines = buffer.split("\n")
                    buffer = lines.pop()

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
                            if "<!DOCTYPE" in data_str or "<html" in data_str:
                                html_content += data_str
                            continue

                        etype = event.get("type", "")
                        emsg = event.get("content") or event.get("message", "")

                        if etype == "progress":
                            pct = event.get("percentage")
                            msg = event.get("message", "")
                            if pct is not None:
                                last_progress = f"{pct}%"
                            elif msg:
                                last_progress = msg
                            if html_content and (len(html_content) - last_display_chars) >= 5000:
                                sys.stdout.write(f"\r[RECV] 已接收 {len(html_content)} 字符 {last_progress}    ")
                                sys.stdout.flush()
                                last_display_chars = len(html_content)

                        elif etype == "section_generating":
                            section_index += 1
                            sec = event.get("section")
                            sec_name = sec if sec else (
                                section_names[section_index - 1]
                                if section_index <= len(section_names)
                                else f"区块{section_index}"
                            )
                            print(f"\n[GEN] 正在生成: {sec_name}（{section_index}）")

                        elif etype == "progressive_content":
                            content = event.get("content", "")
                            if content:
                                html_chunks.append(content)
                                html_content = ''.join(html_chunks)
                                if html_content and (len(html_content) - last_display_chars) >= 5000:
                                    sys.stdout.write(f"\r[RECV] 已接收 {len(html_content)} 字符     ")
                                    sys.stdout.flush()
                                    last_display_chars = len(html_content)

                        elif etype == "section_complete":
                            sec = event.get("section")
                            sec_name = sec if sec else (
                                section_names[section_index - 1]
                                if section_index > 0 else "区块"
                            )
                            print(f"  [{sec_name}] done")

                        elif etype == "complete":
                            print('[OK] Website generation complete!')

                        elif etype == "error":
                            print(f"\n[ERROR] SSE 错误: {emsg}")

    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8", errors="replace")
            # SSE 格式：取第一个完整的 JSON 行
            for line in raw.split("\n"):
                line = line.strip()
                if line.startswith("data:"):
                    try:
                        ev = json.loads(line[5:].strip())
                        if ev.get("type") == "error":
                            return {"code": e.code, "msg": ev.get("content", "") or ev.get("message", "")}
                    except json.JSONDecodeError:
                        pass
            # 尝试整体 JSON
            data = json.loads(raw)
            return {"code": data.get("code", e.code), "msg": data.get("message") or data.get("msg", f"HTTP {e.code}")}
        except Exception:
            return {"code": e.code, "msg": f"HTTP {e.code}"}
    except Exception as e:
        return {"code": 1, "msg": str(e)}

    if html_chunks:
        html_content = "".join(html_chunks)
    if buffer.strip():
        try:
            ev = json.loads(buffer.strip())
            if ev.get("type") == "progressive_content":
                c = ev.get("content", "")
                if c:
                    html_content += c
        except json.JSONDecodeError:
            if "<!DOCTYPE" in buffer or "<html" in buffer:
                html_content += buffer

    # 移除网站内容验证，直接认为生成成功
    if html_content:
        print(f'\n[DONE] 网站生成完成，接收 {len(html_content)} 字符')
        return {"code": 0, "html_len": len(html_content), "timed_out": False}

    return {"code": 1, "msg": "No HTML content received"}


# ═══════════════════════════════════════════════════════════════════════════════
# 追问：从已回答中提取子字段
# ═══════════════════════════════════════════════════════════════════════════════

def build_followup_question(parent_field, sub_field):
    """根据父字段的回答构建追问问题。"""
    prompts = {
        "email": {
            "question": "请提供您的联系邮箱？",
            "placeholder": "例如：contact@example.com",
        },
        "address": {
            "question": "请提供您的公司地址？",
            "placeholder": "例如：北京市朝阳区建国门外大街1号国贸大厦B座15层",
        },
    }
    return prompts.get(sub_field, {"question": f"请提供{FIELD_LABELS.get(sub_field, sub_field)}？",
                                     "placeholder": ""})


def auto_extract_from_parent(parent_field, sub_field, parent_answer):
    """
    尝试从父字段的回答中自动提取子字段信息。
    返回提取到的内容，或 None（无法提取，需要追问）。
    """
    if sub_field == "email":
        # 从 parent_answer 中提取邮箱
        phones, emails = [], []
        # 简单邮箱提取
        found = re.findall(r"[\w.\-]+@[\w.\-]+\.\w+", parent_answer)
        if found:
            return found[0]
    elif sub_field == "address":
        # 地址特征词
        match = re.search(
            r"[\u4e00-\u9fa5]{2,}[\u4e00-\u9fa5\s\d\-省市区县镇路街号楼单元层座]",
            parent_answer
        )
        if match:
            return match.group().strip()
    # 其他字段暂不自动提取
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# CLI 模式
# ═══════════════════════════════════════════════════════════════════════════════

def mode_status():
    """查看当前进度。"""
    state = load_state()
    current = state.get("current_index", 0)
    collected = state.get("collected", {})
    pending = state.get("pending_followups", [])
    answered = [v for v in collected.values() if v and v != "未填写"]

    result = {
        "status": "in_progress" if current < len(QUESTIONS) or pending else "ready_to_generate",
        "total_questions": len(QUESTIONS),
        "answered_count": len(answered),
        "pending_followups": pending,
        "current_question_index": current,
        "next_question": (
            {"field": pending[0], **build_followup_question(None, pending[0])}
            if pending else (
                QUESTIONS[current] if current < len(QUESTIONS) else None
            )
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def mode_questions():
    """列出全部 7 个问题。"""
    out = [{
        "index": i,
        "field": q["field"],
        "label": FIELD_LABELS.get(q["field"], q["field"]),
        "question": q["question"],
        "placeholder": q.get("placeholder", ""),
        "required": q.get("required", False),
        "followups": q.get("followups", []),
    } for i, q in enumerate(QUESTIONS)]
    print(json.dumps(out, ensure_ascii=False, indent=2))


def mode_next():
    """打印下一个要问的问题（含追问）。
    
    [WARN] 重要：此函数输出问题后，AI 必须停下来等待用户回复！
    """
    state = load_state()
    pending = state.get("pending_followups", [])
    current = state.get("current_index", 0)
    collected = state.get("collected", {})

    if pending:
        sub = pending[0]
        prompt = build_followup_question(None, sub)
        print(json.dumps({
            "done": False,
            "type": "followup",
            "field": sub,
            "label": FIELD_LABELS.get(sub, sub),
            "question": prompt["question"],
            "placeholder": prompt.get("placeholder", ""),
            "tip": "回复「跳过」跳过此项",
            "_ai_instruction": "【AI 注意】请将此问题展示给用户，然后停下来等待用户回复。不要自动生成答案！",
        }, ensure_ascii=False, indent=2))
        return

    if current >= len(QUESTIONS):
        print(json.dumps({
            "done": True, 
            "message": "所有问题已收集完毕，请确认汇总后生成网站",
            "_ai_instruction": "【AI 注意】请将此信息展示给用户，然后停下来等待用户确认。不要自动执行 generate 命令！",
        }, ensure_ascii=False, indent=2))
        return

    q = QUESTIONS[current]
    
    # 使用智能提示生成问题
    smart_q = build_smart_question(q, collected)
    
    print(json.dumps({
        "done": False,
        "type": "main",
        "index": current,
        "field": q["field"],
        "label": FIELD_LABELS.get(q["field"], q["field"]),
        "question": smart_q["question"],
        "placeholder": smart_q["placeholder"],
        "required": q.get("required", False),
        "followups": q.get("followups", []),
        "tip": "回复「跳过」跳过此题（记为未填写），回复「完成」提前结束",
        "_ai_instruction": "【AI 注意】请将此问题展示给用户，然后停下来等待用户回复。不要自动生成答案！",
    }, ensure_ascii=False, indent=2))


def mode_answer(args):
    """记录用户回答，支持追问流程。"""
    raw = args.answer.strip()

    # 特殊命令
    if raw == "跳过":
        answer = "未填写"
    elif raw == "完成":
        state = load_state()
        state["finished_early"] = True
        save_state(state)
        print_summary(state.get("collected", {}))
        return
    else:
        answer = raw if raw else "未填写"

    state = load_state()
    pending = state.get("pending_followups", [])

    # ── 追问模式：处理子字段回答 ──
    if pending:
        sub_field = pending[0]
        if raw == "跳过":
            state["pending_followups"] = pending[1:]
            save_state(state)
            if state["pending_followups"]:
                next_sub = state["pending_followups"][0]
                prompt = build_followup_question(None, next_sub)
                print(json.dumps({
                    "type": "followup",
                    "field": next_sub,
                    "label": FIELD_LABELS.get(next_sub, next_sub),
                    "question": prompt["question"],
                    "placeholder": prompt.get("placeholder", ""),
                    "hint": "可回复「跳过」跳过此项",
                }, ensure_ascii=False))
            else:
                advance(state)
            return
        
        state["collected"][sub_field] = answer
        state["pending_followups"] = pending[1:]
        save_state(state)
        
        if state["pending_followups"]:
            next_sub = state["pending_followups"][0]
            prompt = build_followup_question(None, next_sub)
            print(json.dumps({
                "type": "followup",
                "field": next_sub,
                "label": FIELD_LABELS.get(next_sub, next_sub),
                "question": prompt["question"],
                "placeholder": prompt.get("placeholder", ""),
                "hint": "可回复「跳过」跳过此项",
            }, ensure_ascii=False))
        else:
            advance(state)
        return

    # ── 主问题模式 ──
    if raw == "跳过":
        state = load_state()
        if state.get("current_index", 0) < len(QUESTIONS):
            state["collected"][QUESTIONS[state["current_index"]]["field"]] = "未填写"
            state["current_index"] += 1
            save_state(state)
        advance(state)
        return

    if raw == "完成":
        state = load_state()
        state["finished_early"] = True
        save_state(state)
        print_summary(state.get("collected", {}))
        return

    state = load_state()
    current = state.get("current_index", 0)
    if current >= len(QUESTIONS) or state.get("finished_early"):
        print(json.dumps({"error": "所有问题已收集完毕"}))
        return

    q = QUESTIONS[current]
    field = q["field"]
    followups = q.get("followups", [])

    # 联系方式字段：智能解析
    if field == "phone":
        phone_val, email_val, address_val = parse_contact(answer)
        state["collected"]["phone"] = phone_val if phone_val else answer
        # 自动提取 email/address 并加入追问
        new_followups = []
        if email_val:
            state["collected"]["email"] = email_val
        else:
            new_followups.append("email")
        if address_val:
            state["collected"]["address"] = address_val
        else:
            new_followups.append("address")

        state["pending_followups"] = new_followups
        state["current_index"] = current + 1
        save_state(state)

        if new_followups:
            next_sub = new_followups[0]
            prompt = build_followup_question(field, next_sub)
            print(json.dumps({
                "collected": {
                    "phone": state["collected"].get("phone", ""),
                    "email": state["collected"].get("email", ""),
                    "address": state["collected"].get("address", ""),
                },
                "type": "followup",
                "field": next_sub,
                "label": FIELD_LABELS.get(next_sub, next_sub),
                "question": prompt["question"],
                "placeholder": prompt.get("placeholder", ""),
                "hint": "可回复「跳过」跳过此项",
            }, ensure_ascii=False))
        else:
            state["collected"]["phone"] = raw
            print(json.dumps({
                "collected": {
                    "phone": state["collected"].get("phone", ""),
                    "email": None,
                    "address": None,
                },
                "next": None,
                "all_contact_collected": True,
            }, ensure_ascii=False))
            advance(state)

    # 其他普通字段
    else:
        state["collected"][field] = answer
        state["current_index"] += 1
        save_state(state)
        advance(state)


def _advance_to_next(state, next_index):
    """推进到下一个问题，处理追问队列和提前结束。"""
    pending = state.get("pending_followups", [])

    if pending:
        next_sub = pending[0]
        prompt = build_followup_question(None, next_sub)
        print(json.dumps({
            "action": "next",
            "all_done": False,
            "next_type": "followup",
            "next_field": next_sub,
            "next_label": FIELD_LABELS.get(next_sub, next_sub),
            "next_question": prompt["question"],
            "next_placeholder": prompt.get("placeholder", ""),
        }, ensure_ascii=False, indent=2))
        return

    if next_index >= len(QUESTIONS) or state.get("finished_early"):
        answered = len([v for v in state["collected"].values()
                       if v and v != "未填写"])
        skipped = len([v for v in state["collected"].values()
                       if v == "未填写"])
        print(json.dumps({
            "action": "all_done",
            "answered_count": answered,
            "skipped_count": skipped,
            "message": f"所有问题收集完毕！共 {answered} 项已填，{skipped} 项跳过。请生成网站。",
        }, ensure_ascii=False, indent=2))
    else:
        q = QUESTIONS[next_index]
        print(json.dumps({
            "action": "next",
            "all_done": False,
            "next_type": "main",
            "next_index": next_index,
            "next_field": q["field"],
            "next_label": FIELD_LABELS.get(q["field"], q["field"]),
            "next_question": q["question"],
            "next_placeholder": q.get("placeholder", ""),
            "required": q.get("required", False),
            "followups": q.get("followups", []),
            "tip": "回复「跳过」跳过此题，回复「完成」提前结束",
        }, ensure_ascii=False, indent=2))


def mode_summary():
    """显示汇总（生成前确认）。"""
    state = load_state()
    collected = state.get("collected", {})
    info = sanitize_company_info(collected)

    lines = ["=" * 50, "[SUMMARY] 网站需求汇总", "=" * 50, ""]
    for q in QUESTIONS:
        f = q["field"]
        v = info.get(f, "未填写")
        tag = " [REQ]必填" if f in REQUIRED_API_FIELDS else ""
        lines.append(f"  {FIELD_LABELS.get(f, f)}：{v}{tag}")
    # 追问字段也显示
    for f in ["email", "address"]:
        if f in collected and collected[f] and collected[f] != "未填写":
            lines.append(f"  {FIELD_LABELS.get(f, f)}：{collected[f]}")

    lines += ["", "=" * 50]
    print("\n".join(lines))

    answered = len([v for v in info.values() if v != "未填写"])
    skipped = len([v for v in info.values() if v == "未填写"])
    print(json.dumps({
        "answered_count": answered,
        "skipped_count": skipped,
        "collected": info,
        "_ai_instruction": "【AI 注意】请将此汇总展示给用户，然后停下来等待用户确认是否生成。不要自动执行 generate 命令！",
    }, ensure_ascii=False, indent=2))

    # 标记等待确认状态
    state["summary_confirmed"] = "pending"
    save_state(state)
    # 然后输出确认选项
    print(json.dumps({
        "need_summary_confirm": True,
        "stage": "summary",
        "message": "以上是您填写的信息汇总，请确认是否需要补充？",
        "options": ["补充信息", "确认无误，生成网站"],
        "tip": "回复「补充信息」继续填写或修改，回复「确认无误，生成网站」直接进入生成流程",
        "_ai_instruction": "【AI 注意】请将此确认选项展示给用户，然后停下来等待用户回复。不要自动回复！",
    }, ensure_ascii=False))


def mode_supplement():
    """补充信息命令 - 用户选择补充信息，回到问题继续收集"""
    state = load_state()
    is_done = state.get("current_index", 0) >= len(QUESTIONS) or state.get("finished_early")
    if is_done:
        # 已完成所有问题，回到第一题重新填写
        state["current_index"] = 0
        state["finished_early"] = False
    save_state(state)
    print("好的，请继续补充信息：")
    if state.get("current_index", 0) < len(QUESTIONS):
        q = QUESTIONS[state.get("current_index", 0)]
        print(json.dumps({
            "index": state.get("current_index", 0),
            "total": len(QUESTIONS),
            "field": q["field"],
            "label": FIELD_LABELS.get(q["field"], q["field"]),
            "question": q["question"],
            "placeholder": q.get("placeholder", ""),
            "required": q.get("required", False),
            "hint": "可回复「跳过」跳过此题，回复「完成」提前结束所有问答",
        }, ensure_ascii=False))


def mode_init_confirm(args):
    """处理用户对初始化确认的回复。"""
    raw = args.answer.strip()
    state = load_state()

    if raw in ("确认", "是", "确认初始化", "确认"):
        state["init_confirmed"] = True
        save_state(state)
        result = initialize_site()
        if result.get("code") == 0:
            state["initialized"] = True
            save_state(state)
            print(json.dumps({"action": "init_ok", "message": "[OK] 确认初始化完成，正在生成网站..."}))
            do_generate(state)
        else:
            print(json.dumps({"action": "init_failed",
                              "message": f"[ERROR] 初始化失败：{result.get('msg', '')}，无法生成网站"}))
        return

    if raw in ("取消", "取消操作", "否", "不生成"):
        state["init_confirmed"] = False
        save_state(state)
        print(json.dumps({
            "action": "cancelled",
            "message": "已取消操作，不生成网站。如需重新生成，请先重置状态。",
        }, ensure_ascii=False))
        return

    # 其他回复：重新询问
    print(json.dumps({
        "action": "confirm_again",
        "message": (
            "请明确回复「确认」继续初始化并生成网站\n"
            "或回复「取消」取消操作"
        ),
        "options": ["确认", "取消"],
    }, ensure_ascii=False))


# ═══════════════════════════════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════════════════════════════

def mode_ask_init():
    """第1次确认，收集问题前"""
    state = load_state()
    
    # 已取消
    if state.get("init_confirmed") is False:
        print("您之前已取消操作，请先 reset 后重新开始。")
        return
    
    # 已确认且已初始化 → 直接显示下一题
    if state.get("init_confirmed") is True and state.get("initialized"):
        print("已确认并初始化完成，请直接回答以下问题：")
        next_q = QUESTIONS[state.get("current_index", 0)] if state.get("current_index", 0) < len(QUESTIONS) else None
        if next_q:
            print(json.dumps({
                "index": state.get("current_index", 0),
                "total": len(QUESTIONS),
                "field": next_q["field"],
                "label": FIELD_LABELS.get(next_q["field"], next_q["field"]),
                "question": next_q["question"],
                "placeholder": next_q.get("placeholder", ""),
                "required": next_q.get("required", False),
                "hint": "可回复「跳过」跳过此题，回复「完成」提前结束所有问答",
            }, ensure_ascii=False))
        return
    
    # 等待回复中 → 再次弹出提示
    if state.get("init_confirmed") == "pending":
        output_confirm_prompt("ask-init")
        return
    
    # 首次检查
    languages = check_site_languages()
    if languages:
        # 有数据 → 弹出确认
        state["init_confirmed"] = "pending"
        save_state(state)
        output_confirm_prompt("ask-init")
    else:
        # 无数据 → 自动初始化，直接进入收集问题
        state["init_confirmed"] = True
        print("站点为空，无需初始化数据...")
        do_initialize(state, "自动初始化")
        print("请直接回答以下问题：")
        next_q = QUESTIONS[state.get("current_index", 0)] if state.get("current_index", 0) < len(QUESTIONS) else None
        if next_q:
            print(json.dumps({
                "index": state.get("current_index", 0),
                "total": len(QUESTIONS),
                "field": next_q["field"],
                "label": FIELD_LABELS.get(next_q["field"], next_q["field"]),
                "question": next_q["question"],
                "placeholder": next_q.get("placeholder", ""),
                "required": next_q.get("required", False),
                "hint": "可回复「跳过」跳过此题，回复「完成」提前结束所有问答",
            }, ensure_ascii=False))


def mode_confirm(args):
    """统一确认命令，两个阶段共用"""
    raw = args.answer.strip()
    state = load_state()

    # ── summary 阶段的确认 ──────────────────────────────────────────────────
    if state.get("summary_confirmed") == "pending":
        if raw == "补充信息":
            # 用户选择补充信息，回到问题继续收集
            state["summary_confirmed"] = None
            is_done = state.get("current_index", 0) >= len(QUESTIONS) or state.get("finished_early")
            if is_done:
                # 已完成所有问题，回到第一题重新填写
                state["current_index"] = 0
                state["finished_early"] = False
            save_state(state)
            print("好的，请继续补充信息：")
            if state.get("current_index", 0) < len(QUESTIONS):
                q = QUESTIONS[state.get("current_index", 0)]
                print(json.dumps({
                    "index": state.get("current_index", 0),
                    "total": len(QUESTIONS),
                    "field": q["field"],
                    "label": FIELD_LABELS.get(q["field"], q["field"]),
                    "question": q["question"],
                    "placeholder": q.get("placeholder", ""),
                    "required": q.get("required", False),
                    "hint": "可回复「跳过」跳过此题，回复「完成」提前结束所有问答",
                }, ensure_ascii=False))
        elif raw in ("确认无误，生成网站", "确认生成", "生成"):
            # 用户确认无误，进入生成流程
            state["summary_confirmed"] = True
            save_state(state)
            print("\n信息已确认，正在进入生成流程...")
            print("请输入：python generate_website.py generate")
        else:
            # 重新显示 summary 确认选项
            print(json.dumps({
                "need_summary_confirm": True,
                "stage": "summary",
                "message": "请选择：补充信息 or 生成网站？",
                "options": ["补充信息", "确认无误，生成网站"],
                "tip": "回复「补充信息」继续填写，回复「确认无误，生成网站」进入生成",
            }, ensure_ascii=False))
        return

    # 第1次确认待回复（ask-init 阶段）
    if state.get("init_confirmed") == "pending":
        if raw == "确认":
            state["init_confirmed"] = True
            save_state(state)
            do_initialize(state, "收到确认")
            # 显示下一题
            answered = len([v for v in state.get("collected", {}).values() if v and v != "未填写"])
            print(f"\n当前进度：已回答 {answered}/{len(QUESTIONS)} 题")
            if state.get("current_index", 0) < len(QUESTIONS):
                q = QUESTIONS[state.get("current_index", 0)]
                print(json.dumps({
                    "index": state.get("current_index", 0),
                    "total": len(QUESTIONS),
                    "field": q["field"],
                    "label": FIELD_LABELS.get(q["field"], q["field"]),
                    "question": q["question"],
                    "placeholder": q.get("placeholder", ""),
                    "required": q.get("required", False),
                    "hint": "可回复「跳过」跳过此题，回复「完成」提前结束所有问答",
                }, ensure_ascii=False))
            else:
                print("所有问题已收集完毕，请输入：python generate_website.py generate")
        elif raw == "取消":
            state["init_confirmed"] = False
            save_state(state)
            print("已取消，后续操作已终止。\n如需重新开始，请输入：python generate_website.py reset")
        else:
            output_confirm_prompt("ask-init")
        return

    # 第2次确认待回复（generate 阶段）
    if state.get("generate_confirmed") == "pending":
        if raw == "确认":
            state["generate_confirmed"] = True
            save_state(state)
            # 确认后初始化并生成
            if not state.get("initialized"):
                do_initialize(state, "收到确认")
            do_generate(state)
        elif raw == "取消":
            state["generate_confirmed"] = False
            save_state(state)
            print("已取消，后续操作已终止。\n如需重新开始，请输入：python generate_website.py reset")
        else:
            output_confirm_prompt("generate")
        return

    # 没有待确认的
    print("当前没有待确认的操作。")


def mode_generate(args):
    """第2次确认，生成网站前"""
    state = load_state()

    # 检查是否已完成信息汇总确认
    if not state.get("summary_confirmed") and state.get("current_index", 0) >= len(QUESTIONS):
        # 用户还没做 summary 确认，引导先做 summary
        mode_summary()
        print(json.dumps({
            "need_summary_confirm": True,
            "stage": "summary",
            "message": "请先确认信息汇总后再生成网站。是否需要补充信息？",
            "options": ["补充信息", "确认无误，生成网站"],
            "tip": "回复「补充信息」继续填写，回复「确认无误，生成网站」进入生成"
        }, ensure_ascii=False))
        return

    # 任一阶段已取消
    if state.get("init_confirmed") is False or state.get("generate_confirmed") is False:
        print("操作已取消，无法生成网站。如需重新开始，请先 reset。")
        return
    
    # 第1次确认还在等待
    if state.get("init_confirmed") == "pending":
        print("请先完成初始化确认（ask-init 阶段）。")
        output_confirm_prompt("ask-init")
        return
    
    # 第2次确认等待回复中
    if state.get("generate_confirmed") == "pending":
        output_confirm_prompt("generate")
        return
    
    # 第2次已确认 → 直接生成
    if state.get("generate_confirmed") is True:
        if not state.get("initialized"):
            do_initialize(state, "正在初始化站点")
        do_generate(state)
        return
    
    # ── 首次进入 generate，检查站点数据（第2次确认） ──
    languages = check_site_languages()
    if languages:
        # 有数据 → 弹出第2次确认
        state["generate_confirmed"] = "pending"
        save_state(state)
        output_confirm_prompt("generate")
    else:
        # 无数据 → 直接生成
        state["generate_confirmed"] = True
        save_state(state)
        if not state.get("initialized"):
            do_initialize(state, "站点为空，自动初始化")
        do_generate(state)


def mode_direct_generate(args):
    """直接生成模式：绕过交互流程，直接调用 API 生成网站。
    适用于：Python 进程 SIGKILL、脚本挂起、需要快速重试的场景。
    
    步骤：
    1. 读取状态文件中的已收集信息
    2. 直接调用 initializeData 初始化站点
    3. 直接调用 generateWebsite 生成网站（SSE 流）
    4. 验证生成结果
    5. 获取分享链接
    """
    state = load_state()
    collected = state.get("collected", {})
    
    if not collected.get("company_name") or collected.get("company_name") == "未填写":
        print(json.dumps({"error": "缺少公司名称，请先完成问答流程"}, ensure_ascii=False))
        return
    
    info = sanitize_company_info(collected)
    
    # Step 1: 初始化站点
    print("Step 1: 初始化站点...")
    init_result = initialize_site()
    print(f"初始化结果: code={init_result.get('code')}")
    
    if init_result.get("code") != 0:
        print(f"初始化失败: {init_result.get('msg')}")
        return
    
    time_module.sleep(1)  # 等待初始化完成
    
    # Step 2: 构建需求字符串
    print("Step 2: 构建需求字符串...")
    requirement_parts = []
    for key, label in FIELD_LABELS.items():
        value = info.get(key, "未填写")
        if value and value != "未填写":
            requirement_parts.append(f"{label}：{value}")
    requirement = "\n".join(requirement_parts)
    
    # Step 3: 直接调用 generateWebsite API
    print(f"Step 3: 正在生成网站（SSE 流式）...")
    result = call_generate_website(requirement)
    
    if result.get("code") != 0:
        print(f"生成失败: {result.get('msg')}")
        return
    
    # Step 4: 验证生成结果
    print("Step 4: 验证生成结果...")
    verify_result = call_read_index_html()
    if verify_result.get("status") is True:
        print(f"[OK] 验证通过：{verify_result.get('message')}")
    else:
        print(f"[WARN] 验证失败：{verify_result.get('message')}")
        return
    
    # Step 5: 获取分享链接
    print("Step 5: 获取分享链接...")
    share_result = call_generate_share_url()
    if share_result and share_result.get("code") == 0:
        share_url = share_result.get("data", {}).get("share_url", "")
        print(f"分享链接: {share_url}")
    
    print("\n[DONE] 网站生成完成！")
    print(json.dumps({
        "need_publish_confirm": True,
        "stage": "direct_generate",
        "message": "网站生成成功！是否需要发布到线上？",
        "options": ["确认发布", "暂不发布"]
    }, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(
        description="生成网站 - 交互式多轮对话（Python 版 · 双重确认机制）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
推荐工作流程：
  1. ask-init          ← 【必须第一步】检查站点数据（第1次确认）
  2. answer "内容"     ← 逐题收集信息（可随时「跳过」或「完成」）
  3. summary           ← 查看信息汇总，确认是否需要补充
  4. confirm "补充信息"        ← 如需补充，继续填写
  5. confirm "确认无误，生成网站" ← 确认后进入生成流程
  6. generate          ← 生成网站（第2次确认，如需重新确认）

双重确认说明：
  ask-init 和 generate 都会检查站点数据
  如果站点有数据，两次都会弹出相同的确认提示
  确认 → 初始化站点并继续  |  取消 → 终止所有操作

[FAST] 快速生成模式（绕过交互）：
  python generate_website.py direct-generate  ← 直接使用已收集的信息生成网站

命令列表：
  python generate_website.py reset              # 重置对话状态
  python generate_website.py status             # 查看当前进度
  python generate_website.py ask-init           # 【第1步】检查站点（第1次确认）
  python generate_website.py confirm "确认"     # 确认（两个阶段通用）
  python generate_website.py confirm "取消"     # 取消（两个阶段通用）
  python generate_website.py questions          # 列出全部 8 个问题
  python generate_website.py next               # 打印下一题
  python generate_website.py answer "内容"      # 记录回答
  python generate_website.py summary            # 显示需求汇总
  python generate_website.py generate           # 【第4步】生成网站（第2次确认）
  python generate_website.py direct-generate   # 【快速】直接生成，绕过交互
        """,
    )
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("status", help="查看进度")
    sub.add_parser("questions", help="列出所有问题")
    sub.add_parser("next", help="打印下一个问题")
    
    answer_parser = sub.add_parser("answer", help="记录回答")
    answer_parser.add_argument("answer", help="用户回复内容")
    
    confirm_parser = sub.add_parser("confirm", help="确认（两个阶段通用）")
    confirm_parser.add_argument("answer", help="确认回复（确认/取消）")
    
    sub.add_parser("ask-init", help="【第1步】检查站点（第1次确认）")
    sub.add_parser("summary", help="显示汇总")
    sub.add_parser("supplement", help="补充信息")
    sub.add_parser("generate", help="【第4步】生成网站（第2次确认）")
    sub.add_parser("direct-generate", help="【快速】直接生成，绕过交互流程")
    sub.add_parser("reset", help="重置状态")

    args = parser.parse_args()

    if not API_KEY:
        print(json.dumps({"error": "AIBOX_API_KEY not set"}))
        sys.exit(2)

    if args.cmd == "status":
        mode_status()
    elif args.cmd == "questions":
        mode_questions()
    elif args.cmd == "next":
        mode_next()
    elif args.cmd == "answer":
        mode_answer(args)
    elif args.cmd == "confirm":
        mode_confirm(args)
    elif args.cmd == "ask-init":
        mode_ask_init()
    elif args.cmd == "summary":
        mode_summary()
    elif args.cmd == "supplement":
        mode_supplement()
    elif args.cmd == "generate":
        mode_generate(args)
    elif args.cmd == "direct-generate":
        mode_direct_generate(args)
    elif args.cmd == "reset":
        reset_state()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
