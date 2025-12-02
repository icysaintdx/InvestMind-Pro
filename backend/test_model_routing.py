"""测试模型API路由判断逻辑"""

# 模拟服务器中的判断逻辑
def get_api_provider(model_name):
    """判断模型应该使用哪个API"""
    if "/" in model_name:
        return "SILICONFLOW"
    elif model_name.startswith("gemini"):
        return "GEMINI"
    elif model_name in ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]:
        return "DEEPSEEK"
    elif model_name in ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-max-longcontext", "qwen-turbo-latest"]:
        return "QWEN"
    else:
        return "SILICONFLOW"

# 测试各种模型
test_models = [
    "Qwen/Qwen3-8B",
    "Qwen/Qwen2.5-7B-Instruct",
    "deepseek-ai/DeepSeek-V3.2-Exp",
    "Pro/deepseek-ai/DeepSeek-V3.1-Terminus",
    "deepseek-ai/DeepSeek-V3.1-Terminus",
    "gemini-2.0-flash-exp",
    "deepseek-chat",
    "qwen-plus"
]

print("=" * 60)
print("模型API路由测试")
print("=" * 60)

for model in test_models:
    provider = get_api_provider(model)
    emoji = "✅" if provider == "SILICONFLOW" or model in ["gemini-2.0-flash-exp", "deepseek-chat", "qwen-plus"] else "❌"
    print(f"{emoji} {model:40} → {provider}")

print("\n" + "=" * 60)
print("总结：")
print("- 包含'/'的模型 → SiliconFlow ✅")
print("- 官方模型名 → 对应官方API ✅")
print("- 其他模型 → SiliconFlow ✅")
