<template>
  <div class="strategy-form">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <!-- 基本信息 -->
      <div class="form-section">
        <h4>基本信息</h4>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="策略名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入策略名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="英文名称">
              <el-input v-model="form.name_en" placeholder="可选" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="策略类型" prop="type">
              <el-select v-model="form.type" placeholder="选择类型" style="width: 100%">
                <el-option 
                  v-for="(type, key) in strategyTypes" 
                  :key="key" 
                  :label="type.name_cn" 
                  :value="key" 
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="策略分类">
              <el-select v-model="form.category" placeholder="选择分类" style="width: 100%">
                <el-option 
                  v-for="(cat, key) in categories" 
                  :key="key" 
                  :label="key" 
                  :value="key" 
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="难度等级">
              <el-select v-model="form.difficulty" placeholder="选择难度" style="width: 100%">
                <el-option 
                  v-for="(level, key) in difficultyLevels" 
                  :key="key" 
                  :label="level.name_cn" 
                  :value="key" 
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="策略描述">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="3" 
            placeholder="描述策略的核心逻辑和适用场景"
          />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="适用市场">
              <el-select v-model="form.suitable_market" multiple placeholder="选择市场" style="width: 100%">
                <el-option label="A股" value="A股" />
                <el-option label="港股" value="港股" />
                <el-option label="美股" value="美股" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="标签">
              <el-select 
                v-model="form.tags" 
                multiple 
                filterable 
                allow-create 
                placeholder="添加标签"
                style="width: 100%"
              >
                <el-option v-for="tag in commonTags" :key="tag" :label="tag" :value="tag" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </div>
      
      <!-- 指标配置 -->
      <div class="form-section">
        <div class="section-header">
          <h4>指标配置</h4>
          <el-button type="primary" size="small" @click="addIndicator">
            <el-icon><Plus /></el-icon>
            添加指标
          </el-button>
        </div>
        
        <el-table :data="form.indicators.required" border size="small">
          <el-table-column label="指标" width="180">
            <template #default="{ row, $index }">
              <el-select 
                v-model="row.name" 
                filterable 
                placeholder="选择指标"
                @change="onIndicatorChange($index)"
              >
                <el-option-group 
                  v-for="(group, category) in groupedIndicators" 
                  :key="category" 
                  :label="indicatorCategories[category]?.name_cn || category"
                >
                  <el-option 
                    v-for="ind in group" 
                    :key="ind.name" 
                    :label="`${ind.name_cn} (${ind.name})`" 
                    :value="ind.name"
                  />
                </el-option-group>
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="操作符" width="100">
            <template #default="{ row }">
              <el-select v-model="row.operator" placeholder="操作符">
                <el-option v-for="(op, key) in operators" :key="key" :label="op.name_cn" :value="key" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="阈值" width="120">
            <template #default="{ row }">
              <el-input v-model="row.value" placeholder="值" />
            </template>
          </el-table-column>
          <el-table-column label="权重" width="100">
            <template #default="{ row }">
              <el-input-number 
                v-model="row.weight" 
                :min="0" 
                :max="1" 
                :step="0.1" 
                :precision="2"
                size="small"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="60" align="center">
            <template #default="{ $index }">
              <el-button type="danger" size="small" text @click="removeIndicator($index)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <!-- 入场条件 -->
      <div class="form-section">
        <h4>入场条件</h4>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="逻辑关系">
              <el-radio-group v-model="form.entry_conditions.logic">
                <el-radio label="AND">全部满足</el-radio>
                <el-radio label="OR">满足其一</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="最低得分">
              <el-slider 
                v-model="form.entry_conditions.min_score" 
                :min="0" 
                :max="1" 
                :step="0.05"
                :format-tooltip="val => (val * 100).toFixed(0) + '%'"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>
      
      <!-- 出场条件 -->
      <div class="form-section">
        <h4>出场条件</h4>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="止盈类型">
              <el-select v-model="form.exit_conditions.take_profit.type" style="width: 100%">
                <el-option label="百分比" value="percentage" />
                <el-option label="固定价格" value="price" />
                <el-option label="移动止盈" value="trailing_stop" />
                <el-option label="不设止盈" value="none" />
              </el-select>
            </el-form-item>
            <el-form-item label="止盈值" v-if="form.exit_conditions.take_profit.type !== 'none'">
              <el-input-number 
                v-model="form.exit_conditions.take_profit.value" 
                :min="0" 
                :step="0.01"
                style="width: 100%"
              />
              <span class="input-hint" v-if="form.exit_conditions.take_profit.type === 'percentage'">
                (如0.2表示20%)
              </span>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="止损类型">
              <el-select v-model="form.exit_conditions.stop_loss.type" style="width: 100%">
                <el-option label="百分比" value="percentage" />
                <el-option label="固定价格" value="price" />
                <el-option label="均线破位" value="ma_break" />
                <el-option label="支撑位破位" value="support_break" />
              </el-select>
            </el-form-item>
            <el-form-item label="止损值">
              <el-input-number 
                v-model="form.exit_conditions.stop_loss.value" 
                :min="0" 
                :step="0.01"
                style="width: 100%"
              />
              <span class="input-hint" v-if="form.exit_conditions.stop_loss.type === 'percentage'">
                (如0.1表示10%)
              </span>
            </el-form-item>
          </el-col>
        </el-row>
      </div>
      
      <!-- 仓位管理 -->
      <div class="form-section">
        <h4>仓位管理</h4>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="仓位方法">
              <el-select v-model="form.position_sizing.method" style="width: 100%">
                <el-option label="固定比例" value="fixed_percentage" />
                <el-option label="ATR动态" value="atr_based" />
                <el-option label="凯利公式" value="kelly" />
                <el-option label="等权重" value="equal_weight" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="最大仓位">
              <el-slider 
                v-model="form.position_sizing.max_position" 
                :min="0" 
                :max="1" 
                :step="0.05"
                :format-tooltip="val => (val * 100).toFixed(0) + '%'"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="单笔风险">
              <el-slider 
                v-model="form.position_sizing.risk_per_trade" 
                :min="0" 
                :max="0.1" 
                :step="0.005"
                :format-tooltip="val => (val * 100).toFixed(1) + '%'"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>
      
      <!-- 其他设置 -->
      <div class="form-section">
        <h4>其他设置</h4>
        <el-form-item label="公开策略">
          <el-switch v-model="form.is_public" />
          <span class="switch-hint">公开后其他用户可以查看和使用此策略</span>
        </el-form-item>
      </div>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'
import { strategyApi } from '@/api/strategy'

const emit = defineEmits(['submit'])

// 表单引用
const formRef = ref(null)

// 元数据
const strategyTypes = ref({})
const categories = ref({})
const difficultyLevels = ref({})
const indicators = ref([])
const indicatorCategories = ref({})
const operators = ref({})

// 常用标签
const commonTags = [
  '价值投资', '成长投资', '趋势跟踪', '均线', '技术分析',
  '短线', '中线', '长线', '低估值', '高增长', '龙头', '板块'
]

// 表单数据
const form = reactive({
  name: '',
  name_en: '',
  type: 'technical',
  category: '自定义策略',
  description: '',
  difficulty: 'intermediate',
  suitable_market: ['A股'],
  tags: [],
  indicators: {
    required: []
  },
  entry_conditions: {
    logic: 'AND',
    min_score: 0.7
  },
  exit_conditions: {
    take_profit: {
      type: 'percentage',
      value: 0.2
    },
    stop_loss: {
      type: 'percentage',
      value: 0.1
    }
  },
  position_sizing: {
    method: 'fixed_percentage',
    max_position: 0.25,
    risk_per_trade: 0.02
  },
  is_public: false
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择策略类型', trigger: 'change' }
  ]
}

// 按分类分组的指标
const groupedIndicators = computed(() => {
  const groups = {}
  for (const ind of indicators.value) {
    const cat = ind.category || 'other'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(ind)
  }
  return groups
})

// 添加指标
const addIndicator = () => {
  form.indicators.required.push({
    name: '',
    name_cn: '',
    type: 'technical',
    operator: '>',
    value: '',
    weight: 0.2
  })
}

// 移除指标
const removeIndicator = (index) => {
  form.indicators.required.splice(index, 1)
}

// 指标选择变化
const onIndicatorChange = (index) => {
  const row = form.indicators.required[index]
  const ind = indicators.value.find(i => i.name === row.name)
  if (ind) {
    row.name_cn = ind.name_cn
    row.type = ind.category
  }
}

// 提交表单
const submit = async () => {
  try {
    await formRef.value.validate()
    emit('submit', { ...form })
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

// 暴露方法
defineExpose({ submit })

// 加载元数据
onMounted(async () => {
  try {
    const [typesRes, catsRes, diffRes, indsRes, indCatsRes, opsRes] = await Promise.all([
      strategyApi.getStrategyTypes(),
      strategyApi.getStrategyCategories(),
      strategyApi.getDifficultyLevels(),
      strategyApi.getIndicators(),
      strategyApi.getIndicatorCategories(),
      strategyApi.getOperators()
    ])
    
    if (typesRes.success) strategyTypes.value = typesRes.data
    if (catsRes.success) categories.value = catsRes.data
    if (diffRes.success) difficultyLevels.value = diffRes.data
    if (indsRes.success) indicators.value = indsRes.data
    if (indCatsRes.success) indicatorCategories.value = indCatsRes.data
    if (opsRes.success) operators.value = opsRes.data
  } catch (error) {
    console.error('加载元数据失败:', error)
  }
})
</script>

<style scoped lang="scss">
.strategy-form {
  .form-section {
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #ebeef5;
    
    &:last-child {
      border-bottom: none;
    }
    
    h4 {
      font-size: 14px;
      font-weight: 600;
      margin: 0 0 16px 0;
      color: #303133;
    }
    
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      
      h4 {
        margin: 0;
      }
    }
  }
  
  .input-hint {
    font-size: 12px;
    color: #909399;
    margin-left: 8px;
  }
  
  .switch-hint {
    font-size: 12px;
    color: #909399;
    margin-left: 12px;
  }
}
</style>