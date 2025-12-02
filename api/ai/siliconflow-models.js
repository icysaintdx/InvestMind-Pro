import fetch from 'node-fetch';

const SILICONFLOW_API_KEY = process.env.SILICONFLOW_API_KEY;

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ success: false, error: 'Method not allowed' });
  }

  const { apiKey } = req.query;
  const effectiveApiKey = apiKey || SILICONFLOW_API_KEY;

  if (!effectiveApiKey) {
    return res.status(500).json({
      success: false,
      error: '未配置 SiliconFlow API Key'
    });
  }

  try {
    const response = await fetch('https://api.siliconflow.cn/v1/models', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${effectiveApiKey}`
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`SiliconFlow API 错误: ${error.error?.message || response.statusText}`);
    }

    const data = await response.json();
    
    const models = data.data
      .filter(model => model.id.includes('chat') || model.id.includes('instruct') || model.id.includes('Instruct'))
      .map(model => ({
        id: model.id,
        name: model.id,
        label: model.id.split('/').pop() || model.id,
        owned_by: model.owned_by || 'unknown'
      }));

    return res.json({
      success: true,
      models: models
    });
  } catch (error) {
    console.error('[SiliconFlow Models] 请求失败:', error.message);
    return res.status(500).json({
      success: false,
      error: error.message,
      models: []
    });
  }
}
