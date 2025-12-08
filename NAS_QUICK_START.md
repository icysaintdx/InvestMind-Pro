# 🚀 NAS 部署快速开始

## 本地操作（Windows）

### 1. 构建并保存镜像
```bash
# 使用 NAS 专用构建脚本（推荐）
docker-build-for-nas.bat

# 或使用通用脚本
docker-build-offline.bat
```

等待完成后，会生成：
- `alphacouncil-backend.tar` (~500MB)
- `alphacouncil-frontend.tar` (~200MB)

### 2. 准备文件
```
需要上传到 NAS 的文件：
├── alphacouncil-backend.tar
├── alphacouncil-frontend.tar
├── docker-compose-nas.yml
├── .env (包含 API Keys)
└── backend/agent_configs.json
```

---

## NAS 操作

### 1. 上传文件
将上述文件上传到 NAS 目录（如 `/volume1/docker/alphacouncil/`）

### 2. SSH 连接
```bash
ssh admin@your-nas-ip
cd /volume1/docker/alphacouncil
```

### 3. 加载镜像
```bash
docker load -i alphacouncil-backend.tar
docker load -i alphacouncil-frontend.tar
```

### 4. 创建目录
```bash
mkdir -p data backend
```

### 5. 配置环境变量
```bash
vi .env
```
添加你的 API Keys

### 6. 启动服务

**方法 A: 使用 docker-compose（推荐）**
```bash
docker-compose -f docker-compose-nas.yml up -d
```

**方法 B: 单独运行容器**
```bash
# 启动后端
docker run -d --name alphacouncil-backend \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/backend/agent_configs.json:/app/backend/agent_configs.json \
  --env-file .env \
  alphacouncil-backend:latest

# 启动前端
docker run -d --name alphacouncil-frontend \
  -p 80:80 \
  alphacouncil-frontend:latest
```

### 7. 查看状态
```bash
docker-compose -f docker-compose-nas.yml ps
docker-compose -f docker-compose-nas.yml logs -f
```

---

## 访问

- **前端**: http://your-nas-ip
- **后端**: http://your-nas-ip:8000
- **API 文档**: http://your-nas-ip:8000/docs

---

## 常用命令

```bash
# 启动
docker-compose -f docker-compose-nas.yml up -d

# 停止
docker-compose -f docker-compose-nas.yml stop

# 重启
docker-compose -f docker-compose-nas.yml restart

# 查看日志
docker-compose -f docker-compose-nas.yml logs -f

# 备份数据
cp data/alphacouncil.db data/backup_$(date +%Y%m%d).db
```

---

## 故障排查

### 镜像加载失败
```bash
# 检查文件
ls -lh *.tar

# 重新加载
docker load -i alphacouncil-backend.tar
```

### 容器无法启动
```bash
# 查看日志
docker-compose -f docker-compose-nas.yml logs backend

# 检查端口
netstat -tuln | grep 8000
```

### 无法访问
- 检查 NAS 防火墙设置
- 确保 80 和 8000 端口已开放

---

## 📚 详细文档

查看 `docs/NAS部署指南.md` 获取完整说明。

---

## ✅ 完成！

现在访问 http://your-nas-ip 开始使用 AlphaCouncil！
