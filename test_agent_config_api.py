"""
测试智能体配置API
验证依赖管理、配置验证、保存加载等功能
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_get_profiles():
    """测试获取配置方案"""
    print("\n=== 测试获取配置方案 ===")
    response = requests.get(f"{BASE_URL}/api/agents/config/profiles")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"可用方案: {list(data['profiles'].keys())}")
        for key, profile in data['profiles'].items():
            print(f"  - {key}: {profile['name']} ({profile['description']})")
    else:
        print(f"错误: {response.text}")

def test_get_current_config():
    """测试获取当前配置"""
    print("\n=== 测试获取当前配置 ===")
    response = requests.get(f"{BASE_URL}/api/agents/config/current")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"启用的智能体数量: {data['impact']['enabled_count']}")
        print(f"预计时间: {data['impact']['estimated_time']}秒")
        print(f"质量评分: {data['impact']['quality_score']}%")
    else:
        print(f"错误: {response.text}")

def test_apply_profile(profile_name):
    """测试应用配置方案"""
    print(f"\n=== 测试应用配置方案: {profile_name} ===")
    response = requests.post(f"{BASE_URL}/api/agents/config/profile/{profile_name}")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"消息: {data['message']}")
        print(f"启用的智能体: {data['impact']['enabled_count']}")
        print(f"预计时间: {data['impact']['estimated_time']}秒")
        print(f"质量评分: {data['impact']['quality_score']}%")
    else:
        print(f"错误: {response.text}")

def test_validate_config():
    """测试配置验证"""
    print("\n=== 测试配置验证 ===")
    
    # 测试有效配置
    valid_config = {
        "enabled": {
            "news_analyst": True,
            "fundamental": True,
            "technical": True,
            "bull_researcher": True,
            "bear_researcher": True,
            "research_manager": True,
            "risk_manager": True,
            "gm": True,
            "trader": True
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/agents/config/validate",
        json=valid_config
    )
    print(f"有效配置 - 状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"验证结果: {'通过' if data['valid'] else '失败'}")
        if data['warnings']:
            print(f"警告: {data['warnings']}")
    
    # 测试无效配置（缺少核心依赖）
    invalid_config = {
        "enabled": {
            "bull_researcher": True,  # 依赖news_analyst但未启用
            "bear_researcher": True
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/agents/config/validate",
        json=invalid_config
    )
    print(f"\n无效配置 - 状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"验证结果: {'通过' if data['valid'] else '失败'}")
        if data['warnings']:
            print(f"警告:")
            for warning in data['warnings']:
                print(f"  - {warning}")

def test_enable_disable_agent():
    """测试启用/禁用智能体"""
    print("\n=== 测试启用/禁用智能体 ===")
    
    # 测试启用可选智能体
    print("\n启用可选智能体: social_media_analyst")
    response = requests.post(
        f"{BASE_URL}/api/agents/config/enable/social_media_analyst",
        params={"auto_deps": True}
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"消息: {data['message']}")
    else:
        print(f"错误: {response.text}")
    
    # 测试禁用可选智能体
    print("\n禁用可选智能体: social_media_analyst")
    response = requests.post(
        f"{BASE_URL}/api/agents/config/disable/social_media_analyst"
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"消息: {data['message']}")
    else:
        print(f"错误: {response.text}")
    
    # 测试禁用核心智能体（应该失败）
    print("\n尝试禁用核心智能体: news_analyst")
    response = requests.post(
        f"{BASE_URL}/api/agents/config/disable/news_analyst"
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 400:
        print(f"预期的错误: {response.json()['detail']['message']}")
    else:
        print(f"意外结果: {response.text}")

def test_get_agents_by_priority():
    """测试按优先级获取智能体"""
    print("\n=== 测试按优先级获取智能体 ===")
    
    for priority in ['core', 'important', 'optional']:
        response = requests.get(f"{BASE_URL}/api/agents/config/priority/{priority}")
        print(f"\n{priority.upper()} 智能体:")
        if response.status_code == 200:
            data = response.json()
            print(f"数量: {data['count']}")
            for agent in data['agents']:
                print(f"  - {agent['icon']} {agent['name']} (Stage {agent['stage']})")
        else:
            print(f"错误: {response.text}")

def main():
    """运行所有测试"""
    print("=" * 60)
    print("智能体配置API测试")
    print("=" * 60)
    
    try:
        # 测试基础功能
        test_get_profiles()
        test_get_current_config()
        
        # 测试配置方案
        test_apply_profile("minimal")
        test_apply_profile("balanced")
        
        # 测试配置验证
        test_validate_config()
        
        # 测试启用/禁用
        test_enable_disable_agent()
        
        # 测试按优先级查询
        test_get_agents_by_priority()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误: 无法连接到后端服务器")
        print("请确保后端服务器正在运行: python backend/server.py")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
