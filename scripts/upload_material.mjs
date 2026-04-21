#!/usr/bin/env node
/**
 * OpenClaw 素材上传脚本 (Node.js 版本)
 * 功能：上传图片文件到站点资源库，自动判断文件类型
 */

import fs from 'fs';
import path from 'path';
import fetch from 'node-fetch';
import yargs from 'yargs';

// API端点（base_url 已包含 /api/openclaw，此处只写相对路径）
const ENDPOINT_UPLOAD = '/material/upload';

/**
 * 加载配置
 * 从环境变量构造
 */
function loadConfig() {
  // 从环境变量构造
  const baseUrl = process.env.AIBOX_BASE_URL || "https://ai.nicebox.cn/api/openclaw";
  const apiKey = process.env.AIBOX_API_KEY || "";
  
  if (!apiKey) {
    console.error('错误：缺少 API 配置，请设置 AIBOX_API_KEY 环境变量');
    process.exit(1);
  }
  
  return {
    api_url: baseUrl,
    api_key: apiKey
  };
}

/**
 * 自动检测文件类型
 * 返回对应的 source 值
 */
function detectFileType(filePath) {
  const fileName = path.basename(filePath).toLowerCase();
  
  // 检测 logo 文件
  if (fileName.includes('logo')) {
    return 'guide_logo';
  }
  
  // 检测产品图片
  if (fileName.includes('product') || fileName.includes('产品') || fileName.includes('商品')) {
    return 'openclaw_products';
  }
  
  // 检测新闻图片
  if (fileName.includes('news') || fileName.includes('新闻') || fileName.includes('资讯')) {
    return 'openclaw_news';
  }
  
  // 默认类型
  return 'openclaw_other';
}

/**
 * 上传文件到站点资源库
 */
async function uploadFile(filePath, source = null) {
  const config = loadConfig();
  const apiUrl = config.api_url;
  const apiKey = config.api_key;
  
  // 检查文件是否存在
  if (!fs.existsSync(filePath)) {
    console.error(`错误：文件不存在: ${filePath}`);
    return false;
  }
  
  // 检查文件大小
  const fileStats = fs.statSync(filePath);
  const fileSize = fileStats.size;
  if (fileSize > 10 * 1024 * 1024) { // 10MB 限制
    console.error('错误：文件大小超过 10MB 限制');
    return false;
  }
  
  // 自动检测文件类型
  if (source === null) {
    source = detectFileType(filePath);
    console.log(`自动检测文件类型: ${source}`);
  }
  
  // 构建请求URL
  const url = `${apiUrl}${ENDPOINT_UPLOAD}`;
  
  // 准备请求头
  const headers = {
    'Authorization': apiKey
  };
  
  // 准备表单数据
  const formData = new FormData();
  formData.append('source', source);
  
  // 读取文件
  const fileBuffer = fs.readFileSync(filePath);
  const fileName = path.basename(filePath);
  
  // 根据类型选择字段名
  if (source === 'guide_logo') {
    formData.append('logoFile', new Blob([fileBuffer], { type: 'image/' + fileName.split('.').pop() }), fileName);
  } else {
    formData.append('file', new Blob([fileBuffer], { type: 'image/' + fileName.split('.').pop() }), fileName);
  }
  
  console.log(`正在上传文件: ${filePath}`);
  console.log(`目标类型: ${source}`);
  console.log(`请求URL: ${url}`);
  
  try {
    // 发送请求
    const response = await fetch(url, {
      method: 'POST',
      headers: headers,
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    // 解析响应
    const result = await response.json();
    
    if (result.code === 0) {
      console.log('\n上传成功！');
      console.log(`文件ID: ${result.data.fileId}`);
      console.log(`文件URL: ${result.data.filePath}`);
      if (result.data.isOld) {
        console.log('提示：该文件已存在，返回的是已有文件ID');
      }
      return true;
    } else {
      console.log(`\n上传失败: ${result.message}`);
      return false;
    }
    
  } catch (error) {
    console.log(`\n网络错误: ${error.message}`);
    return false;
  }
}

/**
 * 主函数
 */
async function main() {
  const argv = yargs(
    process.argv.slice(2)
  )
  .usage('Usage: $0 <command> [options]')
  .command('upload', '上传文件', (yargs) => {
    yargs
      .positional('file', {
        describe: '要上传的文件路径',
        type: 'string',
        demandOption: true
      })
      .option('source', {
        describe: '文件类型（不指定则自动检测）',
        choices: ['guide_logo', 'openclaw_products', 'openclaw_news']
      });
  })
  .demandCommand(1, '请指定命令')
  .help()
  .argv;

  const { command, file, source } = argv;

  if (command === 'upload') {
    const success = await uploadFile(file, source);
    process.exit(success ? 0 : 1);
  }
}

// 运行主函数
main().catch(error => {
  console.error('错误:', error);
  process.exit(1);
});
