"""
测试数据库集成
验证整个流程是否正常工作
"""

import sys
import os
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

import time
from backend.database.database import init_database, get_db_context
from backend.database.services import SessionService, AgentResultService
from backend.database.analysis_helper import save_agent_result, complete_analysis, get_agent_name_map

def test_full_workflow():
    """测试完整的分析工作流"""
    print("=" * 60)
    print("测试数据库集成")
    print("=" * 60)
    
    # 1. 初始化数据库
    print("\n1. 初始化数据库...")
    init_database()
    print("✅ 数据库初始化完成")
    
    # 2. 创建会话
    print("\n2. 创建测试会话...")
    session_id = f"test_session_{int(time.time())}"
    
    with get_db_context() as db:
        session = SessionService.create_session(
            db=db,
            session_id=session_id,
            stock_code="600000",
            stock_name="浦发银行"
        )
        print(f"✅ 会话创建成功: {session.session_id}")
    
    # 3. 模拟智能体分析
    print("\n3. 模拟智能体分析...")
    agent_map = get_agent_name_map()
    test_agents = ['news_analyst', 'social_analyst', 'china_market']
    
    for i, agent_id in enumerate(test_agents):
        print(f"\n   [{i+1}/{len(test_agents)}] {agent_map[agent_id]}...")
        
        # 开始运行
        save_agent_result(
            session_id=session_id,
            agent_id=agent_id,
            agent_name=agent_map[agent_id],
            status='running'
        )
        
        # 模拟分析耗时
        time.sleep(0.5)
        
        # 完成
        save_agent_result(
            session_id=session_id,
            agent_id=agent_id,
            agent_name=agent_map[agent_id],
            status='completed',
            output=f"这是{agent_map[agent_id]}的分析结果...",
            tokens=1000 + i * 100,
            thoughts=[
                {'step': 1, 'content': '收集数据'},
                {'step': 2, 'content': '分析数据'},
                {'step': 3, 'content': '得出结论'}
            ],
            data_sources=[
                {'source': '数据源A', 'count': 5},
                {'source': '数据源B', 'count': 3}
            ]
        )
        print(f"   ✅ {agent_map[agent_id]} 完成")
    
    # 4. 查询进度
    print("\n4. 查询分析进度...")
    with get_db_context() as db:
        session = SessionService.get_session(db, session_id)
        completed = AgentResultService.get_completed_agents(db, session_id)
        
        print(f"   会话状态: {session.status}")
        print(f"   进度: {session.progress}%")
        print(f"   当前阶段: {session.current_stage}")
        print(f"   已完成智能体: {len(completed)}/21")
        print(f"   完成列表: {', '.join(completed)}")
    
    # 5. 查询智能体结果
    print("\n5. 查询智能体结果...")
    with get_db_context() as db:
        result = AgentResultService.get_result(db, session_id, 'news_analyst')
        if result:
            print(f"   智能体: {result.agent_name}")
            print(f"   状态: {result.status}")
            print(f"   输出: {result.output[:50]}...")
            print(f"   Tokens: {result.tokens}")
            print(f"   耗时: {result.duration_seconds}秒")
    
    # 6. 完成分析
    print("\n6. 标记分析完成...")
    complete_analysis(session_id=session_id, success=True)
    
    with get_db_context() as db:
        session = SessionService.get_session(db, session_id)
        print(f"   最终状态: {session.status}")
        print(f"   最终进度: {session.progress}%")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！所有功能正常工作")
    print("=" * 60)
    
    print("\n📊 数据库文件位置: ./InvestMindPro.db")
    print("可以使用 DB Browser for SQLite 查看数据")
    
    print("\n🔍 查询示例:")
    print("  SELECT * FROM analysis_sessions;")
    print("  SELECT * FROM agent_results;")
    
    return session_id


def test_api_endpoints():
    """测试 API 端点"""
    print("\n" + "=" * 60)
    print("测试 API 端点")
    print("=" * 60)
    
    import requests
    
    base_url = "http://localhost:8000"
    
    tests = [
        ("GET", "/api/analysis/db/sessions/active", "查看活跃会话"),
        ("GET", "/api/analysis/db/history/recent?limit=5", "查看最近分析"),
        ("GET", "/api/analysis/db/stats/overview?days=7", "查看统计概览"),
    ]
    
    print("\n⚠️  请确保后端服务器正在运行: python backend/server.py")
    input("按回车继续测试 API...")
    
    for method, endpoint, desc in tests:
        try:
            print(f"\n测试: {desc}")
            print(f"  {method} {endpoint}")
            
            response = requests.get(f"{base_url}{endpoint}")
            
            if response.ok:
                data = response.json()
                print(f"  ✅ 成功: {response.status_code}")
                print(f"  响应: {str(data)[:100]}...")
            else:
                print(f"  ❌ 失败: {response.status_code}")
        
        except Exception as e:
            print(f"  ❌ 错误: {e}")


if __name__ == "__main__":
    # 测试数据库集成
    session_id = test_full_workflow()
    
    # 询问是否测试 API
    print("\n是否测试 API 端点？(需要启动后端服务器)")
    choice = input("输入 'yes' 测试 API，其他键跳过: ").strip().lower()
    
    if choice == 'yes':
        test_api_endpoints()
    
    print("\n✅ 所有测试完成！")
