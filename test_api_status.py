"""
测试API配置状态
验证后端是否正确返回API配置信息
"""

import requests
import json

print("="*60)
print("测试API配置状态")
print("="*60)

try:
    # 测试配置端点
    response = requests.get('http://localhost:8000/api/config')
    
    if response.status_code == 200:
        data = response.json()
        
        print("\n✅ 后端连接成功")
        print("-"*40)
        
        # 检查API Keys
        if 'api_keys' in data:
            print("\n已配置的API:")
            for provider, key in data['api_keys'].items():
                if key:
                    # 只显示前10个字符
                    masked_key = key[:10] + '...' if len(key) > 10 else key
                    print(f"  ✅ {provider}: {masked_key}")
                else:
                    print(f"  ❌ {provider}: 未配置")
        
        # 检查端点
        if 'endpoints' in data:
            print(f"\n可用端点数: {len(data['endpoints'])}")
        
        # 检查后端状态
        if 'backend_status' in data:
            print(f"后端状态: {data['backend_status']}")
            
        # 生成前端期望的格式
        print("\n前端期望看到的状态:")
        print("-"*40)
        
        ai_providers = ['gemini', 'deepseek', 'qwen', 'siliconflow']
        for provider in ai_providers:
            if data.get('api_keys', {}).get(provider):
                print(f"  {provider}: configured ✅")
            else:
                print(f"  {provider}: not_configured ❌")
        
        data_providers = ['juhe', 'finnhub', 'tushare']
        print("\n数据源状态:")
        for provider in data_providers:
            if data.get('api_keys', {}).get(provider):
                print(f"  {provider}: configured ✅")
            else:
                print(f"  {provider}: not_configured ❌")
                
    else:
        print(f"❌ 后端返回错误: HTTP {response.status_code}")
        print("请确保后端已启动: python backend/server.py")
        
except requests.exceptions.ConnectionError:
    print("❌ 无法连接到后端")
    print("请先启动后端服务器:")
    print("  python backend/server.py")
except Exception as e:
    print(f"❌ 测试失败: {str(e)}")

print("\n" + "="*60)
