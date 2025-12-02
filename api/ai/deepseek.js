import fetch from 'node-fetch';

const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY;

if (!DEEPSEEK_API_KEY) {
  console.error('[DeepSeek] 未配置 DEEPSEEK_API_KEY 环境变量');
}

export default async function handler(req, res) {
  // 设置 CORS 头
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ success: false, error: 'Method not allowed' });
  }

  const { model, systemPrompt, prompt, temperature, apiKey } = req.body;

  // 优先使用前端传递的 API Key，其次使用环境变量
  const effectiveApiKey = apiKey || DEEPSEEK_API_KEY;

  if (!effectiveApiKey) {
    return res.status(500).json({
      success: false,
      error: '未配置 DeepSeek API Key。请在前端输入 API Key 或联系管理员设置环境变量 DEEPSEEK_API_KEY'
    });
  }

  try {
    const response = await fetch('https://api.deepseek.com/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${effectiveApiKey}`
      },
      body: JSON.stringify({
        model: model || 'deepseek-chat',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: prompt }
        ],
        temperature: temperature || 0.7,
        stream: false
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`DeepSeek API 错误: ${error.error?.message || response.statusText}`);
    }

    const data = await response.json();
    return res.json({
      success: true,
      text: data.choices?.[0]?.message?.content || ''
    });
  } catch (error) {
    console.error('[DeepSeek] 请求失败:', error.message);
    return res.status(500).json({
      success: false,
      error: error.message
    });
  }
}
