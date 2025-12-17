# NAS Docker 部署指南

## 📦 准备工作

### 1. 在本地构建并保存镜像

```bash
# Windows
docker-build-and-save.bat

# 或手动执行
cd backend
docker build -t InvestMindPro-backend:latest .
cd ..

cd alpha-council-vue
docker build -t InvestMindPro-frontend:latest .
cd ..

# 保存为 tar 文件
docker save InvestMindPro-backend:latest -o InvestMindPro-backend.tar
docker save InvestMindPro-frontend:latest -o InvestMindPro-frontend.tar
```

### 2. 文件清单

需要上传到 NAS 的文件：
```
InvestMindPro/
├── InvestMindPro-backend.tar       # 后端镜像
├── InvestMindPro-frontend.tar      # 前端镜像
├── docker-compose-nas.yml         # NAS 专用配置
├── .env                           # 环境变量（包含 API Keys）
├── data/                          # 数据目录（可选）
└── backend/
    └── agent_configs.json         # 智能体配置
```

---

## 🚀 NAS 部署步骤

### 步骤 1: 上传文件到 NAS

将以下文件上传到 NAS 的某个目录（如 `/volume1/docker/InvestMindPro/`）：
- `InvestMindPro-backend.tar`
- `InvestMindPro-frontend.tar`
- `docker-compose-nas.yml`
- `.env`
- `backend/agent_configs.json`

### 步骤 2: SSH 连接到 NAS

```bash
ssh admin@your-nas-ip
```

### 步骤 3: 加载 Docker 镜像

```bash
cd /volume1/docker/InvestMindPro

# 加载后端镜像
docker load -i InvestMindPro-backend.tar

# 加载前端镜像
docker load -i InvestMindPro-frontend.tar

# 验证镜像已加载
docker images | grep InvestMindPro
```

应该看到：
```
InvestMindPro-backend   latest   xxx   xxx   xxx MB
InvestMindPro-frontend  latest   xxx   xxx   xxx MB
```

### 步骤 4: 创建数据目录

```bash
mkdir -p data
mkdir -p backend
```

### 步骤 5: 配置环境变量

编辑 `.env` 文件：
```bash
vi .env
```

添加你的 API Keys：
```env
GEMINI_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here
DASHSCOPE_API_KEY=your_key_here
SILICONFLOW_API_KEY=your_key_here
JUHE_API_KEY=your_key_here
```

### 步骤 6: 启动服务

```bash
# 使用 NAS 专用配置启动
docker-compose -f docker-compose-nas.yml up -d

# 查看日志
docker-compose -f docker-compose-nas.yml logs -f

# 查看状态
docker-compose -f docker-compose-nas.yml ps
```

### 步骤 7: 访问应用

- **前端**: http://your-nas-ip
- **后端 API**: http://your-nas-ip:8000
- **API 文档**: http://your-nas-ip:8000/docs

---

## 🔧 NAS 常用命令

### 服务管理

```bash
cd /volume1/docker/InvestMindPro

# 启动
docker-compose -f docker-compose-nas.yml up -d

# 停止
docker-compose -f docker-compose-nas.yml stop

# 重启
docker-compose -f docker-compose-nas.yml restart

# 查看日志
docker-compose -f docker-compose-nas.yml logs -f

# 查看状态
docker-compose -f docker-compose-nas.yml ps

# 停止并删除
docker-compose -f docker-compose-nas.yml down
```

### 镜像管理

```bash
# 查看镜像
docker images

# 删除旧镜像
docker rmi InvestMindPro-backend:latest
docker rmi InvestMindPro-frontend:latest

# 清理未使用的镜像
docker image prune -a
```

### 数据备份

```bash
# 备份数据库
cp data/InvestMindPro.db data/backup_$(date +%Y%m%d).db

# 或打包整个数据目录
tar -czf InvestMindPro_backup_$(date +%Y%m%d).tar.gz data/
```

---

## 📊 群晖 NAS 特殊说明

### 使用 Container Manager

1. 打开 **Container Manager**
2. 点击 **映像** → **新增** → **从文件添加**
3. 上传 `InvestMindPro-backend.tar` 和 `InvestMindPro-frontend.tar`
4. 等待导入完成

### 使用 Docker Compose

1. 在 Container Manager 中点击 **项目**
2. 点击 **新增**
3. 选择 `docker-compose-nas.yml` 文件
4. 配置环境变量
5. 点击 **启动**

### 端口映射

如果 80 端口被占用，可以修改 `docker-compose-nas.yml`：
```yaml
ports:
  - "8080:80"  # 前端改为 8080
```

---

## 🔍 故障排查

### 1. 镜像加载失败

```bash
# 检查 tar 文件是否完整
ls -lh InvestMindPro-*.tar

# 重新加载
docker load -i InvestMindPro-backend.tar
```

### 2. 容器启动失败

```bash
# 查看详细日志
docker-compose -f docker-compose-nas.yml logs backend
docker-compose -f docker-compose-nas.yml logs frontend

# 检查容器状态
docker ps -a
```

### 3. 无法访问

```bash
# 检查端口是否开放
netstat -tuln | grep 8000
netstat -tuln | grep 80

# 检查防火墙
# 在 NAS 控制面板中开放 80 和 8000 端口
```

### 4. 数据库权限问题

```bash
# 修改数据目录权限
chmod -R 777 data/
```

---

## 🔄 更新应用

### 方法 1: 重新构建并上传

1. 在本地重新构建镜像
2. 保存为 tar 文件
3. 上传到 NAS
4. 停止旧容器
5. 删除旧镜像
6. 加载新镜像
7. 启动新容器

```bash
# 在 NAS 上执行
docker-compose -f docker-compose-nas.yml down
docker rmi InvestMindPro-backend:latest
docker rmi InvestMindPro-frontend:latest
docker load -i InvestMindPro-backend-new.tar
docker load -i InvestMindPro-frontend-new.tar
docker-compose -f docker-compose-nas.yml up -d
```

### 方法 2: 使用版本标签

构建时使用版本标签：
```bash
docker build -t InvestMindPro-backend:v2.0 .
docker save InvestMindPro-backend:v2.0 -o InvestMindPro-backend-v2.0.tar
```

---

## 📈 性能优化

### 1. 资源限制

编辑 `docker-compose-nas.yml`：
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
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

### 3. 使用 SSD 缓存

将数据目录放在 SSD 缓存卷上：
```yaml
volumes:
  - /volume1/@docker/InvestMindPro/data:/app/data
```

---

## 🔐 安全建议

### 1. 使用反向代理

在 NAS 上配置 Nginx 反向代理：
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:80;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000;
    }
}
```

### 2. 限制访问

使用 NAS 防火墙限制访问 IP。

### 3. 定期备份

设置定时任务自动备份数据库：
```bash
# 在 NAS 控制面板中创建计划任务
0 2 * * * cd /volume1/docker/InvestMindPro && tar -czf backup_$(date +\%Y\%m\%d).tar.gz data/
```

---

## 📝 完整部署脚本

创建 `deploy-to-nas.sh`：
```bash
#!/bin/bash

# 配置
NAS_IP="192.168.1.100"
NAS_USER="admin"
NAS_PATH="/volume1/docker/InvestMindPro"

# 上传文件
echo "Uploading files to NAS..."
scp InvestMindPro-backend.tar ${NAS_USER}@${NAS_IP}:${NAS_PATH}/
scp InvestMindPro-frontend.tar ${NAS_USER}@${NAS_IP}:${NAS_PATH}/
scp docker-compose-nas.yml ${NAS_USER}@${NAS_IP}:${NAS_PATH}/
scp .env ${NAS_USER}@${NAS_IP}:${NAS_PATH}/

# SSH 到 NAS 并部署
echo "Deploying on NAS..."
ssh ${NAS_USER}@${NAS_IP} << 'EOF'
cd /volume1/docker/InvestMindPro

# 停止旧容器
docker-compose -f docker-compose-nas.yml down

# 加载新镜像
docker load -i InvestMindPro-backend.tar
docker load -i InvestMindPro-frontend.tar

# 启动新容器
docker-compose -f docker-compose-nas.yml up -d

# 查看状态
docker-compose -f docker-compose-nas.yml ps
EOF

echo "Deployment complete!"
echo "Access: http://${NAS_IP}"
```

---

## ✅ 部署检查清单

- [ ] 在本地构建镜像
- [ ] 保存为 tar 文件
- [ ] 上传到 NAS
- [ ] 加载镜像
- [ ] 配置 .env 文件
- [ ] 创建数据目录
- [ ] 启动服务
- [ ] 检查容器状态
- [ ] 测试前端访问
- [ ] 测试 API 功能
- [ ] 进行一次完整分析
- [ ] 配置自动备份
- [ ] 配置防火墙规则

---

## 🎉 完成！

现在你的 InvestMindPro 已经在 NAS 上运行了！

访问 http://your-nas-ip 开始使用！
