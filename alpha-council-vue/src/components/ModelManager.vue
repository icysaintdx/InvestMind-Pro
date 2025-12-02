<template>
  <div v-if="visible" class="modal-overlay" @click.self="close">
    <div class="modal-container" @wheel.stop @touchmove.stop>
      <!-- 头部 -->
      <div class="modal-header">
        <h2 class="modal-title"> 模型管理</h2>
        <button @click="close" class="close-btn">×</button>
      </div>
      
      <!-- 内容 -->
      <div class="modal-body">
        <!-- 搜索和控制栏 -->
        <div class="search-control-bar">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索模型..."
            class="search-input"
          />
          
          <div class="control-buttons">
            <button @click="selectAll" class="control-btn">全选</button>
            <button @click="clearSelection" class="control-btn">取消全选</button>
            <button @click="saveSelection" class="save-btn">保存</button>
          </div>
        </div>
        
        <!-- 品牌筛选按钮（始终显示） -->
        <div class="brand-filters">
          <button
            v-for="brand in brandTypes"
            :key="brand.value"
            @click="currentBrand = brand.value"
            :class="['brand-btn', { active: currentBrand === brand.value }]"
          >
            {{ brand.label }}
          </button>
        </div>
        
        <!-- LLM筛选开关 -->
        <div class="filter-toggle-container">
          <label class="filter-toggle">
            <input type="checkbox" v-model="onlyLLM" />
            <span class="toggle-slider"></span>
            <span class="toggle-label">仅显示大语言模型</span>
          </label>
        </div>

        <!-- 模型列表 -->
        <div class="model-list">
          <!-- 直接渲染所有过滤后的模型 -->
          <div 
            v-for="model in filteredModels" 
            :key="model.name"
            class="model-item"
            @click="toggleModel(model)"
          >
            <div class="model-info">
              <input 
                type="checkbox" 
                :checked="isSelected(model)"
                @click.stop
                @change="toggleModel(model)"
                class="model-checkbox"
              >
              <div>
                <div class="model-name">{{ model.label }}</div>
                <div class="model-meta">
                  <span class="model-provider">{{ model.provider }}</span>
                  <span class="model-channel" v-if="model.channel">{{ model.channel }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部信息 -->
        <div class="modal-footer">
          <span class="selection-info">
            已加载 {{ filteredModels.length }} 个模型 | 已选中 {{ selectedModels.size }} 个
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

export default {
  name: 'ModelManager',
  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'save'],
  setup(props, { emit }) {
    const onlyLLM = ref(false)  // 默认显示所有模型（避免过滤问题）
    const currentBrand = ref('all')
    const searchQuery = ref('')
    const selectedModels = ref(new Set())
    const allModels = ref([])  // 改为动态加载
    const loading = ref(false)
    const modelsLoaded = ref(false) // 标记模型是否已加载
    
    // 从API加载模型列表（仅加载一次）
    const loadModels = async () => {
      // 如果已经加载过，直接返回
      if (modelsLoaded.value && allModels.value.length > 0) {
        console.log(`[ModelManager] 使用缓存的模型列表，共 ${allModels.value.length} 个模型`)
        return
      }
      
      // 如果正在加载中，也直接返回
      if (loading.value) {
        console.log('[ModelManager] 模型正在加载中，跳过重复请求')
        return
      }
      
      loading.value = true
      try {
        const response = await fetch('http://localhost:8000/api/models')
        if (response.ok) {
          const data = await response.json()
          if (data.success && data.models) {
            allModels.value = data.models
            modelsLoaded.value = true // 标记已加载
            console.log(`[ModelManager] 首次加载 ${data.models.length} 个模型`)
            console.log(`[ModelManager] 第一个模型示例:`, data.models[0])
            console.log(`[ModelManager] allModels.value长度:`, allModels.value.length)
          } else {
            console.error('加载模型失败:', data.error)
          }
        } else {
          console.error('API请求失败:', response.status)
        }
      } catch (error) {
        console.error('加载模型列表失败:', error)
      } finally {
        loading.value = false
      }
    }

    // 从后端文件加载模型配置
    const loadModelConfigs = async () => {
      try {
        // 从后端加载智能体配置（包括selectedModels）
        const response = await fetch('http://localhost:8000/api/config/agents')
        if (response.ok) {
          const data = await response.json()
          console.log('从后端加载配置:', data)
          
          if (data.data) {
            // 加载已选择的模型
            if (data.data.selectedModels && data.data.selectedModels.length > 0) {
              selectedModels.value = new Set(data.data.selectedModels)
              console.log('从后端文件加载了', data.data.selectedModels.length, '个已选模型')
            } else {
              console.log('后端文件中没有保存的模型选择')
            }
          }
        }
      } catch (error) {
        console.error('加载模型配置失败:', error)
      }
    }
    
    // 品牌筛选按钮（按照图片样式）
    const brandTypes = [
      { value: 'all', label: '全部' },
      { value: 'qwen', label: 'Qwen' },
      { value: 'llama', label: 'Llama' },
      { value: 'deepseek', label: 'DeepSeek' },
      { value: 'gemini', label: 'Gemini' },
      { value: 'mistral', label: 'Mistral' },
      { value: 'yi', label: 'Yi' },
      { value: 'glm', label: 'GLM' }
    ]

    // 删除硬编码的模型列表，使用动态加载
    /*
    const allModels_old = ref([
      // === Gemini渠道 (Google) ===
      { provider: 'GEMINI', name: 'gemini-2.0-flash-exp', label: 'Gemini 2.0 Flash (实验版)', type: 'llm', channel: 'Google' },
      { provider: 'GEMINI', name: 'gemini-exp-1206', label: 'Gemini 实验版 1206', type: 'llm', channel: 'Google' },
      { provider: 'GEMINI', name: 'gemini-exp-1121', label: 'Gemini 实验版 1121', type: 'llm', channel: 'Google' },
      { provider: 'GEMINI', name: 'gemini-1.5-pro-002', label: 'Gemini 1.5 Pro 002', type: 'llm', channel: 'Google' },
      { provider: 'GEMINI', name: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro', type: 'llm', channel: 'Google' },
      { provider: 'GEMINI', name: 'gemini-1.5-flash-002', label: 'Gemini 1.5 Flash 002', type: 'llm', channel: 'Google' },
      { provider: 'GEMINI', name: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash', type: 'llm', channel: 'Google' },
      { provider: 'GEMINI', name: 'gemini-1.5-flash-8b', label: 'Gemini 1.5 Flash 8B', type: 'llm', channel: 'Google' },
      
      // === DeepSeek渠道 ===
      { provider: 'DEEPSEEK', name: 'deepseek-chat', label: 'DeepSeek Chat', type: 'llm', channel: 'DeepSeek' },
      { provider: 'DEEPSEEK', name: 'deepseek-coder', label: 'DeepSeek Coder', type: 'llm', channel: 'DeepSeek' },
      { provider: 'DEEPSEEK', name: 'deepseek-reasoner', label: 'DeepSeek Reasoner', type: 'llm', channel: 'DeepSeek' },
      
      // === 通义千问渠道 (阿里云) ===
      { provider: 'QWEN', name: 'qwen-max', label: '通义千问 Max', type: 'llm', channel: '阿里云' },
      { provider: 'QWEN', name: 'qwen-max-longcontext', label: '通义千问 Max 长文本', type: 'llm', channel: '阿里云' },
      { provider: 'QWEN', name: 'qwen-plus', label: '通义千问 Plus', type: 'llm', channel: '阿里云' },
      { provider: 'QWEN', name: 'qwen-turbo', label: '通义千问 Turbo', type: 'llm', channel: '阿里云' },
      { provider: 'QWEN', name: 'qwen-turbo-latest', label: '通义千问 Turbo 最新', type: 'llm', channel: '阿里云' },
      { provider: 'QWEN', name: 'qwen2.5-72b-instruct', label: 'Qwen2.5 72B', type: 'llm', channel: '阿里云' },
      { provider: 'QWEN', name: 'qwen2.5-32b-instruct', label: 'Qwen2.5 32B', type: 'llm', channel: '阿里云' },
      { provider: 'QWEN', name: 'qwen2.5-14b-instruct', label: 'Qwen2.5 14B', type: 'llm', channel: '阿里云' },
      { provider: 'QWEN', name: 'qwen2.5-7b-instruct', label: 'Qwen2.5 7B', type: 'llm', channel: '阿里云' },
      { provider: 'QWEN', name: 'qwen2.5-3b-instruct', label: 'Qwen2.5 3B', type: 'llm', channel: '阿里云' },
      { provider: 'QWEN', name: 'qwen2.5-1.5b-instruct', label: 'Qwen2.5 1.5B', type: 'llm', channel: '阿里云' },
      { provider: 'QWEN', name: 'qwen2.5-0.5b-instruct', label: 'Qwen2.5 0.5B', type: 'llm', channel: '阿里云' },
      { provider: 'QWEN', name: 'qwen2.5-coder-32b-instruct', label: 'Qwen2.5 Coder 32B', type: 'llm', channel: '阿里云' },
      { provider: 'QWEN', name: 'qwen2.5-coder-7b-instruct', label: 'Qwen2.5 Coder 7B', type: 'llm', channel: '阿里云' },
      { provider: 'QWEN', name: 'qwen2.5-math-72b-instruct', label: 'Qwen2.5 Math 72B', type: 'llm', channel: '阿里云' },
      { provider: 'QWEN', name: 'qwen2.5-math-7b-instruct', label: 'Qwen2.5 Math 7B', type: 'llm', channel: '阿里云' },
      
      // === 硅基流动渠道 (SiliconFlow) - Qwen系列 ===
      // Qwen3系列
      { provider: 'QWEN', name: 'Qwen/Qwen3-72B', label: 'Qwen3 72B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen3-32B', label: 'Qwen3 32B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen3-14B', label: 'Qwen3 14B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen3-8B', label: 'Qwen3 8B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen3-7B', label: 'Qwen3 7B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen3-4B', label: 'Qwen3 4B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen3-2B', label: 'Qwen3 2B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen3-1.8B', label: 'Qwen3 1.8B', type: 'llm', channel: '硅基流动' },
      
      // Qwen2.5系列  
      { provider: 'QWEN', name: 'Qwen/Qwen2.5-72B-Instruct', label: 'Qwen2.5 72B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen2.5-32B-Instruct', label: 'Qwen2.5 32B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen2.5-14B-Instruct', label: 'Qwen2.5 14B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen2.5-7B-Instruct', label: 'Qwen2.5 7B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen2.5-3B-Instruct', label: 'Qwen2.5 3B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen2.5-1.5B-Instruct', label: 'Qwen2.5 1.5B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen2.5-0.5B-Instruct', label: 'Qwen2.5 0.5B', type: 'llm', channel: '硅基流动' },
      
      // Qwen2.5-Coder系列
      { provider: 'QWEN', name: 'Qwen/Qwen2.5-Coder-32B-Instruct', label: 'Qwen2.5 Coder 32B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen2.5-Coder-14B-Instruct', label: 'Qwen2.5 Coder 14B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen2.5-Coder-7B-Instruct', label: 'Qwen2.5 Coder 7B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen2.5-Coder-3B-Instruct', label: 'Qwen2.5 Coder 3B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen2.5-Coder-1.5B-Instruct', label: 'Qwen2.5 Coder 1.5B', type: 'llm', channel: '硅基流动' },
      
      // Qwen2系列
      { provider: 'QWEN', name: 'Qwen/Qwen2-72B-Instruct', label: 'Qwen2 72B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen2-57B-A14B-Instruct', label: 'Qwen2 57B-A14B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen2-32B-Instruct', label: 'Qwen2 32B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen2-7B-Instruct', label: 'Qwen2 7B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen2-1.5B-Instruct', label: 'Qwen2 1.5B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen2-0.5B-Instruct', label: 'Qwen2 0.5B', type: 'llm', channel: '硅基流动' },
      
      // Qwen1.5系列
      { provider: 'QWEN', name: 'Qwen/Qwen1.5-110B-Chat', label: 'Qwen1.5 110B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen1.5-72B-Chat', label: 'Qwen1.5 72B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen1.5-32B-Chat', label: 'Qwen1.5 32B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen1.5-14B-Chat', label: 'Qwen1.5 14B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen1.5-7B-Chat', label: 'Qwen1.5 7B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen1.5-4B-Chat', label: 'Qwen1.5 4B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen1.5-1.8B-Chat', label: 'Qwen1.5 1.8B', type: 'llm', channel: '硅基流动' },
      { provider: 'QWEN', name: 'Qwen/Qwen1.5-0.5B-Chat', label: 'Qwen1.5 0.5B', type: 'llm', channel: '硅基流动' },
      
      // === 硅基流动渠道 - DeepSeek系列 ===
      { provider: 'DEEPSEEK', name: 'deepseek-ai/DeepSeek-V2.5', label: 'DeepSeek V2.5', type: 'llm', channel: '硅基流动' },
      { provider: 'DEEPSEEK', name: 'deepseek-ai/DeepSeek-V2-Chat', label: 'DeepSeek V2 Chat', type: 'llm', channel: '硅基流动' },
      { provider: 'DEEPSEEK', name: 'deepseek-ai/deepseek-llm-67b-chat', label: 'DeepSeek LLM 67B', type: 'llm', channel: '硅基流动' },
      { provider: 'DEEPSEEK', name: 'deepseek-ai/DeepSeek-Coder-V2-Instruct', label: 'DeepSeek Coder V2', type: 'llm', channel: '硅基流动' },
      
      // === 硅基流动渠道 - Llama系列 ===
      // Llama 3.1系列
      { provider: 'LLAMA', name: 'meta-llama/Meta-Llama-3.1-405B-Instruct', label: 'Llama 3.1 405B', type: 'llm', channel: '硅基流动' },
      { provider: 'LLAMA', name: 'meta-llama/Meta-Llama-3.1-70B-Instruct', label: 'Llama 3.1 70B', type: 'llm', channel: '硅基流动' },
      { provider: 'LLAMA', name: 'meta-llama/Meta-Llama-3.1-8B-Instruct', label: 'Llama 3.1 8B', type: 'llm', channel: '硅基流动' },
      
      // Llama 3系列
      { provider: 'LLAMA', name: 'meta-llama/Meta-Llama-3-70B-Instruct', label: 'Llama 3 70B', type: 'llm', channel: '硅基流动' },
      { provider: 'LLAMA', name: 'meta-llama/Meta-Llama-3-8B-Instruct', label: 'Llama 3 8B', type: 'llm', channel: '硅基流动' },
      
      // Llama 3.2系列
      { provider: 'LLAMA', name: 'meta-llama/Llama-3.2-90B-Vision-Instruct', label: 'Llama 3.2 90B Vision', type: 'llm', channel: '硅基流动' },
      { provider: 'LLAMA', name: 'meta-llama/Llama-3.2-11B-Vision-Instruct', label: 'Llama 3.2 11B Vision', type: 'llm', channel: '硅基流动' },
      { provider: 'LLAMA', name: 'meta-llama/Llama-3.2-3B-Instruct', label: 'Llama 3.2 3B', type: 'llm', channel: '硅基流动' },
      { provider: 'LLAMA', name: 'meta-llama/Llama-3.2-1B-Instruct', label: 'Llama 3.2 1B', type: 'llm', channel: '硅基流动' },
      
      // Llama 2系列
      { provider: 'LLAMA', name: 'meta-llama/Llama-2-70b-chat-hf', label: 'Llama 2 70B Chat', type: 'llm', channel: '硅基流动' },
      { provider: 'LLAMA', name: 'meta-llama/Llama-2-13b-chat-hf', label: 'Llama 2 13B Chat', type: 'llm', channel: '硅基流动' },
      { provider: 'LLAMA', name: 'meta-llama/Llama-2-7b-chat-hf', label: 'Llama 2 7B Chat', type: 'llm', channel: '硅基流动' },
      
      // CodeLlama系列
      { provider: 'LLAMA', name: 'meta-llama/CodeLlama-70b-Instruct-hf', label: 'CodeLlama 70B', type: 'llm', channel: '硅基流动' },
      { provider: 'LLAMA', name: 'meta-llama/CodeLlama-34b-Instruct-hf', label: 'CodeLlama 34B', type: 'llm', channel: '硅基流动' },
      { provider: 'LLAMA', name: 'meta-llama/CodeLlama-13b-Instruct-hf', label: 'CodeLlama 13B', type: 'llm', channel: '硅基流动' },
      { provider: 'LLAMA', name: 'meta-llama/CodeLlama-7b-Instruct-hf', label: 'CodeLlama 7B', type: 'llm', channel: '硅基流动' },
      
      // === 硅基流动渠道 - Mistral系列 ===
      { provider: 'MISTRAL', name: 'mistralai/Mistral-7B-Instruct-v0.3', label: 'Mistral 7B v0.3', type: 'llm', channel: '硅基流动' },
      { provider: 'MISTRAL', name: 'mistralai/Mistral-7B-Instruct-v0.2', label: 'Mistral 7B v0.2', type: 'llm', channel: '硅基流动' },
      { provider: 'MISTRAL', name: 'mistralai/Mixtral-8x7B-Instruct-v0.1', label: 'Mixtral 8x7B', type: 'llm', channel: '硅基流动' },
      { provider: 'MISTRAL', name: 'mistralai/Mixtral-8x22B-Instruct-v0.1', label: 'Mixtral 8x22B', type: 'llm', channel: '硅基流动' },
      { provider: 'MISTRAL', name: 'mistralai/Mistral-Large-Instruct-2407', label: 'Mistral Large 2407', type: 'llm', channel: '硅基流动' },
      { provider: 'MISTRAL', name: 'mistralai/Mistral-Nemo-Instruct-2407', label: 'Mistral Nemo 2407', type: 'llm', channel: '硅基流动' },
      
      // === 硅基流动渠道 - Yi系列 ===
      { provider: 'YI', name: '01-ai/Yi-1.5-34B-Chat-16K', label: 'Yi-1.5 34B 16K', type: 'llm', channel: '硅基流动' },
      { provider: 'YI', name: '01-ai/Yi-1.5-9B-Chat-16K', label: 'Yi-1.5 9B 16K', type: 'llm', channel: '硅基流动' },
      { provider: 'YI', name: '01-ai/Yi-1.5-6B-Chat', label: 'Yi-1.5 6B', type: 'llm', channel: '硅基流动' },
      { provider: 'YI', name: '01-ai/Yi-34B-Chat', label: 'Yi 34B Chat', type: 'llm', channel: '硅基流动' },
      { provider: 'YI', name: '01-ai/Yi-6B-Chat', label: 'Yi 6B Chat', type: 'llm', channel: '硅基流动' },
      { provider: 'YI', name: '01-ai/Yi-Coder-9B-Chat', label: 'Yi-Coder 9B', type: 'llm', channel: '硅基流动' },
      { provider: 'YI', name: '01-ai/Yi-Coder-1.5B-Chat', label: 'Yi-Coder 1.5B', type: 'llm', channel: '硅基流动' },
      
      // === 硅基流动渠道 - GLM系列 ===
      { provider: 'GLM', name: 'THUDM/glm-4-9b-chat', label: 'GLM-4 9B', type: 'llm', channel: '硅基流动' },
      { provider: 'GLM', name: 'THUDM/chatglm3-6b', label: 'ChatGLM3 6B', type: 'llm', channel: '硅基流动' },
      { provider: 'GLM', name: 'THUDM/glm-4-9b-chat-1m', label: 'GLM-4 9B 1M', type: 'llm', channel: '硅基流动' },
      { provider: 'GLM', name: 'THUDM/chatglm3-6b-128k', label: 'ChatGLM3 6B 128K', type: 'llm', channel: '硅基流动' },
      { provider: 'GLM', name: 'THUDM/codegeex4-all-9b', label: 'CodeGeeX4 9B', type: 'llm', channel: '硅基流动' },
      
      // === 硅基流动渠道 - 其他开源模型 ===
      // InternLM系列
      { provider: 'INTERNLM', name: 'internlm/internlm2_5-20b-chat', label: 'InternLM2.5 20B', type: 'llm', channel: '硅基流动' },
      { provider: 'INTERNLM', name: 'internlm/internlm2_5-7b-chat', label: 'InternLM2.5 7B', type: 'llm', channel: '硅基流动' },
      { provider: 'INTERNLM', name: 'internlm/internlm2-chat-20b', label: 'InternLM2 20B', type: 'llm', channel: '硅基流动' },
      { provider: 'INTERNLM', name: 'internlm/internlm2-chat-7b', label: 'InternLM2 7B', type: 'llm', channel: '硅基流动' },
      { provider: 'INTERNLM', name: 'internlm/internlm-chat-7b', label: 'InternLM 7B', type: 'llm', channel: '硅基流动' },
      
      // Baichuan系列
      { provider: 'BAICHUAN', name: 'baichuan-inc/Baichuan2-53B-Chat', label: 'Baichuan2 53B', type: 'llm', channel: '硅基流动' },
      { provider: 'BAICHUAN', name: 'baichuan-inc/Baichuan2-13B-Chat', label: 'Baichuan2 13B', type: 'llm', channel: '硅基流动' },
      { provider: 'BAICHUAN', name: 'baichuan-inc/Baichuan2-7B-Chat', label: 'Baichuan2 7B', type: 'llm', channel: '硅基流动' },
      { provider: 'BAICHUAN', name: 'baichuan-inc/Baichuan-13B-Chat', label: 'Baichuan 13B', type: 'llm', channel: '硅基流动' },
      { provider: 'BAICHUAN', name: 'baichuan-inc/Baichuan-7B', label: 'Baichuan 7B', type: 'llm', channel: '硅基流动' },
      
      // Gemma系列
      { provider: 'GEMMA', name: 'google/gemma-2-27b-it', label: 'Gemma 2 27B', type: 'llm', channel: '硅基流动' },
      { provider: 'GEMMA', name: 'google/gemma-2-9b-it', label: 'Gemma 2 9B', type: 'llm', channel: '硅基流动' },
      { provider: 'GEMMA', name: 'google/gemma-7b-it', label: 'Gemma 7B', type: 'llm', channel: '硅基流动' },
      { provider: 'GEMMA', name: 'google/gemma-2b-it', label: 'Gemma 2B', type: 'llm', channel: '硅基流动' },
      
      // Phi系列 (Microsoft)
      { provider: 'PHI', name: 'microsoft/Phi-3.5-mini-instruct', label: 'Phi 3.5 Mini', type: 'llm', channel: '硅基流动' },
      { provider: 'PHI', name: 'microsoft/Phi-3-medium-128k-instruct', label: 'Phi 3 Medium 128K', type: 'llm', channel: '硅基流动' },
      { provider: 'PHI', name: 'microsoft/Phi-3-small-128k-instruct', label: 'Phi 3 Small 128K', type: 'llm', channel: '硅基流动' },
      { provider: 'PHI', name: 'microsoft/Phi-3-mini-128k-instruct', label: 'Phi 3 Mini 128K', type: 'llm', channel: '硅基流动' },
      
      // Aquila系列
      { provider: 'AQUILA', name: 'BAAI/Aquila2-34B', label: 'Aquila2 34B', type: 'llm', channel: '硅基流动' },
      { provider: 'AQUILA', name: 'BAAI/Aquila2-7B', label: 'Aquila2 7B', type: 'llm', channel: '硅基流动' },
      { provider: 'AQUILA', name: 'BAAI/AquilaChat2-34B', label: 'AquilaChat2 34B', type: 'llm', channel: '硅基流动' },
      { provider: 'AQUILA', name: 'BAAI/AquilaChat2-7B', label: 'AquilaChat2 7B', type: 'llm', channel: '硅基流动' },
      
      // Vicuna系列
      { provider: 'VICUNA', name: 'lmsys/vicuna-33b-v1.3', label: 'Vicuna 33B v1.3', type: 'llm', channel: '硅基流动' },
      { provider: 'VICUNA', name: 'lmsys/vicuna-13b-v1.5', label: 'Vicuna 13B v1.5', type: 'llm', channel: '硅基流动' },
      { provider: 'VICUNA', name: 'lmsys/vicuna-7b-v1.5', label: 'Vicuna 7B v1.5', type: 'llm', channel: '硅基流动' },
      
      // WizardLM系列
      { provider: 'WIZARDLM', name: 'WizardLM/WizardLM-70B-V1.0', label: 'WizardLM 70B', type: 'llm', channel: '硅基流动' },
      { provider: 'WIZARDLM', name: 'WizardLM/WizardLM-13B-V1.2', label: 'WizardLM 13B', type: 'llm', channel: '硅基流动' },
      { provider: 'WIZARDLM', name: 'WizardLM/WizardCoder-33B-V1.1', label: 'WizardCoder 33B', type: 'llm', channel: '硅基流动' },
      { provider: 'WIZARDLM', name: 'WizardLM/WizardCoder-15B-V1.0', label: 'WizardCoder 15B', type: 'llm', channel: '硅基流动' },
      
      // Falcon系列
      { provider: 'FALCON', name: 'tiiuae/falcon-180B-chat', label: 'Falcon 180B Chat', type: 'llm', channel: '硅基流动' },
      { provider: 'FALCON', name: 'tiiuae/falcon-40b-instruct', label: 'Falcon 40B', type: 'llm', channel: '硅基流动' },
      { provider: 'FALCON', name: 'tiiuae/falcon-7b-instruct', label: 'Falcon 7B', type: 'llm', channel: '硅基流动' },
      
      // Alpaca系列
      { provider: 'ALPACA', name: 'stanford/alpaca-65b', label: 'Alpaca 65B', type: 'llm', channel: '硅基流动' },
      { provider: 'ALPACA', name: 'stanford/alpaca-30b', label: 'Alpaca 30B', type: 'llm', channel: '硅基流动' },
      { provider: 'ALPACA', name: 'stanford/alpaca-13b', label: 'Alpaca 13B', type: 'llm', channel: '硅基流动' },
      { provider: 'ALPACA', name: 'stanford/alpaca-7b', label: 'Alpaca 7B', type: 'llm', channel: '硅基流动' },
      
      // === 更多开源模型 ===
      // Orion系列 (猎户星空)
      { provider: 'ORION', name: 'OrionStarAI/Orion-14B-Chat', label: 'Orion 14B Chat', type: 'llm', channel: '硅基流动' },
      { provider: 'ORION', name: 'OrionStarAI/Orion-14B-Chat-Plugin', label: 'Orion 14B Plugin', type: 'llm', channel: '硅基流动' },
      { provider: 'ORION', name: 'OrionStarAI/Orion-14B-LongChat', label: 'Orion 14B LongChat', type: 'llm', channel: '硅基流动' },
      
      // BlueLM系列 (vivo)
      { provider: 'BLUELM', name: 'vivo-ai/BlueLM-7B-Chat', label: 'BlueLM 7B Chat', type: 'llm', channel: '硅基流动' },
      { provider: 'BLUELM', name: 'vivo-ai/BlueLM-7B-Chat-32K', label: 'BlueLM 7B 32K', type: 'llm', channel: '硅基流动' },
      
      // Zephyr系列
      { provider: 'ZEPHYR', name: 'HuggingFaceH4/zephyr-7b-beta', label: 'Zephyr 7B Beta', type: 'llm', channel: '硅基流动' },
      { provider: 'ZEPHYR', name: 'HuggingFaceH4/zephyr-7b-alpha', label: 'Zephyr 7B Alpha', type: 'llm', channel: '硅基流动' },
      
      // OpenChat系列
      { provider: 'OPENCHAT', name: 'openchat/openchat-3.5-1210', label: 'OpenChat 3.5 1210', type: 'llm', channel: '硅基流动' },
      { provider: 'OPENCHAT', name: 'openchat/openchat-3.5-0106', label: 'OpenChat 3.5 0106', type: 'llm', channel: '硅基流动' },
      { provider: 'OPENCHAT', name: 'openchat/openchat_3.5', label: 'OpenChat 3.5', type: 'llm', channel: '硅基流动' },
      
      // Nous系列
      { provider: 'NOUS', name: 'NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO', label: 'Nous Hermes 2 Mixtral', type: 'llm', channel: '硅基流动' },
      { provider: 'NOUS', name: 'NousResearch/Nous-Hermes-2-Yi-34B', label: 'Nous Hermes 2 Yi 34B', type: 'llm', channel: '硅基流动' },
      { provider: 'NOUS', name: 'NousResearch/Nous-Capybara-7B-V1.9', label: 'Nous Capybara 7B', type: 'llm', channel: '硅基流动' },
      
      // Starling系列
      { provider: 'STARLING', name: 'berkeley-nest/Starling-LM-7B-alpha', label: 'Starling 7B Alpha', type: 'llm', channel: '硅基流动' },
      { provider: 'STARLING', name: 'berkeley-nest/Starling-LM-7B-beta', label: 'Starling 7B Beta', type: 'llm', channel: '硅基流动' },
      
      // SOLAR系列
      { provider: 'SOLAR', name: 'upstage/SOLAR-10.7B-Instruct-v1.0', label: 'SOLAR 10.7B', type: 'llm', channel: '硅基流动' },
      { provider: 'SOLAR', name: 'upstage/SOLAR-10.7B-v1.0', label: 'SOLAR 10.7B Base', type: 'llm', channel: '硅基流动' },
      
      // Dolphin系列
      { provider: 'DOLPHIN', name: 'cognitivecomputations/dolphin-2.9.1-llama-3-70b', label: 'Dolphin 2.9.1 Llama3 70B', type: 'llm', channel: '硅基流动' },
      { provider: 'DOLPHIN', name: 'cognitivecomputations/dolphin-2.8-mistral-7b-v02', label: 'Dolphin 2.8 Mistral 7B', type: 'llm', channel: '硅基流动' },
      { provider: 'DOLPHIN', name: 'cognitivecomputations/dolphin-2.6-mixtral-8x7b', label: 'Dolphin 2.6 Mixtral', type: 'llm', channel: '硅基流动' },
      
      // === OpenAI兼容渠道 ===
      { provider: 'OPENAI', name: 'gpt-4-turbo', label: 'GPT-4 Turbo', type: 'llm', channel: 'OpenAI' },
      { provider: 'OPENAI', name: 'gpt-4-turbo-preview', label: 'GPT-4 Turbo Preview', type: 'llm', channel: 'OpenAI' },
      { provider: 'OPENAI', name: 'gpt-4-1106-preview', label: 'GPT-4 1106 Preview', type: 'llm', channel: 'OpenAI' },
      { provider: 'OPENAI', name: 'gpt-4', label: 'GPT-4', type: 'llm', channel: 'OpenAI' },
      { provider: 'OPENAI', name: 'gpt-4-32k', label: 'GPT-4 32K', type: 'llm', channel: 'OpenAI' },
      { provider: 'OPENAI', name: 'gpt-4o', label: 'GPT-4o', type: 'llm', channel: 'OpenAI' },
      { provider: 'OPENAI', name: 'gpt-4o-mini', label: 'GPT-4o Mini', type: 'llm', channel: 'OpenAI' },
      { provider: 'OPENAI', name: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', type: 'llm', channel: 'OpenAI' },
      { provider: 'OPENAI', name: 'gpt-3.5-turbo-16k', label: 'GPT-3.5 Turbo 16K', type: 'llm', channel: 'OpenAI' },
      { provider: 'OPENAI', name: 'gpt-3.5-turbo-1106', label: 'GPT-3.5 Turbo 1106', type: 'llm', channel: 'OpenAI' },
      
      // === Claude系列 ===
      { provider: 'ANTHROPIC', name: 'claude-3-opus-20240229', label: 'Claude 3 Opus', type: 'llm', channel: 'Anthropic' },
      { provider: 'ANTHROPIC', name: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet', type: 'llm', channel: 'Anthropic' },
      { provider: 'ANTHROPIC', name: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku', type: 'llm', channel: 'Anthropic' },
      { provider: 'ANTHROPIC', name: 'claude-3.5-sonnet-20241022', label: 'Claude 3.5 Sonnet', type: 'llm', channel: 'Anthropic' },
      { provider: 'ANTHROPIC', name: 'claude-2.1', label: 'Claude 2.1', type: 'llm', channel: 'Anthropic' },
      { provider: 'ANTHROPIC', name: 'claude-2.0', label: 'Claude 2.0', type: 'llm', channel: 'Anthropic' },
      { provider: 'ANTHROPIC', name: 'claude-instant-1.2', label: 'Claude Instant 1.2', type: 'llm', channel: 'Anthropic' },
      
      // === 视觉模型 (非LLM) ===
      { provider: 'VISION', name: 'stable-diffusion-3-medium', label: 'Stable Diffusion 3', type: 'vision', channel: '硅基流动' },
      { provider: 'VISION', name: 'stable-diffusion-xl-base-1.0', label: 'SDXL Base', type: 'vision', channel: '硅基流动' },
      { provider: 'VISION', name: 'stable-diffusion-2-1', label: 'SD 2.1', type: 'vision', channel: '硅基流动' },
      { provider: 'VISION', name: 'playground-v2.5-1024px', label: 'Playground v2.5', type: 'vision', channel: '硅基流动' },
      { provider: 'VISION', name: 'flux.1-schnell', label: 'FLUX.1 Schnell', type: 'vision', channel: '硅基流动' },
      { provider: 'VISION', name: 'flux.1-dev', label: 'FLUX.1 Dev', type: 'vision', channel: '硅基流动' },
      
      // === 嵌入模型 ===
      { provider: 'EMBED', name: 'BAAI/bge-large-zh-v1.5', label: 'BGE Large 中文', type: 'embedding', channel: '硅基流动' },
      { provider: 'EMBED', name: 'BAAI/bge-m3', label: 'BGE M3', type: 'embedding', channel: '硅基流动' },
      { provider: 'EMBED', name: 'jinaai/jina-embeddings-v2-base-zh', label: 'Jina v2 中文', type: 'embedding', channel: '硅基流动' },
      
      // === 语音模型 ===
      { provider: 'AUDIO', name: 'FunAudioLLM/CosyVoice-300M-SFT', label: 'CosyVoice 300M', type: 'audio', channel: '硅基流动' },
      { provider: 'AUDIO', name: 'fishaudio/fish-speech-1.5', label: 'Fish Speech 1.5', type: 'audio', channel: '硅基流动' }
    ])
    */

    // 设置默认选中（只在没有保存的模型时才使用）
    const setDefaultSelection = () => {
      // 不再自动设置默认选择，让用户自己选择
      if (selectedModels.value.size === 0) {
        console.log('没有已保存的模型选择')
      }
    }
    
    const filteredModels = computed(() => {
      let models = [...allModels.value]  // 创建副本，避免修改原数组
      
      console.log(`[过滤开始] 原始模型数: ${models.length}, allModels长度: ${allModels.value.length}`)
      
      // 如果没有模型，直接返回空数组
      if (models.length === 0) {
        console.log('[警告] allModels为空！')
        return []
      }

      // 1. LLM筛选（根据开关）
      if (onlyLLM.value) {
        const beforeFilter = models.length
        models = models.filter(m => {
          // 更宽松的判断，type可能是undefined或其他值
          const typeOk = !m.type || m.type === 'llm' || (typeof m.type === 'string' && m.type.toLowerCase() === 'llm')
          return typeOk
        })
        console.log(`[LLM筛选] 筛选前: ${beforeFilter}, 筛选后: ${models.length}`)
      }

      // 2. 品牌筛选（始终生效）
      if (currentBrand.value && currentBrand.value !== 'all') {
        const beforeBrand = models.length
        const brand = currentBrand.value.toLowerCase()
        models = models.filter(m => {
          if (!m.provider) {
            console.log(`[品牌筛选] 模型没有provider字段:`, m.name)
            return false
          }
          const provider = (m.provider || '').toLowerCase()
          const name = (m.name || '').toLowerCase()
          
          // 优化：减少不必要的计算
          if (brand === 'gemini') return provider === 'gemini'
          if (brand === 'deepseek') return provider === 'deepseek' || name.includes('deepseek')
          if (brand === 'qwen') return provider === 'qwen' || name.includes('qwen')
          if (brand === 'llama') return provider === 'llama' || name.includes('llama')
          if (brand === 'mistral') return provider === 'mistral' || name.includes('mistral')
          if (brand === 'yi') return provider === 'yi' || name.includes('yi-')
          if (brand === 'glm') return provider === 'glm' || name.includes('glm')
          return true
        })
        console.log(`[品牌筛选] 品牌: '${brand}', 筛选前: ${beforeBrand}, 筛选后: ${models.length}`)
      }

      // 3. 搜索过滤
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        const beforeSearch = models.length
        models = models.filter(m => {
          // 优化：短路评估
          const label = m.label.toLowerCase()
          if (label.includes(query)) return true
          const name = m.name.toLowerCase()
          if (name.includes(query)) return true
          return m.provider.toLowerCase().includes(query)
        })
        console.log(`[搜索过滤] 搜索词: '${query}', 筛选前: ${beforeSearch}, 筛选后: ${models.length}`)
      }

      console.log(`[过滤结果] 最终模型数: ${models.length}`)
      return models
    })
    

    const isSelected = (model) => {
      return selectedModels.value.has(model.name)
    }

    const toggleModel = (model) => {
      if (isSelected(model)) {
        selectedModels.value.delete(model.name)
      } else {
        selectedModels.value.add(model.name)
      }
    }

    const selectAll = () => {
      filteredModels.value.forEach(model => {
        selectedModels.value.add(model.name)
      })
    }

    const invertSelection = () => {
      const newSelection = new Set()
      filteredModels.value.forEach(model => {
        if (!selectedModels.value.has(model.name)) {
          newSelection.add(model.name)
        }
      })
      selectedModels.value = newSelection
    }

    const clearSelection = () => {
      selectedModels.value.clear()
    }

    const close = () => {
      // 恢复背景滚动
      document.body.style.overflow = ''
      emit('close')
    }

    const saveSelection = () => {
      emit('save', Array.from(selectedModels.value))
      close()
    }

    // 监听visible属性，当模态框显示时加载配置
    watch(() => props.visible, async (newVal) => {
      if (newVal) {
        // 阻止背景滚动
        document.body.style.overflow = 'hidden'
        
        // 并行加载，提高速度
        const promises = [
          loadModels(),       // 加载模型（有缓存）
          loadModelConfigs()  // 加载配置
        ]
        await Promise.all(promises)
        setDefaultSelection()
        
        // 加载完成后检查状态
        console.log(`[模态框打开] allModels数量: ${allModels.value.length}`)
        console.log(`[模态框打开] filteredModels数量: ${filteredModels.value.length}`)
      } else {
        // 恢复背景滚动
        document.body.style.overflow = ''
      }
    })
    
    
    // 组件挂载时预加载
    onMounted(() => {
      // 在后台预加载模型列表，不阻塞页面
      setTimeout(() => {
        loadModels()
      }, 100)
    })
    
    // 组件卸载时清理
    onUnmounted(() => {
      // 确保恢复body滚动
      document.body.style.overflow = ''
    })

    return {
      onlyLLM,
      currentBrand,
      searchQuery,
      selectedModels,
      brandTypes,
      allModels,
      filteredModels,
      isSelected,
      toggleModel,
      selectAll,
      invertSelection,
      clearSelection,
      close,
      saveSelection,
      loading,
      loadModels,
      setDefaultSelection
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.modal-container {
  background: #1e293b;
  border-radius: 0.75rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  width: 90%;
  max-width: 800px;
  min-height: 500px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #334155;
}

.modal-title {
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
}

.close-btn {
  color: #94a3b8;
  font-size: 2rem;
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
}

.close-btn:hover {
  color: white;
}

.modal-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 1rem 1.5rem;
}

/* 搜索和控制栏 */
.search-control-bar {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
  align-items: center;
}

.search-input {
  flex: 1;
  padding: 0.625rem 0.875rem;
  background: #0f172a;
  border: 1px solid #475569;
  border-radius: 0.5rem;
  color: white;
  font-size: 0.875rem;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.2);
}

.search-input::placeholder {
  color: #64748b;
}

.control-buttons {
  display: flex;
  gap: 0.5rem;
}

.control-btn {
  padding: 0.5rem 1rem;
  background: #475569;
  color: #e2e8f0;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.control-btn:hover {
  background: #64748b;
}

.search-control-bar .save-btn {
  padding: 0.5rem 1rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.search-control-bar .save-btn:hover {
  background: #059669;
}

/* LLM筛选开关容器 */
.filter-toggle-container {
  margin-bottom: 1rem;
}

/* 筛选开关 */
.filter-toggle {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
}

.filter-toggle input[type="checkbox"] {
  display: none;
}

.toggle-slider {
  position: relative;
  width: 40px;
  height: 20px;
  background: #334155;
  border-radius: 10px;
  transition: background 0.3s;
  margin-right: 0.5rem;
}

.toggle-slider:before {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  background: white;
  border-radius: 50%;
  top: 2px;
  left: 2px;
  transition: transform 0.3s;
}

.filter-toggle input:checked + .toggle-slider {
  background: #3b82f6;
}

.filter-toggle input:checked + .toggle-slider:before {
  transform: translateX(20px);
}

.toggle-label {
  color: #94a3b8;
  font-size: 0.875rem;
  user-select: none;
}

/* 品牌筛选按钮 */
.brand-filters {
  display: flex;
  gap: 0.375rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.brand-btn {
  padding: 0.375rem 0.875rem;
  background: #334155;
  color: #94a3b8;
  border: 1px solid #475569;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.75rem;
  font-weight: 500;
}

.brand-btn:hover {
  background: #475569;
  color: #e2e8f0;
  border-color: #64748b;
}

.brand-btn.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

/* 模型列表 */

.model-list {
  flex: 1;
  min-height: 200px;
  max-height: calc(60vh - 200px); /* 动态高度，确保适应窗口大小 */
  overflow-y: auto;
  overflow-x: hidden;
  background: #0f172a;
  border-radius: 0.5rem;
  padding: 0.5rem;
  /* 性能优化 */
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch; /* iOS平滑滚动 */
}

/* 自定义滚动条 */
.model-list::-webkit-scrollbar {
  width: 8px;
}

.model-list::-webkit-scrollbar-track {
  background: #1e293b;
  border-radius: 4px;
}

.model-list::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 4px;
}

.model-list::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}

.model-item {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  min-height: 60px;
  background: #1e293b;
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.model-item:hover {
  background: #334155;
  border-color: #3b82f6;
}

.model-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
}

.model-checkbox {
  width: 1.25rem;
  height: 1.25rem;
  cursor: pointer;
}

.model-name {
  color: #e2e8f0;
  font-weight: 500;
  margin-bottom: 0.125rem;
}

.model-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
}

.model-provider {
  color: #64748b;
}

.model-channel {
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.modal-footer {
  padding: 0.75rem 1rem;
  border-top: 1px solid #334155;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: #1e293b;
  position: relative;
  z-index: 10;
}

.selection-info {
  color: #94a3b8;
  font-size: 0.75rem;
}

/* 滚动条样式 */

.model-list::-webkit-scrollbar-track {
  background: #1e293b;
  border-radius: 3px;
}

.model-list::-webkit-scrollbar {
  width: 6px;
}


.model-list::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 3px;
}

.model-list::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}
</style>
