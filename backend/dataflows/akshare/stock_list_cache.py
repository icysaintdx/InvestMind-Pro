"""
股票列表本地缓存模块
定期从AKShare下载股票列表并保存到本地SQLite数据库
"""

import sqlite3
import akshare as ak
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from backend.utils.logging_config import get_logger

logger = get_logger("StockListCache")


class StockListCache:
    """股票列表缓存类"""

    def __init__(self, db_path: str = None):
        """初始化"""
        if db_path is None:
            # Docker 环境使用 /app/data 目录
            import os
            if os.path.exists('/app/data'):
                data_dir = Path('/app/data')
            else:
                # 本地开发使用 backend/data 目录
                data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "stock_list.db")

        self.db_path = db_path
        self.logger = logger
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建股票列表表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_list (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                market TEXT NOT NULL,
                update_time TEXT NOT NULL
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_name ON stock_list(name)
        """)
        
        # 创建更新记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS update_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                update_time TEXT NOT NULL,
                stock_count INTEGER NOT NULL,
                status TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        self.logger.info(f"✅ 数据库初始化完成: {self.db_path}")
    
    def need_update(self) -> bool:
        """检查是否需要更新（每天更新一次）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查是否有数据
        cursor.execute("SELECT COUNT(*) FROM stock_list")
        count = cursor.fetchone()[0]
        
        if count == 0:
            conn.close()
            return True  # 没有数据，需要更新
        
        # 检查最后更新时间
        cursor.execute("""
            SELECT update_time FROM update_log 
            WHERE status = 'success' 
            ORDER BY id DESC LIMIT 1
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if result is None:
            return True
        
        last_update = datetime.fromisoformat(result[0])
        return datetime.now() - last_update > timedelta(days=1)
    
    def update_stock_list(self) -> bool:
        """更新股票列表"""
        self.logger.info("开始更新股票列表...")
        
        try:
            stock_list = []
            
            # 获取沪市A股
            self.logger.info("获取沪市A股...")
            try:
                df_sh = ak.stock_info_sh_name_code(symbol="主板A股")
                for _, row in df_sh.iterrows():
                    stock_list.append({
                        'code': f"SH{row['证券代码']}",
                        'name': row['证券简称'],
                        'market': '上交所'
                    })
                self.logger.info(f"✅ 获取到{len(df_sh)}只沪市A股")
            except Exception as e:
                self.logger.error(f"❌ 获取沪市A股失败: {e}")
            
            # 获取深市A股
            self.logger.info("获取深市A股...")
            try:
                df_sz = ak.stock_info_sz_name_code(symbol="A股列表")
                for _, row in df_sz.iterrows():
                    stock_list.append({
                        'code': f"SZ{row['A股代码']}",
                        'name': row['A股简称'],
                        'market': '深交所'
                    })
                self.logger.info(f"✅ 获取到{len(df_sz)}只深市A股")
            except Exception as e:
                self.logger.error(f"❌ 获取深市A股失败: {e}")
            
            if not stock_list:
                self.logger.error("❌ 未获取到任何股票数据")
                return False
            
            # 保存到数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 清空旧数据
            cursor.execute("DELETE FROM stock_list")
            
            # 插入新数据
            update_time = datetime.now().isoformat()
            for stock in stock_list:
                cursor.execute("""
                    INSERT INTO stock_list (code, name, market, update_time)
                    VALUES (?, ?, ?, ?)
                """, (stock['code'], stock['name'], stock['market'], update_time))
            
            # 记录更新日志
            cursor.execute("""
                INSERT INTO update_log (update_time, stock_count, status)
                VALUES (?, ?, ?)
            """, (update_time, len(stock_list), 'success'))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ 股票列表更新完成: {len(stock_list)}只")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 更新股票列表失败: {e}")
            
            # 记录失败日志
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO update_log (update_time, stock_count, status)
                    VALUES (?, ?, ?)
                """, (datetime.now().isoformat(), 0, f'failed: {str(e)}'))
                conn.commit()
                conn.close()
            except:
                pass
            
            return False
    
    def search(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索股票"""
        if not keyword:
            return []
        
        keyword = keyword.strip().upper()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 先精确匹配代码
        cursor.execute("""
            SELECT code, name, market FROM stock_list
            WHERE code LIKE ?
            LIMIT ?
        """, (f'%{keyword}%', limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'code': row[0],
                'name': row[1],
                'market': row[2]
            })
        
        # 如果结果不够，模糊匹配名称
        if len(results) < limit:
            cursor.execute("""
                SELECT code, name, market FROM stock_list
                WHERE name LIKE ? AND code NOT IN ({})
                LIMIT ?
            """.format(','.join('?' * len(results))), 
            (f'%{keyword}%', *[r['code'] for r in results], limit - len(results)))
            
            for row in cursor.fetchall():
                results.append({
                    'code': row[0],
                    'name': row[1],
                    'market': row[2]
                })
        
        conn.close()
        return results
    
    def get_stock_count(self) -> int:
        """获取股票总数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stock_list")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_last_update_time(self) -> str:
        """获取最后更新时间"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT update_time FROM update_log 
            WHERE status = 'success' 
            ORDER BY id DESC LIMIT 1
        """)
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None


# 全局实例
_cache = None

def get_stock_cache():
    """获取股票缓存实例（单例）"""
    global _cache
    if _cache is None:
        _cache = StockListCache()
        # 检查是否需要更新
        if _cache.need_update():
            logger.info("检测到需要更新股票列表...")
            _cache.update_stock_list()
    return _cache
