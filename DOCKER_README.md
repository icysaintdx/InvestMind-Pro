# 🐳 InvestMindPro Docker 快速开始

## 一键启动

### Windows
```bash
docker-start.bat
```

### Linux/Mac
```bash
chmod +x docker-start.sh
./docker-start.sh
```

或手动执行：
```bash
docker-compose up -d
```

---

## 访问地址

- **前端**: http://localhost
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

---

## 常用命令

```bash
# 启动
docker-compose up -d

# 停止
docker-compose stop

# 查看日志
docker-compose logs -f

# 重启
docker-compose restart

# 停止并删除
docker-compose down
```

---

## 配置

1. 复制 `.env.example` 为 `.env`
2. 填写 API Keys
3. 运行 `docker-start.bat`

---

## 详细文档

查看 `docs/Docker部署指南.md` 获取完整文档。

---

## 架构

```
┌─────────────────┐
│   Frontend      │  Port 80
│   (Nginx)       │
└────────┬────────┘
         │
         │ API Proxy
         │
┌────────▼────────┐
│   Backend       │  Port 8000
│   (FastAPI)     │
└────────┬────────┘
         │
         │
┌────────▼────────┐
│   Database      │
│   (SQLite)      │
└─────────────────┘
```

---

## 数据持久化

数据保存在 `./data/` 目录：
- `InvestMindPro.db` - 数据库文件
- `logs/` - 日志文件

---

## 故障排查

### 查看日志
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 检查状态
```bash
docker-compose ps
docker stats
```

### 进入容器
```bash
docker-compose exec backend bash
docker-compose exec frontend sh
```

---

## 更新

```bash
git pull
docker-compose up -d --build
```

---

## 🎉 完成！

现在访问 http://localhost 开始使用 InvestMindPro！
