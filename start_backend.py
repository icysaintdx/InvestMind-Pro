#!/usr/bin/env python
"""
后端启动脚本 - 检查配置并启动服务器
"""
import os
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

# 切换到backend目录
os.chdir(backend_dir)

# 导入并检查配置
from dotenv import load_dotenv

# 加载环境变量
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    load_dotenv(env_file, override=True)
    print(f"✅ 加载环境变量文件: {env_file}")

# 检查API Keys
print("\n📋 环境变量检查:")
api_keys = {
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
    "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY"),
    "DASHSCOPE_API_KEY": os.getenv("DASHSCOPE_API_KEY"),
    "QWEN_API_KEY": os.getenv("QWEN_API_KEY"),
    "SILICONFLOW_API_KEY": os.getenv("SILICONFLOW_API_KEY"),
    "JUHE_API_KEY": os.getenv("JUHE_API_KEY")
}

for key, value in api_keys.items():
    if value:
        print(f"  ✅ {key}: 已配置 (长度: {len(value)})")
    else:
        print(f"  ❌ {key}: 未配置")

# 检查agent_configs.json
config_file = backend_dir / 'agent_configs.json'
if config_file.exists():
    import json
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(f"\n📁 配置文件检查:")
    print(f"  ✅ agent_configs.json 存在")
    print(f"  - 智能体数量: {len(config.get('agents', []))}")
    print(f"  - 选中模型数量: {len(config.get('selectedModels', []))}")
    if config.get('selectedModels'):
        print(f"  - 选中的模型:")
        for model in config['selectedModels'][:5]:  # 只显示前5个
            print(f"    • {model}")
        if len(config['selectedModels']) > 5:
            print(f"    ... 还有 {len(config['selectedModels']) - 5} 个模型")

# 启动服务器
print("\n🚀 启动后端服务器...")
print("=" * 60)

# 使用 subprocess 启动 uvicorn
import subprocess
subprocess.run([
    sys.executable, "-m", "uvicorn",
    "server:app",
    "--host", "0.0.0.0",
    "--port", "8000",
    "--reload"
])
