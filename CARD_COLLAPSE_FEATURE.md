# ✅ 智能体卡片自动折叠展开功能

**时间**: 2025-12-05 08:20

---

## 🎯 需求

智能体卡片的内容区（card-content）默认折叠，点击"开始分析"按钮时自动全部展开，无需手动点击折叠/展开按钮。只有刷新页面时才恢复默认折叠状态。

---

## ✅ 实现方案

### 1. AgentCard组件修改

#### 添加isExpanded prop
```vue
props: {
  // ... 其他props
  isExpanded: {
    type: Boolean,
    default: false  // 默认折叠
  }
}
```

#### 修改内容区显示逻辑
```vue
<!-- 之前 -->
<div class="card-content">
  <!-- 内容 -->
</div>

<!-- 现在 -->
<div v-show="isExpanded" class="card-content">
  <!-- 内容 -->
</div>
```

---

### 2. AnalysisView组件修改

#### 添加cardsExpanded状态
```javascript
const cardsExpanded = ref(false) // 卡片是否展开，默认折叠
```

#### 开始分析时自动展开
```javascript
const startAnalysis = async () => {
  if (!isValidCode.value || isAnalyzing.value) return
  isAnalyzing.value = true
  cardsExpanded.value = true // 🔥 开始分析时自动展开所有卡片
  // ... 其他逻辑
}
```

#### 传递给所有AgentCard
```vue
<AgentCard 
  v-for="agent in stage1Agents" 
  :key="agent.id"
  :agent="agent"
  :status="agentStatus[agent.id]"
  :output="agentOutputs[agent.id]"
  :is-expanded="cardsExpanded"  <!-- 🔥 传递展开状态 -->
/>
```

---

## 📊 状态流程

### 初始状态
```
页面加载
  ↓
cardsExpanded = false
  ↓
所有卡片折叠（只显示头部）
```

### 开始分析
```
点击"开始分析"按钮
  ↓
cardsExpanded = true
  ↓
所有卡片立即展开
  ↓
显示分析内容
```

### 刷新页面
```
刷新页面
  ↓
cardsExpanded = false（重置）
  ↓
所有卡片恢复折叠状态
```

---

## 🎨 用户体验

### 之前
- ❌ 卡片内容始终显示
- ❌ 页面初始很长
- ❌ 需要滚动查看

### 现在
- ✅ 初始状态简洁（只显示卡片头部）
- ✅ 点击分析自动展开
- ✅ 无需手动操作
- ✅ 刷新页面恢复折叠

---

## 📝 修改文件

1. ✅ `alpha-council-vue/src/components/AgentCard.vue`
   - 添加 `isExpanded` prop
   - 修改 `card-content` 使用 `v-show`

2. ✅ `alpha-council-vue/src/views/AnalysisView.vue`
   - 添加 `cardsExpanded` 状态
   - 在 `startAnalysis` 中设置为 `true`
   - 传递给所有 `AgentCard` 组件

---

## 🧪 测试步骤

### 1. 初始状态测试
```
1. 打开页面
2. 观察智能体卡片
3. ✅ 应该只显示头部，内容区折叠
```

### 2. 展开测试
```
1. 输入股票代码
2. 点击"开始分析"
3. ✅ 所有卡片立即展开
4. ✅ 显示分析内容
```

### 3. 刷新测试
```
1. 刷新页面
2. 观察智能体卡片
3. ✅ 恢复折叠状态
```

---

## 💡 技术细节

### v-show vs v-if
使用 `v-show` 而不是 `v-if`：
- ✅ 元素始终渲染，只是切换 `display` 属性
- ✅ 切换速度更快
- ✅ 适合频繁切换的场景

### 响应式传递
```javascript
// 父组件
const cardsExpanded = ref(false)

// 传递给子组件
:is-expanded="cardsExpanded"

// 子组件接收
props: {
  isExpanded: Boolean
}

// 自动响应变化
v-show="isExpanded"
```

---

## 🎯 效果展示

### 初始状态（折叠）
```
┌─────────────────────────────┐
│ 📰 新闻舆情分析师    [待命] │
│ NEWS                         │
└─────────────────────────────┘

┌─────────────────────────────┐
│ 🗣️ 社交媒体分析师   [待命] │
│ SOCIAL                       │
└─────────────────────────────┘

... (其他卡片)
```

### 分析中（展开）
```
┌─────────────────────────────┐
│ 📰 新闻舆情分析师  [分析中] │
│ NEWS                         │
├─────────────────────────────┤
│ 📊 参考数据                  │
│ • 东方财富 (5条)             │
│ • 新浪财经 (3条)             │
├─────────────────────────────┤
│ 正在分析新闻数据...          │
│ ████████░░░░ 60%             │
└─────────────────────────────┘

┌─────────────────────────────┐
│ 🗣️ 社交媒体分析师 [分析中] │
│ SOCIAL                       │
├─────────────────────────────┤
│ 📊 参考数据                  │
│ • 微博热议 (50条)            │
│ • 雪球社区 (3条)             │
├─────────────────────────────┤
│ 正在分析社交媒体数据...      │
│ ████████░░░░ 60%             │
└─────────────────────────────┘
```

---

## 🚀 优势

1. **简洁的初始界面**
   - 页面加载时不会太长
   - 用户可以快速浏览所有智能体

2. **自动化体验**
   - 无需手动展开每个卡片
   - 点击分析即可看到所有内容

3. **性能优化**
   - 使用 `v-show` 而不是 `v-if`
   - 切换速度快

4. **状态管理清晰**
   - 单一状态控制所有卡片
   - 易于维护和扩展

---

## 📌 注意事项

### 1. 刷新页面
- 刷新页面会重置所有状态
- `cardsExpanded` 会恢复为 `false`
- 卡片会恢复折叠状态

### 2. 浏览器后退
- 后退不会触发页面刷新
- 状态保持不变
- 卡片保持展开状态

### 3. 多次分析
- 每次点击"开始分析"都会重新展开
- 不会影响已展开的卡片

---

## 🎉 完成状态

- ✅ AgentCard组件修改完成
- ✅ AnalysisView组件修改完成
- ✅ 所有卡片支持折叠展开
- ✅ 自动化流程实现
- ✅ 文档编写完成

---

**当前状态**: ✅ 功能完成，等待测试验证
