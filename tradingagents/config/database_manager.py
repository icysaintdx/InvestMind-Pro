"""
tradingagents.config.database_manager 兼容层
提供数据库管理器的兼容实现
"""
import os

def get_mongodb_client():
    """获取 MongoDB 客户端（如果可用）"""
    try:
        from pymongo import MongoClient
        mongo_uri = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')
        return MongoClient(mongo_uri)
    except ImportError:
        return None
    except Exception:
        return None

def get_database_manager():
    """获取数据库管理器"""
    class DatabaseManager:
        def __init__(self):
            self.mongodb_config = {
                'database': os.environ.get('MONGODB_DATABASE', 'investmind'),
                'uri': os.environ.get('MONGODB_URI', 'mongodb://localhost:27017'),
            }
            self.redis_config = {
                'host': os.environ.get('REDIS_HOST', 'localhost'),
                'port': int(os.environ.get('REDIS_PORT', 6379)),
            }

        def get_mongodb_client(self):
            return get_mongodb_client()

    return DatabaseManager()

__all__ = ['get_mongodb_client', 'get_database_manager']
