// IcySaint AI - 完整的10个智能体系统

const API_BASE = window.location.protocol + '//' + window.location.hostname + ':8000';

// 完整的10个智能体配置（与 constants.ts 完全对应）
const AGENTS = [
    // 第一阶段：5个专业分析师
    { id: 'macro', role: 'MACRO', title: '宏观政策分析师', icon: '🌍', color: 'slate', temperature: 0.2, modelProvider: 'GEMINI', modelName: 'gemini-2.5-flash', systemPrompt: '你是资深A股宏观政策分析师。' },
    { id: 'industry', role: 'INDUSTRY', title: '行业轮动分析师', icon: '🏭', color: 'cyan', temperature: 0.3, modelProvider: 'GEMINI', modelName: 'gemini-2.5-flash', systemPrompt: '你是A股行业轮动专家。' },
    { id: 'technical', role: 'TECHNICAL', title: '技术分析专家', icon: '📈', color: 'violet', temperature: 0.15, modelProvider: 'DEEPSEEK', modelName: 'deepseek-chat', systemPrompt: '你是A股技术分析专家。' },
    { id: 'funds', role: 'FUNDS', title: '资金流向分析师', icon: '💰', color: 'emerald', temperature: 0.3, modelProvider: 'GEMINI', modelName: 'gemini-2.5-flash', systemPrompt: '你是资金流向分析专家。' },
    { id: 'fundamental', role: 'FUNDAMENTAL', title: '基本面估值分析师', icon: '💼', color: 'blue', temperature: 0.2, modelProvider: 'DEEPSEEK', modelName: 'deepseek-chat', systemPrompt: '你是基本面估值专家。' },
    
    // 第二阶段：2个经理团队
    { id: 'manager_fundamental', role: 'MANAGER_FUNDAMENTAL', title: '基本面研究总监', icon: '👔', color: 'indigo', temperature: 0.35, modelProvider: 'DEEPSEEK', modelName: 'deepseek-chat', systemPrompt: '你是基本面研究总监。' },
    { id: 'manager_momentum', role: 'MANAGER_MOMENTUM', title: '市场动能总监', icon: '⚡', color: 'fuchsia', temperature: 0.4, modelProvider: 'DEEPSEEK', modelName: 'deepseek-chat', systemPrompt: '你是市场动能总监。' },
    
    // 第三阶段：2个风控团队
    { id: 'risk_system', role: 'RISK_SYSTEM', title: '系统性风险总监', icon: '⚠️', color: 'orange', temperature: 0.1, modelProvider: 'DEEPSEEK', modelName: 'deepseek-chat', systemPrompt: '你是系统性风险总监。' },
    { id: 'risk_portfolio', role: 'RISK_PORTFOLIO', title: '组合风险总监', icon: '⚖️', color: 'amber', temperature: 0.2, modelProvider: 'DEEPSEEK', modelName: 'deepseek-chat', systemPrompt: '你是组合风险总监。' },
    
    // 第四阶段：总经理
    { id: 'gm', role: 'GM', title: '投资决策总经理', icon: '👑', color: 'red', temperature: 0.45, modelProvider: 'DEEPSEEK', modelName: 'deepseek-chat', systemPrompt: '你是投资决策总经理。' }
];

const MODEL_OPTIONS = [
    { provider: 'GEMINI', name: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
    { provider: 'DEEPSEEK', name: 'deepseek-chat', label: 'DeepSeek' },
    { provider: 'QWEN', name: 'qwen-plus', label: 'Qwen Plus' },
    { provider: 'SILICONFLOW', name: 'Qwen/Qwen2.5-7B-Instruct', label: 'Qwen 2.5 7B (SF)' }
];

let appState = {
    status: 'IDLE',
    stockSymbol: '',
    stockData: null,
    outputs: {},
    agentConfigs: JSON.parse(JSON.stringify(AGENTS)),
    apiKeys: { gemini: '', deepseek: '', qwen: '', siliconflow: '', juhe: '' }
};

// 打字机效果
class TypeWriter {
    constructor(element, text, speed = 20) {
        this.element = element;
        this.text = text;
        this.speed = speed;
        this.index = 0;
        this.isTyping = false;
    }
    start() {
        if (this.isTyping) return;
        this.isTyping = true;
        this.element.innerHTML = '';
        this.type();
    }
    type() {
        if (this.index < this.text.length) {
            const char = this.text.charAt(this.index);
            this.element.innerHTML += char === '\n' ? '<br>' : char;
            this.element.innerHTML = this.element.innerHTML.replace(/<span class="typing-cursor"><\/span>/g, '');
            this.element.innerHTML += '<span class="typing-cursor"></span>';
            this.index++;
            
            // 打字时滚动到底部
            this.element.scrollTop = this.element.scrollHeight;
            
            setTimeout(() => this.type(), this.speed + Math.random() * 20);
        } else {
            setTimeout(() => {
                this.element.innerHTML = this.element.innerHTML.replace(/<span class="typing-cursor"><\/span>/g, '');
                this.isTyping = false;
                
                // 完成后滚动到顶部
                this.element.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            }, 500);
        }
    }
}

const typeWriters = {};

// 获取股票数据
async function fetchStockData(symbol) {
    const response = await fetch(`${API_BASE}/api/stock/${symbol}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, apiKey: appState.apiKeys.juhe })
    });
    const data = await response.json();
    if (!data.success) throw new Error(data.error || '获取股票数据失败');
    const d = data.data.data;
    return `【实时行情】股票: ${d.name} (${d.gid})\n价格: ¥${d.nowPri} | 涨跌: ${d.increPer}%\n开盘: ¥${d.todayStartPri} | 昨收: ¥${d.yestodEndPri}\n最高: ¥${d.todayMax} | 最低: ¥${d.todayMin}`;
}

// 调用AI
async function generateAgentResponse(config, stockSymbol, stockData, context = '', otherOutputs = {}) {
    const prompt = `作为${config.title}，分析股票 ${stockSymbol}：\n\n${stockData}\n\n${Object.entries(otherOutputs).map(([role, content]) => {
        const agent = AGENTS.find(a => a.role === role);
        return agent ? `【${agent.title}】\n${content}\n` : '';
    }).join('\n')}\n\n${config.systemPrompt}`;

    const endpoint = config.modelProvider === 'GEMINI' ? '/api/ai/gemini' : config.modelProvider === 'QWEN' ? '/api/ai/qwen' : config.modelProvider === 'SILICONFLOW' ? '/api/ai/siliconflow' : '/api/ai/deepseek';

    const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            model: config.modelName,
            prompt: prompt,
            systemPrompt: config.systemPrompt,
            temperature: config.temperature,
            apiKey: appState.apiKeys[config.modelProvider.toLowerCase()]
        })
    });

    const data = await response.json();
    if (!data.success) throw new Error(data.error || 'AI分析失败');
    return {
        text: data.text,
        usage: data.usage || { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 }
    };
}

// 更新智能体状态
function updateAgentStatus(agentId, status, content = null) {
    const card = document.getElementById(`agent-${agentId}`);
    if (!card) return;

    const statusEl = card.querySelector('.status-badge');
    const contentEl = card.querySelector('.agent-content');

    const statusConfig = {
        idle: { class: 'bg-slate-700 text-slate-300', text: '待命' },
        loading: { class: 'bg-yellow-500/20 text-yellow-400 animate-pulse', text: '分析中...' },
        success: { class: 'bg-green-500/20 text-green-400', text: '完成' },
        error: { class: 'bg-red-500/20 text-red-400', text: '错误' }
    };

    const config = statusConfig[status];
    statusEl.className = `status-badge px-2 py-1 rounded-full text-xs font-medium ${config.class}`;
    statusEl.textContent = config.text;

    if (content !== null && content !== '') {
        if (status === 'success') {
            if (!typeWriters[agentId]) typeWriters[agentId] = new TypeWriter(contentEl, content, 15);
            else { typeWriters[agentId].text = content; typeWriters[agentId].index = 0; }
            typeWriters[agentId].start();
        } else contentEl.innerHTML = content;
    } else if (content === '') {
        contentEl.innerHTML = '<span class="text-slate-500">等待分析...</span>';
    }
}

// 开始分析
async function startAnalysis() {
    const stockCode = document.getElementById('stockCode').value.trim();
    if (!stockCode || !/^\d{6}$/.test(stockCode)) {
        alert('请输入正确的6位股票代码');
        return;
    }

    appState.apiKeys = {
        gemini: document.getElementById('geminiKey')?.value || '',
        deepseek: document.getElementById('deepseekKey')?.value || '',
        qwen: document.getElementById('qwenKey')?.value || '',
        siliconflow: document.getElementById('siliconflowKey')?.value || '',
        juhe: document.getElementById('juheKey')?.value || ''
    };

    appState.status = 'LOADING';
    appState.stockSymbol = stockCode;
    appState.outputs = {};

    const btn = document.getElementById('analyzeBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span> 分析中...';

    AGENTS.forEach(agent => updateAgentStatus(agent.id, 'idle', ''));

    try {
        updateAgentStatus('technical', 'loading', '正在获取实时行情数据...');
        const stockData = await fetchStockData(stockCode);
        appState.stockData = stockData;
        updateAgentStatus('technical', 'idle', '');

        // 第一阶段：5个分析师
        console.log('第一阶段：分析师团队...');
        await Promise.all(AGENTS.slice(0, 5).map(agent => {
            updateAgentStatus(agent.id, 'loading', '正在分析，请耐心等待（最长可能需要3分钟）...');
            const config = appState.agentConfigs.find(c => c.id === agent.id);
            return generateAgentResponse(config, stockCode, stockData)
                .then(result => {
                    updateAgentStatus(agent.id, 'success', result.text, result.usage);
                    appState.outputs[agent.role] = result.text;
                })
                .catch(error => {
                    updateAgentStatus(agent.id, 'error', `分析失败: ${error.message}`);
                    appState.outputs[agent.role] = `分析失败: ${error.message}`;
                });
        }));

        // 第二阶段：2个经理
        console.log('第二阶段：经理团队...');
        await Promise.all(AGENTS.slice(5, 7).map(agent => {
            updateAgentStatus(agent.id, 'loading', '正在分析，请耐心等待...');
            const config = appState.agentConfigs.find(c => c.id === agent.id);
            return generateAgentResponse(config, stockCode, stockData, '', appState.outputs)
                .then(result => {
                    updateAgentStatus(agent.id, 'success', result.text, result.usage);
                    appState.outputs[agent.role] = result.text;
                })
                .catch(error => {
                    updateAgentStatus(agent.id, 'error', `分析失败: ${error.message}`);
                    appState.outputs[agent.role] = `分析失败: ${error.message}`;
                });
        }));

        // 第三阶段：2个风控
        console.log('第三阶段：风控团队...');
        await Promise.all(AGENTS.slice(7, 9).map(agent => {
            updateAgentStatus(agent.id, 'loading', '正在分析，请耐心等待...');
            const config = appState.agentConfigs.find(c => c.id === agent.id);
            return generateAgentResponse(config, stockCode, stockData, '', appState.outputs)
                .then(result => {
                    updateAgentStatus(agent.id, 'success', result.text, result.usage);
                    appState.outputs[agent.role] = result.text;
                })
                .catch(error => {
                    updateAgentStatus(agent.id, 'error', `分析失败: ${error.message}`);
                    appState.outputs[agent.role] = `分析失败: ${error.message}`;
                });
        }));

        // 第四阶段：总经理
        console.log('第四阶段：总经理决策...');
        const gmAgent = AGENTS[9];
        updateAgentStatus(gmAgent.id, 'loading', '正在综合分析所有信息，请耐心等待...');
        const gmConfig = appState.agentConfigs.find(c => c.id === gmAgent.id);
        const gmResult = await generateAgentResponse(gmConfig, stockCode, stockData, '', appState.outputs);
        updateAgentStatus(gmAgent.id, 'success', gmResult.text, gmResult.usage);
        appState.outputs[gmAgent.role] = gmResult.text;
        
        // 等待总经理的打字机效果完成（预估时间）
        const estimatedTime = gmResult.text.length * 15; // 15ms per character
        await new Promise(resolve => setTimeout(resolve, Math.min(estimatedTime, 3000))); // 最多等3秒

        // 显示最终结果
        const resultSection = document.getElementById('resultSection');
        const resultContent = document.getElementById('finalResult');
        resultContent.textContent = `股票代码: ${stockCode}\n\n${stockData}\n\n${'='.repeat(60)}\n\n${Object.entries(appState.outputs).map(([role, content]) => {
            const agent = AGENTS.find(a => a.role === role);
            return agent ? `【${agent.title}】\n${content}\n` : '';
        }).join('\n' + '='.repeat(60) + '\n')}`;
        resultSection.classList.remove('hidden');
        resultSection.scrollIntoView({ behavior: 'smooth' });

        appState.status = 'COMPLETE';
    } catch (error) {
        console.error('分析失败:', error);
        alert('分析失败: ' + error.message);
        appState.status = 'ERROR';
    } finally {
        btn.disabled = false;
        btn.innerHTML = '开始分析';
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('IcySaint AI 系统初始化... 10个智能体已加载');
    document.getElementById('stockCode')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') startAnalysis();
    });
});
