# NAS 调试指南

## 问题：前端 500 错误

后端已启动成功，但访问前端时 Nginx 报 500 错误。

## 调试步骤

### 1. 检查 Nginx 错误日志

```bash
# 进入容器
docker exec -it InvestMindPro bash

# 查看 Nginx 错误日志
cat /var/log/nginx/error.log

# 查看 Nginx 访问日志
cat /var/log/nginx/access.log

# 检查 Nginx 配置
nginx -t

# 查看 Nginx 进程
ps aux | grep nginx
```

### 2. 检查前端文件

```bash
# 检查前端构建产物是否存在
ls -la /app/frontend/dist/

# 检查 index.html
ls -la /app/frontend/dist/index.html

# 查看文件权限
ls -la /usr/share/nginx/html/
```

### 3. 检查 Nginx 配置文件

```bash
# 查看配置
cat /etc/nginx/sites-available/InvestMindPro

# 检查软链接
ls -la /etc/nginx/sites-enabled/
```

### 4. 手动测试

```bash
# 测试后端
curl http://localhost:8000/health

# 测试前端静态文件
curl http://localhost/

# 重启 Nginx
nginx -s reload
```

---

## 可能的原因

### 原因 1: 前端文件不存在

```bash
# 检查
ls -la /app/frontend/dist/

# 如果不存在，重新构建
cd /app/frontend
npm run build
```

### 原因 2: Nginx 配置错误

```bash
# 检查配置
nginx -t

# 查看错误
cat /var/log/nginx/error.log
```

### 原因 3: 权限问题

```bash
# 修复权限
chmod -R 755 /app/frontend/dist/
chown -R nginx:nginx /app/frontend/dist/
```

---

## 快速修复

### 方案 A: 重新配置 Nginx

```bash
docker exec -it InvestMindPro bash

# 创建简单的 Nginx 配置
cat > /etc/nginx/sites-available/InvestMindPro << 'EOF'
server {
    listen 80;
    server_name localhost;
    
    root /app/frontend/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# 重启 Nginx
nginx -s reload

exit
```

### 方案 B: 使用默认配置

```bash
docker exec -it InvestMindPro bash

# 使用默认配置
rm /etc/nginx/sites-enabled/InvestMindPro
cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
    listen 80;
    root /app/frontend/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
    }
}
EOF

nginx -s reload
exit
```

---

## 测试

```bash
# 查看日志
docker logs -f InvestMindPro

# 访问
curl http://your-nas-ip:8808
```

---

## 如果还是不行

重新构建镜像，确保前端正确构建：

```bash
# 本地重新构建
docker-build-all-in-one.bat

# 上传到 NAS
# 重新部署
```
