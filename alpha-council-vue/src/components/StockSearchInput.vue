<template>
  <div class="stock-search-input">
    <input
      ref="inputRef"
      :value="searchQuery"
      @input="handleInput"
      @keyup="handleKeyup"
      @change="handleChange"
      @focus="handleFocus"
      @blur="handleBlur"
      @touchstart="handleTouch"
      type="search"
      inputmode="search"
      autocomplete="off"
      autocorrect="off"
      autocapitalize="off"
      spellcheck="false"
      :placeholder="placeholder"
      class="search-input"
    />
    
    <!-- 搜索结果下拉框 -->
    <div v-if="showDropdown && searchResults.length > 0" class="search-dropdown">
      <div
        v-for="stock in searchResults"
        :key="stock.code"
        class="search-item"
        @mousedown="selectStock(stock)"
      >
        <span class="stock-code">{{ stock.code }}</span>
        <span class="stock-name">{{ stock.name }}</span>
        <span class="stock-market">{{ stock.market }}</span>
      </div>
    </div>
    
    <!-- 加载中 -->
    <div v-if="loading" class="search-loading">
      <span class="spinner"></span>
    </div>
  </div>
</template>

<script>
import { ref, watch, onUnmounted } from 'vue'
import axios from 'axios'
import API_BASE_URL from '@/config/api.js'

export default {
  name: 'StockSearchInput',
  props: {
    modelValue: {
      type: String,
      default: ''
    },
    placeholder: {
      type: String,
      default: '输入股票代码或名称搜索'
    }
  },
  emits: ['update:modelValue', 'select'],
  setup(props, { emit }) {
    const inputRef = ref(null)
    const searchQuery = ref(props.modelValue)
    const searchResults = ref([])
    const showDropdown = ref(false)
    const loading = ref(false)
    let searchTimeout = null
    let pollingInterval = null
    let lastValue = ''
    
    // 搜索触发函数
    const triggerSearch = (value) => {
      searchQuery.value = value
      emit('update:modelValue', value)
      
      // 清除旧的防抖定时器
      if (searchTimeout) {
        clearTimeout(searchTimeout)
      }
      
      if (!value || value.length < 1) {
        searchResults.value = []
        showDropdown.value = false
        return
      }
      
      // 移动端使用更短的防抖
      const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)
      const delay = isMobile ? 100 : 300
      
      searchTimeout = setTimeout(() => {
        searchStock()
      }, delay)
    }

    const handleInput = (event) => {
      triggerSearch(event.target.value)
    }
    
    const handleKeyup = (event) => {
      triggerSearch(event.target.value)
    }
    
    const handleChange = (event) => {
      triggerSearch(event.target.value)
    }
    
    const handleFocus = () => {
      showDropdown.value = true
      startPolling()
      
      if (searchResults.value.length > 0) {
        showDropdown.value = true
      }
    }
    
    // iOS 修复：轮询检查输入框值变化
    const startPolling = () => {
      if (pollingInterval) return
      
      pollingInterval = setInterval(() => {
        if (!inputRef.value) return
        
        const currentValue = inputRef.value.value
        if (currentValue !== lastValue) {
          lastValue = currentValue
          triggerSearch(currentValue)
        }
      }, 100)
    }
    
    const stopPolling = () => {
      if (pollingInterval) {
        clearInterval(pollingInterval)
        pollingInterval = null
      }
    }
    
    const handleTouch = () => {
      startPolling()
    }

    const searchStock = async () => {
      if (!searchQuery.value) {
        searchResults.value = []
        return
      }

      loading.value = true

      try {
        // 使用统一的 API 配置
        const apiUrl = `${API_BASE_URL}/api/akshare/stock/search`

        const response = await axios.get(apiUrl, {
          params: {
            keyword: searchQuery.value,
            limit: 10
          }
        })

        if (response.data.success) {
          searchResults.value = response.data.data
          showDropdown.value = true
        }
      } catch (err) {
        console.error('搜索股票失败:', err)
        searchResults.value = []
      } finally {
        loading.value = false
      }
    }

    const selectStock = (stock) => {
      searchQuery.value = stock.code.replace('SH', '').replace('SZ', '')
      emit('update:modelValue', searchQuery.value)
      emit('select', stock)
      searchResults.value = []
      showDropdown.value = false
    }

    const handleBlur = () => {
      // 延迟关闭，以便点击事件能触发
      setTimeout(() => {
        showDropdown.value = false
        stopPolling()  // 停止轮询
      }, 200)
    }

    watch(() => props.modelValue, (newVal) => {
      searchQuery.value = newVal
    })
    
    // 清理轮询
    onUnmounted(() => {
      stopPolling()
    })

    return {
      inputRef,
      searchQuery,
      searchResults,
      showDropdown,
      loading,
      handleInput,
      handleKeyup,
      handleChange,
      handleFocus,
      handleTouch,
      selectStock,
      handleBlur
    }
  }
}
</script>

<style scoped>
.stock-search-input {
  position: relative;
  width: 100%;
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 0.5rem;
  color: #e2e8f0;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  background: rgba(30, 41, 59, 0.8);
}

.search-input::placeholder {
  color: #64748b;
}

.search-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 0.5rem;
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
  backdrop-filter: blur(12px);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.search-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid rgba(71, 85, 105, 0.2);
}

.search-item:last-child {
  border-bottom: none;
}

.search-item:hover {
  background: rgba(59, 130, 246, 0.1);
}

.stock-code {
  font-weight: 600;
  color: #3b82f6;
  font-size: 0.875rem;
  min-width: 80px;
}

.stock-name {
  flex: 1;
  color: #e2e8f0;
  font-size: 0.875rem;
}

.stock-market {
  color: #64748b;
  font-size: 0.75rem;
}

.search-loading {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(59, 130, 246, 0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 滚动条样式 */
.search-dropdown::-webkit-scrollbar {
  width: 6px;
}

.search-dropdown::-webkit-scrollbar-track {
  background: rgba(30, 41, 59, 0.3);
}

.search-dropdown::-webkit-scrollbar-thumb {
  background: rgba(71, 85, 105, 0.5);
  border-radius: 3px;
}

.search-dropdown::-webkit-scrollbar-thumb:hover {
  background: rgba(71, 85, 105, 0.7);
}
</style>
