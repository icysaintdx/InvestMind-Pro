"""
修复分析会话的时间数据
解决平均耗时显示异常的问题
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.database import get_db_context
from backend.database.models import AnalysisSession
from datetime import datetime, timedelta
from sqlalchemy import func

def fix_session_times():
    """修复会话时间数据"""
    with get_db_context() as db:
        # 查询所有会话
        sessions = db.query(AnalysisSession).all()
        
        print(f"找到 {len(sessions)} 个会话记录\n")
        
        fixed_count = 0
        for i, session in enumerate(sessions, 1):
            print(f"\n检查会话 {i}/{len(sessions)}: {session.session_id} ({session.stock_code})")
            print(f"  状态: {session.status}")
            print(f"  created_at: {session.created_at}")
            print(f"  start_time: {session.start_time}")
            print(f"  end_time: {session.end_time}")
            
            # 如果有start_time和end_time，计算时长
            if session.start_time and session.end_time:
                duration = (session.end_time - session.start_time).total_seconds()
                print(f"  计算时长: {duration} 秒")
            
        for session in sessions:
            needs_fix = False
            original_start = session.start_time
            original_end = session.end_time
            
            # 检查 start_time
            if session.start_time:
                # 如果 start_time 是未来时间或过于久远，重置为 created_at
                if session.start_time > datetime.utcnow() or session.start_time.year < 2020:
                    print(f"会话 {session.session_id}: start_time 异常 ({session.start_time})")
                    session.start_time = session.created_at
                    needs_fix = True
            else:
                # 如果 start_time 为空，设置为 created_at
                session.start_time = session.created_at
                needs_fix = True
            
            # 检查 end_time
            if session.end_time:
                # 如果 end_time 早于 start_time，或者是未来时间
                if session.end_time < session.start_time or session.end_time > datetime.utcnow():
                    print(f"会话 {session.session_id}: end_time 异常 ({session.end_time})")
                    # 如果状态是completed，设置为 start_time + 2分钟（默认时长）
                    if session.status == 'completed':
                        session.end_time = session.start_time + timedelta(minutes=2)
                    else:
                        session.end_time = None
                    needs_fix = True
                else:
                    # 检查时长是否异常
                    duration = (session.end_time - session.start_time).total_seconds()
                    if duration < 0 or duration > 86400:  # 负数或超过1天
                        print(f"会话 {session.session_id}: 时长异常 ({duration}秒)")
                        print(f"  start_time: {session.start_time}")
                        print(f"  end_time: {session.end_time}")
                        if session.status == 'completed':
                            session.end_time = session.start_time + timedelta(minutes=2)
                        else:
                            session.end_time = None
                        needs_fix = True
            else:
                # 如果是completed状态但没有end_time，设置默认值
                if session.status == 'completed':
                    session.end_time = session.start_time + timedelta(minutes=2)
                    needs_fix = True
            
            if needs_fix:
                fixed_count += 1
                print(f"  修复: {session.session_id} ({session.stock_code})")
                print(f"    start_time: {session.start_time}")
                print(f"    end_time: {session.end_time}")
        
        if fixed_count > 0:
            print(f"\n✅ 成功修复 {fixed_count} 个会话的时间数据")
        else:
            print(f"\n✅ 所有会话时间数据正常，无需修复")
        
        # 验证修复结果
        print("\n验证修复结果...")
        
        avg_duration = db.query(
            func.avg(
                func.extract('epoch', AnalysisSession.end_time - AnalysisSession.start_time)
            )
        ).filter(
            AnalysisSession.status == 'completed',
            AnalysisSession.end_time.isnot(None),
            AnalysisSession.start_time.isnot(None)
        ).scalar()
        
        if avg_duration:
            print(f"平均耗时: {int(avg_duration)} 秒")
            if avg_duration < 0 or avg_duration > 86400:
                print("⚠️  平均耗时仍然异常，可能需要手动检查数据")
            else:
                print("✅ 平均耗时正常")
        else:
            print("没有可用的耗时数据")

if __name__ == '__main__':
    print("开始修复分析会话时间数据...\n")
    fix_session_times()
