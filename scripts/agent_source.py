# -*- coding: utf-8 -*-
"""Build sanitized OpenClaw Agent source headers for every REST fallback request."""

import json
import os
import re


CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
SKILL_VERSION = '0.3.30'


def _config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as handle:
            value = json.load(handle)
            return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _plain(value, limit):
    value = re.sub(r'[\x00-\x1f\x7f]', '', str(value or '')).strip()
    return value[:limit]


def _agent_code(value):
    slug = re.sub(r'[^a-z0-9]+', '_', _plain(value, 100).lower()).strip('_')[:32]
    if not slug:
        return 'unknown'
    if 'workbuddy' in slug or 'work_buddy' in slug:
        return 'workbuddy'
    if 'codex' in slug:
        return 'codex'
    if 'deepseek' in slug:
        return 'deepseek'
    return slug if re.fullmatch(r'[a-z0-9][a-z0-9_]{0,31}', slug) else 'unknown'


def _version(value):
    value = _plain(value, 32)
    return value if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._+\-]{0,31}', value) else ''


def source_headers(path='', purpose=''):
    config = _config()
    environment_agent = os.environ.get('NICEBOX_AGENT', '')
    configured_agent = environment_agent or config.get('agent_code', '')
    agent_code = _agent_code(configured_agent)
    distribution = _plain(
        os.environ.get('NICEBOX_DISTRIBUTION') or config.get('distribution_channel') or 'git',
        32,
    )
    request_purpose = purpose or ('connection_sync' if path.rstrip('/').endswith('/site/status') else 'business_call')
    headers = {
        'X-Nicebox-Agent': agent_code,
        'X-Nicebox-Agent-Evidence': 'environment' if environment_agent else ('runtime_config' if configured_agent else 'unknown'),
        'X-Nicebox-Distribution': distribution,
        'X-Nicebox-Skill-Version': _version(config.get('skill_version')) or SKILL_VERSION,
        'X-Nicebox-Request-Purpose': request_purpose,
    }
    raw_name = _plain(os.environ.get('NICEBOX_AGENT_RAW') or config.get('agent_raw_name'), 100)
    agent_version = _version(os.environ.get('NICEBOX_AGENT_VERSION') or config.get('agent_version'))
    if raw_name and raw_name.isascii():
        headers['X-Nicebox-Agent-Raw'] = raw_name
    if agent_version:
        headers['X-Nicebox-Agent-Version'] = agent_version
    return headers
