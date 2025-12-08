"""
检查FastAPI应用的所有端点
"""
import sys
import os

# 添加backend到path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# 导入server模块
from server import app

# 获取所有路由
print("=" * 60)
print("FastAPI 注册的所有端点:")
print("=" * 60)

routes = []
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        routes.append({
            'path': route.path,
            'methods': list(route.methods),
            'name': route.name
        })

# 按路径排序
routes.sort(key=lambda x: x['path'])

# 打印所有路由
for route in routes:
    if route['methods']:
        methods = ', '.join(route['methods'])
        print(f"{methods:8} {route['path']:<40} [{route['name']}]")

print("=" * 60)

# 检查 /api/analyze 是否存在
analyze_routes = [r for r in routes if '/analyze' in r['path']]
if analyze_routes:
    print("\n✅ 找到 /api/analyze 路由:")
    for route in analyze_routes:
        print(f"  - {route['methods']}: {route['path']}")
else:
    print("\n❌ 没有找到 /api/analyze 路由！")
    
print("\n注意: 如果端点存在但请求失败，可能是:")
print("1. CORS问题")
print("2. 请求体格式问题")
print("3. 中间件拦截")
