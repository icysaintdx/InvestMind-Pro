<template>
  <div v-if="visible" class="modal-overlay" @click="handleClose">
    <div class="config-panel" @click.stop>
      <!-- 头部 -->
      <div class="panel-header">
        <h2 class="panel-title">
          <span class="icon">⚙️</span>
          智能体配置管理
        </h2>
        <button @click="handleClose" class="close-btn">✕</button>
      </div>

      <!-- 快速配置方案 -->
      <div class="quick-profiles">
        <h3 class="section-title">快速配置方案 <span style="color: red; font-size: 12px;">(current: {{ currentProfile }})</span></h3>
        <div class="profile-buttons">
          <button 
            v-for="(profile, key) in profiles" 
            :key="key"
            @click="applyProfile(key)"
            :class="['profile-btn', { active: currentProfile === key }]"
          >
            <div class="profile-icon">{{ getProfileIcon(key) }}</div>
            <div class="profile-info">
              <div class="profile-name">{{ profile.name }}</div>
              <div class="profile-desc">{{ profile.description }}</div>
            </div>
          </button>
          <!-- 自定义配置按钮 -->
          <button 
            @click="applyCustomProfile"
            :class="['profile-btn', { active: currentProfile === 'custom' }]"
          >
            <div class="profile-icon">🎯</div>
            <div class="profile-info">
              <div class="profile-name">自定义配置</div>
              <div class="profile-desc">手动选择启用的智能体</div>
            </div>
          </button>
        </div>
      </div>

      <!-- 详细配置 -->
      <div class="detailed-config">
        <h3 class="section-title">详细配置</h3>
        
        <!-- 核心智能体 -->
        <div class="agent-group core">
          <div class="group-header" @click="toggleGroup('core')">
            <span class="collapse-icon">{{ collapsedGroups.core ? '▶' : '▼' }}</span>
            <span class="group-icon">🔴</span>
            <span class="group-title">核心智能体（必需）</span>
            <span class="group-badge">不可禁用</span>
          </div>
          <div v-show="!collapsedGroups.core" class="agent-list">
            <div v-for="agent in coreAgents" :key="agent.id" class="agent-item disabled">
              <label class="agent-label">
                <input type="checkbox" :checked="true" disabled />
                <span class="agent-icon">{{ agent.icon }}</span>
                <span class="agent-name">{{ agent.name }}</span>
                <span class="agent-badge core-badge">必需</span>
              </label>
              <div class="agent-desc">{{ agent.description }}</div>
            </div>
          </div>
        </div>

        <!-- 重要智能体 -->
        <div class="agent-group important">
          <div class="group-header" @click="toggleGroup('important')">
            <span class="collapse-icon">{{ collapsedGroups.important ? '▶' : '▼' }}</span>
            <span class="group-icon">🟡</span>
            <span class="group-title">重要智能体（推荐）</span>
            <span class="group-count">{{ enabledImportantCount }}/{{ importantAgents.length }}</span>
          </div>
          <div v-show="!collapsedGroups.important" class="agent-list">
            <div v-for="agent in importantAgents" :key="agent.id" class="agent-item">
              <label class="agent-label">
                <input 
                  type="checkbox" 
                  v-model="config[agent.id]"
                  @change="handleToggle()"
                />
                <span class="agent-icon">{{ agent.icon }}</span>
                <span class="agent-name">{{ agent.name }}</span>
                <span v-if="agent.dependencies && agent.dependencies.length > 0" class="dep-indicator" :title="`依赖: ${agent.dependencies.join(', ')}`">
                  🔗
                </span>
              </label>
              <div class="agent-desc">{{ agent.description }}</div>
            </div>
          </div>
        </div>

        <!-- 可选智能体 -->
        <div class="agent-group optional">
          <div class="group-header" @click="toggleGroup('optional')">
            <span class="collapse-icon">{{ collapsedGroups.optional ? '▶' : '▼' }}</span>
            <span class="group-icon">🟢</span>
            <span class="group-title">可选智能体</span>
            <span class="group-count">{{ enabledOptionalCount }}/{{ optionalAgents.length }}</span>
          </div>
          <div v-show="!collapsedGroups.optional" class="agent-list">
            <div v-for="agent in optionalAgents" :key="agent.id" class="agent-item">
              <label class="agent-label">
                <input 
                  type="checkbox" 
                  v-model="config[agent.id]"
                  @change="handleToggle()"
                />
                <span class="agent-icon">{{ agent.icon }}</span>
                <span class="agent-name">{{ agent.name }}</span>
              </label>
              <div class="agent-desc">{{ agent.description }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 影响预览 -->
      <div v-if="impact" class="impact-preview">
        <h3 class="section-title">配置影响预览</h3>
        <div class="impact-stats">
          <div class="stat-item">
            <div class="stat-label">启用智能体</div>
            <div class="stat-value">{{ impact.enabled_count }}/{{ impact.total_agents }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">预计时间</div>
            <div class="stat-value">{{ impact.estimated_time }}秒</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">分析质量</div>
            <div class="stat-value" :class="getQualityClass(impact.quality_score)">
              {{ impact.quality_score }}%
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-label">效率比</div>
            <div class="stat-value">{{ impact.efficiency_ratio }}</div>
          </div>
        </div>
      </div>

      <!-- 成功消息 -->
      <div v-if="successMessage" class="success-message">
        <div class="success-item">
          ✅ {{ successMessage }}
        </div>
      </div>

      <!-- 警告信息 -->
      <div v-if="warnings.length > 0" class="warnings">
        <div v-for="(warning, index) in warnings" :key="index" class="warning-item">
          ⚠️ {{ warning }}
        </div>
      </div>

      <!-- 底部按钮 -->
      <div class="panel-footer">
        <button @click="handleClose" class="btn btn-cancel">取消</button>
        <button @click="handleReset" class="btn btn-reset">重置</button>
        <button @click="handleSave" class="btn btn-save" :disabled="saving">
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import axios from 'axios'

export default {
  name: 'AgentConfigPanel',
  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'save'],
  setup(props, { emit }) {
    const config = ref({})
    const profiles = ref({})
    const currentProfile = ref(null)
    const impact = ref(null)
    const warnings = ref([])
    const successMessage = ref('')
    const saving = ref(false)
    const allAgents = ref([])
    
    // 折叠状态
    const collapsedGroups = ref({
      core: false,
      important: false,
      optional: false
    })

    // 按优先级分组的智能体
    const coreAgents = computed(() => 
      allAgents.value.filter(a => a.priority === 'core')
    )
    const importantAgents = computed(() => 
      allAgents.value.filter(a => a.priority === 'important')
    )
    const optionalAgents = computed(() => 
      allAgents.value.filter(a => a.priority === 'optional')
    )

    // 统计启用数量
    const enabledImportantCount = computed(() => 
      importantAgents.value.filter(a => config.value[a.id]).length
    )
    const enabledOptionalCount = computed(() => 
      optionalAgents.value.filter(a => config.value[a.id]).length
    )

    // 加载配置
    const loadConfig = async () => {
      try {
        // 加载所有智能体
        const agentsRes = await axios.get('/api/agents/list')
        allAgents.value = agentsRes.data.agents

        // 加载当前配置
        const configRes = await axios.get('/api/agents/config/current')
        config.value = configRes.data.config
        impact.value = configRes.data.impact

        // 加载配置方案
        const profilesRes = await axios.get('/api/agents/config/profiles')
        profiles.value = profilesRes.data.profiles
        
        // ✅ 检测当前配置对应哪个方案
        detectCurrentProfile()
      } catch (error) {
        console.error('加载配置失败:', error)
      }
    }
    
    // 检测当前配置对应的方案
    const detectCurrentProfile = () => {
      console.log('[AgentConfig] 检测当前配置对应的方案')
      console.log('[AgentConfig] profiles.value:', profiles.value)
      console.log('[AgentConfig] config.value:', config.value)
      
      // 遍历所有预设方案，看是否匹配
      for (const [key, profile] of Object.entries(profiles.value)) {
        console.log(`[AgentConfig] 检查方案: ${key}`, profile)
        // ✅ 修复：使用 profile.enabled 而不是 profile.agents
        const profileConfig = profile.enabled || profile.agents || {}
        if (isConfigMatchProfile(config.value, profileConfig)) {
          console.log(`[AgentConfig] 匹配到方案: ${key}`)
          currentProfile.value = key
          return
        }
      }
      // 如果没有匹配任何预设方案，设为自定义
      console.log('[AgentConfig] 没有匹配任何方案，设为自定义')
      currentProfile.value = 'custom'
    }
    
    // 判断配置是否匹配方案
    const isConfigMatchProfile = (currentConfig, profileConfig) => {
      console.log('[AgentConfig] 匹配检查 - profileConfig:', profileConfig)
      
      if (!profileConfig) {
        console.log('[AgentConfig] profileConfig 为空')
        return false
      }
      
      // 获取所有非核心智能体的 ID
      const nonCoreAgents = allAgents.value
        .filter(a => a.priority !== 'core')
        .map(a => a.id)
      
      console.log('[AgentConfig] 非核心智能体:', nonCoreAgents)
      
      // 检查每个非核心智能体的状态是否一致
      for (const agentId of nonCoreAgents) {
        const isEnabledInCurrent = currentConfig[agentId] === true
        // ✅ 修复：profileConfig 是对象而不是数组
        const isEnabledInProfile = profileConfig[agentId] === true
        
        if (isEnabledInCurrent !== isEnabledInProfile) {
          console.log(`[AgentConfig] 不匹配: ${agentId}, current=${isEnabledInCurrent}, profile=${isEnabledInProfile}`)
          return false
        }
      }
      
      console.log('[AgentConfig] 匹配成功')
      return true
    }

    // 应用配置方案
    const applyProfile = async (profileKey) => {
      try {
        const res = await axios.post(`/api/agents/config/profile/${profileKey}`)
        config.value = res.data.config
        impact.value = res.data.impact
        currentProfile.value = profileKey
        warnings.value = []
      } catch (error) {
        console.error('应用方案失败:', error)
        warnings.value = [error.response?.data?.detail || '应用方案失败']
      }
    }

    // 处理智能体切换
    const handleToggle = async () => {
      try {
        // 验证配置
        const res = await axios.post('/api/agents/config/validate', {
          enabled: config.value
        })

        warnings.value = res.data.warnings || []

        // 更新影响预览（基于当前修改的配置）
        updateImpactLocal()

        // ✅ 重新检测当前配置对应的方案
        detectCurrentProfile()
      } catch (error) {
        console.error('验证配置失败:', error)
      }
    }

    // 本地计算影响预览（不依赖后端保存的配置）
    const updateImpactLocal = () => {
      // 核心智能体始终启用
      const coreCount = coreAgents.value.length

      // 计算重要智能体中启用的数量
      const enabledImportant = importantAgents.value.filter(a => config.value[a.id] === true).length

      // 计算可选智能体中启用的数量
      const enabledOptional = optionalAgents.value.filter(a => config.value[a.id] === true).length

      // 总启用数 = 核心 + 启用的重要 + 启用的可选
      const totalEnabled = coreCount + enabledImportant + enabledOptional

      // 总智能体数
      const totalAgents = allAgents.value.length

      // 计算预计时间（每个智能体约5-8秒）
      const estimatedTime = totalEnabled * 6

      // 计算质量分数
      const qualityScore = totalAgents > 0 ? Math.round((totalEnabled / totalAgents) * 100) : 0

      // 计算效率比
      const efficiencyRatio = estimatedTime > 0 ? (qualityScore / (estimatedTime / 10)).toFixed(1) : '0.0'

      impact.value = {
        enabled_count: totalEnabled,
        total_agents: totalAgents,
        estimated_time: estimatedTime,
        quality_score: qualityScore,
        efficiency_ratio: efficiencyRatio
      }

      console.log(`[配置面板] 启用统计: 核心=${coreCount}, 重要=${enabledImportant}, 可选=${enabledOptional}, 总计=${totalEnabled}/${totalAgents}`)
    }

    // 更新影响预览（从后端获取）
    // eslint-disable-next-line no-unused-vars
    const updateImpact = async () => {
      try {
        const res = await axios.get('/api/agents/config/impact')
        impact.value = res.data.impact
      } catch (error) {
        console.error('获取影响失败:', error)
      }
    }

    // 保存配置
    const handleSave = async () => {
      saving.value = true
      try {
        const res = await axios.post('/api/agents/config/apply', {
          enabled: config.value
        })
        
        if (res.data.success) {
          emit('save', config.value)
          emit('close')
          
          // 显示成功提示
          successMessage.value = '配置已保存，正在刷新页面...'
          warnings.value = []
          
          // 延迟刷新页面，让用户看到成功提示
          setTimeout(() => {
            window.location.reload()
          }, 1000)
        }
      } catch (error) {
        console.error('保存配置失败:', error)
        warnings.value = [
          error.response?.data?.detail?.message || '保存配置失败'
        ]
      } finally {
        saving.value = false
      }
    }

    // 重置配置
    const handleReset = async () => {
      try {
        // 先重置到默认配置
        const res = await axios.post('/api/agents/config/reset')
        
        if (res.data.success) {
          loadConfig()
          warnings.value = []
          
          // 显示成功提示
          successMessage.value = '配置已重置，正在刷新页面...'
          
          // 延迟刷新页面
          setTimeout(() => {
            window.location.reload()
          }, 1000)
        }
      } catch (error) {
        console.error('重置配置失败:', error)
        warnings.value = [
          error.response?.data?.detail?.message || '重置配置失败'
        ]
        
        // 即使API失败，也重新加载本地配置
        loadConfig()
        warnings.value = []
      }
    }
    
    // 切换分组折叠状态
    const toggleGroup = (groupName) => {
      collapsedGroups.value[groupName] = !collapsedGroups.value[groupName]
    }
    
    // 应用自定义配置
    const applyCustomProfile = () => {
      // 设置为自定义模式
      currentProfile.value = 'custom'
      // 保持当前配置不变，用户可以手动调整
      // 展开所有分组以便用户配置
      collapsedGroups.value.core = false
      collapsedGroups.value.important = false
      collapsedGroups.value.optional = false
      warnings.value = []
    }

    // 关闭面板
    const handleClose = () => {
      emit('close')
    }

    // 获取方案图标
    const getProfileIcon = (key) => {
      const icons = {
        minimal: '⚡',
        balanced: '⚖️',
        complete: '🎯'
      }
      return icons[key] || '📋'
    }

    // 获取质量等级样式
    const getQualityClass = (score) => {
      if (score >= 95) return 'excellent'
      if (score >= 85) return 'good'
      if (score >= 70) return 'fair'
      return 'poor'
    }

    // 监听visible变化
    watch(() => props.visible, (newVal) => {
      if (newVal) {
        loadConfig()
      }
    })

    return {
      config,
      profiles,
      currentProfile,
      impact,
      warnings,
      successMessage,
      saving,
      allAgents,
      coreAgents,
      importantAgents,
      optionalAgents,
      enabledImportantCount,
      enabledOptionalCount,
      collapsedGroups,
      applyProfile,
      applyCustomProfile,
      toggleGroup,
      handleToggle,
      handleSave,
      handleReset,
      handleClose,
      getProfileIcon,
      getQualityClass
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
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.config-panel {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 16px;
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* 美化滚动条 */
.config-panel::-webkit-scrollbar {
  width: 8px;
}

.config-panel::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.5);
  border-radius: 4px;
}

.config-panel::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 4px;
  transition: background 0.3s;
}

.config-panel::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, #60a5fa 0%, #3b82f6 100%);
}

/* Firefox 滚动条 */
.config-panel {
  scrollbar-width: thin;
  scrollbar-color: #3b82f6 rgba(15, 23, 42, 0.5);
}

/* 详细配置区域滚动条 */
.detailed-config::-webkit-scrollbar {
  width: 6px;
}

.detailed-config::-webkit-scrollbar-track {
  background: transparent;
}

.detailed-config::-webkit-scrollbar-thumb {
  background: rgba(59, 130, 246, 0.5);
  border-radius: 3px;
}

.detailed-config::-webkit-scrollbar-thumb:hover {
  background: rgba(59, 130, 246, 0.8);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.panel-title {
  font-size: 24px;
  font-weight: bold;
  color: white;
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
}

.icon {
  font-size: 28px;
}

.close-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: white;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 20px;
  transition: all 0.3s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #94a3b8;
  margin: 0 0 16px 0;
}

/* 快速配置方案 */
.quick-profiles {
  padding: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.profile-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.profile-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid transparent;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  text-align: left;
}

.profile-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(59, 130, 246, 0.5);
}

.profile-btn.active {
  background: rgba(59, 130, 246, 0.2);
  border-color: #3b82f6;
}

.profile-icon {
  font-size: 32px;
}

.profile-info {
  flex: 1;
}

.profile-name {
  font-size: 16px;
  font-weight: 600;
  color: white;
  margin-bottom: 4px;
}

.profile-desc {
  font-size: 13px;
  color: #94a3b8;
}

/* 详细配置 */
.detailed-config {
  padding: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.agent-group {
  margin-bottom: 24px;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  user-select: none;
}

.group-header:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateX(2px);
}

.collapse-icon {
  font-size: 14px;
  color: #94a3b8;
  transition: transform 0.3s;
  min-width: 16px;
  text-align: center;
}

.group-icon {
  font-size: 20px;
}

.group-title {
  font-size: 16px;
  font-weight: 600;
  color: white;
  flex: 1;
}

.group-badge, .group-count {
  font-size: 12px;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  color: #94a3b8;
}

.agent-list {
  display: grid;
  gap: 8px;
}

.agent-item {
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  transition: all 0.3s;
}

.agent-item:not(.disabled):hover {
  background: rgba(255, 255, 255, 0.08);
}

.agent-item.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.agent-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: white;
}

.agent-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.agent-label input[type="checkbox"]:disabled {
  cursor: not-allowed;
}

.agent-icon {
  font-size: 18px;
}

.agent-name {
  flex: 1;
  font-weight: 500;
}

.agent-badge {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
}

.dep-indicator {
  font-size: 14px;
  cursor: help;
}

.agent-desc {
  margin-top: 6px;
  margin-left: 26px;
  font-size: 12px;
  color: #64748b;
}

/* 影响预览 */
.impact-preview {
  padding: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.impact-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.stat-item {
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  text-align: center;
}

.stat-label {
  font-size: 13px;
  color: #94a3b8;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: white;
}

.stat-value.excellent { color: #10b981; }
.stat-value.good { color: #3b82f6; }
.stat-value.fair { color: #f59e0b; }
.stat-value.poor { color: #ef4444; }

/* 成功消息 */
.success-message {
  padding: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.success-item {
  color: #22c55e;
  font-size: 14px;
  line-height: 1.6;
  animation: fadeIn 0.3s ease;
}

/* 警告信息 */
.warnings {
  padding: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.warning-item {
  padding: 12px;
  background: rgba(245, 158, 11, 0.1);
  border-left: 3px solid #f59e0b;
  border-radius: 4px;
  color: #fbbf24;
  font-size: 14px;
  margin-bottom: 8px;
}

/* 底部按钮 */
.panel-footer {
  padding: 24px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-cancel {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.15);
}

.btn-reset {
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
}

.btn-reset:hover {
  background: rgba(245, 158, 11, 0.3);
}

.btn-save {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.btn-save:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
}

.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
