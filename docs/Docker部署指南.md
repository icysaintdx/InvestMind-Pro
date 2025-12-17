# Docker 部署指南

## 🐳 快速开始

### 前置要求
- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 可用内存
- 至少 10GB 可用磁盘空间

---

## 📦 一键部署

### 1. 配置环境变量

复制 `.env.example` 为 `.env` 并填写 API Keys：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
# AI API Keys
GEMINI_API_KEY=your_gemini_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
DASHSCOPE_API_KEY=your_qwen_key_here
SILICONFLOW_API_KEY=your_siliconflow_key_here
JUHE_API_KEY=your_juhe_key_here
```

### 2. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 3. 访问应用

- **前端**: http://localhost
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

---

## 🔧 常用命令

### 服务管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose stop

# 重启服务
docker-compose restart

# 停止并删除容器
docker-compose down

# 停止并删除容器、网络、卷
docker-compose down -v
```

### 查看状态

```bash
# 查看运行状态
docker-compose ps

# 查看资源使用
docker stats

# 查看日志
docker-compose logs -f

# 查看最近100行日志
docker-compose logs --tail=100
```

### 重新构建

```bash
# 重新构建所有服务
docker-compose build

# 重新构建特定服务
docker-compose build backend
docker-compose build frontend

# 强制重新构建（不使用缓存）
docker-compose build --no-cache

# 重新构建并启动
docker-compose up -d --build
```

---

## 📊 数据持久化

### 数据卷

数据会持久化到以下位置：

```
./data/
├── InvestMindPro.db      # SQLite 数据库
└── logs/                # 日志文件
```

### 备份数据

```bash
# 备份数据库
docker-compose exec backend cp /app/data/InvestMindPro.db /app/data/backup_$(date +%Y%m%d).db

# 或直接复制本地文件
cp ./data/InvestMindPro.db ./data/backup_$(date +%Y%m%d).db
```

### 恢复数据

```bash
# 停止服务
docker-compose stop

# 恢复数据库
cp ./data/backup_20251208.db ./data/InvestMindPro.db

# 启动服务
docker-compose start
```

---

## 🔍 故障排查

### 查看容器日志

```bash
# 后端日志
docker-compose logs backend

# 前端日志
docker-compose logs frontend

# 实时跟踪日志
docker-compose logs -f backend
```

### 进入容器

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入前端容器
docker-compose exec frontend sh

# 查看文件
docker-compose exec backend ls -la /app
```

### 健康检查

```bash
# 检查后端健康
curl http://localhost:8000/health

# 检查前端健康
curl http://localhost/

# 查看容器健康状态
docker-compose ps
```

### 常见问题

#### 1. 端口被占用

```bash
# 修改 docker-compose.yml 中的端口映射
ports:
  - "8080:80"    # 前端改为 8080
  - "8001:8000"  # 后端改为 8001
```

#### 2. 内存不足

```bash
# 限制容器内存使用
docker-compose.yml:
  backend:
    mem_limit: 2g
  frontend:
    mem_limit: 512m
```

#### 3. 构建失败

```bash
# 清理 Docker 缓存
docker system prune -a

# 重新构建
docker-compose build --no-cache
```

---

## 🚀 生产环境部署

### 1. 使用环境变量

```bash
# 生产环境配置
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 2. 使用 HTTPS

创建 `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  frontend:
    ports:
      - "443:443"
    volumes:
      - ./ssl:/etc/nginx/ssl
```

### 3. 配置反向代理

使用 Nginx 或 Traefik 作为反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:80;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000;
    }
}
```

---

## 📈 性能优化

### 1. 资源限制

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### 2. 日志管理

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 3. 网络优化

```yaml
networks:
  InvestMindPro-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

---

## 🔐 安全建议

### 1. 不要提交 .env 文件

```bash
# .gitignore
.env
*.db
data/
```

### 2. 使用 Docker Secrets

```yaml
services:
  backend:
    secrets:
      - siliconflow_key
      
secrets:
  siliconflow_key:
    file: ./secrets/siliconflow_key.txt
```

### 3. 限制容器权限

```yaml
services:
  backend:
    user: "1000:1000"
    read_only: true
    security_opt:
      - no-new-privileges:true
```

---

## 📝 更新应用

### 更新代码

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建
docker-compose build

# 3. 重启服务
docker-compose up -d

# 4. 查看日志确认
docker-compose logs -f
```

### 滚动更新

```bash
# 逐个更新服务，避免停机
docker-compose up -d --no-deps --build backend
docker-compose up -d --no-deps --build frontend
```

---

## 🧪 测试部署

### 本地测试

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up

# 3. 测试 API
curl http://localhost:8000/health

# 4. 测试前端
curl http://localhost/

# 5. 测试分析功能
# 访问 http://localhost 并进行一次完整分析
```

---

## 📊 监控

### 查看资源使用

```bash
# 实时监控
docker stats

# 查看容器详情
docker inspect InvestMindPro-backend
docker inspect InvestMindPro-frontend
```

### 日志分析

```bash
# 查看错误日志
docker-compose logs backend | grep ERROR

# 统计请求数
docker-compose logs backend | grep "POST /api/analyze" | wc -l
```

---

## 🎯 快速命令参考

```bash
# 启动
docker-compose up -d

# 停止
docker-compose stop

# 重启
docker-compose restart

# 查看日志
docker-compose logs -f

# 重新构建
docker-compose up -d --build

# 清理
docker-compose down -v

# 备份数据
cp ./data/InvestMindPro.db ./data/backup.db

# 进入容器
docker-compose exec backend bash
```

---

## ✅ 部署检查清单

- [ ] 配置 .env 文件
- [ ] 检查端口是否可用
- [ ] 确保有足够的磁盘空间
- [ ] 启动服务
- [ ] 检查容器状态
- [ ] 测试健康检查端点
- [ ] 测试前端访问
- [ ] 测试 API 功能
- [ ] 进行一次完整分析测试
- [ ] 检查数据库是否正常保存
- [ ] 配置日志轮转
- [ ] 设置自动备份

---

## 🆘 获取帮助

如果遇到问题：

1. 查看日志: `docker-compose logs -f`
2. 检查容器状态: `docker-compose ps`
3. 查看健康检查: `curl http://localhost:8000/health`
4. 进入容器调试: `docker-compose exec backend bash`

---

## 🎉 完成！

现在你的 InvestMindPro 已经通过 Docker 部署完成！

访问 http://localhost 开始使用！
