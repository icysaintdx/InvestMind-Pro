<template>
  <div v-if="visible" class="style-panel-container">
    <div class="style-panel">
      <!-- 头部 -->
      <div class="modal-header">
        <h2 class="modal-title">🎨 样式配置</h2>
        <button @click="close" class="close-btn">×</button>
      </div>
      
      <!-- 内容 -->
      <div class="modal-body">
        <!-- 卡片样式 -->
        <div class="config-section">
          <h3 class="section-title">智能体卡片样式</h3>
          
          <div class="config-item">
            <label class="config-label">卡片透明度</label>
            <div class="slider-container">
              <input 
                type="range" 
                v-model.number="localStyles.cardOpacity"
                min="0" 
                max="100" 
                step="5"
                class="style-slider"
              >
              <span class="value-display">{{ localStyles.cardOpacity }}%</span>
            </div>
            <div class="preview-box" :style="{ opacity: localStyles.cardOpacity / 100 }">
              预览效果
            </div>
          </div>

          <div class="config-item">
            <label class="config-label">卡片模糊度</label>
            <div class="slider-container">
              <input 
                type="range" 
                v-model.number="localStyles.cardBlur"
                min="0" 
                max="20" 
                step="1"
                class="style-slider"
              >
              <span class="value-display">{{ localStyles.cardBlur }}px</span>
            </div>
          </div>

          <div class="config-item">
            <label class="config-label">边框宽度</label>
            <div class="slider-container">
              <input 
                type="range" 
                v-model.number="localStyles.borderWidth"
                min="0" 
                max="5" 
                step="0.5"
                class="style-slider"
              >
              <span class="value-display">{{ localStyles.borderWidth }}px</span>
            </div>
          </div>
        </div>

        <!-- 背景样式 -->
        <div class="config-section">
          <h3 class="section-title">背景渐变设置</h3>
          
          <div class="config-item">
            <label class="config-label">渐变起始颜色</label>
            <div class="color-picker-container">
              <input 
                type="color" 
                v-model="localStyles.gradientStart"
                class="color-picker"
              >
              <input 
                type="text" 
                v-model="localStyles.gradientStart"
                class="color-input"
              >
            </div>
          </div>

          <div class="config-item">
            <label class="config-label">渐变结束颜色</label>
            <div class="color-picker-container">
              <input 
                type="color" 
                v-model="localStyles.gradientEnd"
                class="color-picker"
              >
              <input 
                type="text" 
                v-model="localStyles.gradientEnd"
                class="color-input"
              >
            </div>
          </div>

          <div class="config-item">
            <label class="config-label">渐变角度</label>
            <div class="slider-container">
              <input 
                type="range" 
                v-model.number="localStyles.gradientAngle"
                min="0" 
                max="360" 
                step="15"
                class="style-slider"
              >
              <span class="value-display">{{ localStyles.gradientAngle }}°</span>
            </div>
          </div>

          <div class="gradient-preview-container">
            <div class="gradient-preview" 
                 :style="{ 
                   background: `linear-gradient(${localStyles.gradientAngle}deg, 
                                ${localStyles.gradientStart} 0%, 
                                ${localStyles.gradientEnd} 100%)` 
                 }">
              背景预览
            </div>
          </div>
        </div>

        <!-- 粒子背景 -->
        <div class="config-section">
          <h3 class="section-title">粒子背景效果</h3>
          
          <div class="config-item">
            <label class="config-label">启用粒子背景</label>
            <div class="toggle-container">
              <label class="toggle-switch">
                <input type="checkbox" v-model="localStyles.particlesEnabled">
                <span class="toggle-slider"></span>
              </label>
              <span class="toggle-label">{{ localStyles.particlesEnabled ? '开启' : '关闭' }}</span>
            </div>
          </div>

          <div v-if="localStyles.particlesEnabled" class="config-item">
            <label class="config-label">粒子数量</label>
            <div class="slider-container">
              <input 
                type="range" 
                v-model.number="localStyles.particleCount"
                min="10" 
                max="200" 
                step="10"
                class="style-slider"
              >
              <span class="value-display">{{ localStyles.particleCount }}</span>
            </div>
          </div>

          <div v-if="localStyles.particlesEnabled" class="config-item">
            <label class="config-label">粒子速度</label>
            <div class="slider-container">
              <input 
                type="range" 
                v-model.number="localStyles.particleSpeed"
                min="0.1" 
                max="5" 
                step="0.1"
                class="style-slider"
              >
              <span class="value-display">{{ localStyles.particleSpeed }}x</span>
            </div>
          </div>

          <div v-if="localStyles.particlesEnabled" class="config-item">
            <label class="config-label">粒子颜色</label>
            <div class="color-picker-container">
              <input 
                type="color" 
                v-model="localStyles.particleColor"
                class="color-picker"
              >
              <input 
                type="text" 
                v-model="localStyles.particleColor"
                class="color-input"
              >
            </div>
          </div>
        </div>

        <!-- 预设主题 -->
        <div class="config-section">
          <h3 class="section-title">预设主题</h3>
          <div class="theme-grid">
            <button 
              v-for="theme in presetThemes" 
              :key="theme.id"
              @click="applyTheme(theme)"
              class="theme-btn"
              :class="{ active: currentTheme === theme.id }"
            >
              <span class="theme-icon">{{ theme.icon }}</span>
              <span class="theme-name">{{ theme.name }}</span>
            </button>
          </div>
        </div>

        <!-- 底部按钮 -->
        <div class="modal-footer">
          <button @click="resetDefaults" class="save-btn secondary">
            🔄 恢复默认
          </button>
          <button @click="saveStyles" class="save-btn primary">
            💾 保存样式
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'

export default {
  name: 'StyleConfig',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    styles: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['close', 'save'],
  setup(props, { emit }) {
    const currentTheme = ref('default')
    
    const defaultStyles = {
      cardOpacity: 95,
      cardBlur: 10,
      borderWidth: 1,
      gradientStart: '#0f172a',
      gradientEnd: '#1e293b',
      gradientAngle: 135,
      particlesEnabled: true,
      particleCount: 80,
      particleSpeed: 1,
      particleColor: '#3b82f6'
    }

    const localStyles = ref({ ...defaultStyles, ...props.styles })
    
    // 监听props变化
    watch(() => props.styles, (newVal) => {
      localStyles.value = { ...defaultStyles, ...newVal }
    }, { deep: true })

    const presetThemes = [
      { 
        id: 'default', 
        name: '默认深色', 
        icon: '🌙',
        styles: { ...defaultStyles }
      },
      { 
        id: 'ocean', 
        name: '深海蓝', 
        icon: '🌊',
        styles: {
          ...defaultStyles,
          gradientStart: '#001e3c',
          gradientEnd: '#003566',
          particleColor: '#00b4d8'
        }
      },
      { 
        id: 'purple', 
        name: '紫罗兰', 
        icon: '💜',
        styles: {
          ...defaultStyles,
          gradientStart: '#2e1065',
          gradientEnd: '#581c87',
          particleColor: '#a855f7'
        }
      },
      { 
        id: 'forest', 
        name: '森林绿', 
        icon: '🌲',
        styles: {
          ...defaultStyles,
          gradientStart: '#052e16',
          gradientEnd: '#14532d',
          particleColor: '#22c55e'
        }
      },
      { 
        id: 'sunset', 
        name: '日落橙', 
        icon: '🌅',
        styles: {
          ...defaultStyles,
          gradientStart: '#431407',
          gradientEnd: '#7c2d12',
          particleColor: '#fb923c'
        }
      },
      { 
        id: 'minimal', 
        name: '极简白', 
        icon: '⚪',
        styles: {
          ...defaultStyles,
          cardOpacity: 100,
          cardBlur: 0,
          gradientStart: '#f1f5f9',
          gradientEnd: '#e2e8f0',
          particlesEnabled: false,
          particleColor: '#94a3b8'
        }
      }
    ]

    const applyTheme = (theme) => {
      currentTheme.value = theme.id
      localStyles.value = { ...theme.styles }
    }

    const resetDefaults = () => {
      currentTheme.value = 'default'
      localStyles.value = { ...defaultStyles }
    }

    const saveStyles = () => {
      emit('save', localStyles.value)
      emit('close')
    }

    const close = () => {
      emit('close')
    }

    return {
      currentTheme,
      localStyles,
      presetThemes,
      applyTheme,
      resetDefaults,
      saveStyles,
      close
    }
  }
}
</script>

<style scoped>
.style-panel-container {
  position: fixed;
  top: 4rem;
  right: 0;
  bottom: 0;
  z-index: 45;
  pointer-events: none;
}

.style-panel {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 420px;
  background: rgba(30, 41, 59, 0.98);
  backdrop-filter: blur(20px);
  border-left: 1px solid #334155;
  box-shadow: -10px 0 40px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  pointer-events: all;
  animation: slideInRight 0.3s ease-out;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem;
  background: rgba(15, 23, 42, 0.9);
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
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding: 1.25rem;
  padding-top: 0;
}

.config-section {
  background: #0f172a;
  border-radius: 0.75rem;
  padding: 1.25rem;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 1rem;
}

.config-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.config-item .config-label {
  min-width: 150px;
  flex-shrink: 0;
}

.config-item:last-child {
  margin-bottom: 0;
}

.config-label {
  color: #94a3b8;
  font-size: 0.875rem;
  font-weight: 500;
}

/* 滑块样式 */
.slider-container {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.style-slider {
  flex: 1;
  -webkit-appearance: none;
  height: 6px;
  background: #1e293b;
  border-radius: 9999px;
  outline: none;
  border: 1px solid #334155;
}

.style-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid #0f172a;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.2);
}

.style-slider::-webkit-slider-thumb:hover {
  background: #60a5fa;
  transform: scale(1.1);
}

.value-display {
  color: #60a5fa;
  font-size: 0.875rem;
  font-weight: 600;
  font-family: monospace;
  min-width: 60px;
  text-align: left;
}

/* 颜色选择器 */
.color-picker-container {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex: 1;
}

.color-picker {
  width: 50px;
  height: 36px;
  border: 2px solid #334155;
  border-radius: 0.5rem;
  cursor: pointer;
  background: transparent;
}

.color-input {
  width: 120px;
  padding: 0.5rem 0.75rem;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 0.5rem;
  color: white;
  font-size: 0.875rem;
  font-family: monospace;
  text-align: center;
}

.color-input:focus {
  outline: none;
  border-color: #3b82f6;
}

/* 开关样式 */
.toggle-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #334155;
  border-radius: 24px;
  transition: 0.3s;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: #94a3b8;
  border-radius: 50%;
  transition: 0.3s;
}

input:checked + .toggle-slider {
  background-color: #3b82f6;
}

input:checked + .toggle-slider:before {
  transform: translateX(24px);
  background-color: white;
}

.toggle-label {
  color: #e2e8f0;
  font-size: 0.875rem;
  font-weight: 500;
}

/* 预览框 */
.gradient-preview-container {
  margin-top: 1rem;
}

.gradient-preview {
  padding: 1.5rem;
  border-radius: 0.75rem;
  color: white;
  text-align: center;
  font-weight: 600;
  font-size: 0.875rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.preview-box {
  padding: 0.75rem 1rem;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(99, 102, 241, 0.05) 100%);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 0.5rem;
  color: #e2e8f0;
  font-size: 0.875rem;
  text-align: center;
}

.gradient-preview {
  margin-top: 1rem;
  padding: 2rem;
  border-radius: 0.75rem;
  color: white;
  text-align: center;
  font-weight: 600;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* 主题网格 */
.theme-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 0.75rem;
}

.theme-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: #1e293b;
  border: 2px solid #334155;
  border-radius: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.theme-btn:hover {
  background: #334155;
  border-color: #475569;
}

.theme-btn.active {
  background: #334155;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.theme-icon {
  font-size: 1.5rem;
}

.theme-name {
  color: #e2e8f0;
  font-size: 0.75rem;
  font-weight: 500;
}

/* 底部 */
.modal-footer {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  padding-top: 1.5rem;
  border-top: 1px solid #334155;
}

.save-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.save-btn.primary {
  background: #3b82f6;
  color: white;
}

.save-btn.primary:hover {
  background: #2563eb;
}

.save-btn.secondary {
  background: #334155;
  color: #e2e8f0;
}

.save-btn.secondary:hover {
  background: #475569;
}

/* 滚动条 */
.modal-body::-webkit-scrollbar {
  width: 6px;
}

.modal-body::-webkit-scrollbar-track {
  background: #1e293b;
  border-radius: 3px;
}

.modal-body::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 3px;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}
</style>
