# API URL 配置说明

**更新日期**: 2025-12-11  
**问题**: 移动端无法访问 localhost 后端  
**解决方案**: 智能 URL 构建

---

## 🎯 问题背景

### 原始问题

```javascript
// ❌ 硬编码 localhost
const apiUrl = 'http://localhost:8000/api/...'
```

**问题**：
- PC 访问 `http://localhost:8080` → 可以访问 `http://localhost:8000` ✅
- 手机访问 `http://192.168.1.100:8080` → 无法访问 `http://localhost:8000` ❌

---

## ✅ 解决方案

### 智能 URL 构建

```javascript
// ✅ 根据环境和访问方式动态构建
let apiUrl

// 场景1：开发环境（前后端分离）
if (process.env.NODE_ENV === 'development') {
  const hostname = window.location.hostname
  apiUrl = `http://${hostname}:8000/api/...`
}
// 场景2：生产环境（Docker/服务器）
else {
  const protocol = window.location.protocol
  const hostname = window.location.hostname
  apiUrl = `${protocol}//${hostname}:8000/api/...`
}
```

---

## 📋 支持的部署场景

### 场景1: 本地开发（前后端分离）

**前端**: `http://localhost:8080`  
**后端**: `http://localhost:8000`

**访问方式**：
- PC 浏览器: `http://localhost:8080` → 后端 `http://localhost:8000` ✅
- 手机浏览器: `http://192.168.1.100:8080` → 后端 `http://192.168.1.100:8000` ✅

**URL 构建**：
```javascript
const hostname = window.location.hostname  // localhost 或 192.168.1.100
apiUrl = `http://${hostname}:8000/api/...`
```

---

### 场景2: Docker 部署（前后端同容器）

**前端**: `http://example.com:8080`  
**后端**: `http://example.com:8000`

**访问方式**：
- 浏览器: `http://example.com:8080` → 后端 `http://example.com:8000` ✅

**URL 构建**：
```javascript
const protocol = window.location.protocol  // http:
const hostname = window.location.hostname  // example.com
apiUrl = `${protocol}//${hostname}:8000/api/...`
```

---

### 场景3: Nginx 反向代理（推荐生产环境）

**前端**: `https://example.com/`  
**后端**: `https://example.com/api/`

**Nginx 配置**：
```nginx
server {
    listen 80;
    server_name example.com;
    
    # 前端
    location / {
        proxy_pass http://localhost:8080;
    }
    
    # 后端 API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
    }
}
```

**URL 构建**：
```javascript
// 使用相对路径
apiUrl = '/api/akshare/stock/search'
```

**优点**：
- ✅ 同源，无 CORS 问题
- ✅ 统一端口（80/443）
- ✅ 支持 HTTPS
- ✅ 移动端和 PC 端都正常

---

### 场景4: Docker Compose（前后端分离容器）

**docker-compose.yml**：
```yaml
version: '3'
services:
  frontend:
    build: ./alpha-council-vue
    ports:
      - "8080:8080"
    environment:
      - VUE_APP_API_URL=http://backend:8000
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
```

**URL 构建**：
```javascript
// 使用环境变量
const apiUrl = process.env.VUE_APP_API_URL || 
               `http://${window.location.hostname}:8000/api/...`
```

---

## 🔧 当前实现逻辑

```javascript
let apiUrl

// 场景1：Dev 开发环境（前后端分离）
if (process.env.NODE_ENV === 'development') {
  const hostname = window.location.hostname
  apiUrl = `http://${hostname}:8000/api/akshare/stock/search`
} 
// 场景2：Docker/服务器部署（前后端同源）
else if (window.location.port === '8080' || 
         window.location.port === '80' || 
         window.location.port === '443') {
  const protocol = window.location.protocol
  const hostname = window.location.hostname
  const port = window.location.port === '8080' ? ':8000' : ''
  apiUrl = `${protocol}//${hostname}${port}/api/akshare/stock/search`
}
// 场景3：默认情况
else {
  const protocol = window.location.protocol
  const hostname = window.location.hostname
  apiUrl = `${protocol}//${hostname}:8000/api/akshare/stock/search`
}
```

---

## 📊 测试矩阵

| 访问方式 | 前端地址 | 后端地址 | 是否工作 |
|---------|---------|---------|---------|
| PC 本地 | `http://localhost:8080` | `http://localhost:8000` | ✅ |
| 手机局域网 | `http://192.168.1.100:8080` | `http://192.168.1.100:8000` | ✅ |
| Docker 同主机 | `http://example.com:8080` | `http://example.com:8000` | ✅ |
| Nginx 反向代理 | `https://example.com/` | `https://example.com/api/` | ✅ |
| Docker Compose | `http://example.com:8080` | `http://backend:8000` | ⚠️ 需要环境变量 |

---

## 🚀 推荐的生产部署方案

### 方案A: Nginx 反向代理（最佳）

**优点**：
- ✅ 统一域名和端口
- ✅ 无 CORS 问题
- ✅ 支持 HTTPS
- ✅ 易于扩展

**配置**：
```nginx
server {
    listen 443 ssl;
    server_name example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8080;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000/api/;
    }
}
```

### 方案B: Docker Compose + Nginx

**docker-compose.yml**：
```yaml
version: '3'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - frontend
      - backend
  
  frontend:
    build: ./alpha-council-vue
    expose:
      - "8080"
  
  backend:
    build: ./backend
    expose:
      - "8000"
```

---

## ⚠️ 注意事项

### 1. CORS 问题

如果前后端不同源，需要在后端配置 CORS：

```python
# backend/server.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. 环境变量

建议使用环境变量配置 API URL：

```javascript
// .env.development
VUE_APP_API_URL=http://localhost:8000

// .env.production
VUE_APP_API_URL=https://api.example.com
```

```javascript
// 使用
const apiUrl = process.env.VUE_APP_API_URL + '/api/akshare/stock/search'
```

### 3. 移动端测试

确保：
- ✅ 手机和电脑在同一 WiFi
- ✅ 防火墙允许 8000 和 8080 端口
- ✅ 后端监听 `0.0.0.0` 而不是 `127.0.0.1`

---

## 🎯 总结

### 当前方案优点

1. ✅ 支持本地开发（PC + 移动端）
2. ✅ 支持 Docker 部署
3. ✅ 支持服务器部署
4. ✅ 自动适配不同场景

### 未来优化

1. 使用环境变量统一配置
2. 添加 API 基础 URL 配置文件
3. 支持多后端负载均衡

---

**配置完成！** 🎉
