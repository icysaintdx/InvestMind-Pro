"""测试配置加载"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量 - 与server.py相同的方式
env_file = Path(__file__).parent.parent / '.env'
print(f"环境文件路径: {env_file}")
print(f"文件是否存在: {env_file.exists()}")

if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ 已加载环境变量文件: {env_file}")
else:
    load_dotenv()
    print("⚠️ 使用默认环境变量加载")

# 测试API Keys
API_KEYS = {
    "gemini": os.getenv("GEMINI_API_KEY", ""),
    "deepseek": os.getenv("DEEPSEEK_API_KEY", ""),
    "qwen": os.getenv("DASHSCOPE_API_KEY", "") or os.getenv("QWEN_API_KEY", ""),
    "siliconflow": os.getenv("SILICONFLOW_API_KEY", ""),
    "juhe": os.getenv("JUHE_API_KEY", "")
}

print("\n📋 API Keys 配置状态:")
for name, key in API_KEYS.items():
    if key:
        # 只显示前10个字符
        display_key = key[:10] + "..." if len(key) > 10 else key
        print(f"  {name.upper()}: ✅ 已配置 ({display_key})")
    else:
        print(f"  {name.upper()}: ❌ 未配置")

print("\n原始环境变量:")
print(f"  GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY', 'NOT FOUND')[:20] if os.getenv('GEMINI_API_KEY') else 'NOT FOUND'}")
print(f"  DEEPSEEK_API_KEY: {os.getenv('DEEPSEEK_API_KEY', 'NOT FOUND')[:20] if os.getenv('DEEPSEEK_API_KEY') else 'NOT FOUND'}")
print(f"  JUHE_API_KEY: {os.getenv('JUHE_API_KEY', 'NOT FOUND')[:20] if os.getenv('JUHE_API_KEY') else 'NOT FOUND'}")
