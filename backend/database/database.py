"""
数据库连接和会话管理
"""

import os
import threading
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from backend.database.models import Base

# 数据库配置
# 优先使用环境变量，否则使用 /app/data 目录（Docker）或当前目录（本地开发）
def get_default_db_path():
    # Docker 环境使用 /app/data 目录
    if os.path.exists('/app/data'):
        return "sqlite:////app/data/InvestMindPro.db"
    # 本地开发使用当前目录
    return "sqlite:///./InvestMindPro.db"

DATABASE_URL = os.getenv("DATABASE_URL", get_default_db_path())

# SQLite 写入锁（防止并发写入冲突）
_sqlite_write_lock = threading.Lock()

# 创建引擎
# SQLite 需要特殊配置以支持多线程
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 30  # 增加超时时间
        },
        poolclass=StaticPool,
        echo=False  # 设置为 True 可以看到 SQL 语句
    )

    # 启用 WAL 模式以提高并发性能
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")  # 30秒超时
        cursor.close()
else:
    # PostgreSQL/MySQL 配置
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False
    )
    _sqlite_write_lock = None  # 非 SQLite 不需要锁

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 线程安全的会话
ScopedSession = scoped_session(SessionLocal)


def init_database():
    """初始化数据库，创建所有表"""
    print("[数据库] 初始化数据库...")
    Base.metadata.create_all(bind=engine)

    # 自动迁移：添加新列（如果不存在）
    migrate_database()

    print("[数据库] 数据库初始化完成")


def migrate_database():
    """
    数据库迁移：添加新列（如果不存在）
    这是一个简单的迁移方案，适用于 SQLite
    """
    try:
        with engine.connect() as conn:
            # 检查并添加 actual_elapsed_seconds 列
            try:
                conn.execute(text("SELECT actual_elapsed_seconds FROM analysis_sessions LIMIT 1"))
            except Exception:
                print("[数据库迁移] 添加 actual_elapsed_seconds 列...")
                conn.execute(text("ALTER TABLE analysis_sessions ADD COLUMN actual_elapsed_seconds INTEGER DEFAULT 0"))
                conn.commit()

            # 检查并添加 last_activity_time 列
            try:
                conn.execute(text("SELECT last_activity_time FROM analysis_sessions LIMIT 1"))
            except Exception:
                print("[数据库迁移] 添加 last_activity_time 列...")
                conn.execute(text("ALTER TABLE analysis_sessions ADD COLUMN last_activity_time DATETIME"))
                conn.commit()

            print("[数据库迁移] 迁移检查完成")
    except Exception as e:
        print(f"[数据库迁移] 迁移失败: {e}")


def drop_all_tables():
    """删除所有表（慎用！）"""
    print("[数据库] 警告：删除所有表...")
    Base.metadata.drop_all(bind=engine)
    print("[数据库] 所有表已删除")


def get_db():
    """
    获取数据库会话（依赖注入）
    用于 FastAPI 的 Depends
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    获取数据库会话（上下文管理器）
    用于普通 Python 代码
    
    使用示例：
    with get_db_context() as db:
        session = db.query(AnalysisSession).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_db_session():
    """
    获取数据库会话（手动管理）
    需要手动 close
    """
    return SessionLocal()


# 测试数据库连接
def test_connection():
    """测试数据库连接"""
    try:
        with get_db_context() as db:
            # 执行简单查询（使用 text() 函数）
            result = db.execute(text("SELECT 1")).fetchone()
            print(f"[数据库] 连接测试成功: {result}")
            return True
    except Exception as e:
        print(f"[数据库] 连接测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    # 初始化数据库
    init_database()
    
    # 测试连接
    test_connection()
