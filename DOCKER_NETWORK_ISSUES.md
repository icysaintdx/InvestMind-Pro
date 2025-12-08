# Docker 网络问题解决方案

## 问题描述

构建时出现错误：
```
ERROR: failed to resolve source metadata for docker.io/library/nginx:alpine
ERROR: failed to resolve source metadata for docker.io/library/node:18-alpine
```

这是因为无法从 Docker Hub 拉取基础镜像。

---

## 解决方案（按优先级）

### 方案 1: 配置 Docker 镜像加速器 ⭐⭐⭐⭐⭐

**最推荐的方法**

1. 打开 Docker Desktop
2. 点击 **设置** (齿轮图标)
3. 选择 **Docker Engine**
4. 添加镜像源：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://dockerproxy.com"
  ]
}
```

5. 点击 **Apply & Restart**
6. 重新运行 `docker-build-offline.bat`

**详细说明**: 查看 `配置Docker镜像源.md`

---

### 方案 2: 手动预拉取镜像 ⭐⭐⭐⭐

如果方案1配置后仍然慢，先手动拉取：

```bash
# 运行预拉取脚本
docker-pull-images.bat

# 或手动执行
docker pull python:3.11-slim
docker pull node:18-alpine
docker pull nginx:alpine
```

拉取成功后再运行构建脚本。

---

### 方案 3: 使用 VPN/代理 ⭐⭐⭐

1. 启用 VPN
2. 在 Docker Desktop 设置中配置代理：
   - Settings → Resources → Proxies
   - 填写代理地址
3. 重新构建

---

### 方案 4: 使用其他镜像源 ⭐⭐

尝试不同的镜像源：

```json
{
  "registry-mirrors": [
    "https://dockerhub.azk8s.cn",
    "https://reg-mirror.qiniu.com",
    "https://docker.mirrors.sjtug.sjtu.edu.cn"
  ]
}
```

---

### 方案 5: 从其他机器复制镜像 ⭐

如果有其他能访问 Docker Hub 的机器：

**在能访问的机器上：**
```bash
# 拉取镜像
docker pull python:3.11-slim
docker pull node:18-alpine
docker pull nginx:alpine

# 保存为 tar
docker save python:3.11-slim -o python-3.11-slim.tar
docker save node:18-alpine -o node-18-alpine.tar
docker save nginx:alpine -o nginx-alpine.tar
```

**在你的机器上：**
```bash
# 加载镜像
docker load -i python-3.11-slim.tar
docker load -i node-18-alpine.tar
docker load -i nginx-alpine.tar

# 然后构建
docker-build-offline.bat
```

---

## 快速诊断

### 测试网络连接

```bash
# 测试 Docker Hub
ping hub.docker.com

# 测试镜像拉取
docker pull hello-world
```

### 查看当前配置

```bash
# 查看镜像源配置
docker info | findstr -i "registry"

# 查看 Docker 版本
docker --version
```

---

## 推荐步骤

1. **首先尝试方案1**（配置镜像加速器）
2. **如果还是慢**，运行 `docker-pull-images.bat` 预拉取
3. **如果还是失败**，使用 VPN 或代理
4. **最后方案**，从其他机器复制镜像

---

## 成功标志

当看到以下输出时，说明镜像拉取成功：

```
Step 1: Pull Python base image
------------------------------------------------------------
3.11-slim: Pulling from library/python
...
Status: Downloaded newer image for python:3.11-slim
Python: OK

Step 2: Pull Node.js base image
------------------------------------------------------------
18-alpine: Pulling from library/node
...
Status: Downloaded newer image for node:18-alpine
Node.js: OK

Step 3: Pull Nginx base image
------------------------------------------------------------
alpine: Pulling from library/nginx
...
Status: Downloaded newer image for nginx:alpine
Nginx: OK
```

然后就可以成功构建了！

---

## 常见问题

### Q: 配置镜像源后还是很慢？
A: 尝试更换不同的镜像源，或者使用 VPN。

### Q: 提示 "connection timeout"？
A: 检查防火墙设置，确保 Docker 可以访问网络。

### Q: 提示 "unauthorized"？
A: 不需要登录 Docker Hub，这是网络问题，不是认证问题。

---

## 联系支持

如果所有方案都失败：

1. 检查 Docker Desktop 日志
2. 尝试重启 Docker Desktop
3. 尝试重启电脑
4. 考虑使用其他网络环境

---

## 🎯 推荐操作流程

```bash
# 1. 配置镜像源（一次性）
# 打开 Docker Desktop → Settings → Docker Engine
# 添加镜像源配置

# 2. 重启 Docker
# Apply & Restart

# 3. 预拉取镜像
docker-pull-images.bat

# 4. 构建项目
docker-build-offline.bat

# 5. 如果成功，会生成 TAR 文件
# alphacouncil-backend.tar
# alphacouncil-frontend.tar
```

---

## ✅ 完成后

镜像构建成功后，按照 `NAS_QUICK_START.md` 部署到 NAS。
