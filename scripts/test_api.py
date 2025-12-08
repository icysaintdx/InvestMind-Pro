"""测试API接口"""
import requests
import json

# 测试 /api/config/agents 接口
print("=" * 50)
print("测试 /api/config/agents 接口")
print("=" * 50)

try:
    response = requests.get("http://localhost:8000/api/config/agents")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"响应成功: {data.get('success')}")
        
        if data.get('data'):
            config = data['data']
            print(f"智能体数量: {len(config.get('agents', []))}")
            print(f"选中模型数量: {len(config.get('selectedModels', []))}")
            
            if config.get('selectedModels'):
                print("\n选中的模型列表:")
                for i, model in enumerate(config['selectedModels'], 1):
                    print(f"  {i}. {model}")
        else:
            print("响应中没有data字段")
    else:
        print(f"请求失败: {response.text}")
        
except Exception as e:
    print(f"错误: {e}")
    print("请确保后端服务器正在运行")

# 测试 /api/config 接口
print("\n" + "=" * 50)
print("测试 /api/config 接口")
print("=" * 50)

try:
    response = requests.get("http://localhost:8000/api/config")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("API密钥状态:")
        for key, value in data.get('api_keys', {}).items():
            status = "✅ 已配置" if value == "configured" else "❌ 未配置"
            print(f"  {key}: {status}")
    else:
        print(f"请求失败: {response.text}")
        
except Exception as e:
    print(f"错误: {e}")
