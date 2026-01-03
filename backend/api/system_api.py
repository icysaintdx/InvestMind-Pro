# -*- coding: utf-8 -*-
"""
系统设置API
提供系统配置、数据库统计、服务状态等功能
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os
import json
from pathlib import Path

from backend.utils.logging_config import get_logger

logger = get_logger('system_api')
router = APIRouter(prefix='/api/system', tags=['System'])

CONFIG_FILE = Path('backend/config/system_settings.json')

DEFAULT_SETTINGS = {
    'newsRetentionDays': 30,
    'analysisRetentionDays': 90,
    'tradingRetentionDays': 365,
    'monitorRetentionDays': 7,
    'autoCleanup': True,
    'cleanupTime': '02:00'
}


class SystemSettings(BaseModel):
    newsRetentionDays: int = 30
    analysisRetentionDays: int = 90
    tradingRetentionDays: int = 365
    monitorRetentionDays: int = 7
    autoCleanup: bool = True
    cleanupTime: str = '02:00'
    cninfoAccessKey: Optional[str] = ''
    cninfoAccessSecret: Optional[str] = ''


def load_settings() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
        except Exception as e:
            logger.error(f'Load config failed: {e}')
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, Any]) -> bool:
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        safe_settings = {k: v for k, v in settings.items() if 'Secret' not in k and 'Key' not in k}
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(safe_settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f'Save config failed: {e}')
        return False


@router.get('/settings')
async def get_settings():
    try:
        settings = load_settings()
        settings['cninfoAccessKey'] = os.getenv('CNINFO_ACCESS_KEY', '')[:8] + '***' if os.getenv('CNINFO_ACCESS_KEY') else ''
        settings['cninfoAccessSecret'] = '******' if os.getenv('CNINFO_ACCESS_SECRET') else ''
        return {'success': True, 'data': settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/settings')
async def update_settings(settings: SystemSettings):
    try:
        if save_settings(settings.dict()):
            return {'success': True, 'message': 'Settings saved'}
        raise HTTPException(status_code=500, detail='Save failed')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/db-stats')
async def get_db_stats():
    try:
        from backend.database.database import engine
        from sqlalchemy import text
        
        stats = {}
        with engine.connect() as conn:
            try:
                result = conn.execute(text('SELECT COUNT(*) FROM market_news'))
                stats['newsCount'] = result.scalar() or 0
            except:
                stats['newsCount'] = 0
            
            try:
                result = conn.execute(text('SELECT COUNT(*) FROM analysis_sessions'))
                stats['analysisCount'] = result.scalar() or 0
            except:
                stats['analysisCount'] = 0
            
            stats['tradingCount'] = 0
            
            try:
                db_path = Path('InvestMindPro.db')
                stats['dbSize'] = db_path.stat().st_size if db_path.exists() else 0
            except:
                stats['dbSize'] = 0
        
        return {'success': True, 'data': stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/services')
async def get_services():
    try:
        services = []
        
        try:
            from backend.services.news_center import get_news_monitor_center
            monitor = get_news_monitor_center()
            services.append({
                'name': 'News Monitor',
                'status': 'running' if monitor._running else 'stopped',
                'statusText': 'Running' if monitor._running else 'Stopped'
            })
        except:
            services.append({'name': 'News Monitor', 'status': 'unknown', 'statusText': 'Unknown'})
        
        try:
            from backend.dataflows.data_cleanup_scheduler import get_cleanup_scheduler
            scheduler = get_cleanup_scheduler()
            services.append({
                'name': 'Cleanup Scheduler',
                'status': 'running' if scheduler.running else 'stopped',
                'statusText': 'Running' if scheduler.running else 'Stopped'
            })
        except:
            services.append({'name': 'Cleanup Scheduler', 'status': 'unknown', 'statusText': 'Unknown'})
        
        return {'success': True, 'data': services}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/cleanup')
async def manual_cleanup():
    try:
        settings = load_settings()
        results = {}
        
        try:
            from backend.services.news_center.news_storage import get_news_storage
            storage = get_news_storage()
            results['news'] = storage.cleanup_old_news(days=settings.get('newsRetentionDays', 30))
        except Exception as e:
            results['news'] = f'Error: {e}'
        
        try:
            from backend.database.database import get_db_context
            from backend.database.models import AnalysisSession
            
            with get_db_context() as db:
                cutoff = datetime.now() - timedelta(days=settings.get('analysisRetentionDays', 90))
                deleted = db.query(AnalysisSession).filter(AnalysisSession.created_at < cutoff).delete()
                results['analysis'] = deleted
        except Exception as e:
            results['analysis'] = f'Error: {e}'
        
        return {'success': True, 'message': 'Cleanup done', 'results': results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/test-cninfo')
async def test_cninfo():
    try:
        from backend.dataflows.announcement.cninfo_api import get_cninfo_api_client, CninfoConfig

        if not CninfoConfig.is_configured():
            return {'success': False, 'message': 'API not configured'}

        client = get_cninfo_api_client()
        token = await client._get_access_token()
        if token:
            return {'success': True, 'message': 'Connection OK'}
        return {'success': False, 'message': 'Token failed'}
    except Exception as e:
        return {'success': False, 'message': str(e)}


@router.get('/info')
async def get_system_info():
    """获取系统运行信息"""
    try:
        import sys
        import psutil
        import time

        info = {}

        # Python版本
        info['pythonVersion'] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        # AKShare版本
        try:
            import akshare as ak
            info['akshareVersion'] = ak.__version__
        except:
            info['akshareVersion'] = '--'

        # 数据源和接口统计
        try:
            config_path = Path('data/data_source_config.json')
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                info['dataSourceCount'] = len(config.get('data_sources', {}))
                info['categoryCount'] = len(config.get('data_categories', {}))
                # 统计接口数量
                interface_count = 0
                for cat in config.get('data_categories', {}).values():
                    interfaces = cat.get('interfaces', {})
                    for v in interfaces.values():
                        if isinstance(v, list):
                            interface_count += len(v)
                        else:
                            interface_count += 1
                info['interfaceCount'] = interface_count
            else:
                info['dataSourceCount'] = 5
                info['categoryCount'] = 13
                info['interfaceCount'] = 0
        except:
            info['dataSourceCount'] = 5
            info['categoryCount'] = 13
            info['interfaceCount'] = 0

        # 内存占用
        try:
            process = psutil.Process()
            info['memoryUsage'] = process.memory_info().rss
        except:
            info['memoryUsage'] = 0

        # CPU使用率
        try:
            info['cpuUsage'] = psutil.cpu_percent(interval=0.1)
        except:
            info['cpuUsage'] = 0

        # 运行时间
        try:
            process = psutil.Process()
            create_time = process.create_time()
            uptime_seconds = time.time() - create_time
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            if hours > 24:
                days = hours // 24
                hours = hours % 24
                info['uptime'] = f"{days}天{hours}时{minutes}分"
            else:
                info['uptime'] = f"{hours}时{minutes}分"
        except:
            info['uptime'] = '--'

        # 缓存大小
        try:
            cache_size = 0
            cache_dirs = ['data/cache', 'data/tdx_cache', 'data/news_center_cache']
            for cache_dir in cache_dirs:
                cache_path = Path(cache_dir)
                if cache_path.exists():
                    for f in cache_path.rglob('*'):
                        if f.is_file():
                            cache_size += f.stat().st_size
            info['cacheSize'] = cache_size
        except:
            info['cacheSize'] = 0

        # 日志大小
        try:
            log_size = 0
            log_path = Path('logs')
            if log_path.exists():
                for f in log_path.rglob('*.log'):
                    log_size += f.stat().st_size
            info['logSize'] = log_size
        except:
            info['logSize'] = 0

        # 今日请求数（从监控数据获取）
        try:
            metrics_path = Path('data/api_metrics.json')
            if metrics_path.exists():
                with open(metrics_path, 'r', encoding='utf-8') as f:
                    metrics = json.load(f)
                total_requests = sum(
                    h.get('total_requests', 0)
                    for h in metrics.get('health', {}).values()
                )
                info['requestCount'] = total_requests
            else:
                info['requestCount'] = 0
        except:
            info['requestCount'] = 0

        return {'success': True, 'data': info}
    except Exception as e:
        logger.error(f'Get system info failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
