# InvestMind Pro - 飞牛NAS Docker部署指南

## 概述

本文档介绍如何在飞牛NAS上部署 InvestMind Pro（智投顾问团）。

## 系统要求

- 飞牛NAS（fnOS）
- Docker 已安装
- 至少 2GB 可用内存
- 至少 5GB 可用存储空间

## 部署方式

### 方式一：使用预构建镜像（推荐）

#### 步骤1：在本地构建镜像

在开发机器上执行：

```bash
# Windows (PowerShell)
docker build -f Dockerfile.all-in-one -t investmindpro:latest .

# 导出镜像
docker save -o investmindpro-latest.tar investmindpro:latest

# 压缩（可选，减小传输大小）
gzip investmindpro-latest.tar
```

或使用构建脚本（Linux/Mac）：

```bash
chmod +x build-for-nas.sh
./build-for-nas.sh
```

#### 步骤2：上传镜像到NAS

1. 通过飞牛NAS的文件管理器上传 `investmindpro-latest.tar.gz`
2. 或使用 SCP/SFTP 上传

#### 步骤3：在NAS上导入镜像

通过 SSH 连接到 NAS，执行：

```bash
# 解压（如果压缩了）
gunzip investmindpro-latest.tar.gz

# 导入镜像
docker load -i investmindpro-latest.tar

# 验证镜像
docker images | grep investmindpro
```

#### 步骤4：创建配置文件

在 NAS 上创建部署目录：

```bash
mkdir -p /volume1/docker/investmindpro
cd /volume1/docker/investmindpro

# 创建数据目录
mkdir -p data
```

创建 `.env` 文件配置 API 密钥：

```bash
cat > .env << 'EOF'
# AI API Keys（至少配置一个）
GEMINI_API_KEY=your_gemini_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
QWEN_API_KEY=your_qwen_api_key
SILICONFLOW_API_KEY=your_siliconflow_api_key

# 数据源 API Keys（可选）
JUHE_API_KEY=your_juhe_api_key
TUSHARE_TOKEN=your_tushare_token
EOF
```

上传 `docker-compose-nas.yml` 到该目录。

#### 步骤5：启动容器

```bash
cd /volume1/docker/investmindpro
docker-compose -f docker-compose-nas.yml up -d
```

#### 步骤6：访问应用

打开浏览器访问：`http://NAS_IP:8080`

---

### 方式二：通过飞牛NAS Docker管理界面

#### 步骤1：导入镜像

1. 打开飞牛NAS管理界面
2. 进入 Docker → 镜像
3. 点击"导入"，选择上传的 tar 文件

#### 步骤2：创建容器

1. 在镜像列表中找到 `investmindpro:latest`
2. 点击"创建容器"
3. 配置以下参数：

**基本设置：**
- 容器名称：`investmindpro`
- 自动重启：开启

**端口映射：**
- 本地端口：`8080` → 容器端口：`80`

**存储卷：**
- 本地路径：`/volume1/docker/investmindpro/data` → 容器路径：`/app/data`

**环境变量：**
```
TZ=Asia/Shanghai
GEMINI_API_KEY=your_key
DEEPSEEK_API_KEY=your_key
# ... 其他API密钥
```

4. 点击"创建"启动容器

---

## 配置说明

### API 密钥配置

| 环境变量 | 说明 | 必需 |
|---------|------|------|
| GEMINI_API_KEY | Google Gemini API | 至少一个 |
| DEEPSEEK_API_KEY | DeepSeek API | 至少一个 |
| QWEN_API_KEY | 阿里通义千问 API | 至少一个 |
| SILICONFLOW_API_KEY | SiliconFlow API | 至少一个 |
| JUHE_API_KEY | 聚合数据 API | 可选 |
| TUSHARE_TOKEN | Tushare 数据接口 | 可选 |

### 端口说明

- 默认映射到 `8080` 端口
- 如需修改，编辑 `docker-compose-nas.yml` 中的 `ports` 配置

### 数据持久化

数据存储在 `/app/data` 目录，包括：
- SQLite 数据库
- 监控配置
- 缓存数据

建议映射到 NAS 的持久化存储路径。

---

## 常用命令

```bash
# 查看容器状态
docker ps | grep investmindpro

# 查看日志
docker logs -f investmindpro

# 重启容器
docker restart investmindpro

# 停止容器
docker stop investmindpro

# 删除容器
docker rm investmindpro

# 更新镜像后重新部署
docker-compose -f docker-compose-nas.yml down
docker-compose -f docker-compose-nas.yml up -d
```

---

## 故障排除

### 容器无法启动

1. 检查端口是否被占用：
   ```bash
   netstat -tlnp | grep 8080
   ```

2. 检查日志：
   ```bash
   docker logs investmindpro
   ```

### 无法访问页面

1. 确认容器正在运行：
   ```bash
   docker ps | grep investmindpro
   ```

2. 检查防火墙设置

3. 尝试访问健康检查接口：
   ```bash
   curl http://localhost:8080/api/health
   ```

### API 调用失败

1. 检查 API 密钥是否正确配置
2. 检查网络连接（NAS 需要能访问外网）
3. 查看后端日志：
   ```bash
   docker logs investmindpro | grep -i error
   ```

---

## 资源占用

- **内存**：约 500MB - 1.5GB（取决于使用情况）
- **CPU**：空闲时 < 1%，分析时 10-30%
- **存储**：镜像约 2GB，数据根据使用量增长

---

## 更新升级

1. 在开发机器上构建新镜像
2. 导出并上传到 NAS
3. 导入新镜像
4. 重新创建容器：
   ```bash
   docker-compose -f docker-compose-nas.yml down
   docker-compose -f docker-compose-nas.yml up -d
   ```

---

## 支持

如有问题，请提交 Issue 或查看项目文档。
