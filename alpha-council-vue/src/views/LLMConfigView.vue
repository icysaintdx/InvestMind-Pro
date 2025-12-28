<template>
  <div class="llm-config-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>⚙️ 交易LLM配置</h1>
      <p class="subtitle">配置策略选择、交易决策、市场分析的LLM模型</p>
      <p class="subtitle-note">⚠️ 注意：这是专门用于新功能的LLM配置，与21个智能分析体的配置完全独立</p>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>加载配置中...</p>
    </div>

    <!-- 配置列表 -->
    <div v-else class="config-list">
      <div 
        v-for="task in tasks" 
        :key="task.task_name"
        class="config-card"
      >
        <div class="card-header">
          <div class="task-info">
            <h3>{{ task.display_name || task.task_name }}</h3>
            <span class="task-category">{{ task.category || '未分类' }}</span>
          </div>
          <div class="task-status">
            <span :class="['status-badge', task.enabled ? 'enabled' : 'disabled']">
              {{ task.enabled ? '✅ 启用' : '❌ 禁用' }}
            </span>
          </div>
        </div>

        <div class="card-body">
          <!-- 当前配置 -->
          <div class="config-section">
            <h4>当前配置</h4>
            <div class="config-grid">
              <div class="config-item">
                <label>提供商</label>
                <div class="config-value">{{ task.provider || 'N/A' }}</div>
              </div>
              <div class="config-item">
                <label>模型</label>
                <div class="config-value">{{ task.model || 'N/A' }}</div>
              </div>
              <div class="config-item">
                <label>温度</label>
                <div class="config-value">{{ task.temperature || 'N/A' }}</div>
              </div>
              <div class="config-item">
                <label>最大Tokens</label>
                <div class="config-value">{{ task.max_tokens || 'N/A' }}</div>
              </div>
              <div class="config-item">
                <label>超时(秒)</label>
                <div class="config-value">{{ task.timeout || 'N/A' }}</div>
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="card-actions">
            <button @click="editTask(task)" class="btn-primary-small">
              ✏️ 编辑
            </button>
            <button @click="testTask(task)" class="btn-secondary-small">
              🧪 测试
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑对话框 -->
    <div v-if="showEditDialog" class="modal-overlay" @click="showEditDialog = false">
      <div class="modal-content" @click.stop>
        <h3>编辑配置: {{ editingTask?.display_name }}</h3>

        <div class="form-group">
          <label>提供商</label>
          <select v-model="editForm.provider" class="input-field">
            <option value="">不修改</option>
            <option value="siliconflow">SiliconFlow</option>
            <option value="deepseek">DeepSeek</option>
            <option value="qwen">通义千问</option>
            <option value="gemini">Gemini</option>
          </select>
        </div>

        <div class="form-group">
          <label>模型</label>
          <input 
            v-model="editForm.model" 
            placeholder="如：deepseek-chat"
            class="input-field"
          />
          <small>留空表示不修改</small>
        </div>

        <div class="form-group">
          <label>温度 (0-2)</label>
          <input 
            v-model.number="editForm.temperature" 
            type="number"
            step="0.1"
            min="0"
            max="2"
            placeholder="0.7"
            class="input-field"
          />
          <small>控制输出的随机性，越高越随机</small>
        </div>

        <div class="form-group">
          <label>最大Tokens</label>
          <input 
            v-model.number="editForm.max_tokens" 
            type="number"
            placeholder="2000"
            class="input-field"
          />
        </div>

        <div class="form-group">
          <label>超时时间(秒)</label>
          <input 
            v-model.number="editForm.timeout" 
            type="number"
            placeholder="60"
            class="input-field"
          />
        </div>

        <div class="form-group">
          <label>
            <input type="checkbox" v-model="editForm.enabled" />
            启用此任务
          </label>
        </div>

        <div class="modal-actions">
          <button @click="saveConfig" class="btn-primary">保存</button>
          <button @click="showEditDialog = false" class="btn-secondary">取消</button>
        </div>
      </div>
    </div>

    <!-- 测试对话框 -->
    <div v-if="showTestDialog" class="modal-overlay" @click="showTestDialog = false">
      <div class="modal-content" @click.stop>
        <h3>测试配置: {{ testingTask?.display_name }}</h3>
        
        <div class="test-info">
          <p>这将使用当前配置发送一个测试请求</p>
          <p>测试提示词: "你好，请简单介绍一下你自己"</p>
        </div>

        <div v-if="testResult" class="test-result">
          <h4>测试结果:</h4>
          <div v-if="testResult.success" class="result-success">
            <p>✅ 测试成功！</p>
            <pre>{{ testResult.response }}</pre>
          </div>
          <div v-else class="result-error">
            <p>❌ 测试失败</p>
            <pre>{{ testResult.error }}</pre>
          </div>
        </div>

        <div class="modal-actions">
          <button @click="runTest" class="btn-primary" :disabled="testing">
            {{ testing ? '测试中...' : '开始测试' }}
          </button>
          <button @click="showTestDialog = false" class="btn-secondary">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import API_BASE_URL from '@/config/api.js'

export default {
  name: 'LLMConfigView',
  setup() {
    const API_BASE = `${API_BASE_URL}/api/trading-llm-config`
    
    // 状态
    const loading = ref(true)
    const tasks = ref([])
    const showEditDialog = ref(false)
    const showTestDialog = ref(false)
    const editingTask = ref(null)
    const testingTask = ref(null)
    const testing = ref(false)
    const testResult = ref(null)
    
    // 编辑表单
    const editForm = reactive({
      provider: '',
      model: '',
      temperature: null,
      max_tokens: null,
      timeout: null,
      enabled: true
    })
    
    // 加载所有任务配置
    const loadTasks = async () => {
      try {
        loading.value = true
        console.log('🔍 加载LLM配置...')
        
        const response = await axios.get(`${API_BASE}/tasks`)
        console.log('📦 API响应:', response.data)
        
        if (response.data.success) {
          tasks.value = response.data.tasks
          console.log(`✅ 加载了${tasks.value.length}个任务配置`)
        }
      } catch (error) {
        console.error('❌ 加载配置失败:', error)
        alert('加载配置失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        loading.value = false
      }
    }
    
    // 编辑任务
    const editTask = (task) => {
      editingTask.value = task
      // 重置表单
      editForm.provider = task.provider || ''
      editForm.model = task.model || ''
      editForm.temperature = task.temperature
      editForm.max_tokens = task.max_tokens
      editForm.timeout = task.timeout
      editForm.enabled = task.enabled !== false
      
      showEditDialog.value = true
    }
    
    // 保存配置
    const saveConfig = async () => {
      try {
        // 只发送有值的字段
        const updates = {}
        if (editForm.provider) updates.provider = editForm.provider
        if (editForm.model) updates.model = editForm.model
        if (editForm.temperature !== null) updates.temperature = editForm.temperature
        if (editForm.max_tokens) updates.max_tokens = editForm.max_tokens
        if (editForm.timeout) updates.timeout = editForm.timeout
        updates.enabled = editForm.enabled
        
        console.log('💾 保存配置:', updates)
        
        const response = await axios.put(
          `${API_BASE}/tasks/${editingTask.value.task_name}`,
          updates
        )
        
        if (response.data.success) {
          alert('配置保存成功！')
          showEditDialog.value = false
          await loadTasks()
        }
      } catch (error) {
        console.error('❌ 保存失败:', error)
        alert('保存失败: ' + (error.response?.data?.detail || error.message))
      }
    }
    
    // 测试任务
    const testTask = (task) => {
      testingTask.value = task
      testResult.value = null
      showTestDialog.value = true
    }
    
    // 运行测试
    const runTest = async () => {
      try {
        testing.value = true
        testResult.value = null
        
        // 这里应该调用一个测试API
        // 暂时模拟测试结果
        await new Promise(resolve => setTimeout(resolve, 2000))
        
        testResult.value = {
          success: true,
          response: '你好！我是一个AI助手，专门用于股票分析和投资建议。我可以帮助你分析市场趋势、评估投资风险、提供交易策略建议等。'
        }
      } catch (error) {
        testResult.value = {
          success: false,
          error: error.message
        }
      } finally {
        testing.value = false
      }
    }
    
    // 初始化
    onMounted(() => {
      loadTasks()
    })
    
    return {
      loading,
      tasks,
      showEditDialog,
      showTestDialog,
      editingTask,
      testingTask,
      testing,
      testResult,
      editForm,
      loadTasks,
      editTask,
      saveConfig,
      testTask,
      runTest
    }
  }
}
</script>

<style scoped>
.llm-config-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 28px;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #999;
  margin: 0 0 8px 0;
}

.subtitle-note {
  color: #ffc107;
  margin: 0;
  font-size: 13px;
  background: rgba(255, 193, 7, 0.1);
  padding: 8px 12px;
  border-radius: 4px;
  border-left: 3px solid #ffc107;
}

.loading-state {
  text-align: center;
  padding: 60px 20px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.config-list {
  display: grid;
  gap: 16px;
}

.config-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
}

.task-info h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
}

.task-category {
  display: inline-block;
  padding: 2px 8px;
  background: #e6f7ff;
  color: #1890ff;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.enabled {
  background: #f6ffed;
  color: #52c41a;
}

.status-badge.disabled {
  background: #fff1f0;
  color: #ff4d4f;
}

.card-body {
  padding: 20px;
}

.config-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #666;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.config-item label {
  display: block;
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.config-value {
  font-size: 14px;
  font-weight: 500;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.btn-primary-small,
.btn-secondary-small {
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary-small {
  background: #1890ff;
  color: white;
  border: none;
}

.btn-primary-small:hover {
  background: #40a9ff;
}

.btn-secondary-small {
  background: white;
  color: #333;
  border: 1px solid #d9d9d9;
}

.btn-secondary-small:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 24px;
  border-radius: 12px;
  min-width: 500px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.input-field {
  width: 100%;
  padding: 10px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
}

.form-group small {
  display: block;
  margin-top: 4px;
  color: #999;
  font-size: 12px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn-primary,
.btn-secondary {
  padding: 10px 24px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: #1890ff;
  color: white;
  border: none;
}

.btn-primary:hover {
  background: #40a9ff;
}

.btn-primary:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  color: #333;
  border: 1px solid #d9d9d9;
}

.btn-secondary:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.test-info {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.test-result {
  margin-top: 16px;
  padding: 16px;
  border-radius: 8px;
}

.result-success {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
}

.result-error {
  background: #fff1f0;
  border: 1px solid #ffccc7;
}

.test-result pre {
  margin-top: 8px;
  padding: 12px;
  background: white;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.6;
}
</style>
