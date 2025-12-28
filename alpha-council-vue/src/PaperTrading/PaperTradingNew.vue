<template>
  <div class="paper-trading-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>💼 模拟交易</h1>
      <p class="subtitle">虚拟资金练习交易，零风险学习投资</p>
    </div>

    <!-- 风险提示 -->
    <div class="risk-alert">
      <div class="alert-icon">⚠️</div>
      <div class="alert-content">
        <strong>模拟交易提示：</strong>
        本功能使用虚拟资金，不涉及真实交易。模拟环境与实盘存在差异，请勿将模拟结果作为实盘投资依据。
      </div>
    </div>

    <!-- 账户选择/创建 -->
    <div v-if="!currentAccount" class="account-selection">
      <div class="no-account">
        <div class="empty-icon">📊</div>
        <h3>还没有模拟账户</h3>
        <p>创建一个模拟账户开始练习交易</p>
        <button @click="showCreateAccount = true" class="btn-primary">
          ➕ 创建模拟账户
        </button>
      </div>

      <!-- 账户列表 -->
      <div v-if="accounts.length > 0" class="accounts-list">
        <h3>我的模拟账户</h3>
        <div 
          v-for="account in accounts" 
          :key="account.account_id"
          class="account-card"
          @click="selectAccount(account)"
        >
          <div class="account-info">
            <h4>{{ account.account_name }}</h4>
            <p>总资产: ¥{{ formatAmount(account.total_assets) }}</p>
            <p :class="getProfitClass(account.profit_rate)">
              收益率: {{ formatPercent(account.profit_rate) }}
            </p>
          </div>
          <div class="account-actions">
            <!-- 后端不支持删除账户，暂时隐藏删除按钮 -->
            <!-- <button @click.stop="deleteAccount(account.account_id)" class="btn-danger-small">
              删除
            </button> -->
          </div>
        </div>
      </div>
    </div>

    <!-- 主交易界面 -->
    <div v-if="currentAccount" class="trading-main">
      <!-- 账户总览 -->
      <div class="account-overview">
        <div class="overview-card">
          <div class="card-label">总资产</div>
          <div class="card-value">¥{{ formatAmount(currentAccount.total_assets) }}</div>
        </div>
        <div class="overview-card">
          <div class="card-label">可用资金</div>
          <div class="card-value">¥{{ formatAmount(currentAccount.available_cash) }}</div>
        </div>
        <div class="overview-card">
          <div class="card-label">总盈亏</div>
          <div :class="['card-value', getProfitClass(currentAccount.profit_rate)]">
            ¥{{ formatAmount(currentAccount.total_profit) }}
          </div>
        </div>
        <div class="overview-card">
          <div class="card-label">收益率</div>
          <div :class="['card-value', getProfitClass(currentAccount.profit_rate)]">
            {{ formatPercent(currentAccount.profit_rate) }}
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <button @click="showTradeDialog = true" class="btn-primary">
          📈 买入/卖出
        </button>
        <button @click="refreshAccount" class="btn-secondary">
          🔄 刷新
        </button>
        <button @click="currentAccount = null" class="btn-secondary">
          ↩️ 切换账户
        </button>
      </div>

      <!-- 持仓列表 -->
      <div class="positions-section">
        <h3>📊 持仓列表</h3>
        <div v-if="positions.length === 0" class="empty-state">
          <p>暂无持仓</p>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>股票代码</th>
              <th>股票名称</th>
              <th>持仓数量</th>
              <th>成本价</th>
              <th>现价</th>
              <th>市值</th>
              <th>盈亏</th>
              <th>收益率</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="position in positions" :key="position.stock_code">
              <td>{{ position.stock_code }}</td>
              <td>{{ position.stock_name }}</td>
              <td>{{ position.quantity }}</td>
              <td>¥{{ position.avg_cost.toFixed(2) }}</td>
              <td>¥{{ position.current_price.toFixed(2) }}</td>
              <td>¥{{ formatAmount(position.market_value) }}</td>
              <td :class="getProfitClass(position.profit_loss_rate || position.profit_rate)">
                ¥{{ formatAmount(position.profit_loss || position.profit) }}
              </td>
              <td :class="getProfitClass(position.profit_loss_rate || position.profit_rate)">
                {{ formatPercent(position.profit_loss_rate || position.profit_rate) }}
              </td>
              <td>
                <button 
                  @click="quickSell(position)" 
                  class="btn-danger-small"
                >
                  卖出
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 交易记录 -->
      <div class="trades-section">
        <h3>📝 交易记录</h3>
        <div v-if="tradeRecords.length === 0" class="empty-state">
          <p>暂无交易记录</p>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>股票代码</th>
              <th>方向</th>
              <th>数量</th>
              <th>价格</th>
              <th>金额</th>
              <th>手续费</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="trade in tradeRecords" :key="trade.trade_id">
              <td>{{ formatTime(trade.timestamp) }}</td>
              <td>{{ trade.stock_code }}</td>
              <td :class="(trade.action || trade.side) === 'BUY' || (trade.action || trade.side) === 'buy' ? 'text-success' : 'text-danger'">
                {{ (trade.action || trade.side) === 'BUY' || (trade.action || trade.side) === 'buy' ? '买入' : '卖出' }}
              </td>
              <td>{{ trade.quantity }}</td>
              <td>¥{{ trade.price.toFixed(2) }}</td>
              <td>¥{{ formatAmount(trade.amount) }}</td>
              <td>¥{{ trade.commission.toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 创建账户对话框 -->
    <div v-if="showCreateAccount" class="modal-overlay" @click="showCreateAccount = false">
      <div class="modal-content" @click.stop>
        <h3>创建模拟账户</h3>
        <div class="form-group">
          <label>账户名称</label>
          <input 
            v-model="newAccount.name" 
            placeholder="如：我的第一个账户"
            class="input-field"
          />
        </div>
        <div class="form-group">
          <label>初始资金</label>
          <input 
            v-model.number="newAccount.capital" 
            type="number"
            placeholder="100000"
            class="input-field"
          />
          <small>建议：10万 - 100万</small>
        </div>
        <div class="modal-actions">
          <button @click="createAccount" class="btn-primary">创建</button>
          <button @click="showCreateAccount = false" class="btn-secondary">取消</button>
        </div>
      </div>
    </div>

    <!-- 交易对话框 -->
    <div v-if="showTradeDialog" class="modal-overlay" @click="showTradeDialog = false">
      <div class="modal-content" @click.stop>
        <h3>{{ tradeForm.side === 'buy' ? '买入' : '卖出' }}股票</h3>
        
        <div class="trade-tabs">
          <button 
            :class="['tab-btn', { active: tradeForm.side === 'buy' }]"
            @click="tradeForm.side = 'buy'"
          >
            买入
          </button>
          <button 
            :class="['tab-btn', { active: tradeForm.side === 'sell' }]"
            @click="tradeForm.side = 'sell'"
          >
            卖出
          </button>
        </div>

        <div class="form-group">
          <label>股票代码</label>
          <input 
            v-model="tradeForm.stock_code" 
            placeholder="如：600519"
            class="input-field"
          />
        </div>
        <div class="form-group">
          <label>数量（股）</label>
          <input 
            v-model.number="tradeForm.quantity" 
            type="number"
            placeholder="100"
            class="input-field"
          />
          <small>A股最小100股（1手）</small>
        </div>
        <div class="form-group">
          <label>价格（元）</label>
          <input 
            v-model.number="tradeForm.price" 
            type="number"
            step="0.01"
            placeholder="留空为市价"
            class="input-field"
          />
        </div>
        
        <div class="trade-info">
          <p>预计金额: ¥{{ formatAmount((tradeForm.price || 0) * tradeForm.quantity) }}</p>
          <p>预计手续费: ¥{{ formatAmount((tradeForm.price || 0) * tradeForm.quantity * 0.0003) }}</p>
        </div>

        <div class="modal-actions">
          <button @click="placeTrade" class="btn-primary">
            {{ tradeForm.side === 'buy' ? '买入' : '卖出' }}
          </button>
          <button @click="showTradeDialog = false" class="btn-secondary">取消</button>
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
  name: 'PaperTradingNew',
  setup() {
    const API_BASE = `${API_BASE_URL}/api/trading`
    
    // 状态
    const accounts = ref([])
    const currentAccount = ref(null)
    const positions = ref([])
    const tradeRecords = ref([])
    
    // 对话框
    const showCreateAccount = ref(false)
    const showTradeDialog = ref(false)
    
    // 表单
    const newAccount = reactive({
      name: '我的模拟账户',
      capital: 100000
    })
    
    const tradeForm = reactive({
      side: 'buy',
      stock_code: '',
      quantity: 100,
      price: null
    })
    
    // 加载账户列表
    const loadAccounts = async () => {
      try {
        const response = await axios.get(`${API_BASE}/accounts`)
        if (response.data.success) {
          // 映射后端数据到前端格式
          accounts.value = response.data.accounts.map(acc => ({
            account_id: acc.id,
            account_name: acc.name,
            total_assets: acc.total_value || 0,
            available_cash: acc.balance || 0,
            profit_rate: ((acc.total_value || 0) / 1000000 - 1) * 100, // 计算收益率
            total_profit: (acc.total_value || 0) - 1000000, // 计算总盈亏
            status: acc.status,
            created_at: acc.created_at
          }))
          
          // 如果有账户且当前没有选中账户，自动选中第一个
          if (accounts.value.length > 0 && !currentAccount.value) {
            await selectAccount(accounts.value[0])
          }
        }
      } catch (error) {
        console.error('加载账户失败:', error)
      }
    }
    
    // 创建账户
    const createAccount = async () => {
      try {
        const response = await axios.post(`${API_BASE}/account/create`, {
          account_name: newAccount.name,
          initial_capital: newAccount.capital
        })
        
        if (response.data.success) {
          console.log('账户创建成功：', response.data)
          alert('账户创建成功！')
          showCreateAccount.value = false
          
          // 重新加载账户列表
          await loadAccounts()
          
          // 如果返回了账户信息，直接选中
          if (response.data.account) {
            const mappedAccount = {
              account_id: response.data.account.id,
              account_name: response.data.account.name,
              total_assets: response.data.account.total_value || 0,
              available_cash: response.data.account.balance || 0,
              profit_rate: 0,
              total_profit: 0,
              status: 'active'
            }
            await selectAccount(mappedAccount)
          }
        }
      } catch (error) {
        console.error('创建账户失败:', error)
        alert('创建失败: ' + (error.response?.data?.detail || error.message))
      }
    }
    
    // 选择账户
    const selectAccount = async (account) => {
      currentAccount.value = account
      console.log('选中账户：', account)
      await loadAccountDetail()
    }
        
    // 加载账户详情
    const loadAccountDetail = async () => {
      if (!currentAccount.value) return
          
      try {
        // 加载持仓信息
        const portfolioResponse = await axios.get(`${API_BASE}/portfolio`)
        if (portfolioResponse.data.success) {
          const portfolio = portfolioResponse.data.portfolio
              
          // 更新当前账户信息
          currentAccount.value = {
            ...currentAccount.value,
            total_assets: portfolio.total_value || 0,
            available_cash: portfolio.cash_balance || 0,
            total_profit: (portfolio.total_value || 0) - 1000000,
            profit_rate: ((portfolio.total_value || 0) / 1000000 - 1) * 100
          }
              
          // 设置持仓列表
          positions.value = portfolio.positions || []
        }
            
        // 加载交易记录
        const historyResponse = await axios.get(`${API_BASE}/history?limit=50`)
        if (historyResponse.data.success) {
          tradeRecords.value = (historyResponse.data.trades || []).reverse()
        }
      } catch (error) {
        console.error('加载账户详情失败:', error)
      }
    }
    
    // 刷新账户
    const refreshAccount = async () => {
      await loadAccountDetail()
    }
    
    // 下单
    const placeTrade = async () => {
      if (!tradeForm.stock_code || !tradeForm.quantity) {
        alert('请填写完整信息')
        return
      }
      
      try {
        const response = await axios.post(`${API_BASE}/execute`, {
          stock_code: tradeForm.stock_code,
          action: tradeForm.side.toUpperCase(), // buy -> BUY, sell -> SELL
          quantity: tradeForm.quantity,
          price: tradeForm.price || 0,
          order_type: tradeForm.price ? 'LIMIT' : 'MARKET'
        })
        
        if (response.data.success) {
          alert('交易成功！')
          showTradeDialog.value = false
          // 重置表单
          tradeForm.stock_code = ''
          tradeForm.quantity = 100
          tradeForm.price = null
          // 刷新数据
          await loadAccountDetail()
        }
      } catch (error) {
        console.error('交易失败:', error)
        alert('交易失败: ' + (error.response?.data?.detail || error.message))
      }
    }
    
    // 快速卖出
    const quickSell = (position) => {
      tradeForm.side = 'sell'
      tradeForm.stock_code = position.stock_code
      tradeForm.quantity = position.quantity
      tradeForm.price = position.current_price
      showTradeDialog.value = true
    }
    
    // 删除账户
    const deleteAccount = async (accountId) => {
      if (!confirm('确定要删除这个账户吗？')) return
      
      try {
        await axios.delete(`${API_BASE}/account/${accountId}`)
        alert('账户已删除')
        await loadAccounts()
      } catch (error) {
        console.error('删除账户失败:', error)
        alert('删除失败: ' + error.message)
      }
    }
    
    // 格式化函数
    const formatAmount = (amount) => {
      if (amount === null || amount === undefined || isNaN(amount)) {
        return '0.00'
      }
      return amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }
    
    const formatPercent = (rate) => {
      if (rate === null || rate === undefined || isNaN(rate)) {
        return '0.00%'
      }
      return (rate * 100).toFixed(2) + '%'
    }
    
    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleString('zh-CN')
    }
    
    const getProfitClass = (rate) => {
      if (rate > 0) return 'text-success'
      if (rate < 0) return 'text-danger'
      return ''
    }
    
    // 初始化
    onMounted(() => {
      loadAccounts()
    })
    
    return {
      accounts,
      currentAccount,
      positions,
      tradeRecords,
      showCreateAccount,
      showTradeDialog,
      newAccount,
      tradeForm,
      loadAccounts,
      createAccount,
      selectAccount,
      refreshAccount,
      placeTrade,
      quickSell,
      deleteAccount,
      formatAmount,
      formatPercent,
      formatTime,
      getProfitClass
    }
  }
}
</script>

<style scoped>
.paper-trading-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 28px;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #666;
  margin: 0;
}

.risk-alert {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 8px;
  margin-bottom: 20px;
}

.alert-icon {
  font-size: 24px;
}

.alert-content {
  flex: 1;
  line-height: 1.6;
}

.account-selection {
  display: grid;
  gap: 20px;
}

.no-account {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.accounts-list {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.account-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.account-card:hover {
  border-color: #1890ff;
  box-shadow: 0 4px 12px rgba(24,144,255,0.2);
}

.account-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.overview-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.card-label {
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
}

.card-value {
  font-size: 24px;
  font-weight: bold;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.positions-section,
.trades-section {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 16px;
}

.data-table th,
.data-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.data-table th {
  background: #f5f5f5;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
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
  min-width: 400px;
  max-width: 500px;
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

.trade-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.tab-btn {
  flex: 1;
  padding: 10px;
  border: 1px solid #d9d9d9;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.tab-btn.active {
  background: #1890ff;
  color: white;
  border-color: #1890ff;
}

.trade-info {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 16px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-primary {
  padding: 10px 24px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn-primary:hover {
  background: #40a9ff;
}

.btn-secondary {
  padding: 10px 24px;
  background: white;
  color: #333;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn-secondary:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.btn-danger-small {
  padding: 4px 12px;
  background: #ff4d4f;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.text-success {
  color: #52c41a;
}

.text-danger {
  color: #ff4d4f;
}
</style>
