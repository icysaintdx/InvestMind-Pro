"""
测试智能体列表API是否返回priority字段
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_agents_list_priority():
    """测试智能体列表是否包含priority字段"""
    print("=" * 60)
    print("测试智能体列表API - priority字段")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/agents/list")
        print(f"\n状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            agents = data.get('agents', [])
            
            print(f"智能体总数: {len(agents)}")
            
            # 按优先级分组
            core_agents = [a for a in agents if a.get('priority') == 'core']
            important_agents = [a for a in agents if a.get('priority') == 'important']
            optional_agents = [a for a in agents if a.get('priority') == 'optional']
            no_priority = [a for a in agents if 'priority' not in a]
            
            print(f"\n按优先级分组:")
            print(f"  核心智能体 (core): {len(core_agents)}")
            print(f"  重要智能体 (important): {len(important_agents)}")
            print(f"  可选智能体 (optional): {len(optional_agents)}")
            print(f"  缺少priority字段: {len(no_priority)}")
            
            if no_priority:
                print(f"\n⚠️ 警告: {len(no_priority)}个智能体缺少priority字段:")
                for agent in no_priority:
                    print(f"  - {agent['name']} ({agent['id']})")
            
            # 显示每个分组的智能体
            print(f"\n核心智能体 ({len(core_agents)}个):")
            for agent in core_agents:
                deps = agent.get('dependencies', [])
                deps_str = f" [依赖: {', '.join(deps)}]" if deps else ""
                print(f"  {agent['icon']} {agent['name']}{deps_str}")
            
            print(f"\n重要智能体 ({len(important_agents)}个):")
            for agent in important_agents:
                deps = agent.get('dependencies', [])
                deps_str = f" [依赖: {', '.join(deps)}]" if deps else ""
                print(f"  {agent['icon']} {agent['name']}{deps_str}")
            
            print(f"\n可选智能体 ({len(optional_agents)}个):")
            for agent in optional_agents:
                deps = agent.get('dependencies', [])
                deps_str = f" [依赖: {', '.join(deps)}]" if deps else ""
                print(f"  {agent['icon']} {agent['name']}{deps_str}")
            
            # 验证结果
            if len(core_agents) == 9 and len(important_agents) == 7 and len(optional_agents) == 5:
                print("\n✅ 测试通过: 智能体分组正确!")
                print(f"   核心: 9个 ✓")
                print(f"   重要: 7个 ✓")
                print(f"   可选: 5个 ✓")
                return True
            else:
                print("\n❌ 测试失败: 智能体分组数量不正确!")
                print(f"   核心: 期望9个, 实际{len(core_agents)}个")
                print(f"   重要: 期望7个, 实际{len(important_agents)}个")
                print(f"   可选: 期望5个, 实际{len(optional_agents)}个")
                return False
        else:
            print(f"❌ 错误: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误: 无法连接到后端服务器")
        print("请确保后端服务器正在运行: python backend/server.py")
        return False
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_agents_list_priority()
    print("\n" + "=" * 60)
    if success:
        print("✅ 所有测试通过!")
    else:
        print("❌ 测试失败!")
    print("=" * 60)
