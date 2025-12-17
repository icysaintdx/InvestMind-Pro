# iOS Safari 输入测试指南

**测试日期**: 2025-12-11  
**修复内容**: 移除 v-model，使用原生事件处理

---

## 🔧 最新修复

### 核心改变

1. **移除 v-model**
   ```vue
   <!-- ❌ 旧代码 -->
   <input v-model="searchQuery" />
   
   <!-- ✅ 新代码 -->
   <input :value="searchQuery" @input="handleInput" />
   ```

2. **监听所有可能的事件**
   ```vue
   @input="handleInput"
   @keydown="handleKeydown"
   @keyup="handleKeyup"
   @change="handleChange"
   @compositionend="handleInput"
   ```

3. **详细的调试日志**
   ```javascript
   console.log('[StockSearch] Input event:', value)
   console.log('[StockSearch] Keydown event:', event.key)
   console.log('[StockSearch] Keyup event:', value)
   console.log('[StockSearch] Change event:', value)
   ```

---

## 🧪 测试步骤

### 1. 在 iPhone 上打开 Safari

```
访问: http://your-server-ip:8080
```

### 2. 打开开发者工具

**在 Mac 上**:
1. 连接 iPhone 到 Mac
2. 打开 Safari
3. 菜单栏 → 开发 → [你的 iPhone] → [页面]
4. 打开控制台

### 3. 测试输入

在 iPhone 上输入 `600519`，观察：

**预期在控制台看到**:
```
[StockSearch] Focus event
[StockSearch] Input event: 6
[StockSearch] Keyup event: 6
[StockSearch] Trigger search: 6
[StockSearch] Input event: 60
[StockSearch] Keyup event: 60
[StockSearch] Trigger search: 60
...
```

### 4. 检查结果

- ✅ 每输入一个字符都有日志
- ✅ 搜索下拉框出现
- ✅ 搜索结果正确

---

## 🔍 如果还是不行

### 方案A: 检查事件触发

在控制台运行：
```javascript
document.querySelector('.search-input').addEventListener('input', (e) => {
  console.log('Native input event:', e.target.value)
})
```

如果这个能触发，说明是 Vue 的问题。

### 方案B: 强制触发搜索

添加一个测试按钮：
```vue
<button @click="testSearch">测试搜索</button>

<script>
const testSearch = () => {
  const value = inputRef.value?.value || '600519'
  console.log('Test search:', value)
  triggerSearch(value)
}
</script>
```

### 方案C: 使用 setTimeout 延迟

```javascript
const handleInput = (event) => {
  const value = event.target.value
  console.log('[StockSearch] Input event:', value)
  
  // iOS 可能需要延迟
  setTimeout(() => {
    triggerSearch(value)
  }, 0)
}
```

---

## 📊 调试清单

### 检查项

- [ ] 控制台有 Focus event 日志
- [ ] 控制台有 Input event 日志
- [ ] 控制台有 Keyup event 日志
- [ ] 控制台有 Trigger search 日志
- [ ] 下拉框出现
- [ ] 搜索结果显示

### 如果没有任何日志

说明事件根本没触发，可能是：
1. iOS 版本太旧
2. Safari 设置问题
3. 页面缓存问题（强制刷新）

### 如果有日志但没有搜索

说明搜索逻辑有问题，检查：
1. 后端 API 是否正常
2. 网络请求是否发送
3. 防抖时间是否太长

---

## 🎯 最终测试

### 成功标准

1. ✅ 输入 `6` → 立即触发搜索
2. ✅ 输入 `60` → 更新搜索结果
3. ✅ 输入 `600519` → 显示完整结果
4. ✅ 点击结果 → 填充到输入框

### 失败处理

如果还是不行，请提供：
1. iOS 版本
2. Safari 版本
3. 控制台完整日志
4. 网络请求记录

---

**立即测试！** 🚀
