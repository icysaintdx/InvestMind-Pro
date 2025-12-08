# 🚀 AlphaCouncil 一体化部署（最简单）

## 特点

✅ **一个镜像包含所有内容**
- FastAPI 后端
- Vue 前端
- Nginx 服务器
- 所有依赖

✅ **一条命令启动**
```bash
docker run -d -p 80:80 --env-file .env alphacouncil:latest
```

✅ **只需要一个端口（80）**

---

## 本地构建

```bash
# 一键构建
docker-build-all-in-one.bat
```

等待完成后生成：
- `alphacouncil-all-in-one.tar` (~1-1.5GB)

---

## NAS 部署

### 1. 上传文件到 NAS

```
/volume1/docker/alphacouncil/
├── alphacouncil-all-in-one.tar
├── .env
└── data/ (可选，用于持久化)
```

### 2. SSH 连接到 NAS

```bash
ssh admin@your-nas-ip
cd /volume1/docker/alphacouncil
```

### 3. 加载镜像

```bash
docker load -i alphacouncil-all-in-one.tar
```

### 4. 配置环境变量

```bash
vi .env
```

添加：
```env
GEMINI_API_KEY=your_key
DEEPSEEK_API_KEY=your_key
DASHSCOPE_API_KEY=your_key
SILICONFLOW_API_KEY=your_key
JUHE_API_KEY=your_key
```

### 5. 启动容器

```bash
docker run -d \
  --name alphacouncil \
  -p 8808:80 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  --restart unless-stopped \
  alphacouncil:latest
```

### 6. 查看日志

```bash
docker logs -f alphacouncil
```

### 7. 访问

http://your-nas-ip

---

## 常用命令

```bash
# 启动
docker start alphacouncil

# 停止
docker stop alphacouncil

# 重启
docker restart alphacouncil

# 查看日志
docker logs -f alphacouncil

# 查看状态
docker ps | grep alphacouncil

# 进入容器
docker exec -it alphacouncil bash

# 删除容器
docker rm -f alphacouncil

# 删除镜像
docker rmi alphacouncil:latest
```

---

## 更新应用

```bash
# 1. 停止并删除旧容器
docker stop alphacouncil
docker rm alphacouncil

# 2. 删除旧镜像
docker rmi alphacouncil:latest

# 3. 加载新镜像
docker load -i alphacouncil-all-in-one-new.tar

# 4. 启动新容器
docker run -d \
  --name alphacouncil \
  -p 80:80 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  --restart unless-stopped \
  alphacouncil:latest
```

---

## 数据备份

```bash
# 备份数据库
docker exec alphacouncil cp /app/data/alphacouncil.db /app/data/backup.db

# 或直接复制
cp data/alphacouncil.db data/backup_$(date +%Y%m%d).db
```

---

## 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker logs alphacouncil

# 检查端口占用
netstat -tuln | grep 80
```

### 后端 API 无法访问

```bash
# 进入容器检查
docker exec -it alphacouncil bash

# 检查后端进程
ps aux | grep python

# 检查 Nginx
ps aux | grep nginx

# 测试后端
curl http://localhost:8000/health
```

### 前端无法访问

```bash
# 检查 Nginx 配置
docker exec alphacouncil nginx -t

# 重启 Nginx
docker exec alphacouncil nginx -s reload
```

---

## 端口说明

| 端口 | 服务 | 说明 |
|------|------|------|
| 80 | Nginx | 前端 + API 代理 |
| 8000 | FastAPI | 后端（容器内部） |

只需要开放 **80** 端口！

---

## 优势对比

### 一体化部署 vs 分离部署

| 特性 | 一体化 | 分离部署 |
|------|--------|----------|
| **镜像数量** | 1个 | 2个 |
| **端口数量** | 1个(80) | 2个(80+8000) |
| **启动命令** | 1条 | 2条 |
| **网络配置** | 无需配置 | 需要配置 |
| **镜像大小** | ~1.5GB | ~700MB |
| **维护难度** | 简单 | 中等 |
| **适用场景** | 个人/小团队 | 生产环境 |

---

## 推荐场景

### 使用一体化部署：
✅ 个人使用
✅ 家庭 NAS
✅ 快速测试
✅ 简单部署

### 使用分离部署：
✅ 生产环境
✅ 需要独立扩展
✅ 多实例部署
✅ 专业运维

---

## 🎉 完成！

现在只需要：
1. 运行 `docker-build-all-in-one.bat`
2. 上传 `alphacouncil-all-in-one.tar` 到 NAS
3. 一条命令启动

就这么简单！
