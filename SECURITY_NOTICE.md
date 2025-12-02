# ⚠️ 安全提醒 - SECURITY NOTICE

## GitHub Token已泄露 - URGENT ACTION REQUIRED

你在聊天中分享了GitHub Personal Access Token。这是一个严重的安全问题！

### 立即采取以下行动：

1. **立即撤销此Token**：
   - 访问: https://github.com/settings/tokens
   - 找到名称包含 `github_pat_11AY2QCKQ` 的token
   - 点击 "Delete" 或 "Revoke"

2. **创建新的Token**（如果需要）：
   - 点击 "Generate new token"
   - 只授予必要的权限
   - 设置合理的过期时间

3. **更新本地git配置**：
   ```bash
   git remote remove origin
   git remote add origin https://github.com/icysaintdx/InvestMind-Pro.git
   ```

4. **未来的最佳实践**：
   - 永远不要在聊天、代码或文档中分享token
   - 使用环境变量存储敏感信息
   - 使用SSH密钥代替token进行git操作
   - 定期轮换访问令牌

### 配置SSH（推荐）：
```bash
# 生成SSH密钥
ssh-keygen -t ed25519 -C "your-email@example.com"

# 添加到GitHub
# 复制公钥内容并添加到: https://github.com/settings/keys
cat ~/.ssh/id_ed25519.pub

# 更新远程仓库URL
git remote set-url origin git@github.com:icysaintdx/InvestMind-Pro.git
```

## 项目信息

- **仓库地址**: https://github.com/icysaintdx/InvestMind-Pro
- **已排除目录**: TradingAgents-CN-main/
- **包含内容**: 
  - Vue3前端（alpha-council-vue/）
  - FastAPI后端（backend/）
  - 智能体配置（agents/）
  - API接口（api/）
  - 文档（docs/）

---
**记住：安全第一！立即撤销泄露的token！**
