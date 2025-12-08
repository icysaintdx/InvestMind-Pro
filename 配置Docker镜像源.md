# 配置 Docker 镜像加速器

## Windows Docker Desktop

### 方法 1: 通过界面配置

1. 打开 Docker Desktop
2. 点击右上角 **设置图标** (齿轮)
3. 选择 **Docker Engine**
4. 在 JSON 配置中添加：

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
6. 等待 Docker 重启完成

### 方法 2: 手动编辑配置文件

编辑文件：`C:\Users\你的用户名\.docker\daemon.json`

如果文件不存在，创建它并添加：

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

保存后重启 Docker Desktop。

---

## 验证配置

```bash
# 查看配置
docker info | findstr -i "registry"

# 应该看到类似输出：
# Registry Mirrors:
#  https://docker.mirrors.ustc.edu.cn/
#  https://hub-mirror.c.163.com/
```

---

## 测试拉取镜像

```bash
# 测试拉取 nginx
docker pull nginx:alpine

# 测试拉取 node
docker pull node:18-alpine

# 测试拉取 python
docker pull python:3.11-slim
```

如果成功，再运行构建脚本。

---

## 其他国内镜像源

如果上述镜像源不可用，可以尝试：

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

## 配置完成后

重新运行构建脚本：
```bash
docker-build-offline.bat
```
