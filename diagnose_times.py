"""
诊断时间数据问题
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.database import get_db_context
from backend.database.models import AnalysisSession
from sqlalchemy import func

output_file = 'time_diagnosis.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    with get_db_context() as db:
        sessions = db.query(AnalysisSession).filter(
            AnalysisSession.status == 'completed'
        ).all()
        
        f.write(f"Completed sessions: {len(sessions)}\n\n")
        
        for session in sessions:
            f.write(f"Session: {session.session_id} ({session.stock_code})\n")
            f.write(f"  start_time: {session.start_time} (type: {type(session.start_time)})\n")
            f.write(f"  end_time: {session.end_time} (type: {type(session.end_time)})\n")
            
            if session.start_time and session.end_time:
                # Python calculation
                duration_py = (session.end_time - session.start_time).total_seconds()
                f.write(f"  Python duration: {duration_py} seconds\n")
                
                # Check timestamps
                if hasattr(session.start_time, 'timestamp'):
                    start_ts = session.start_time.timestamp()
                    end_ts = session.end_time.timestamp()
                    f.write(f"  start timestamp: {start_ts}\n")
                    f.write(f"  end timestamp: {end_ts}\n")
                    f.write(f"  timestamp diff: {end_ts - start_ts} seconds\n")
            f.write("\n")
        
        # SQL calculation
        f.write("\nSQL calculation:\n")
        result = db.query(
            AnalysisSession.session_id,
            AnalysisSession.start_time,
            AnalysisSession.end_time,
            func.extract('epoch', AnalysisSession.end_time - AnalysisSession.start_time).label('duration')
        ).filter(
            AnalysisSession.status == 'completed',
            AnalysisSession.end_time.isnot(None),
            AnalysisSession.start_time.isnot(None)
        ).all()
        
        for row in result:
            f.write(f"{row.session_id}: {row.duration} seconds\n")

print(f"Diagnosis complete. Check {output_file}")
