#!/usr/bin/env node
/**
 * FTP配置管理和网站发布工具 (Node.js版本)
 * 
 * 功能：
 * 1. 获取FTP配置
 * 2. 更新FTP配置
 * 3. 测试FTP连接
 * 4. 发布网站
 * 
 * 使用示例：
 * 1. 获取FTP配置：node ftp_manager.mjs get-config
 * 2. 更新FTP配置：node ftp_manager.mjs update-config --host ftp.example.com --port 21 --username user --password pass --path www
 * 3. 测试FTP连接：node ftp_manager.mjs test-connection
 * 4. 发布网站：node ftp_manager.mjs publish
 */

import fs from 'fs';
import path from 'path';
import fetch from 'node-fetch';
import yargs from 'yargs';

// 配置文件路径
const CONFIG_FILE = path.join(path.dirname(import.meta.url.replace('file:///', '')), 'config.json');

// API端点（base_url 已包含 /api/openclaw，此处只写相对路径）
const ENDPOINT_GET_CONFIG = '/site_publish/getConfig';
const ENDPOINT_UPDATE_CONFIG = '/site_publish/updateFtpConfig';
const ENDPOINT_TEST_CONNECTION = '/site_publish/testFtpConnection';
const ENDPOINT_PUBLISH = '/site_publish/publish';
const ENDPOINT_GET_TASK_STATUS = '/site_publish/getTaskStatus';
const ENDPOINT_CANCEL_TASK = '/site_publish/cancelTask';
const ENDPOINT_PREPARE_PUBLISH = '/site_publish/preparePublish';

/**
 * 加载配置
 * 优先读取本地 config.json，不存在则从环境变量构造
 */
function loadConfig() {
  if (fs.existsSync(CONFIG_FILE)) {
    const configContent = fs.readFileSync(CONFIG_FILE, 'utf-8');
    return JSON.parse(configContent);
  }
  
  // config.json 不存在时，从环境变量构造（与 generate_website.mjs 保持一致）
  const baseUrl = process.env.AIBOX_BASE_URL || "http://aidev.nicebox.cn/api/openclaw";
  const apiKey  = process.env.AIBOX_API_KEY  || "4_455_14ed156fdba64c6ccdb7a0cf236ac712078382681f3cb237";
  const siteId  = process.env.AIBOX_SITE_ID  || "455";
  
  if (!apiKey) {
    console.error('错误：缺少 API 配置，请设置 AIBOX_API_KEY 环境变量或创建 config.json');
    process.exit(1);
  }
  
  return {
    api_url: baseUrl,
    api_key: apiKey,
    site_id: siteId
  };
}

/**
 * 获取完整的API URL
 */
function getApiUrl(config, endpoint) {
  return `${config.api_url}${endpoint}`;
}

/**
 * 获取请求头
 */
function getHeaders(config) {
  return {
    'Authorization': config.api_key,
    'Content-Type': 'application/json'
  };
}

/**
 * 获取FTP配置
 */
async function getFtpConfig() {
  console.log('正在获取FTP配置...');
  
  const config = loadConfig();
  const url = getApiUrl(config, ENDPOINT_GET_CONFIG);
  const headers = getHeaders(config);
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: headers,
      timeout: 30000
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.code === 0) {
      console.log('\nFTP配置信息：');
      console.log(`FTP主机: ${result.data.ftp_host}`);
      console.log(`FTP端口: ${result.data.ftp_port}`);
      console.log(`FTP用户名: ${result.data.ftp_username}`);
      // 判断密码是否为空或脱敏：空字符串为未配置，****** 为已配置但脱敏
      const pwd = result.data.ftp_password;
      const pwdDisplay = (!pwd || pwd === '') ? '（未配置）' : '******（已配置）';
      console.log(`FTP密码: ${pwdDisplay}`);
      console.log(`FTP路径: ${result.data.ftp_path}`);
      console.log(`FTP模式: ${result.data.ftp_passive ? '被动' : '主动'}`);
      console.log(`发布模式: ${result.data.publish_mode}`);
      console.log(`站点地图URL: ${result.data.sitemap_url}`);
      return result.data;
    } else {
      console.error(`错误: ${result.message || '获取配置失败'}`);
      return null;
    }
  } catch (error) {
    console.error(`请求失败: ${error.message}`);
    return null;
  }
}

/**
 * 更新FTP配置
 */
async function updateFtpConfig(args) {
  console.log('正在更新FTP配置...');
  
  const config = loadConfig();
  const url = getApiUrl(config, ENDPOINT_UPDATE_CONFIG);
  const headers = getHeaders(config);
  
  // 构建更新参数
  const updateData = {};
  if (args.host) {
    updateData.ftp_host = args.host;
  }
  if (args.port) {
    updateData.ftp_port = args.port;
  }
  if (args.username) {
    updateData.ftp_username = args.username;
  }
  if (args.password) {
    updateData.ftp_password = args.password;
  }
  if (args.path) {
    updateData.ftp_path = args.path;
  }
  if (args.passive !== undefined) {
    updateData.ftp_passive = args.passive ? 1 : 0;
  }
  if (args.publishMode) {
    updateData.publish_mode = args.publishMode;
  }
  
  if (Object.keys(updateData).length === 0) {
    console.error('错误：请至少提供一个要更新的配置项');
    return false;
  }
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(updateData),
      timeout: 30000
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.code === 0) {
      console.log('\nFTP配置更新成功！');
      // 显示更新后的配置
      await getFtpConfig();
      return true;
    } else {
      console.error(`错误: ${result.message || '更新配置失败'}`);
      return false;
    }
  } catch (error) {
    console.error(`请求失败: ${error.message}`);
    return false;
  }
}

/**
 * 测试FTP连接
 */
async function testFtpConnection() {
  console.log('正在测试FTP连接...');
  
  const config = loadConfig();
  const url = getApiUrl(config, ENDPOINT_TEST_CONNECTION);
  const headers = getHeaders(config);
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: headers,
      timeout: 60000
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.code === 0) {
      console.log('\nFTP连接测试成功！');
      console.log(`服务器信息: ${result.data.message || '连接正常'}`);
      return true;
    } else {
      console.error(`错误: ${result.message || '连接测试失败'}`);
      return false;
    }
  } catch (error) {
    console.error(`请求失败: ${error.message}`);
    return false;
  }
}

/**
 * 获取FTP服务器信息
 */
async function getServerInfo() {
  console.log('正在获取FTP服务器信息...');
  
  const config = loadConfig();
  const url = getApiUrl(config, '/api/openclaw/site_publish/getServerInfo');
  const headers = getHeaders(config);
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: headers,
      timeout: 30000
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.code === 0) {
      console.log('\nFTP服务器信息获取成功！');
      console.log(`服务器信息: ${result.data.message || '获取成功'}`);
      if (result.data.server_info) {
        console.log('详细信息:');
        console.log(JSON.stringify(result.data.server_info, null, 2));
      }
      return true;
    } else {
      console.error(`错误: ${result.message || '获取服务器信息失败'}`);
      return false;
    }
  } catch (error) {
    console.error(`请求失败: ${error.message}`);
    return false;
  }
}

/**
 * 获取发布任务状态
 */
async function getTaskStatus() {
  console.log('正在获取发布任务状态...');
  
  const config = loadConfig();
  const url = getApiUrl(config, ENDPOINT_GET_TASK_STATUS);
  const headers = getHeaders(config);
  
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: headers,
      timeout: 30000
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.code === 0) {
      console.log('\n发布任务状态获取成功！');
      console.log(`任务状态: ${result.data.status || '未知'}`);
      if (result.data.message) {
        console.log(`任务信息: ${result.data.message}`);
      }
      return result.data;
    } else {
      console.error(`错误: ${result.message || '获取任务状态失败'}`);
      return null;
    }
  } catch (error) {
    console.error(`请求失败: ${error.message}`);
    return null;
  }
}

/**
 * 取消发布任务
 */
async function cancelTask() {
  console.log('正在取消发布任务...');
  
  const config = loadConfig();
  const url = getApiUrl(config, ENDPOINT_CANCEL_TASK);
  const headers = getHeaders(config);
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: headers,
      timeout: 30000
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.code === 0) {
      console.log('\n发布任务取消成功！');
      return true;
    } else {
      console.error(`错误: ${result.message || '取消任务失败'}`);
      return false;
    }
  } catch (error) {
    console.error(`请求失败: ${error.message}`);
    return false;
  }
}

/**
 * 准备发布（生成文件，创建任务）
 */
async function preparePublish(options) {
  console.log('正在准备发布...');
  
  const config = loadConfig();
  const url = getApiUrl(config, ENDPOINT_PREPARE_PUBLISH);
  const headers = getHeaders(config);
  
  const data = {
    options: options,
    batch_number: 1
  };
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(data),
      timeout: 120000
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.code === 0) {
      console.log('\n发布准备成功！');
      if (result.data) {
        console.log('准备结果:');
        console.log(JSON.stringify(result.data, null, 2));
      }
      return result.data;
    } else {
      console.error(`错误: ${result.message || '准备发布失败'}`);
      return null;
    }
  } catch (error) {
    console.error(`请求失败: ${error.message}`);
    return null;
  }
}

/**
 * 发布网站
 * 
 * 安全机制：必须传入 confirmed=true 才会执行发布，否则返回确认提示
 * 这确保 AI 在发布前一定会询问用户确认
 */
async function publishWebsite(args) {
  // 🔒 发布前强制确认检查
  if (!args.confirmed) {
    console.log(JSON.stringify({
      need_confirm: true,
      stage: "publish",
      message: "⚠️ 发布网站将覆盖线上版本，此操作无法撤销还原！是否确认发布？",
      options: ["确认发布", "取消"],
      tip: "回复「确认发布」继续发布，回复「取消」终止操作"
    }));
    return false;
  }
  
  console.log('正在发布网站...\n');
  let stepNum = 1;
  const nextStep = (label) => console.log(`步骤${stepNum++}：${label}`);

  // 检查FTP配置
  nextStep('检查FTP配置');
  const ftpConfig = await getFtpConfig();
  
  if (!ftpConfig) {
    console.error('错误：无法获取FTP配置');
    return false;
  }
  
  // 注意：ftp_password 为 ****** 时表示后台已配置（脱敏返回），应由 API 判断连接是否可用
  // 不再在此做本地空值检查，避免误判已配置但脱敏的密码
  
  // 测试FTP连接（改为警告而非硬阻断）
  nextStep('测试FTP连接');
  const ftpOk = await testFtpConnection();
  if (!ftpOk) {
    console.warn('\n⚠️ FTP连接测试失败，但仍尝试发布（服务端可能可连接）');
  }
  
  // 检测发布任务状态
  nextStep('检测发布任务状态');
  const taskStatus = await getTaskStatus();
  
  // 检查是否正在发布
  if (taskStatus && taskStatus.status === 'running') {
    console.log('\n检测到有正在进行的发布任务！');
    const readline = require('readline').createInterface({
      input: process.stdin,
      output: process.stdout
    });
    
    return new Promise((resolve) => {
      readline.question('是否要强行终止并发布新的任务？(y/N): ', async (answer) => {
        readline.close();
        const confirm = answer.trim().toLowerCase();
        if (confirm === 'y') {
          nextStep('终止之前的发布任务');
          if (!(await cancelTask())) {
            console.error('错误：无法终止之前的发布任务');
            resolve(false);
            return;
          }
          // 继续发布流程
          await proceedWithPublish(args, resolve);
        } else {
          console.log('取消发布操作');
          resolve(false);
        }
      });
    });
  } else {
    // 没有正在进行的任务，直接继续发布流程
    return await proceedWithPublish(args);
  }
}

/**
 * 带重试的 HTTP POST 请求
 */
async function fetchWithRetry(url, options, maxRetries = 3, delayMs = 3000) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      if (result.code === 0) return result;
      // 业务错误不重试
      if (result.code === 400 || result.code === 401 || result.code === 403) return result;
      // 500 类错误可重试
      if (attempt < maxRetries) {
        console.log(`  第 ${attempt} 次尝试失败: ${result.message}，${delayMs/1000} 秒后重试...`);
        await new Promise(r => setTimeout(r, delayMs));
        continue;
      }
      return result;
    } catch (error) {
      if (attempt < maxRetries) {
        console.log(`  第 ${attempt} 次请求异常: ${error.message}，${delayMs/1000} 秒后重试...`);
        await new Promise(r => setTimeout(r, delayMs));
        continue;
      }
      throw error;
    }
  }
}

/**
 * 继续发布流程
 */
async function proceedWithPublish(args, resolve = null) {
  let stepNum = 1;
  const nextStep = (label) => console.log(`\n步骤${stepNum++}：${label}`);

  // 准备发布
  nextStep('准备发布');
  const prepareOptions = {
    batch_size: args.batchSize,
    overwrite_mode: args.overwriteMode,
    generate_mode: args.generateMode,
    batch_number: 1  // batch_number 必须放在 options 内部
  };
  
  const prepareResult = await preparePublish(prepareOptions);
  if (!prepareResult) {
    console.error('错误：准备发布失败');
    if (resolve) { resolve(false); }
    return false;
  }

  // 处理多批次
  const totalBatches = prepareResult.total_batches || 1;
  let currentBatch = 1;

  while (currentBatch <= totalBatches) {
    // 发布网站
    nextStep(`开始发布网站（批次 ${currentBatch}/${totalBatches}）...`);
    const config = loadConfig();
    const url = getApiUrl(config, ENDPOINT_PUBLISH);
    const headers = getHeaders(config);
    
    // 构建发布选项 — batch_number 必须在 options 内部，否则 PHP 后端报 "Undefined array key batch_number"
    const publishOptions = {
      batch_size: args.batchSize,
      overwrite_mode: args.overwriteMode,
      generate_mode: args.generateMode,
      batch_number: currentBatch
    };
    
    const data = {
      options: publishOptions,
      disable_streaming: true
    };
    
    try {
      const result = await fetchWithRetry(url, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(data),
        timeout: 300000
      });
      
      if (result.code === 0) {
        nextStep('发布完成');
        console.log('网站发布成功！');
        console.log(`发布结果: ${result.message || '发布完成'}`);
        if (result.data) {
          const stats = result.data.stats || {};
          if (stats.files_uploaded) console.log(`  上传文件: ${stats.files_uploaded} 个`);
          if (stats.files_failed)   console.log(`  失败文件: ${stats.files_failed} 个`);
          if (stats.duration)       console.log(`  耗时: ${stats.duration} 秒`);
        }
        if (resolve) { resolve(true); }
        // 多批次时继续下一批
        if (prepareResult.has_more && currentBatch < totalBatches) {
          currentBatch++;
          continue;
        }
        return true;
      } else {
        console.error(`错误: ${result.message || '发布失败'}`);
        if (resolve) { resolve(false); }
        return false;
      }
    } catch (error) {
      console.error(`请求失败: ${error.message}`);
      if (resolve) { resolve(false); }
      return false;
    }
  }

  return true;
}

/**
 * 主函数
 */
async function main() {
  const argv = yargs(process.argv.slice(2))
    .command('get-config', '获取FTP配置')
    .command('update-config', '更新FTP配置', (yargs) => {
      return yargs
        .option('host', { type: 'string', describe: 'FTP主机地址' })
        .option('port', { type: 'number', describe: 'FTP端口' })
        .option('username', { type: 'string', describe: 'FTP用户名' })
        .option('password', { type: 'string', describe: 'FTP密码' })
        .option('path', { type: 'string', describe: 'FTP路径' })
        .option('passive', { type: 'boolean', describe: '启用被动模式' })
        .option('active', { type: 'boolean', describe: '启用主动模式' })
        .option('publish-mode', { type: 'string', choices: ['dynamic', 'static'], describe: '发布模式' });
    })
    .command('test-connection', '测试FTP连接')
    .command('get-server-info', '获取FTP服务器信息')
    .command('get-task-status', '获取发布任务状态')
    .command('cancel-task', '取消发布任务')
    .command('publish', '发布网站', (yargs) => {
      return yargs
        .option('batch-size', { type: 'number', default: 30, choices: [20, 30, 50], describe: '批次大小' })
        .option('overwrite-mode', { type: 'string', default: 'smart', choices: ['smart', 'force'], describe: '覆盖模式' })
        .option('generate-mode', { type: 'string', default: 'default', choices: ['default', 'full_static'], describe: 'HTML生成模式' })
        .option('confirmed', { type: 'boolean', default: false, describe: '已确认发布（必须用户明确确认后才能传入）' });
    })
    .demandCommand(1, '请指定要执行的命令')
    .argv;
  
  const command = argv._[0];
  
  switch (command) {
    case 'get-config':
      await getFtpConfig();
      break;
    case 'update-config':
      await updateFtpConfig({
        host: argv.host,
        port: argv.port,
        username: argv.username,
        password: argv.password,
        path: argv.path,
        passive: argv.passive !== undefined ? argv.passive : (argv.active !== undefined ? !argv.active : undefined),
        publishMode: argv['publish-mode']
      });
      break;
    case 'test-connection':
      await testFtpConnection();
      break;
    case 'get-server-info':
      await getServerInfo();
      break;
    case 'get-task-status':
      await getTaskStatus();
      break;
    case 'cancel-task':
      await cancelTask();
      break;
    case 'publish':
      await publishWebsite({
        batchSize: argv['batch-size'],
        overwriteMode: argv['overwrite-mode'],
        generateMode: argv['generate-mode'],
        confirmed: argv.confirmed
      });
      break;
    default:
      yargs.showHelp();
      break;
  }
}

// 执行主函数
main().catch(error => {
  console.error(`执行失败: ${error.message}`);
  process.exit(1);
});
