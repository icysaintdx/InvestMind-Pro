"""
数据库初始化脚本
运行此脚本创建数据库表
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.database.database import init_database, test_connection, drop_all_tables

def main():
    print("=" * 60)
    print("InvestMindPro 数据库初始化")
    print("=" * 60)
    
    # 测试连接
    print("\n1. 测试数据库连接...")
    if not test_connection():
        print("❌ 数据库连接失败，请检查配置")
        return
    
    print("✅ 数据库连接成功")
    
    # 询问是否重建表
    print("\n2. 是否需要重建所有表？")
    print("   警告：这将删除所有现有数据！")
    choice = input("   输入 'yes' 确认重建，其他键跳过: ").strip().lower()
    
    if choice == 'yes':
        print("\n   删除所有表...")
        drop_all_tables()
        print("   ✅ 所有表已删除")
    
    # 创建表
    print("\n3. 创建数据库表...")
    init_database()
    print("✅ 数据库表创建完成")
    
    # 显示表信息
    print("\n4. 数据库表结构:")
    print("   - analysis_sessions: 分析会话表")
    print("   - agent_results: 智能体结果表")
    print("   - stock_history: 股票历史统计表")
    
    print("\n" + "=" * 60)
    print("✅ 数据库初始化完成！")
    print("=" * 60)
    
    print("\n数据库文件位置: ./InvestMindPro.db")
    print("可以使用 SQLite 工具查看数据库内容")
    print("\n测试 API:")
    print("  curl http://localhost:8000/api/analysis/db/sessions/active")

if __name__ == "__main__":
    main()
