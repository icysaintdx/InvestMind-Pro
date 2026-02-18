<template>
  <div class="strategy-detail">
    <!-- 基本信息 -->
    <div class="section">
      <h3>基本信息</h3>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="策略名称">{{ strategy.name }}</el-descriptions-item>
        <el-descriptions-item label="英文名称">{{ strategy.name_en || '-' }}</el-descriptions-item>
        <el-descriptions-item label="策略类型">
          <el-tag :type="getTypeTagType(strategy.type)">
            {{ strategyTypes[strategy.type]?.name_cn || strategy.type }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="策略分类">{{ strategy.category }}</el-descriptions-item>
        <el-descriptions-item label="作者">{{ strategy.author }}</el-descriptions-item>
        <el-descriptions-item label="来源">
          <el-tag :type="strategy.source === 'preset' ? 'success' : 'primary'" size="small">
            {{ strategy.source === 'preset' ? '预设策略' : '自定义策略' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="难度等级">
          <el-tag :type="getDifficultyType(strategy.difficulty)" size="small">
            {{ difficultyLevels[strategy.difficulty]?.name_cn || strategy.difficulty }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="版本">{{ strategy.version }}</el-descriptions-item>
        <el-descriptions-item label="适用市场" :span="2">
          <el-tag v-for="market in strategy.suitable_market" :key="market" size="small" style="margin-right: 4px">
            {{ market }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="标签" :span="2">
          <el-tag v-for="tag in strategy.tags" :key="tag" size="small" effect="plain" style="margin-right: 4px">
            {{ tag }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ strategy.description || '-' }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 指标配置 -->
    <div class="section">
      <h3>指标配置</h3>
      <el-table :data="indicatorList" border stripe size="small">
        <el-table-column prop="name" label="指标名称" width="120" />
        <el-table-column prop="name_cn" label="中文名称" width="120" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.type === 'technical' ? 'primary' : 'success'" size="small">
              {{ row.type === 'technical' ? '技术指标' : '基本面' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator" label="操作符" width="80" align="center">
          <template #default="{ row }">
            <code>{{ row.operator }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="value" label="阈值" width="100" />
        <el-table-column prop="weight" label="权重" width="80">
          <template #default="{ row }">
            {{ (row.weight * 100).toFixed(0) }}%
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 入场条件 -->
    <div class="section">
      <h3>入场条件</h3>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="逻辑关系">
          <el-tag>{{ strategy.entry_conditions?.logic || 'AND' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="最低得分">
          {{ ((strategy.entry_conditions?.min_score || 0) * 100).toFixed(0) }}%
        </el-descriptions-item>
      </el-descriptions>
      <div v-if="strategy.entry_conditions?.conditions?.length" class="conditions-list">
        <h4>附加条件</h4>
        <ul>
          <li v-for="(cond, idx) in strategy.entry_conditions.conditions" :key="idx">
            {{ cond.indicator }} {{ cond.operator }} {{ cond.value }}
          </li>
        </ul>
      </div>
    </div>

    <!-- 出场条件 -->
    <div class="section">
      <h3>出场条件</h3>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="止盈类型">
          {{ strategy.exit_conditions?.take_profit?.type || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="止盈值">
          {{ formatExitValue(strategy.exit_conditions?.take_profit) }}
        </el-descriptions-item>
        <el-descriptions-item label="止损类型">
          {{ strategy.exit_conditions?.stop_loss?.type || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="止损值">
          {{ formatExitValue(strategy.exit_conditions?.stop_loss) }}
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 仓位管理 -->
    <div class="section">
      <h3>仓位管理</h3>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="仓位方法">
          {{ positionMethods[strategy.position_sizing?.method] || strategy.position_sizing?.method || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="最大仓位">
          {{ ((strategy.position_sizing?.max_position || 0) * 100).toFixed(0) }}%
        </el-descriptions-item>
        <el-descriptions-item label="单笔风险">
          {{ ((strategy.position_sizing?.risk_per_trade || 0) * 100).toFixed(0) }}%
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 风险管理 -->
    <div class="section" v-if="strategy.risk_management && Object.keys(strategy.risk_management).length">
      <h3>风险管理</h3>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="最大回撤" v-if="strategy.risk_management.max_drawdown">
          {{ (strategy.risk_management.max_drawdown * 100).toFixed(0) }}%
        </el-descriptions-item>
        <el-descriptions-item label="日亏损限制" v-if="strategy.risk_management.daily_loss_limit">
          {{ (strategy.risk_management.daily_loss_limit * 100).toFixed(0) }}%
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 统计信息 -->
    <div class="section">
      <h3>使用统计</h3>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="使用次数">{{ strategy.use_count || 0 }}</el-descriptions-item>
        <el-descriptions-item label="成功率">
          {{ strategy.success_rate ? (strategy.success_rate * 100).toFixed(1) + '%' : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(strategy.created_at) }}
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { strategyApi } from '@/api/strategy'

const props = defineProps({
  strategy: {
    type: Object,
    required: true
  }
})

const strategyTypes = ref({})
const difficultyLevels = ref({})

const positionMethods = {
  fixed_percentage: '固定比例',
  atr_based: 'ATR动态',
  kelly: '凯利公式',
  equal_weight: '等权重',
  concentrated: '集中持仓'
}

const indicatorList = computed(() => {
  return props.strategy.indicators?.required || []
})

const getTypeTagType = (type) => {
  const map = {
    value: 'success',
    growth: 'primary',
    momentum: 'warning',
    technical: 'info',
    fundamental: '',
    mean_reversion: 'danger'
  }
  return map[type] || ''
}

const getDifficultyType = (difficulty) => {
  const map = {
    beginner: 'success',
    intermediate: 'warning',
    advanced: 'danger',
    expert: 'danger'
  }
  return map[difficulty] || ''
}

const formatExitValue = (config) => {
  if (!config) return '-'
  if (config.type === 'percentage') {
    return (config.value * 100).toFixed(0) + '%'
  }
  if (config.type === 'price') {
    return '¥' + config.value
  }
  return config.value || '-'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(async () => {
  try {
    const [typesRes, diffRes] = await Promise.all([
      strategyApi.getStrategyTypes(),
      strategyApi.getDifficultyLevels()
    ])
    if (typesRes.success) strategyTypes.value = typesRes.data
    if (diffRes.success) difficultyLevels.value = diffRes.data
  } catch (error) {
    console.error('加载元数据失败:', error)
  }
})
</script>

<style scoped lang="scss">
.strategy-detail {
  .section {
    margin-bottom: 24px;
    
    h3 {
      font-size: 15px;
      font-weight: 600;
      margin: 0 0 12px 0;
      padding-bottom: 8px;
      border-bottom: 1px solid #ebeef5;
    }
    
    h4 {
      font-size: 13px;
      margin: 12px 0 8px 0;
    }
    
    .conditions-list {
      ul {
        margin: 0;
        padding-left: 20px;
        
        li {
          margin-bottom: 4px;
          font-size: 13px;
        }
      }
    }
  }
}
</style>