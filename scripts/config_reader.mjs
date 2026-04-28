/**
 * 配置读取模块 - Node.js 版本
 * 统一从配置文件读取 API 密钥和站点信息
 */
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const CONFIG_FILE = join(__dirname, 'config.json');

function loadConfig() {
    try {
        const data = readFileSync(CONFIG_FILE, 'utf-8');
        return JSON.parse(data);
    } catch (e) {
        return {};
    }
}

export function getApiKey(fallback = '') {
    const config = loadConfig();
    if (config && config.api_key) {
        return config.api_key.trim();
    }
    return fallback;
}

export function getBaseUrl() {
    const config = loadConfig();
    if (config && config.base_url) {
        return config.base_url.replace(/\/$/, '');
    }
    return 'https://ai.qidc.cn/api/openclaw';
}

export function getSiteInfo(key, fallback = '') {
    const config = loadConfig();
    if (config && config.site_info && key in config.site_info) {
        return config.site_info[key];
    }
    return fallback;
}

export function getAllSiteInfo() {
    const config = loadConfig();
    if (config && config.site_info) {
        return config.site_info;
    }
    return {};
}

export function getSiteFrom(fallback = '') {
    const config = loadConfig();
    if (config && config.site_from) {
        return config.site_from.trim();
    }
    return fallback;
}

export function checkConfig() {
    const config = loadConfig();
    if (!Object.keys(config).length) {
        console.log('错误：配置文件不存在，请先运行：python config_manager.py --init');
        return false;
    }
    
    if (!config.api_key) {
        console.log('错误：API 密钥未设置，请运行：python config_manager.py --key <密钥>');
        return false;
    }
    
    return true;
}