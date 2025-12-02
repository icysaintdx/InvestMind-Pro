"""调试配置加载问题"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import json

print("=" * 60)
print("配置调试脚本")
print("=" * 60)

# 1. 检查环境变量加载
env_file = Path(__file__).parent.parent / '.env'
print(f"\n1. 环境变量文件: {env_file}")
print(f"   文件存在: {env_file.exists()}")

if env_file.exists():
    load_dotenv(env_file, override=True)
    print("   ✅ 文件已加载")

# 2. 检查环境变量值
print("\n2. 环境变量检查:")
keys_to_check = [
    "GEMINI_API_KEY",
    "DEEPSEEK_API_KEY", 
    "QWEN_API_KEY",
    "DASHSCOPE_API_KEY",
    "SILICONFLOW_API_KEY",
    "JUHE_API_KEY"
]

for key in keys_to_check:
    value = os.getenv(key, "")
    if value:
        print(f"   ✅ {key}: 已设置 (前10字符: {value[:10]}...)")
    else:
        print(f"   ❌ {key}: 未设置")

# 3. 测试server.py中的API_KEYS
print("\n3. 测试server.py的API_KEYS配置:")
API_KEYS = {
    "gemini": os.getenv("GEMINI_API_KEY", ""),
    "deepseek": os.getenv("DEEPSEEK_API_KEY", ""),
    "qwen": os.getenv("DASHSCOPE_API_KEY", "") or os.getenv("QWEN_API_KEY", ""),
    "siliconflow": os.getenv("SILICONFLOW_API_KEY", ""),
    "juhe": os.getenv("JUHE_API_KEY", "")
}

for key, value in API_KEYS.items():
    if value:
        print(f"   ✅ {key}: 已配置")
    else:
        print(f"   ❌ {key}: 未配置")

# 4. 检查agent_configs.json
print("\n4. 检查agent_configs.json:")
config_file = Path(__file__).parent / 'agent_configs.json'
if config_file.exists():
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print(f"   ✅ 文件存在")
    print(f"   - 智能体数量: {len(config.get('agents', []))}")
    print(f"   - 选中模型数量: {len(config.get('selectedModels', []))}")
    
    if config.get('selectedModels'):
        print("   - 选中的模型:")
        for i, model in enumerate(config['selectedModels'], 1):
            print(f"     {i}. {model}")
else:
    print(f"   ❌ 文件不存在")

print("\n" + "=" * 60)
print("调试完成")
print("=" * 60)
