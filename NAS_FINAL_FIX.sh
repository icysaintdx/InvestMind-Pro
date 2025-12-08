#!/bin/bash
# NAS 最终修复脚本

echo "=========================================="
echo "AlphaCouncil NAS 最终修复"
echo "=========================================="
echo

# 1. 删除所有 Nginx 配置
echo "1. 清理 Nginx 配置..."
rm -f /etc/nginx/sites-enabled/*
rm -f /etc/nginx/conf.d/*

# 2. 创建最简单的配置
echo "2. 创建新配置..."
cat > /etc/nginx/conf.d/default.conf << 'NGINX_EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    root /app/frontend/dist;
    index index.html;
    
    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # 静态文件
    location / {
        try_files $uri $uri/ /index.html;
    }
}
NGINX_EOF

# 3. 修复前端 API 地址
echo "3. 修复前端 API 地址..."
cd /app/frontend/src/views
sed -i 's|http://localhost:8000||g' AnalysisView.vue 2>/dev/null || true
sed -i 's|http://localhost:8000||g' HistoryView.vue 2>/dev/null || true
sed -i 's|http://localhost:8000||g' DocumentView.vue 2>/dev/null || true

# 4. 重新构建前端
echo "4. 重新构建前端..."
cd /app/frontend
npm run build

# 5. 测试 Nginx 配置
echo "5. 测试 Nginx 配置..."
nginx -t

# 6. 重启 Nginx
echo "6. 重启 Nginx..."
nginx -s stop
sleep 2
nginx

# 7. 测试
echo "7. 测试..."
echo "后端健康检查:"
curl -s http://127.0.0.1:8000/health
echo
echo "API 代理测试:"
curl -s http://127.0.0.1/api/models | head -c 100
echo "..."
echo

echo "=========================================="
echo "修复完成！"
echo "=========================================="
echo "现在访问: http://your-nas-ip:8808"
