"""
数据库连接和会话管理
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from backend.database.models import Base

# 数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./alphacouncil.db"  # 默认使用 SQLite
)

# 创建引擎
# SQLite 需要特殊配置以支持多线程
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # 设置为 True 可以看到 SQL 语句
    )
else:
    # PostgreSQL/MySQL 配置
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 线程安全的会话
ScopedSession = scoped_session(SessionLocal)


def init_database():
    """初始化数据库，创建所有表"""
    print("[数据库] 初始化数据库...")
    Base.metadata.create_all(bind=engine)
    print("[数据库] 数据库初始化完成")


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
