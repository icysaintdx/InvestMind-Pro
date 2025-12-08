# NAS 快速修复指南

## 问题
容器启动失败，缺少依赖和导入错误。

## 解决方案

### 步骤 1: 停止并删除旧容器

```bash
docker rm -f alphacouncil
```

### 步骤 2: 重新构建本地镜像

在本地 Windows 上：

```bash
# 1. 确保 requirements.txt 已更新
# 2. 确保 interface.py 已修复
# 3. 重新构建
docker-build-all-in-one.bat
```

### 步骤 3: 上传新镜像到 NAS

上传新生成的 `alphacouncil-all-in-one.tar`

### 步骤 4: 在 NAS 上部署

```bash
# 删除旧镜像
docker rmi alphacouncil:latest

# 加载新镜像
docker load -i alphacouncil-all-in-one.tar

# 启动容器
docker run -d \
  --name alphacouncil \
  -p 8808:80 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  --restart unless-stopped \
  alphacouncil:latest \
  /bin/bash -c "nginx && cd /app/backend && python server.py"

# 查看日志
docker logs -f alphacouncil
```

---

## 临时修复（如果不想重新构建）

### 方案 A: 手动修复文件

```bash
# 1. 启动临时容器
docker run --rm -it \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  alphacouncil:latest \
  /bin/bash

# 2. 在容器内修复 interface.py
cat > /app/backend/dataflows/interface.py.patch << 'EOF'
# 找到第 23-28 行，替换为：
try:
    from backend.utils.logging_config import get_logger
    logger = get_logger('dataflow')
except ImportError:
    import logging
    logger = logging.getLogger('dataflow')
    logging.basicConfig(level=logging.INFO)
EOF

# 3. 手动编辑文件
vi /app/backend/dataflows/interface.py
# 找到 tradingagents 相关的导入，替换为上面的代码

# 4. 安装依赖
pip install tenacity yfinance retrying

# 5. 测试启动
cd /app/backend
python server.py

# 6. 如果成功，退出并提交镜像
exit

# 7. 提交为新镜像
docker commit CONTAINER_ID alphacouncil:fixed
```

---

## 推荐：重新构建

最可靠的方法是在本地重新构建完整镜像：

1. ✅ 已修复 `requirements.txt` - 添加了所有依赖
2. ✅ 已修复 `interface.py` - 移除了 tradingagents 导入
3. ✅ 已修复 `Dockerfile.all-in-one` - 修复了启动脚本

现在运行：
```bash
docker-build-all-in-one.bat
```

等待构建完成（10-15分钟），然后上传到 NAS。

---

## 完整依赖列表

已添加到 `requirements.txt`:
- colorlog
- pandas
- numpy==1.26.4
- sqlalchemy
- akshare
- tushare
- beautifulsoup4
- lxml
- yfinance
- openai
- requests
- python-dateutil
- tenacity
- retrying

---

## 验证

构建完成后，本地测试：

```bash
# 测试运行
docker run -p 8808:80 --env-file .env alphacouncil:latest

# 访问
http://localhost:8808
```

如果成功，再上传到 NAS！
