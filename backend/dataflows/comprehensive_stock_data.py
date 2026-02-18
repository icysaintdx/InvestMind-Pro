"""
综合股票数据获取服务
整合所有数据接口：财务、风险、新闻、股权等
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

from backend.utils.logging_config import get_logger
from backend.dataflows.comprehensive_stock_data_additions import generate_interface_status

logger = get_logger("dataflows.comprehensive")


def extract_pure_symbol(ts_code: str) -> str:
    """
    从各种格式的股票代码中提取纯数字代码
    支持格式: 600519.SH, SH600519, 600519
    返回: 600519
    """
    # 先去除后缀（如 600519.SH -> 600519）
    symbol = ts_code.split('.')[0]
    # 再去除前缀（如 SH600519 -> 600519）
    if symbol.upper().startswith(('SH', 'SZ')):
        symbol = symbol[2:]
    return symbol


class ComprehensiveStockDataService:
    """综合股票数据服务 - 整合所有接口"""

    # 数据分层定义
    DATA_LAYERS = {
        'L1_REALTIME': {
            'name': '实时层',
            'update_interval': 60,  # 1分钟
            'tasks': ['realtime', 'realtime_tick', 'st_status', 'suspend']
        },
        'L2_MEDIUM': {
            'name': '中频层',
            'update_interval': 3600,  # 1小时
            'tasks': ['news_sina', 'announcements', 'hsgt_holding', 'dragon_tiger',
                     'block_trade', 'limit_list', 'margin', 'holder_trade', 'pledge']
        },
        'L3_LOW': {
            'name': '低频层',
            'update_interval': 86400,  # 1天
            'tasks': ['financial', 'forecast', 'audit', 'dividend', 'restricted',
                     'top_inst', 'pledge_detail', 'margin_detail', 'ggt_top10',
                     'hk_hold', 'limit_list_ths', 'manager_rewards']
        },
        'L4_STATIC': {
            'name': '静态层',
            'update_interval': 604800,  # 7天
            'tasks': ['company_info', 'managers', 'main_business']
        }
    }

    def __init__(self):
        self.tushare_token = os.getenv('TUSHARE_TOKEN', '')
        self.tushare_api = None

        # 静态数据缓存（L4层数据缓存）
        self._static_cache: Dict[str, Dict] = {}
        self._static_cache_time: Dict[str, datetime] = {}

        # 初始化Tushare
        if self.tushare_token:
            try:
                import tushare as ts
                ts.set_token(self.tushare_token)
                self.tushare_api = ts.pro_api()
                logger.info("[OK] Tushare API初始化成功")
            except Exception as e:
                logger.error(f"[FAIL] Tushare初始化失败: {e}")

    def get_layered_data(self, ts_code: str, layers: List[str] = None,
                         force_refresh: bool = False) -> Dict:
        """
        分层获取股票数据

        Args:
            ts_code: 股票代码
            layers: 要获取的层级列表，如 ['L1_REALTIME', 'L2_MEDIUM']
                   默认为 None，表示获取所有层级
            force_refresh: 是否强制刷新（忽略缓存）

        Returns:
            分层数据字典
        """
        if layers is None:
            layers = list(self.DATA_LAYERS.keys())

        result = {
            'ts_code': ts_code,
            'timestamp': datetime.now().isoformat(),
            'layers_fetched': layers,
        }

        # 收集需要获取的任务
        tasks_to_fetch = {}

        for layer in layers:
            if layer not in self.DATA_LAYERS:
                continue

            layer_config = self.DATA_LAYERS[layer]

            # 检查静态层缓存
            if layer == 'L4_STATIC' and not force_refresh:
                cache_key = f"{ts_code}_{layer}"
                if cache_key in self._static_cache:
                    cache_time = self._static_cache_time.get(cache_key)
                    if cache_time and (datetime.now() - cache_time).total_seconds() < layer_config['update_interval']:
                        # 使用缓存
                        for task in layer_config['tasks']:
                            result[task] = self._static_cache[cache_key].get(task, {})
                        logger.info(f"[CACHE] 使用静态层缓存: {ts_code}")
                        continue

            # 添加到待获取任务
            for task in layer_config['tasks']:
                tasks_to_fetch[task] = self._get_task_func(task, ts_code)

        # 并发获取数据
        if tasks_to_fetch:
            fetched_data = self._fetch_tasks_concurrent(tasks_to_fetch, ts_code)
            result.update(fetched_data)

            # 更新静态层缓存
            if 'L4_STATIC' in layers:
                cache_key = f"{ts_code}_L4_STATIC"
                self._static_cache[cache_key] = {
                    task: result.get(task, {})
                    for task in self.DATA_LAYERS['L4_STATIC']['tasks']
                }
                self._static_cache_time[cache_key] = datetime.now()

        return result

    def get_monitor_data(self, ts_code: str) -> Dict:
        """
        获取监控所需的数据（仅L1和L2层）
        用于定时监控更新，不获取静态数据
        """
        return self.get_layered_data(ts_code, layers=['L1_REALTIME', 'L2_MEDIUM'])

    def get_detail_data(self, ts_code: str, force_refresh: bool = False) -> Dict:
        """
        获取详情页所需的完整数据（所有层级）
        用于用户查看股票详情时
        """
        return self.get_layered_data(ts_code, layers=None, force_refresh=force_refresh)

    def _get_task_func(self, task: str, ts_code: str):
        """获取任务对应的函数和参数"""
        task_map = {
            'realtime': (self._get_realtime_quote, ts_code),
            'realtime_tick': (self._get_realtime_tick, ts_code),
            'st_status': (self._check_st_status, ts_code),
            'suspend': (self._get_suspend_info, ts_code),
            'news_sina': (self._get_news_sina, ts_code),
            'announcements': (self._get_announcements_akshare, ts_code),
            'hsgt_holding': (self._get_hsgt_holding, ts_code),
            'dragon_tiger': (self._get_dragon_tiger, ts_code),
            'block_trade': (self._get_block_trade, ts_code),
            'limit_list': (self._get_limit_list, ts_code),
            'margin': (self._get_margin_data, ts_code),
            'holder_trade': (self._get_holder_trade, ts_code),
            'pledge': (self._get_pledge_data, ts_code),
            'financial': (self._get_financial_data, ts_code),
            'forecast': (self._get_performance_forecast, ts_code),
            'audit': (self._get_audit_opinion, ts_code),
            'dividend': (self._get_dividend_data, ts_code),
            'restricted': (self._get_restricted_release, ts_code),
            'top_inst': (self._get_top_inst, ts_code),
            'pledge_detail': (self._get_pledge_detail, ts_code),
            'margin_detail': (self._get_margin_detail, ts_code),
            'ggt_top10': (self._get_ggt_top10, ts_code),
            'hk_hold': (self._get_hk_hold, ts_code),
            'limit_list_ths': (self._get_limit_list_ths, ts_code),
            'manager_rewards': (self._get_manager_rewards, ts_code),
            'company_info': (self._get_company_info, ts_code),
            'managers': (self._get_managers, ts_code),
            'main_business': (self._get_main_business, ts_code),
        }
        return task_map.get(task, (lambda x: {'status': 'not_found'}, ts_code))

    def _fetch_tasks_concurrent(self, tasks: Dict, ts_code: str) -> Dict:
        """并发获取任务数据"""
        import concurrent.futures
        import threading
        import time

        result = {}
        log_lock = threading.Lock()

        def execute_task(key, func, arg):
            task_start = time.time()
            try:
                result_data = func(arg)
                elapsed = time.time() - task_start
                with log_lock:
                    if isinstance(result_data, dict) and result_data.get('status') in ['success', 'has_suspend', 'normal']:
                        logger.debug(f"[OK] {key} ({elapsed:.2f}s)")
                    else:
                        logger.debug(f"[WARN] {key} ({elapsed:.2f}s)")
                return result_data
            except Exception as e:
                elapsed = time.time() - task_start
                with log_lock:
                    logger.debug(f"[FAIL] {key} ({elapsed:.2f}s) - {str(e)[:50]}")
                return {'status': 'error', 'message': str(e)}

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_key = {}
            for key, (func, arg) in tasks.items():
                future = executor.submit(execute_task, key, func, arg)
                future_to_key[future] = key

            try:
                for future in concurrent.futures.as_completed(future_to_key, timeout=60):
                    key = future_to_key[future]
                    try:
                        result[key] = future.result(timeout=15)
                    except concurrent.futures.TimeoutError:
                        result[key] = {'status': 'timeout', 'message': '获取超时'}
                    except Exception as e:
                        result[key] = {'status': 'error', 'message': str(e)}
            except concurrent.futures.TimeoutError:
                for future, key in future_to_key.items():
                    if not future.done():
                        result[key] = {'status': 'timeout', 'message': '整体超时'}
                        future.cancel()

        return result
    
    def get_all_stock_data(self, ts_code: str) -> Dict:
        """
        获取股票的所有数据
        
        Returns:
            {
                'basic_info': {},  # 基础信息
                'realtime': {},  # 实时行情
                'realtime_tick': {},  # 实时成交
                'suspend': {},  # 停复牌
                'st_status': {},  # ST状态
                'financial': {},  # 财务数据
                'audit': {},  # 审计意见
                'forecast': {},  # 业绩预告
                'dividend': {},  # 分红送股
                'restricted': {},  # 限售解禁
                'pledge': {},  # 股权质押
                'holder_trade': {},  # 股东增减持
                'dragon_tiger': {},  # 龙虎榜
                'top_inst': {},  # 龙虎榜机构明细
                'block_trade': {},  # 大宗交易
                'limit_list': {},  # 涨跌停数据
                'margin': {},  # 融资融券
                'company_info': {},  # 公司基本信息
                'managers': {},  # 管理层
                'manager_rewards': {},  # 管理层薪酬
                'main_business': {},  # 主营业务
                'hsgt_holding': {},  # 沪深港通持股
                'announcements': {},  # 公告  
                'news_sina': {},  # 新浪新闻
                'market_news': {},  # 市场快讯
                'cninfo_news': {},  # 巨潮资讯
                'industry_policy': {},  # 行业政策
                'akshare_ext': {},  # AKShare扩展数据
                'news': {},  # 多源新闻聚合

            }
        """
        logger.info(f"📊 开始获取 {ts_code} 的全面数据...")

        result = {
            'ts_code': ts_code,
            'timestamp': datetime.now().isoformat(),
            'data_summary': {},
            'basic_info': {},
            'realtime': {},
            'realtime_tick': {},
            'realtime_list': {},
            'suspend': {},
            'st_status': {},
            'financial': {},
            'audit': {},
            'forecast': {},
            'dividend': {},
            'restricted': {},
            'pledge': {},
            'pledge_detail': {},
            'holder_trade': {},
            'dragon_tiger': {},
            'top_inst': {},
            'block_trade': {},
            'limit_list': {},
            'limit_list_ths': {},
            'margin': {},
            'margin_detail': {},
            'company_info': {},
            'managers': {},
            'manager_rewards': {},
            'main_business': {},
            'hsgt_holding': {},
            'ggt_top10': {},
            'hk_hold': {},
            'moneyflow_hsgt': {},
            'announcements': {},
            'news_sina': {},
            'news_em': {},
            'market_news': {},
            'industry_policy': {},
            'news': {},
            'akshare_ext': {},
            # 巨潮官方API数据
            'cninfo_announcement': {},
            'cninfo_news': {},
            'cninfo_research': {},
        }

        # 使用并发执行加速数据获取
        import concurrent.futures
        from functools import partial
        import threading
        import time

        logger.info("🔄 开始并发获取数据...")
        start_time = time.time()

        # 定义数据获取任务（所有接口都实际获取，不再使用deferred）
        tasks = {
            # 核心数据（优先级高）
            'realtime': (self._get_realtime_quote, ts_code),
            'st_status': (self._check_st_status, ts_code),
            'suspend': (self._get_suspend_info, ts_code),
            'financial': (self._get_financial_data, ts_code),
            'forecast': (self._get_performance_forecast, ts_code),
            'pledge': (self._get_pledge_data, ts_code),
            'holder_trade': (self._get_holder_trade, ts_code),
            'news_sina': (self._get_news_sina, ts_code),

            # 次要数据
            'audit': (self._get_audit_opinion, ts_code),
            'dividend': (self._get_dividend_data, ts_code),
            'restricted': (self._get_restricted_release, ts_code),
            'dragon_tiger': (self._get_dragon_tiger, ts_code),
            'block_trade': (self._get_block_trade, ts_code),
            'margin': (self._get_margin_data, ts_code),
            'company_info': (self._get_company_info, ts_code),
            'announcements': (self._get_announcements_akshare, ts_code),

            # 公司信息
            'managers': (self._get_managers, ts_code),
            'manager_rewards': (self._get_manager_rewards, ts_code),
            'main_business': (self._get_main_business, ts_code),

            # 原deferred接口，现在全部实际获取
            'realtime_tick': (self._get_realtime_tick, ts_code),
            'top_inst': (self._get_top_inst, ts_code),
            'limit_list': (self._get_limit_list, ts_code),
            'hsgt_holding': (self._get_hsgt_holding, ts_code),
            'pledge_detail': (self._get_pledge_detail, ts_code),
            'margin_detail': (self._get_margin_detail, ts_code),
            'ggt_top10': (self._get_ggt_top10, ts_code),
            'hk_hold': (self._get_hk_hold, ts_code),
            'limit_list_ths': (self._get_limit_list_ths, ts_code),

            # 巨潮官方API数据
            'cninfo_announcement': (self._get_cninfo_announcement, ts_code),
            'cninfo_news': (self._get_cninfo_stock_news, ts_code),
            'cninfo_research': (self._get_cninfo_research_report, ts_code),
        }

        # 创建一个锁来保护日志输出
        log_lock = threading.Lock()

        def execute_task(key, func, arg):
            """执行单个任务并记录日志"""
            task_start = time.time()
            logger.info(f"📥 开始获取 {key}...")
            try:
                result_data = func(arg)
                elapsed = time.time() - task_start
                with log_lock:
                    if isinstance(result_data, dict) and result_data.get('status') in ['success', 'has_suspend', 'normal']:
                        logger.info(f"✅ {key} 获取成功 ({elapsed:.2f}s) - 状态: {result_data.get('status')}")
                    else:
                        logger.warning(f"⚠️ {key} 获取失败 ({elapsed:.2f}s) - {str(result_data)[:100]}")
                return result_data
            except Exception as e:
                elapsed = time.time() - task_start
                with log_lock:
                    logger.error(f"❌ {key} 执行异常 ({elapsed:.2f}s) - {str(e)[:100]}")
                return {'status': 'error', 'message': str(e)}

        # 使用线程池并发执行（增加并发数和超时时间以处理更多接口）
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # 提交所有任务
            future_to_key = {}
            for key, (func, arg) in tasks.items():
                future = executor.submit(execute_task, key, func, arg)
                future_to_key[future] = key

            # 等待所有任务完成（增加超时时间到60秒）
            completed_count = 0
            try:
                for future in concurrent.futures.as_completed(future_to_key, timeout=60):
                    key = future_to_key[future]
                    try:
                        result[key] = future.result(timeout=15)
                        completed_count += 1
                    except concurrent.futures.TimeoutError:
                        logger.warning(f"[WARN] {key} 获取超时")
                        result[key] = {'status': 'timeout', 'message': '获取超时'}
                    except Exception as e:
                        logger.warning(f"[WARN] {key} 获取失败: {e}")
                        result[key] = {'status': 'error', 'message': str(e)}
            except concurrent.futures.TimeoutError:
                # 整体超时，处理未完成的任务
                unfinished_count = 0
                for future, key in future_to_key.items():
                    if not future.done():
                        unfinished_count += 1
                        result[key] = {'status': 'timeout', 'message': '整体超时未完成'}
                        future.cancel()
                    elif key not in result:
                        # 已完成但未处理的任务
                        try:
                            result[key] = future.result(timeout=0.1)
                            completed_count += 1
                        except Exception as e:
                            result[key] = {'status': 'error', 'message': str(e)}
                if unfinished_count > 0:
                    logger.warning(f"[WARN] 整体超时，{unfinished_count}个任务未完成")

        total_time = time.time() - start_time
        logger.info(f"📊 数据获取完成: {completed_count}/{len(tasks)} 个接口，耗时 {total_time:.2f} 秒")

        # 获取新闻数据（单独处理，避免阻塞）
        try:
            result['news'] = self._get_news_data(ts_code)
        except Exception as e:
            logger.warning(f"⚠️ 新闻数据获取失败: {e}")
            result['news'] = []

        # 获取不需要ts_code参数的全市场数据
        try:
            result['market_news'] = self._get_market_news_cninfo()
        except Exception as e:
            logger.warning(f"⚠️ 市场新闻获取失败: {e}")
            result['market_news'] = {'status': 'error', 'message': str(e)}

        try:
            result['industry_policy'] = self._get_industry_policy()
        except Exception as e:
            logger.warning(f"⚠️ 行业政策获取失败: {e}")
            result['industry_policy'] = {'status': 'error', 'message': str(e)}

        try:
            result['realtime_list'] = self._get_realtime_list()
        except Exception as e:
            logger.warning(f"⚠️ 全市场行情获取失败: {e}")
            result['realtime_list'] = {'status': 'error', 'message': str(e)}

        try:
            result['moneyflow_hsgt'] = self._get_moneyflow_hsgt()
        except Exception as e:
            logger.warning(f"⚠️ 北向资金获取失败: {e}")
            result['moneyflow_hsgt'] = {'status': 'error', 'message': str(e)}

        # 东方财富新闻和AKShare扩展数据暂不获取（接口不稳定）
        result['news_em'] = {'status': 'no_data', 'message': '暂不支持'}
        result['akshare_ext'] = {'status': 'no_data', 'message': '暂不支持'}

        # 调整数据结构以匹配前端期望
        result = self._adjust_data_structure(result)

        # 生成数据摘要
        result['data_summary'] = self._generate_summary(result)

        # 生成接口状态报告
        result['interface_status'] = generate_interface_status(result)

        logger.info(f"✅ 数据获取完成，共 {len(result['data_summary'])} 个类别")

        return result

    def _adjust_data_structure(self, result: Dict) -> Dict:
        """调整数据结构以匹配前端期望"""
        logger.info("🔄 调整数据结构以匹配前端期望...")

        # 1. 调整财务数据结构
        if 'financial' not in result or not result['financial']:
            result['financial'] = {
                'income': [],
                'balancesheet': [],
                'cashflow': []
            }
        elif isinstance(result['financial'], dict) and result['financial'].get('status') == 'success':
            # 保持原有结构
            pass
        else:
            # 确保有默认结构
            result['financial'] = {
                'income': result['financial'].get('income', []),
                'balancesheet': result['financial'].get('balancesheet', []),
                'cashflow': result['financial'].get('cashflow', [])
            }

        # 2. 调整limit_list结构
        if 'limit_list' in result and result['limit_list'].get('status') == 'success':
            # 数据结构已正确
            pass

        # 3. 调整forecast结构
        if 'forecast' in result and result['forecast'].get('status') == 'success':
            # 确保forecast有正确的结构
            if 'forecast' not in result['forecast']:
                result['forecast']['forecast'] = result['forecast'].get('data', [])

        # 4. 调整st_status结构
        if 'st_status' in result:
            if 'is_st' not in result['st_status']:
                result['st_status']['is_st'] = result['st_status'].get('status') in ['st', 'success'] and 'ST' in str(result['st_status']).upper()
            if 'message' not in result['st_status']:
                result['st_status']['message'] = result['st_status'].get('message', '正常状态')

        # 5. 确保realtime数据正确
        if 'realtime' in result and result['realtime'].get('status') == 'success':
            # 确保有价格变化百分比
            if 'pct_change' not in result['realtime']['data']:
                result['realtime']['data']['pct_change'] = result['realtime']['data'].get('change_pct', 0)

        # 6. 调整suspend状态
        if 'suspend' not in result or not result['suspend']:
            result['suspend'] = {
                'status': 'normal',
                'message': '近期无停复牌记录'
            }

        # 7. 调整pledge数据，确保有pledge_ratio
        if 'pledge' in result and result['pledge'].get('status') == 'success':
            data = result['pledge']
            if isinstance(data.get('data'), list) and data['data']:
                # 计算质押比例
                record = data['data'][0]
                if 'pledge_ratio' not in record:
                    # 尝试从其他字段计算
                    record['pledge_ratio'] = 0  # 默认值
            else:
                data['pledge_ratio'] = 0

        return result

    def _get_realtime_quote(self, ts_code: str) -> Dict:
        """获取实时行情（优先TDX，降级到AKShare单股票API）"""
        # 提取纯数字股票代码
        symbol = extract_pure_symbol(ts_code)

        # 优先使用TDX（最快最可靠）
        try:
            from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
            tdx = get_tdx_native_provider()
            if tdx and tdx.is_available():
                quote = tdx.get_realtime_quote(symbol)
                if quote:
                    return {
                        'status': 'success',
                        'source': 'tdx',
                        'data': {
                            'name': quote.get('name', ''),
                            'price': quote.get('price', 0),
                            'change': quote.get('change', 0),
                            'pct_change': quote.get('change_pct', 0),
                            'change_pct': quote.get('change_pct', 0),
                            'volume': quote.get('volume', 0),
                            'amount': quote.get('amount', 0),
                            'high': quote.get('high', 0),
                            'low': quote.get('low', 0),
                            'open': quote.get('open', 0),
                            'pre_close': quote.get('pre_close', 0),
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'time': datetime.now().strftime('%H:%M:%S')
                        }
                    }
        except Exception as e:
            logger.debug(f"TDX实时行情获取失败: {e}")

        # 降级：使用AKShare单股票API
        try:
            import akshare as ak

            # 使用 stock_bid_ask_em 获取单只股票实时行情
            df = ak.stock_bid_ask_em(symbol=symbol)
            if df is not None and not df.empty:
                # 转换为字典
                data = {}
                for _, row in df.iterrows():
                    item = row['item']
                    value = row['value']
                    data[item] = value

                # 安全转换函数
                def safe_float(val, default=0):
                    if val is None:
                        return default
                    if isinstance(val, (int, float)):
                        return float(val)
                    if isinstance(val, str):
                        val = val.strip().replace(',', '')
                        if val == '' or val == '-' or '--' in val:
                            return default
                        try:
                            return float(val)
                        except ValueError:
                            return default
                    return default

                return {
                    'status': 'success',
                    'source': 'akshare',
                    'data': {
                        'name': '',  # bid_ask_em 不返回名称
                        'price': safe_float(data.get('最新')),
                        'change': safe_float(data.get('涨跌')),
                        'pct_change': safe_float(data.get('涨幅')),  # 前端使用pct_change
                        'change_pct': safe_float(data.get('涨幅')),  # 兼容旧字段
                        'volume': int(safe_float(data.get('总手'))),
                        'amount': safe_float(data.get('金额')),
                        'high': safe_float(data.get('最高')),
                        'low': safe_float(data.get('最低')),
                        'open': safe_float(data.get('今开')),
                        'pre_close': safe_float(data.get('昨收')),
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'time': datetime.now().strftime('%H:%M:%S')
                    }
                }
        except Exception as e:
            logger.debug(f"AKShare实时行情获取失败: {e}")

        # 备选：使用Tushare
        try:
            import tushare as ts
            df = ts.realtime_quote(ts_code=ts_code)

            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无实时行情数据'}

            data = df.iloc[0].to_dict()
            pct = ((float(data.get('PRICE', 0) or 0) - float(data.get('PRE_CLOSE', 0) or 0)) / float(data.get('PRE_CLOSE', 1) or 1) * 100) if data.get('PRE_CLOSE') else 0
            return {
                'status': 'success',
                'source': 'tushare',
                'data': {
                    'name': data.get('NAME', ''),
                    'price': float(data.get('PRICE', 0) or 0),
                    'change': float(data.get('PRICE', 0) or 0) - float(data.get('PRE_CLOSE', 0) or 0),
                    'pct_change': pct,  # 前端使用pct_change
                    'change_pct': pct,  # 兼容旧字段
                    'volume': int(data.get('VOLUME', 0) or 0),
                    'amount': float(data.get('AMOUNT', 0) or 0),
                    'high': float(data.get('HIGH', 0) or 0),
                    'low': float(data.get('LOW', 0) or 0),
                    'open': float(data.get('OPEN', 0) or 0),
                    'pre_close': float(data.get('PRE_CLOSE', 0) or 0),
                    'date': data.get('DATE', ''),
                    'time': data.get('TIME', '')
                }
            }
        except Exception as e:
            logger.warning(f"⚠️ 实时行情获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_suspend_info(self, ts_code: str) -> Dict:
        """获取停复牌信息"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            # 获取最近30天的停复牌记录
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            df = self.tushare_api.suspend_d(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is None or df.empty:
                return {
                    'status': 'normal',
                    'message': '近期无停复牌记录',
                    'records': []
                }
            
            records = []
            for _, row in df.iterrows():
                records.append({
                    'suspend_date': row.get('suspend_date', ''),
                    'resume_date': row.get('resume_date', ''),
                    'suspend_reason': row.get('suspend_reason', ''),
                    'suspend_type': row.get('suspend_type', '')
                })
            
            return {
                'status': 'has_suspend',
                'message': f'近期有{len(records)}条停复牌记录',
                'count': len(records),
                'records': records
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 停复牌信息获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _check_st_status(self, ts_code: str) -> Dict:
        """检查ST状态"""
        try:
            import akshare as ak

            # 使用AKShare的ST风险警示板接口
            df = ak.stock_zh_a_st_em()

            if df is None or df.empty:
                return {'status': 'normal', 'is_st': False, 'message': '非ST股票'}

            # 检查是否在ST列表中
            stock_code = extract_pure_symbol(ts_code)
            is_st = stock_code in df['代码'].values
            
            if is_st:
                st_info = df[df['代码'] == stock_code].iloc[0]
                return {
                    'status': 'st_stock',
                    'is_st': True,
                    'name': st_info.get('名称', ''),
                    'message': f'{stock_code} 为ST股票'
                }
            else:
                return {
                    'status': 'normal',
                    'is_st': False,
                    'message': '非ST股票'
                }
                
        except Exception as e:
            logger.warning(f"⚠️ ST状态检查失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_financial_data(self, ts_code: str) -> Dict:
        """获取财务数据（利润表、资产负债表、现金流量表）"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            result = {
                'status': 'success',
                'income': [],  # 利润表
                'balance': [],  # 资产负债表
                'cashflow': []  # 现金流量表
            }
            
            # 1. 利润表（最近3期）
            try:
                income_df = self.tushare_api.income(ts_code=ts_code, fields=[
                    'ts_code', 'end_date', 'total_revenue', 'revenue', 'operate_profit',
                    'total_profit', 'n_income', 'n_income_attr_p'
                ])
                
                if income_df is not None and not income_df.empty:
                    for _, row in income_df.head(3).iterrows():
                        result['income'].append({
                            'period': row.get('end_date', ''),
                            'total_revenue': float(row.get('total_revenue', 0) or 0),
                            'operate_profit': float(row.get('operate_profit', 0) or 0),
                            'net_profit': float(row.get('n_income_attr_p', 0) or 0)
                        })
            except Exception as e:
                logger.debug(f"利润表获取失败: {e}")
            
            # 2. 资产负债表（最近3期）
            try:
                balance_df = self.tushare_api.balancesheet(ts_code=ts_code, fields=[
                    'ts_code', 'end_date', 'total_assets', 'total_liab', 'total_hldr_eqy_exc_min_int'
                ])
                
                if balance_df is not None and not balance_df.empty:
                    for _, row in balance_df.head(3).iterrows():
                        result['balance'].append({
                            'period': row.get('end_date', ''),
                            'total_assets': float(row.get('total_assets', 0) or 0),
                            'total_liab': float(row.get('total_liab', 0) or 0),
                            'equity': float(row.get('total_hldr_eqy_exc_min_int', 0) or 0)
                        })
            except Exception as e:
                logger.debug(f"资产负债表获取失败: {e}")
            
            # 3. 现金流量表（最近3期）
            try:
                cashflow_df = self.tushare_api.cashflow(ts_code=ts_code, fields=[
                    'ts_code', 'end_date', 'n_cashflow_act', 'n_cashflow_inv_act', 'n_cash_flows_fnc_act'
                ])
                
                if cashflow_df is not None and not cashflow_df.empty:
                    for _, row in cashflow_df.head(3).iterrows():
                        result['cashflow'].append({
                            'period': row.get('end_date', ''),
                            'operating_cash': float(row.get('n_cashflow_act', 0) or 0),
                            'investing_cash': float(row.get('n_cashflow_inv_act', 0) or 0),
                            'financing_cash': float(row.get('n_cash_flows_fnc_act', 0) or 0)
                        })
            except Exception as e:
                logger.debug(f"现金流量表获取失败: {e}")
            
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ 财务数据获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_audit_opinion(self, ts_code: str) -> Dict:
        """获取财务审计意见"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            df = self.tushare_api.fina_audit(ts_code=ts_code)
            
            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无审计意见数据'}
            
            latest = df.iloc[0]
            return {
                'status': 'success',
                'period': latest.get('end_date', ''),
                'opinion': latest.get('audit_result', ''),
                'agency': latest.get('audit_agency', ''),
                'is_standard': latest.get('audit_result', '') == '标准无保留意见'
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 审计意见获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_performance_forecast(self, ts_code: str) -> Dict:
        """获取业绩预告/快报"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            # 获取业绩预告
            forecast_df = self.tushare_api.forecast(ts_code=ts_code)
            
            # 获取业绩快报
            express_df = self.tushare_api.express(ts_code=ts_code)
            
            result = {
                'status': 'success',
                'forecast': [],
                'express': []
            }
            
            if forecast_df is not None and not forecast_df.empty:
                for _, row in forecast_df.head(3).iterrows():
                    result['forecast'].append({
                        'period': row.get('end_date', ''),
                        'type': row.get('type', ''),
                        'profit_min': float(row.get('p_change_min', 0) or 0),
                        'profit_max': float(row.get('p_change_max', 0) or 0),
                        'summary': row.get('summary', '')
                    })
            
            if express_df is not None and not express_df.empty:
                for _, row in express_df.head(3).iterrows():
                    result['express'].append({
                        'period': row.get('end_date', ''),
                        'revenue': float(row.get('revenue', 0) or 0),
                        'profit': float(row.get('operate_profit', 0) or 0),
                        'eps': float(row.get('eps', 0) or 0)
                    })
            
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ 业绩预告获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_dividend_data(self, ts_code: str) -> Dict:
        """获取分红送股数据"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            df = self.tushare_api.dividend(ts_code=ts_code)
            
            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无分红数据'}
            
            records = []
            for _, row in df.head(5).iterrows():
                records.append({
                    'year': row.get('end_date', ''),
                    'cash_div': float(row.get('cash_div', 0) or 0),
                    'bonus_share': float(row.get('stk_bo_rate', 0) or 0),
                    'record_date': row.get('record_date', ''),
                    'ex_date': row.get('ex_date', '')
                })
            
            return {
                'status': 'success',
                'count': len(records),
                'records': records
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 分红数据获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_restricted_release(self, ts_code: str) -> Dict:
        """获取限售股解禁数据"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            # 获取未来6个月的解禁数据
            df = self.tushare_api.share_float(ts_code=ts_code)
            
            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无解禁数据'}
            
            records = []
            for _, row in df.head(5).iterrows():
                records.append({
                    'release_date': row.get('float_date', ''),
                    'float_share': float(row.get('float_share', 0) or 0),
                    'float_ratio': float(row.get('float_ratio', 0) or 0),
                    'holder_name': row.get('holder_name', '')
                })
            
            return {
                'status': 'success',
                'count': len(records),
                'records': records
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 解禁数据获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_pledge_data(self, ts_code: str) -> Dict:
        """获取股权质押数据"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            # 获取股权质押统计
            df = self.tushare_api.pledge_stat(ts_code=ts_code)
            
            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无质押数据'}
            
            latest = df.iloc[0]
            return {
                'status': 'success',
                'end_date': latest.get('end_date', ''),
                'pledge_count': int(latest.get('pledge_count', 0) or 0),
                'pledge_ratio': float(latest.get('pledge_ratio', 0) or 0),
                'un_pledge_ratio': float(latest.get('unrest_pledge', 0) or 0)
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 质押数据获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_holder_trade(self, ts_code: str) -> Dict:
        """获取股东增减持数据"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            # 获取最近6个月的增减持
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')
            
            df = self.tushare_api.stk_holdertrade(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is None or df.empty:
                return {'status': 'no_data', 'message': '无增减持数据'}
            
            records = []
            for _, row in df.head(10).iterrows():
                records.append({
                    'date': row.get('ann_date', ''),
                    'holder': row.get('holder_name', ''),
                    'type': row.get('holder_type', ''),
                    'volume': float(row.get('vol', 0) or 0),
                    'total_share': float(row.get('total_share', 0) or 0)
                })
            
            return {
                'status': 'success',
                'count': len(records),
                'records': records
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 增减持数据获取失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _get_dragon_tiger(self, ts_code: str) -> Dict:
        """获取龙虎榜数据"""
        if not self.tushare_api:
            return {'status': 'api_unavailable'}
        
        try:
            # 获取最近30天的龙虎榜，逐天查询
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            all_records = []
            current_date = end_date
            days_checked = 0
            
            # 最多查询30个交易日，或者找到10条记录
            while current_date >= start_date and len(all_records) < 10 and days_checked < 45:
                # 跳过周末
                if current_date.weekday() < 5:  # 0-4为周一到周五
                    try:
                        trade_date_str = current_date.strftime('%Y%m%d')
                        df = self.tushare_api.top_list(
                            trade_date=trade_date_str
                        )
                        
                        if df is not None and not df.empty:
                            # 筛选出当前股票的记录
                            stock_df = df[df['ts_code'] == ts_code]
                            if not stock_df.empty:
                                for _, row in stock_df.iterrows():
                                    all_records.append({
                                        'date': row.get('trade_date', ''),
                                        'reason': row.get('reason', ''),
                                        'buy': float(row.get('buy', 0) or 0),
                                        'sell': float(row.get('sell', 0) or 0),
                                        'net': float(row.get('net', 0) or 0)
                                    })
                    except Exception as day_error:
                        # 单日查询失败，继续下一天
                        pass
                
                current_date -= timedelta(days=1)
                days_checked += 1
            
            if all_records:
                return {
                    'status': 'success',
                    'count': len(all_records),
                    'records': all_records
                }
            else:
                return {'status': 'no_data', 'message': '近30天无龙虎榜数据'}
            
        except Exception as e:
            logger.warning(f"⚠️ 龙虎榜数据获取失败: {e}")
            return {'status': 'no_data', 'message': f'龙虎榜查询失败'}

    def _get_top_inst(self, ts_code: str) -> Dict:
        """获取龙虎榜机构明细（优先Tushare，备选AKShare）"""
        symbol = extract_pure_symbol(ts_code)

        # 1. 尝试 Tushare
        if self.tushare_api:
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)

                all_records = []
                current_date = end_date
                days_checked = 0

                while current_date >= start_date and len(all_records) < 10 and days_checked < 45:
                    if current_date.weekday() < 5:
                        try:
                            trade_date_str = current_date.strftime('%Y%m%d')
                            df = self.tushare_api.top_inst(
                                trade_date=trade_date_str
                            )

                            if df is not None and not df.empty:
                                stock_df = df[df['ts_code'] == ts_code]
                                if not stock_df.empty:
                                    for _, row in stock_df.iterrows():
                                        all_records.append({
                                            'trade_date': row.get('trade_date', ''),
                                            'exalter': row.get('exalter', ''),
                                            'buy': float(row.get('buy', 0) or 0),
                                            'buy_rate': float(row.get('buy_rate', 0) or 0),
                                            'sell': float(row.get('sell', 0) or 0),
                                            'sell_rate': float(row.get('sell_rate', 0) or 0),
                                            'net_buy': float(row.get('net_buy', 0) or 0),
                                            'source': 'tushare'
                                        })
                        except:
                            pass

                    current_date -= timedelta(days=1)
                    days_checked += 1

                if all_records:
                    return {
                        'status': 'success',
                        'count': len(all_records),
                        'records': all_records,
                        'source': 'tushare'
                    }
            except Exception as e:
                logger.debug(f"Tushare龙虎榜机构明细获取失败: {e}")

        # 2. 备选：使用 AKShare
        try:
            import akshare as ak

            records = []

            # 获取机构龙虎榜统计
            try:
                df = ak.stock_lhb_jgstatistic_em(symbol="近一月")
                if df is not None and not df.empty:
                    # 筛选当前股票
                    stock_df = df[df['代码'].astype(str) == symbol]
                    if not stock_df.empty:
                        for _, row in stock_df.iterrows():
                            records.append({
                                'trade_date': '',
                                'exalter': '机构专用',
                                'buy': float(row.get('买入额', 0) or 0),
                                'buy_rate': 0,
                                'sell': float(row.get('卖出额', 0) or 0),
                                'sell_rate': 0,
                                'net_buy': float(row.get('净买入额', 0) or 0),
                                'times': int(row.get('上榜次数', 0) or 0),
                                'source': 'akshare_jgstatistic'
                            })
            except Exception as e1:
                logger.debug(f"AKShare机构龙虎榜统计获取失败: {e1}")

            # 如果统计数据为空，尝试获取个股龙虎榜明细
            if not records:
                try:
                    today = datetime.now().strftime('%Y%m%d')
                    df = ak.stock_lhb_stock_detail_em(symbol=symbol, date=today, flag="买入")
                    if df is not None and not df.empty:
                        for _, row in df.iterrows():
                            if '机构' in str(row.get('营业部名称', '')):
                                records.append({
                                    'trade_date': today,
                                    'exalter': row.get('营业部名称', ''),
                                    'buy': float(row.get('买入金额', 0) or 0),
                                    'buy_rate': 0,
                                    'sell': 0,
                                    'sell_rate': 0,
                                    'net_buy': float(row.get('买入金额', 0) or 0),
                                    'source': 'akshare_stock_detail'
                                })
                except Exception as e2:
                    logger.debug(f"AKShare个股龙虎榜明细获取失败: {e2}")

            if records:
                return {
                    'status': 'success',
                    'count': len(records),
                    'records': records,
                    'source': 'akshare'
                }
        except Exception as e:
            logger.debug(f"AKShare龙虎榜机构明细获取失败: {e}")

        return {'status': 'no_data', 'message': '近30天无机构龙虎榜'}
    
    def _get_block_trade(self, ts_code: str) -> Dict:
        """获取大宗交易数据（AKShare）"""
        try:
            import akshare as ak
            from datetime import datetime, timedelta

            # 获取全市场大宗交易数据，然后筛选
            symbol = extract_pure_symbol(ts_code)

            # 使用stock_dzjy_mrmx获取大宗交易每日明细（这是正确的API）
            try:
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')

                df = ak.stock_dzjy_mrmx(symbol='A股', start_date=start_date, end_date=end_date)
                if df is not None and not df.empty:
                    # 找到证券代码列
                    code_col = None
                    for col in df.columns:
                        if '证券代码' in str(col) or '代码' in str(col):
                            code_col = col
                            break

                    if code_col:
                        stock_data = df[df[code_col].astype(str) == symbol]
                        if not stock_data.empty:
                            records = stock_data.head(20).to_dict('records')
                            return {
                                'status': 'success',
                                'count': len(records),
                                'data': records,
                                'description': '大宗交易明细'
                            }
            except Exception as e1:
                logger.debug(f"stock_dzjy_mrmx失败: {e1}")

            # 备选：获取每日统计
            try:
                df = ak.stock_dzjy_mrtj()
                if df is not None and not df.empty:
                    # 找到证券代码列
                    code_col = None
                    for col in df.columns:
                        if '证券代码' in str(col) or '代码' in str(col):
                            code_col = col
                            break

                    if code_col:
                        stock_data = df[df[code_col].astype(str) == symbol]
                        if not stock_data.empty:
                            records = stock_data.head(20).to_dict('records')
                            return {
                                'status': 'success',
                                'count': len(records),
                                'data': records,
                                'description': '大宗交易每日统计'
                            }
            except Exception as e2:
                logger.debug(f"stock_dzjy_mrtj失败: {e2}")

            return {
                'status': 'no_data',
                'message': '近期无大宗交易'
            }

        except Exception as e:
            logger.warning(f"⚠️ 大宗交易数据获取失败: {e}")
            return {'status': 'no_data', 'message': '大宗交易查询暂不可用'}
    
    def _get_announcements_akshare(self, ts_code: str) -> Dict:
        """获取上市公司公告（AKShare）"""
        try:
            import akshare as ak

            symbol = extract_pure_symbol(ts_code)

            # 方法1: 使用巨潮资讯公告查询
            try:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

                df = ak.stock_notice_report(symbol=symbol, date=start_date)
                if df is not None and not df.empty:
                    records = []
                    for _, row in df.head(20).iterrows():
                        records.append({
                            'date': str(row.get('公告日期', row.get('日期', ''))),
                            'title': str(row.get('公告标题', row.get('标题', ''))),
                            'type': str(row.get('公告类型', '')),
                            'url': str(row.get('公告链接', row.get('链接', '')))
                        })
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records
                    }
            except Exception as e1:
                logger.debug(f"stock_notice_report失败: {e1}")

            # 方法2: 使用东方财富公告
            try:
                df = ak.stock_ggcg_em(symbol=symbol)
                if df is not None and not df.empty:
                    records = []
                    for _, row in df.head(20).iterrows():
                        records.append({
                            'date': str(row.get('公告日期', '')),
                            'title': str(row.get('公告标题', '')),
                            'type': '公告',
                            'url': ''
                        })
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records
                    }
            except Exception as e2:
                logger.debug(f"stock_ggcg_em失败: {e2}")

            return {
                'status': 'no_data',
                'message': '近期无公告'
            }

        except Exception as e:
            logger.warning(f"⚠️ 公告数据获取失败: {e}")
            return {'status': 'no_data', 'message': '公告查询暂不可用'}
    
    def _get_news_sina(self, ts_code: str) -> Dict:
        """获取个股新闻（使用东方财富）"""
        try:
            import akshare as ak
            from backend.dataflows.stock.akshare_utils import get_stock_news_em

            symbol = extract_pure_symbol(ts_code)

            # 方法1: 使用修复版东方财富个股新闻函数
            try:
                df = get_stock_news_em(symbol=symbol, max_news=20)
                if df is not None and not df.empty:
                    records = []
                    for _, row in df.iterrows():
                        records.append({
                            'title': str(row.get('新闻标题', '')),
                            'content': str(row.get('新闻内容', ''))[:200],
                            'time': str(row.get('发布时间', '')),
                            'source': str(row.get('文章来源', '东方财富')),
                            'url': str(row.get('新闻链接', ''))
                        })
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records
                    }
            except Exception as e1:
                logger.debug(f"get_stock_news_em失败: {e1}")

            # 方法2: 使用财联社电报 (stock_telegraph_cls已改名为stock_info_global_cls)
            try:
                df = ak.stock_info_global_cls()
                if df is not None and not df.empty:
                    records = []
                    for _, row in df.head(20).iterrows():
                        records.append({
                            'title': str(row.get('标题', '')),
                            'content': str(row.get('内容', ''))[:200],
                            'time': str(row.get('发布时间', '')),
                            'source': '财联社',
                            'url': ''
                        })
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records
                    }
            except Exception as e2:
                logger.debug(f"stock_info_global_cls失败: {e2}")

            return {'status': 'no_data', 'message': '无新闻数据'}

        except Exception as e:
            logger.warning(f"⚠️ 新闻数据获取失败: {e}")
            return {'status': 'no_data', 'message': '新闻暂不可用'}
    
    def _get_market_news_cninfo(self) -> Dict:
        """获取市场快讯（百度财经）"""
        try:
            import akshare as ak
            
            # 百度财经新闻
            df = ak.news_economic_baidu()
            
            if df is not None and not df.empty:
                records = []
                for _, row in df.head(30).iterrows():
                    records.append({
                        'time': str(row.get('发布时间', '')),
                        'title': str(row.get('标题', '')),
                        'content': str(row.get('内容', '')),
                        'source': '百度财经'
                    })
                
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records
                }
            else:
                return {'status': 'no_data', 'message': '无市场快讯'}
                
        except Exception as e:
            logger.warning(f"⚠️ 市场快讯获取失败: {e}")
            return {'status': 'no_data', 'message': '市场快讯暂不可用'}
    
    def _get_cninfo_news(self) -> Dict:
        """获取巨潮资讯公告快讯（AKShare）"""
        try:
            import akshare as ak

            # 方法1: 使用东方财富公告
            try:
                df = ak.stock_gsgg_em()
                if df is not None and not df.empty:
                    records = []
                    for _, row in df.head(50).iterrows():
                        records.append({
                            'time': str(row.get('公告日期', '')),
                            'code': str(row.get('代码', '')),
                            'name': str(row.get('名称', '')),
                            'title': str(row.get('公告标题', '')),
                            'category': str(row.get('公告类型', '')),
                            'source': '东方财富'
                        })
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records
                    }
            except Exception as e1:
                logger.debug(f"stock_gsgg_em失败: {e1}")

            # 方法2: 使用财联社电报作为替代 (stock_telegraph_cls已改名为stock_info_global_cls)
            try:
                df = ak.stock_info_global_cls()
                if df is not None and not df.empty:
                    records = []
                    for _, row in df.head(50).iterrows():
                        records.append({
                            'time': str(row.get('发布时间', '')),
                            'code': '',
                            'name': '',
                            'title': str(row.get('标题', '')),
                            'category': '快讯',
                            'source': '财联社'
                        })
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records
                    }
            except Exception as e2:
                logger.debug(f"stock_info_global_cls失败: {e2}")

            return {'status': 'no_data', 'message': '无公告快讯'}

        except Exception as e:
            logger.warning(f"⚠️ 公告快讯获取失败: {e}")
            return {'status': 'no_data', 'message': '公告快讯暂不可用'}

    def _get_cninfo_announcement(self, ts_code: str) -> Dict:
        """获取巨潮官方API个股公告（使用同步版本避免事件循环冲突）"""
        try:
            from backend.dataflows.announcement.cninfo_api import CninfoConfig, get_announcement_info_sync

            if not CninfoConfig.is_configured():
                return {'status': 'no_data', 'message': '巨潮API未配置'}

            symbol = extract_pure_symbol(ts_code)

            # 使用同步版本
            result = get_announcement_info_sync(stock_code=symbol, page_size=50)

            if result.get('success') and result.get('data'):
                records = []
                for item in result['data'][:20]:
                    records.append({
                        'date': str(item.get('F001D', '')),  # 公告日期
                        'title': str(item.get('F002V', '')),  # 公告标题
                        'type': str(item.get('F003V', '')),   # 公告类型
                        'code': str(item.get('SECCODE', symbol)),
                        'source': '巨潮资讯'
                    })
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records
                }
            return {'status': 'no_data', 'message': result.get('error', '无公告数据')}

        except Exception as e:
            logger.warning(f"⚠️ 巨潮公告获取失败: {e}")
            return {'status': 'no_data', 'message': f'巨潮公告暂不可用: {str(e)[:50]}'}

    def _get_cninfo_stock_news(self, ts_code: str) -> Dict:
        """获取巨潮官方API个股新闻（使用同步版本避免事件循环冲突）"""
        try:
            from backend.dataflows.announcement.cninfo_api import CninfoConfig, get_news_list_sync

            if not CninfoConfig.is_configured():
                return {'status': 'no_data', 'message': '巨潮API未配置'}

            symbol = extract_pure_symbol(ts_code)

            # 使用同步版本
            result = get_news_list_sync(stock_code=symbol, limit=30)

            if result.get('success') and result.get('data'):
                records = []
                for item in result['data'][:20]:
                    records.append({
                        'time': str(item.get('F001D', '')),      # 发布时间
                        'title': str(item.get('F006V', '')),     # 新闻标题
                        'news_id': str(item.get('TEXTID', '')),  # 新闻ID
                        'category': str(item.get('F005V', '')),  # 新闻分类
                        'author': str(item.get('F007V', '')),    # 发布作者
                        'source': '巨潮资讯'
                    })
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records
                }
            return {'status': 'no_data', 'message': result.get('error', '无新闻数据')}

        except Exception as e:
            logger.warning(f"⚠️ 巨潮新闻获取失败: {e}")
            return {'status': 'no_data', 'message': f'巨潮新闻暂不可用: {str(e)[:50]}'}

    def _get_cninfo_research_report(self, ts_code: str) -> Dict:
        """获取巨潮官方API个股研报摘要（使用同步版本避免事件循环冲突）"""
        try:
            from backend.dataflows.announcement.cninfo_api import CninfoConfig, get_research_report_summary_sync

            if not CninfoConfig.is_configured():
                return {'status': 'no_data', 'message': '巨潮API未配置'}

            symbol = extract_pure_symbol(ts_code)

            # 使用同步版本
            result = get_research_report_summary_sync(row_count=100)

            if result.get('success') and result.get('data'):
                # 筛选当前股票的研报
                records = []
                for item in result['data']:
                    item_code = str(item.get('SECCODE', ''))
                    if symbol in item_code or item_code in symbol:
                        records.append({
                            'date': str(item.get('F001D', '')),       # 资讯发布日期
                            'title': str(item.get('F002V', '')),      # 资讯标题
                            'content': str(item.get('F003V', ''))[:500],  # 资讯内容
                            'institution': str(item.get('F004V', '')),  # 研报发布机构
                            'report_date': str(item.get('F005D', '')),  # 研报发布日期
                            'category': str(item.get('F006V', '')),   # 资讯分类名称
                            'source': '巨潮资讯'
                        })
                if records:
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records[:10]  # 最多返回10条
                    }
            return {'status': 'no_data', 'message': '无研报数据'}

        except Exception as e:
            logger.warning(f"⚠️ 巨潮研报获取失败: {e}")
            return {'status': 'no_data', 'message': f'巨潮研报暂不可用: {str(e)[:50]}'}
    
    def _get_industry_policy(self) -> Dict:
        """获取行业政策动态（AKShare）- 使用财经新闻作为政策信息源"""
        try:
            import akshare as ak

            all_news = []

            # 1. 尝试获取财联社电报（实时财经新闻，包含政策信息）(stock_telegraph_cls已改名为stock_info_global_cls)
            try:
                df_cls = ak.stock_info_global_cls()
                if df_cls is not None and not df_cls.empty:
                    for _, row in df_cls.head(30).iterrows():
                        title = str(row.get('标题', ''))
                        content = str(row.get('内容', ''))
                        # 筛选政策相关新闻
                        policy_keywords = ['政策', '监管', '央行', '证监会', '发改委', '国务院',
                                         '部委', '法规', '条例', '意见', '通知', '规定']
                        if any(kw in title or kw in content for kw in policy_keywords):
                            all_news.append({
                                'time': str(row.get('发布时间', '')),
                                'title': title,
                                'content': content[:200] if len(content) > 200 else content,
                                'source': '财联社',
                                'type': 'policy'
                            })
            except Exception as e:
                logger.debug(f"财联社电报获取失败: {e}")

            # 2. 尝试获取东方财富全球资讯（不使用个股新闻API，避免混淆）
            try:
                df_em = ak.stock_info_global_em()
                if df_em is not None and not df_em.empty:
                    for _, row in df_em.head(20).iterrows():
                        title = str(row.get('标题', row.get('title', '')))
                        content = str(row.get('内容', row.get('content', '')))
                        # 筛选政策相关新闻
                        policy_keywords = ['政策', '监管', '央行', '证监会', '发改委', '国务院',
                                         '部委', '法规', '条例', '意见', '通知', '规定']
                        if any(kw in title or kw in content for kw in policy_keywords):
                            all_news.append({
                                'time': str(row.get('发布时间', row.get('time', ''))),
                                'title': title,
                                'content': content[:200] if len(content) > 200 else content,
                                'source': '东方财富',
                                'url': str(row.get('链接', row.get('url', ''))),
                                'type': 'financial_news'
                            })
            except Exception as e:
                logger.debug(f"东方财富全球资讯获取失败: {e}")

            if all_news:
                return {
                    'status': 'success',
                    'count': len(all_news),
                    'data': all_news,
                    'description': '财经政策新闻'
                }
            else:
                return {'status': 'no_data', 'message': '暂无政策新闻'}

        except Exception as e:
            logger.warning(f"⚠️ 行业政策获取失败: {e}")
            return {'status': 'no_data', 'message': '行业政策暂不可用'}
    
    def _get_stock_st_info_ak(self, ts_code: str) -> Dict:
        """获取ST股票详细信息（AKShare）"""
        try:
            import akshare as ak
            symbol = extract_pure_symbol(ts_code)
            
            # ST股票统计
            df = ak.stock_zh_a_st_em()
            if df is not None and not df.empty:
                stock_data = df[df['代码'] == symbol]
                if not stock_data.empty:
                    return {
                        'status': 'success',
                        'data': stock_data.iloc[0].to_dict()
                    }
            return {'status': 'no_data', 'message': '非ST股票'}
        except Exception as e:
            logger.warning(f"⚠️ ST信息获取失败: {e}")
            return {'status': 'no_data', 'message': 'ST信息暂不可用'}
    
    def _get_suspension_info_ak(self, ts_code: str) -> Dict:
        """获取停复牌信息（AKShare）"""
        try:
            import akshare as ak
            symbol = extract_pure_symbol(ts_code)
            
            # 停复牌信息
            df = ak.stock_zh_a_stop_em()
            if df is not None and not df.empty:
                stock_data = df[df['代码'] == symbol]
                if not stock_data.empty:
                    return {
                        'status': 'success',
                        'count': len(stock_data),
                        'data': stock_data.to_dict('records')
                    }
            return {'status': 'no_data', 'message': '无停复牌记录'}
        except Exception as e:
            logger.warning(f"⚠️ 停复牌信息获取失败: {e}")
            return {'status': 'no_data', 'message': '停复牌信息暂不可用'}
    
    def _get_pledge_detail_ak(self, ts_code: str) -> Dict:
        """获取股权质押详情（AKShare）"""
        try:
            import akshare as ak
            symbol = extract_pure_symbol(ts_code)

            # 方法1: 使用股权质押市场概况
            try:
                df = ak.stock_gpzy_pledge_ratio_em()
                if df is not None and not df.empty:
                    stock_data = df[df['股票代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.to_dict('records')
                        }
            except Exception as e1:
                logger.debug(f"stock_gpzy_pledge_ratio_em失败: {e1}")

            # 方法2: 使用质押统计
            try:
                df = ak.stock_gpzy_profile_em()
                if df is not None and not df.empty:
                    stock_data = df[df['股票代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.to_dict('records')
                        }
            except Exception as e2:
                logger.debug(f"stock_gpzy_profile_em失败: {e2}")

            return {'status': 'no_data', 'message': '无质押记录'}
        except Exception as e:
            logger.warning(f"⚠️ 质押详情获取失败: {e}")
            return {'status': 'no_data', 'message': '质押详情暂不可用'}
    
    def _get_restricted_shares_ak(self, ts_code: str) -> Dict:
        """获取限售股解禁（AKShare）- 多接口降级"""
        try:
            import akshare as ak
            symbol = extract_pure_symbol(ts_code)
            market = ts_code.split('.')[1] if '.' in ts_code else 'SH'

            # 方法1: 尝试新浪限售解禁接口
            try:
                sina_symbol = f"sh{symbol}" if market == 'SH' or symbol.startswith('6') else f"sz{symbol}"
                df = ak.stock_restricted_release_queue_sina(symbol=sina_symbol)
                if df is not None and not df.empty:
                    return {
                        'status': 'success',
                        'count': len(df),
                        'data': df.to_dict('records'),
                        'source': 'sina'
                    }
            except Exception as e1:
                logger.debug(f"新浪限售解禁接口失败: {e1}")

            # 方法2: 尝试东财限售解禁接口
            try:
                df = ak.stock_restricted_release_summary_em()
                if df is not None and not df.empty:
                    # 筛选当前股票
                    stock_data = df[df['代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.to_dict('records'),
                            'source': 'eastmoney'
                        }
            except Exception as e2:
                logger.debug(f"东财限售解禁接口失败: {e2}")

            return {'status': 'no_data', 'message': '无解禁数据（接口暂不可用）'}
        except Exception as e:
            logger.warning(f"⚠️ 限售股获取失败: {e}")
            return {'status': 'no_data', 'message': '限售股暂不可用'}
    
    def _get_shareholder_change_ak(self, ts_code: str) -> Dict:
        """获取股东增减持（AKShare）- 使用股东人数变化数据"""
        try:
            import akshare as ak
            symbol = extract_pure_symbol(ts_code)

            # 使用stock_zh_a_gdhs获取股东户数变化（这是正确的接口）
            # 股东户数变化可以反映筹码集中度
            df = ak.stock_zh_a_gdhs(symbol=symbol)
            if df is not None and not df.empty:
                records = []
                for _, row in df.head(20).iterrows():
                    records.append({
                        '截止日期': str(row.get('截止日期', '')),
                        '股东户数': int(row.get('股东户数', 0)) if pd.notna(row.get('股东户数')) else 0,
                        '较上期变化': float(row.get('较上期变化', 0)) if pd.notna(row.get('较上期变化')) else 0,
                        '人均流通股': float(row.get('人均流通股', 0)) if pd.notna(row.get('人均流通股')) else 0,
                        '股价': float(row.get('股价', 0)) if pd.notna(row.get('股价')) else 0,
                        '人均持股金额': float(row.get('人均持股金额', 0)) if pd.notna(row.get('人均持股金额')) else 0
                    })
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'description': '股东户数变化（筹码集中度指标）'
                }
            return {'status': 'no_data', 'message': '无股东户数数据'}
        except Exception as e:
            logger.warning(f"⚠️ 股东户数获取失败: {e}")
            return {'status': 'no_data', 'message': '股东户数暂不可用'}
    
    def _get_dragon_tiger_ak(self, ts_code: str) -> Dict:
        """获取龙虎榜（AKShare）"""
        try:
            import akshare as ak
            symbol = extract_pure_symbol(ts_code)

            # 方法1: 获取龙虎榜每日详情（不需要symbol参数）
            try:
                # 获取最近的龙虎榜数据
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

                df = ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date)
                if df is not None and not df.empty:
                    # 筛选当前股票
                    stock_data = df[df['代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.head(10).to_dict('records')
                        }
            except Exception as e1:
                logger.debug(f"stock_lhb_detail_em失败: {e1}")

            # 方法2: 使用龙虎榜营业部统计
            try:
                df = ak.stock_lhb_stock_statistic_em(symbol="近一月")
                if df is not None and not df.empty:
                    stock_data = df[df['代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.to_dict('records')
                        }
            except Exception as e2:
                logger.debug(f"stock_lhb_stock_statistic_em失败: {e2}")

            return {'status': 'no_data', 'message': '无龙虎榜数据'}
        except Exception as e:
            logger.warning(f"⚠️ 龙虎榜获取失败: {e}")
            return {'status': 'no_data', 'message': '龙虎榜暂不可用'}
    
    def _get_performance_forecast_ak(self, ts_code: str) -> Dict:
        """获取业绩预告（AKShare）"""
        try:
            import akshare as ak
            symbol = extract_pure_symbol(ts_code)

            # 方法1: 获取业绩预告汇总
            try:
                # 获取最新一期业绩预告
                df = ak.stock_yjyg_em(date="")  # 空字符串获取最新
                if df is not None and not df.empty:
                    stock_data = df[df['股票代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.to_dict('records')
                        }
            except Exception as e1:
                logger.debug(f"stock_yjyg_em失败: {e1}")

            # 方法2: 使用业绩快报
            try:
                df = ak.stock_yjkb_em(date="")
                if df is not None and not df.empty:
                    stock_data = df[df['股票代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.to_dict('records'),
                            'description': '业绩快报'
                        }
            except Exception as e2:
                logger.debug(f"stock_yjkb_em失败: {e2}")

            return {'status': 'no_data', 'message': '无业绩预告'}
        except Exception as e:
            logger.warning(f"⚠️ 业绩预告获取失败: {e}")
            return {'status': 'no_data', 'message': '业绩预告暂不可用'}
    
    def _get_audit_opinion_ak(self, ts_code: str) -> Dict:
        """获取审计意见（AKShare）"""
        try:
            import akshare as ak
            symbol = extract_pure_symbol(ts_code)

            # 方法1: 使用财务审计意见汇总
            try:
                df = ak.stock_fhps_detail_em()
                if df is not None and not df.empty:
                    stock_data = df[df['代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.to_dict('records')
                        }
            except Exception as e1:
                logger.debug(f"stock_fhps_detail_em失败: {e1}")

            # 方法2: 使用Tushare的审计意见（如果可用）
            if self.tushare_api:
                try:
                    df = self.tushare_api.fina_audit(ts_code=ts_code)
                    if df is not None and not df.empty:
                        return {
                            'status': 'success',
                            'count': len(df),
                            'data': df.to_dict('records'),
                            'source': 'tushare'
                        }
                except Exception as e2:
                    logger.debug(f"tushare fina_audit失败: {e2}")

            return {'status': 'no_data', 'message': '无审计意见'}
        except Exception as e:
            logger.warning(f"⚠️ 审计意见获取失败: {e}")
            return {'status': 'no_data', 'message': '审计意见暂不可用'}

    def _get_margin_trading_ak(self, ts_code: str) -> Dict:
        """获取融资融券（AKShare）"""
        try:
            import akshare as ak
            symbol = extract_pure_symbol(ts_code)

            # 方法1: 使用融资融券明细
            try:
                df = ak.stock_margin_detail_szse(date="")  # 最新日期
                if df is not None and not df.empty:
                    stock_data = df[df['证券代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.head(20).to_dict('records')
                        }
            except Exception as e1:
                logger.debug(f"stock_margin_detail_szse失败: {e1}")

            # 方法2: 使用上交所融资融券
            try:
                df = ak.stock_margin_detail_sse(date="")
                if df is not None and not df.empty:
                    stock_data = df[df['标的证券代码'].astype(str) == symbol]
                    if not stock_data.empty:
                        return {
                            'status': 'success',
                            'count': len(stock_data),
                            'data': stock_data.head(20).to_dict('records')
                        }
            except Exception as e2:
                logger.debug(f"stock_margin_detail_sse失败: {e2}")

            # 方法3: 使用东方财富融资融券汇总
            try:
                df = ak.stock_margin_sse(start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'))
                if df is not None and not df.empty:
                    return {
                        'status': 'success',
                        'count': len(df),
                        'data': df.head(20).to_dict('records'),
                        'description': '市场融资融券汇总'
                    }
            except Exception as e3:
                logger.debug(f"stock_margin_sse失败: {e3}")

            return {'status': 'no_data', 'message': '无融资融券数据'}
        except Exception as e:
            logger.warning(f"⚠️ 融资融券获取失败: {e}")
            return {'status': 'no_data', 'message': '融资融券暂不可用'}
    
    def _get_realtime_tick(self, ts_code: str) -> Dict:
        """获取实时成交数据（优先使用AKShare）"""
        symbol = extract_pure_symbol(ts_code)

        # 构建带市场前缀的代码（stock_zh_a_tick_tx_js 需要 sh600187 或 sz000001 格式）
        if symbol.startswith('6'):
            ak_symbol = f'sh{symbol}'
        else:
            ak_symbol = f'sz{symbol}'

        # 方法1: 使用AKShare获取分时数据
        try:
            import akshare as ak

            # 获取分时成交数据（需要带市场前缀）
            df = ak.stock_zh_a_tick_tx_js(symbol=ak_symbol)
            if df is not None and not df.empty:
                records = df.tail(20).to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'source': 'akshare',
                    'message': '分时成交数据'
                }
        except Exception as e:
            logger.debug(f"AKShare分时数据获取失败: {e}")

        # 方法2: 使用AKShare获取分钟K线（也需要带市场前缀）
        try:
            import akshare as ak

            df = ak.stock_zh_a_minute(symbol=ak_symbol, period='5', adjust="qfq")
            if df is not None and not df.empty:
                records = df.tail(20).to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'source': 'akshare',
                    'message': '5分钟K线数据'
                }
        except Exception as e:
            logger.debug(f"AKShare分钟K线获取失败: {e}")

        # 方法3: 备选Tushare（如果有高权限）
        try:
            if self.tushare_api:
                df = self.tushare_api.stk_mins(
                    ts_code=ts_code,
                    freq='5min'
                )
                if df is not None and not df.empty:
                    records = df.head(20).to_dict('records')
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records,
                        'source': 'tushare',
                        'message': '5分钟tick数据'
                    }
        except Exception as e:
            logger.debug(f"Tushare分钟数据获取失败: {e}")

        return {
            'status': 'no_data',
            'message': '暂无分时数据'
        }
    
    def _get_limit_list(self, ts_code: str) -> Dict:
        """获取涨跌停数据（优先Tushare，备选AKShare）"""
        symbol = extract_pure_symbol(ts_code)

        # 1. 尝试 Tushare
        if self.tushare_api:
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)

                df = self.tushare_api.limit_list_d(
                    ts_code=ts_code,
                    start_date=start_date.strftime('%Y%m%d'),
                    end_date=end_date.strftime('%Y%m%d')
                )

                if df is not None and not df.empty:
                    records = df.to_dict('records')
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records,
                        'source': 'tushare'
                    }
            except Exception as e:
                logger.debug(f"Tushare涨跌停数据获取失败: {e}")

        # 2. 备选：使用 AKShare
        try:
            import akshare as ak
            from datetime import datetime

            # 获取今日涨停池
            today = datetime.now().strftime('%Y%m%d')
            records = []

            # 尝试获取涨停池
            try:
                zt_df = ak.stock_zt_pool_em(date=today)
                if zt_df is not None and not zt_df.empty:
                    # 筛选当前股票
                    stock_zt = zt_df[zt_df['代码'].astype(str) == symbol]
                    if not stock_zt.empty:
                        for _, row in stock_zt.iterrows():
                            records.append({
                                'trade_date': today,
                                'limit': 'U',  # 涨停
                                'name': row.get('名称', ''),
                                'close': row.get('最新价', 0),
                                'pct_chg': row.get('涨跌幅', 0),
                                'source': 'akshare_zt_pool'
                            })
            except Exception as e1:
                logger.debug(f"AKShare涨停池获取失败: {e1}")

            # 尝试获取跌停池
            try:
                dt_df = ak.stock_dt_pool_em(date=today)
                if dt_df is not None and not dt_df.empty:
                    stock_dt = dt_df[dt_df['代码'].astype(str) == symbol]
                    if not stock_dt.empty:
                        for _, row in stock_dt.iterrows():
                            records.append({
                                'trade_date': today,
                                'limit': 'D',  # 跌停
                                'name': row.get('名称', ''),
                                'close': row.get('最新价', 0),
                                'pct_chg': row.get('涨跌幅', 0),
                                'source': 'akshare_dt_pool'
                            })
            except Exception as e2:
                logger.debug(f"AKShare跌停池获取失败: {e2}")

            if records:
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'source': 'akshare'
                }
        except Exception as e:
            logger.debug(f"AKShare涨跌停数据获取失败: {e}")

        return {
            'status': 'no_data',
            'message': '近期无涨跌停记录'
        }
    
    def _get_margin_data(self, ts_code: str) -> Dict:
        """获取融资融券数据（优先Tushare，备选AKShare）"""
        symbol = extract_pure_symbol(ts_code)
        exchange = 'SH' if ts_code.endswith('.SH') else 'SZ'

        # 1. 尝试 Tushare
        if self.tushare_api:
            try:
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

                df = self.tushare_api.margin(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )

                if df is not None and not df.empty:
                    records = df.head(10).to_dict('records')
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records,
                        'latest': records[0] if records else None,
                        'source': 'tushare'
                    }
            except Exception as e:
                logger.debug(f"Tushare融资融券数据获取失败: {e}")

        # 2. 备选：使用 AKShare
        try:
            import akshare as ak

            records = []

            # 根据交易所选择接口
            if exchange == 'SH':
                # 上交所融资融券
                try:
                    df = ak.stock_margin_detail_sse(date="")
                    if df is not None and not df.empty:
                        # 筛选当前股票
                        stock_df = df[df['标的证券代码'].astype(str) == symbol]
                        if not stock_df.empty:
                            for _, row in stock_df.head(10).iterrows():
                                records.append({
                                    'trade_date': row.get('信用交易日期', ''),
                                    'rzye': row.get('融资余额', 0),
                                    'rzmre': row.get('融资买入额', 0),
                                    'rzche': row.get('融资偿还额', 0),
                                    'rqye': row.get('融券余量', 0),
                                    'rqmcl': row.get('融券卖出量', 0),
                                    'rqchl': row.get('融券偿还量', 0),
                                    'source': 'akshare_sse'
                                })
                except Exception as e1:
                    logger.debug(f"AKShare上交所融资融券获取失败: {e1}")
            else:
                # 深交所融资融券
                try:
                    df = ak.stock_margin_detail_szse(date="")
                    if df is not None and not df.empty:
                        stock_df = df[df['证券代码'].astype(str) == symbol]
                        if not stock_df.empty:
                            for _, row in stock_df.head(10).iterrows():
                                records.append({
                                    'trade_date': row.get('交易日期', ''),
                                    'rzye': row.get('融资余额', 0),
                                    'rzmre': row.get('融资买入额', 0),
                                    'rzche': row.get('融资偿还额', 0),
                                    'rqye': row.get('融券余量', 0),
                                    'rqmcl': row.get('融券卖出量', 0),
                                    'rqchl': row.get('融券偿还量', 0),
                                    'source': 'akshare_szse'
                                })
                except Exception as e2:
                    logger.debug(f"AKShare深交所融资融券获取失败: {e2}")

            if records:
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'latest': records[0] if records else None,
                    'source': 'akshare'
                }
        except Exception as e:
            logger.debug(f"AKShare融资融券数据获取失败: {e}")

        return {
            'status': 'no_data',
            'message': '无融资融券数据'
        }
    
    def _get_company_info(self, ts_code: str) -> Dict:
        """获取上市公司基本信息"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'error': 'Tushare API未初始化'}
            
            df = self.tushare_api.stock_company(
                ts_code=ts_code,
                fields='ts_code,chairman,manager,secretary,reg_capital,setup_date,province,city,introduction,website,email,office,employees,main_business,business_scope'
            )
            
            if df is not None and not df.empty:
                info = df.iloc[0].to_dict()
                return {
                    'status': 'success',
                    'data': info
                }
            else:
                return {
                    'status': 'no_data',
                    'message': '无公司基本信息'
                }
                
        except Exception as e:
            logger.warning(f"⚠️ 公司基本信息获取失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_managers(self, ts_code: str) -> Dict:
        """获取管理层信息"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'error': 'Tushare API未初始化'}
            
            df = self.tushare_api.stk_managers(
                ts_code=ts_code
            )
            
            if df is not None and not df.empty:
                records = df.to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records
                }
            else:
                return {
                    'status': 'no_data',
                    'message': '无管理层信息'
                }
                
        except Exception as e:
            logger.warning(f"⚠️ 管理层信息获取失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_manager_rewards(self, ts_code: str) -> Dict:
        """获取管理层薪酬和持股"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'error': 'Tushare API未初始化'}
            
            # 获取最近3年的薪酬数据
            end_year = datetime.now().year
            
            df = self.tushare_api.stk_rewards(
                ts_code=ts_code,
                end_date=f'{end_year}1231'
            )
            
            if df is not None and not df.empty:
                records = df.to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records
                }
            else:
                return {
                    'status': 'no_data',
                    'message': '无薪酬数据'
                }
                
        except Exception as e:
            logger.warning(f"⚠️ 管理层薪酬获取失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_main_business(self, ts_code: str) -> Dict:
        """获取主营业务构成（优先Tushare，备选AKShare多接口降级）"""
        # 1. 尝试Tushare
        if self.tushare_api:
            try:
                # 不指定 period 参数，获取所有可用数据
                # fina_mainbz 的 period 参数需要是季度末日期（如20240630），不指定则返回所有数据
                df = self.tushare_api.fina_mainbz(
                    ts_code=ts_code,
                    type='P'  # P按产品 D按地区
                )

                if df is not None and not df.empty:
                    # Tushare fina_mainbz 返回字段: ts_code, end_date, bz_item, bz_sales, bz_profit, bz_cost, curr_type
                    # 需要计算 bz_sales_ratio 和 gross_margin
                    # 按报告期分组计算占比
                    records = []
                    df_sorted = df.head(20)

                    # 计算每个报告期的总收入用于计算占比
                    if 'end_date' in df_sorted.columns:
                        period_totals = df_sorted.groupby('end_date')['bz_sales'].sum()
                    else:
                        period_totals = {'total': df_sorted['bz_sales'].sum()}

                    for _, row in df_sorted.iterrows():
                        bz_sales = row.get('bz_sales', 0) or 0
                        bz_profit = row.get('bz_profit', 0) or 0
                        bz_cost = row.get('bz_cost', 0) or 0
                        end_date = row.get('end_date', '')

                        # 计算营收占比
                        if 'end_date' in df_sorted.columns and end_date in period_totals:
                            total_sales = period_totals[end_date]
                        else:
                            total_sales = period_totals.get('total', bz_sales)

                        bz_sales_ratio = bz_sales / total_sales if total_sales > 0 else None

                        # 计算毛利率 = (收入 - 成本) / 收入
                        if bz_sales > 0 and bz_cost > 0:
                            gross_margin = (bz_sales - bz_cost) / bz_sales
                        elif bz_sales > 0 and bz_profit > 0:
                            # 如果没有成本数据，尝试用利润计算
                            gross_margin = bz_profit / bz_sales
                        else:
                            gross_margin = None

                        records.append({
                            'bz_item': row.get('bz_item', '') or '',
                            'bz_sales': bz_sales,
                            'bz_sales_ratio': bz_sales_ratio,
                            'bz_profit': bz_profit,
                            'bz_cost': bz_cost,
                            'gross_margin': gross_margin,
                            'report_date': str(end_date) if end_date else ''
                        })

                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records,
                        'source': 'tushare'
                    }
            except Exception as e:
                logger.debug(f"Tushare主营业务获取失败: {e}")

        # 2. 备选：使用AKShare获取主营业务
        import akshare as ak
        stock_code = extract_pure_symbol(ts_code)
        # 获取市场标识
        if '.' in ts_code:
            market = ts_code.split('.')[1]
        elif ts_code.upper().startswith('SH'):
            market = 'SH'
        elif ts_code.upper().startswith('SZ'):
            market = 'SZ'
        else:
            # 根据股票代码推断市场
            market = 'SH' if stock_code.startswith(('6', '9')) else 'SZ'

        # 方法2a: 尝试 stock_zygc_em 接口
        try:
            symbol = f"{market}{stock_code}"
            df = ak.stock_zygc_em(symbol=symbol)

            if df is not None and not df.empty:
                # 转换列名以匹配前端期望
                # 新版AKShare列名: ['股票代码', '报告日期', '分类类型', '主营构成', '主营收入', '收入比例', '主营成本', '成本比例', '主营利润', '利润比例', '毛利率']
                records = []
                for _, row in df.head(20).iterrows():
                    # 安全获取数值，处理 NaN 和 None（使用 pd.isna 可以处理 numpy 和 python 的 NaN）
                    # 返回 None 表示数据不可用，前端会显示 NaN%
                    def safe_float(val, default=None):
                        if val is None or pd.isna(val):
                            return default
                        try:
                            return float(val)
                        except:
                            return default

                    # 收入比例已经是小数形式（如0.86），不需要除以100
                    sales_ratio = safe_float(row.get('收入比例'))
                    profit_ratio = safe_float(row.get('利润比例'))
                    cost_ratio = safe_float(row.get('成本比例'))
                    gross_margin = safe_float(row.get('毛利率'))

                    # 如果比例大于1，说明是百分比形式，需要除以100
                    if sales_ratio is not None and sales_ratio > 1:
                        sales_ratio = sales_ratio / 100
                    if profit_ratio is not None and profit_ratio > 1:
                        profit_ratio = profit_ratio / 100
                    if cost_ratio is not None and cost_ratio > 1:
                        cost_ratio = cost_ratio / 100
                    # 毛利率通常是百分比形式（如30表示30%），需要除以100
                    if gross_margin is not None and gross_margin > 1:
                        gross_margin = gross_margin / 100

                    records.append({
                        'bz_item': row.get('主营构成', '') or '',
                        'bz_type': row.get('分类类型', '') or '',
                        'bz_sales': safe_float(row.get('主营收入'), 0),
                        'bz_sales_ratio': sales_ratio,
                        'bz_profit': safe_float(row.get('主营利润'), 0),
                        'bz_profit_ratio': profit_ratio,
                        'bz_cost': safe_float(row.get('主营成本'), 0),
                        'bz_cost_ratio': cost_ratio,
                        'gross_margin': gross_margin,
                        'report_date': str(row.get('报告日期', '') or '')
                    })

                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'source': 'akshare_zygc_em'
                }
        except KeyError as e:
            # stock_zygc_em 已知bug：东财API返回格式变更导致KeyError
            logger.debug(f"AKShare stock_zygc_em KeyError: {e}")
        except Exception as e:
            logger.debug(f"AKShare stock_zygc_em 失败: {e}")

        # 方法2b: 尝试从财务指标中获取主营业务相关数据
        try:
            df = ak.stock_financial_analysis_indicator(symbol=stock_code, start_year="2023")
            if df is not None and not df.empty:
                # 提取主营业务相关指标
                records = []
                for _, row in df.head(4).iterrows():
                    records.append({
                        'bz_item': '主营业务',
                        'bz_sales': row.get('营业总收入', 0),
                        'bz_sales_ratio': 1.0,
                        'bz_profit': row.get('净利润', 0),
                        'bz_profit_ratio': row.get('净利润率', 0) / 100 if row.get('净利润率', 0) else 0,
                        'bz_cost': row.get('营业总成本', 0),
                        'report_date': str(row.get('日期', ''))
                    })
                if records:
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records,
                        'source': 'akshare_financial',
                        'note': '从财务指标提取，非详细主营构成'
                    }
        except Exception as e:
            logger.debug(f"AKShare财务指标获取失败: {e}")

        return {
            'status': 'no_data',
            'message': '无主营业务数据（接口暂不可用）'
        }

    def _get_hsgt_holding(self, ts_code: str) -> Dict:
        """获取沪深港通持股数据"""
        symbol = extract_pure_symbol(ts_code)

        # 方法1: 使用AKShare获取港股通持股数据
        try:
            import akshare as ak

            # 判断市场
            market = '沪股通' if symbol.startswith('6') else '深股通'
            df = ak.stock_hsgt_hold_stock_em(market=market)

            if df is not None and not df.empty:
                # 找到代码列
                code_col = None
                for col in df.columns:
                    if '代码' in str(col):
                        code_col = col
                        break

                if code_col:
                    stock_data = df[df[code_col].astype(str) == symbol]
                    if not stock_data.empty:
                        records = stock_data.to_dict('records')
                        return {
                            'status': 'success',
                            'count': len(records),
                            'data': records,
                            'latest': records[0] if records else None,
                            'source': 'akshare'
                        }
        except Exception as e:
            logger.debug(f"AKShare港股通持股获取失败: {e}")

        # 方法2: 使用Tushare
        try:
            if self.tushare_api:
                # 获取最近30天的数据
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

                df = self.tushare_api.hsgt_top10(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )

                if df is not None and not df.empty:
                    records = df.to_dict('records')
                    return {
                        'status': 'success',
                        'count': len(records),
                        'data': records,
                        'latest': records[0] if records else None,
                        'source': 'tushare'
                    }
        except Exception as e:
            logger.debug(f"Tushare港股通持股获取失败: {e}")

        return {
            'status': 'no_data',
            'message': '无港股通持股数据'
        }
    
    def _get_announcements(self, ts_code: str) -> Dict:
        """获取上市公司公告（暂无可用接口）"""
        # Tushare的公告接口需要高积分权限，AKShare的stock_notice_report也不稳定
        # 作为替代，我们使用业绩预告和快报作为“重要公告”
        try:
            if not self.tushare_api:
                return {'status': 'no_data', 'message': '公告查询暂不可用'}
            
            # 使用业绩预告作为重要公告的替代
            announcements = []
            
            # 1. 业绩预告
            try:
                forecast_df = self.tushare_api.forecast(
                    ts_code=ts_code,
                    start_date=(datetime.now() - timedelta(days=365)).strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d')
                )
                if forecast_df is not None and not forecast_df.empty:
                    for _, row in forecast_df.head(5).iterrows():
                        announcements.append({
                            'type': '业绩预告',
                            'ann_date': row.get('ann_date', ''),
                            'end_date': row.get('end_date', ''),
                            'summary': row.get('summary', ''),
                            'change_reason': row.get('change_reason', '')
                        })
            except:
                pass
            
            # 2. 业绩快报
            try:
                express_df = self.tushare_api.express(
                    ts_code=ts_code,
                    start_date=(datetime.now() - timedelta(days=365)).strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d')
                )
                if express_df is not None and not express_df.empty:
                    for _, row in express_df.head(5).iterrows():
                        announcements.append({
                            'type': '业绩快报',
                            'ann_date': row.get('ann_date', ''),
                            'end_date': row.get('end_date', ''),
                            'revenue': row.get('revenue', 0),
                            'profit': row.get('operate_profit', 0)
                        })
            except:
                pass
            
            if announcements:
                return {
                    'status': 'success',
                    'count': len(announcements),
                    'data': announcements,
                    'message': '重要公告（业绩预告/快报）'
                }
            else:
                return {
                    'status': 'no_data',
                    'message': '近一年无重要公告'
                }
                
        except Exception as e:
            logger.warning(f"⚠️ 公告数据获取失败: {e}")
            return {
                'status': 'no_data',
                'message': '公告查询暂不可用'
            }

    def _get_news_data(self, ts_code: str) -> List[Dict]:
        """获取新闻数据（调用现有的新闻聚合器 + 巨潮官方API）

        数据源接口说明:
        - 多源新闻聚合器: AKShare东方财富个股新闻、东方财富全球资讯、财联社全球资讯、百度财经新闻、备用源realtime_news
        - 巨潮官方API: 个股公告(announcement)、个股新闻(news)、个股研报摘要(research)
        """
        all_news = []

        # 1. 从新闻聚合器获取（默认分类为news）
        try:
            from backend.dataflows.news.multi_source_news_aggregator import get_news_aggregator

            aggregator = get_news_aggregator()
            result = aggregator.aggregate_news(
                ts_code=ts_code,
                limit_per_source=50,  # 每个源50条
                include_tushare=False,
                include_akshare=True,
                include_market_news=True
            )

            merged_news = result.get('merged_news', [])
            # 为聚合器返回的新闻添加默认字段
            for news in merged_news:
                news['report_type'] = news.get('report_type', 'news')  # 默认为新闻类型
                news['sentiment'] = news.get('sentiment', 'neutral')
                news['score'] = news.get('score', 50)
                news['urgency'] = news.get('urgency', 'normal')
            all_news.extend(merged_news)
        except Exception as e:
            logger.warning(f"新闻聚合器获取失败: {e}")

        # 2. 从巨潮官方API获取公告
        try:
            cninfo_ann = self._get_cninfo_announcement(ts_code)
            if cninfo_ann.get('status') == 'success' and cninfo_ann.get('data'):
                for item in cninfo_ann['data']:
                    all_news.append({
                        'title': item.get('title', ''),
                        'content': f"公告类型: {item.get('type', '未知')}",
                        'pub_time': item.get('date', ''),
                        'source': '巨潮资讯',
                        'report_type': 'announcement',
                        'sentiment': 'neutral',
                        'score': 50,
                        'urgency': 'normal',
                        'url': ''
                    })
        except Exception as e:
            logger.debug(f"巨潮公告获取失败: {e}")

        # 3. 从巨潮官方API获取新闻
        try:
            cninfo_news = self._get_cninfo_stock_news(ts_code)
            if cninfo_news.get('status') == 'success' and cninfo_news.get('data'):
                for item in cninfo_news['data']:
                    all_news.append({
                        'title': item.get('title', ''),
                        'content': f"分类: {item.get('category', '未知')} | 作者: {item.get('author', '未知')}",
                        'pub_time': item.get('time', ''),
                        'source': '巨潮资讯',
                        'report_type': 'news',
                        'sentiment': 'neutral',
                        'score': 50,
                        'urgency': 'normal',
                        'url': ''
                    })
        except Exception as e:
            logger.debug(f"巨潮新闻获取失败: {e}")

        # 4. 从巨潮官方API获取研报
        try:
            cninfo_research = self._get_cninfo_research_report(ts_code)
            if cninfo_research.get('status') == 'success' and cninfo_research.get('data'):
                for item in cninfo_research['data']:
                    all_news.append({
                        'title': item.get('title', ''),
                        'content': f"机构: {item.get('institution', '未知')} | {item.get('content', '')[:200]}",
                        'pub_time': item.get('date', ''),
                        'source': '巨潮资讯',
                        'report_type': 'research',
                        'sentiment': 'neutral',
                        'score': 50,
                        'urgency': 'normal',
                        'url': ''
                    })
        except Exception as e:
            logger.debug(f"巨潮研报获取失败: {e}")

        # 按时间排序（最新的在前）
        try:
            all_news.sort(key=lambda x: x.get('pub_time', ''), reverse=True)
        except:
            pass

        return all_news

    # ==================== 缺失的Tushare接口补充 ====================

    def _get_realtime_list(self) -> Dict:
        """获取实时行情列表（Tushare realtime_list）- 全市场实时行情"""
        try:
            import tushare as ts
            # 使用爬虫接口获取全市场实时行情
            df = ts.realtime_list(src='dc')  # dc=东财

            if df is not None and not df.empty:
                records = df.head(100).to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'description': '全市场实时行情TOP100'
                }
            return {'status': 'no_data', 'message': '无实时行情数据'}
        except Exception as e:
            logger.warning(f"⚠️ 实时行情列表获取失败: {e}")
            return {'status': 'no_data', 'message': '实时行情列表暂不可用'}

    def _get_pledge_detail(self, ts_code: str) -> Dict:
        """获取股权质押明细（Tushare pledge_detail）"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'message': 'Tushare API未初始化'}

            df = self.tushare_api.pledge_detail(ts_code=ts_code)

            if df is not None and not df.empty:
                records = df.head(20).to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'description': '股权质押明细'
                }
            return {'status': 'no_data', 'message': '无质押明细数据'}
        except Exception as e:
            logger.warning(f"⚠️ 质押明细获取失败: {e}")
            return {'status': 'no_data', 'message': '质押明细暂不可用'}

    def _get_margin_detail(self, ts_code: str) -> Dict:
        """获取融资融券明细（Tushare margin_detail）"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'message': 'Tushare API未初始化'}

            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

            df = self.tushare_api.margin_detail(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

            if df is not None and not df.empty:
                records = df.head(30).to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'description': '融资融券明细'
                }
            return {'status': 'no_data', 'message': '无融资融券明细'}
        except Exception as e:
            logger.warning(f"⚠️ 融资融券明细获取失败: {e}")
            return {'status': 'no_data', 'message': '融资融券明细暂不可用'}

    def _get_ggt_top10(self, ts_code: str = None) -> Dict:
        """获取港股通十大成交股（Tushare ggt_top10）"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'message': 'Tushare API未初始化'}

            trade_date = datetime.now().strftime('%Y%m%d')

            # 尝试获取最近5个交易日的数据
            for i in range(5):
                try:
                    check_date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
                    df = self.tushare_api.ggt_top10(trade_date=check_date)
                    if df is not None and not df.empty:
                        if ts_code:
                            df = df[df['ts_code'] == ts_code]
                        if not df.empty:
                            records = df.to_dict('records')
                            return {
                                'status': 'success',
                                'count': len(records),
                                'data': records,
                                'trade_date': check_date,
                                'description': '港股通十大成交股'
                            }
                except:
                    continue

            return {'status': 'no_data', 'message': '无港股通十大成交数据'}
        except Exception as e:
            logger.warning(f"⚠️ 港股通十大成交获取失败: {e}")
            return {'status': 'no_data', 'message': '港股通十大成交暂不可用'}

    def _get_hk_hold(self, ts_code: str) -> Dict:
        """获取沪深港通持股明细（Tushare hk_hold）"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'message': 'Tushare API未初始化'}

            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

            df = self.tushare_api.hk_hold(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

            if df is not None and not df.empty:
                records = df.head(30).to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'description': '沪深港通持股明细'
                }
            return {'status': 'no_data', 'message': '无沪深港通持股明细'}
        except Exception as e:
            logger.warning(f"⚠️ 沪深港通持股明细获取失败: {e}")
            return {'status': 'no_data', 'message': '沪深港通持股明细暂不可用'}

    def _get_moneyflow_hsgt(self) -> Dict:
        """获取沪深港通资金流向（Tushare moneyflow_hsgt）"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'message': 'Tushare API未初始化'}

            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')

            df = self.tushare_api.moneyflow_hsgt(
                start_date=start_date,
                end_date=end_date
            )

            if df is not None and not df.empty:
                records = df.to_dict('records')
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'description': '沪深港通资金流向'
                }
            return {'status': 'no_data', 'message': '无沪深港通资金流向数据'}
        except Exception as e:
            logger.warning(f"⚠️ 沪深港通资金流向获取失败: {e}")
            return {'status': 'no_data', 'message': '沪深港通资金流向暂不可用'}

    def _get_limit_list_ths(self, ts_code: str = None) -> Dict:
        """获取同花顺涨跌停数据（Tushare limit_list_ths）- 备用接口"""
        try:
            if not self.tushare_api:
                return {'status': 'error', 'message': 'Tushare API未初始化'}

            trade_date = datetime.now().strftime('%Y%m%d')

            # 尝试获取最近5个交易日的数据
            for i in range(5):
                try:
                    check_date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
                    df = self.tushare_api.limit_list_d(trade_date=check_date)
                    if df is not None and not df.empty:
                        if ts_code:
                            df = df[df['ts_code'] == ts_code]
                        if not df.empty:
                            records = df.to_dict('records')
                            return {
                                'status': 'success',
                                'count': len(records),
                                'data': records,
                                'trade_date': check_date,
                                'description': '涨跌停数据'
                            }
                except:
                    continue

            return {'status': 'no_data', 'message': '无涨跌停数据'}
        except Exception as e:
            logger.warning(f"⚠️ 涨跌停数据获取失败: {e}")
            return {'status': 'no_data', 'message': '涨跌停数据暂不可用'}

    # ==================== 缺失的AKShare接口补充 ====================

    def _get_stock_news_em(self, ts_code: str) -> Dict:
        """获取东方财富个股新闻（使用修复版函数）"""
        try:
            from backend.dataflows.stock.akshare_utils import get_stock_news_em
            symbol = extract_pure_symbol(ts_code)

            df = get_stock_news_em(symbol=symbol, max_news=30)

            if df is not None and not df.empty:
                records = []
                for _, row in df.iterrows():
                    records.append({
                        'title': str(row.get('新闻标题', '')),
                        'content': str(row.get('新闻内容', ''))[:300],
                        'time': str(row.get('发布时间', '')),
                        'source': str(row.get('文章来源', '东方财富')),
                        'url': str(row.get('新闻链接', ''))
                    })
                return {
                    'status': 'success',
                    'count': len(records),
                    'data': records,
                    'description': '东方财富个股新闻'
                }
            return {'status': 'no_data', 'message': '无个股新闻'}
        except Exception as e:
            logger.warning(f"⚠️ 东方财富新闻获取失败: {e}")
            return {'status': 'no_data', 'message': '东方财富新闻暂不可用'}

    def _generate_summary(self, data: Dict) -> Dict:
        """生成数据摘要"""
        summary = {}
        
        # 1. 实时行情
        if data['realtime'].get('status') == 'success':
            summary['realtime'] = '✅ 已获取'
        
        # 2. 实时成交
        if data['realtime_tick'].get('status') == 'success':
            summary['realtime_tick'] = f"✅ 成交{data['realtime_tick']['count']}条"
        elif data['realtime_tick'].get('status') == 'no_data':
            summary['realtime_tick'] = '🔴 无成交数据'
        
        # 3. 停复牌
        if data['suspend'].get('status') in ['normal', 'has_suspend']:
            summary['suspend'] = f"✅ {data['suspend']['message']}"
        
        # 4. ST状态
        if data['st_status'].get('status') in ['normal', 'st_stock']:
            summary['st_status'] = f"✅ {data['st_status']['message']}"
        
        # 5. 财务数据
        if data['financial'].get('status') == 'success':
            summary['financial'] = f"✅ 利润表{len(data['financial']['income'])}期 资产负债表{len(data['financial']['balance'])}期 现金流{len(data['financial']['cashflow'])}期"
        
        # 6. 审计意见
        if data.get('audit', {}).get('status') == 'success':
            count = data['audit'].get('count', len(data['audit'].get('data', [])))
            summary['audit'] = f"✅ 审计意见{count}条"
        elif data.get('audit', {}).get('status') == 'no_data':
            summary['audit'] = '🔴 无审计数据'
        
        # 7. 业绩预告
        if data['forecast'].get('status') == 'success':
            summary['forecast'] = f"✅ 业绩预告{len(data['forecast']['forecast'])}条 快报{len(data['forecast']['express'])}条"
        elif data['forecast'].get('status') == 'no_data':
            summary['forecast'] = '🔴 无业绩预告'
        
        # 8. 分红送股
        if data['dividend'].get('status') == 'success':
            summary['dividend'] = f"✅ 分红记录{data['dividend']['count']}条"
        elif data['dividend'].get('status') == 'no_data':
            summary['dividend'] = '🔴 无分红记录'
        
        # 9. 限售解禁
        if data['restricted'].get('status') == 'success':
            summary['restricted'] = f"✅ 解禁数据{data['restricted']['count']}条"
        elif data['restricted'].get('status') == 'no_data':
            summary['restricted'] = '🔴 无解禁数据'
        
        # 10. 股权质押
        if data['pledge'].get('status') == 'success':
            summary['pledge'] = f"✅ 质押比例{data['pledge']['pledge_ratio']}%"
        elif data['pledge'].get('status') == 'no_data':
            summary['pledge'] = '🔴 无质押数据'
        
        # 11. 股东增减持
        if data['holder_trade'].get('status') == 'success':
            summary['holder_trade'] = f"✅ 增减持{data['holder_trade']['count']}条"
        elif data['holder_trade'].get('status') == 'no_data':
            summary['holder_trade'] = '🔴 无增减持记录'
        
        # 12. 龙虎榜
        if data['dragon_tiger'].get('status') == 'success':
            summary['dragon_tiger'] = f"✅ 龙虎榜{data['dragon_tiger']['count']}次"
        elif data['dragon_tiger'].get('status') == 'no_data':
            summary['dragon_tiger'] = '🔴 无龙虎榜数据'
        
        # 12.5 机构龙虎榜
        if data.get('top_inst', {}).get('status') == 'success':
            summary['top_inst'] = f"✅ 机构龙虎榜{data['top_inst']['count']}条"
        
        # 12.6 大宗交易
        if data.get('block_trade', {}).get('status') == 'success':
            summary['block_trade'] = f"✅ 大宗交易{data['block_trade']['count']}条"
        
        # 13. 涨跌停
        if data['limit_list'].get('status') == 'success':
            summary['limit_list'] = f"✅ 涨跌停{data['limit_list']['count']}次"
        elif data['limit_list'].get('status') == 'no_data':
            summary['limit_list'] = '🔴 近30天无涨跌停'
        
        # 14. 融资融券
        if data['margin'].get('status') == 'success':
            summary['margin'] = f"✅ 融资融券{data['margin']['count']}条"
        elif data['margin'].get('status') == 'no_data':
            summary['margin'] = '🔴 无融资融券数据'
        
        # 15. 公司信息
        if data['company_info'].get('status') == 'success':
            summary['company_info'] = '✅ 已获取公司信息'
        elif data['company_info'].get('status') == 'no_data':
            summary['company_info'] = '🔴 无公司信息'
        
        # 16. 管理层
        if data['managers'].get('status') == 'success':
            summary['managers'] = f"✅ 管理层{data['managers']['count']}人"
        elif data['managers'].get('status') == 'no_data':
            summary['managers'] = '🔴 无管理层信息'
        
        # 17. 管理层薪酬
        if data['manager_rewards'].get('status') == 'success':
            summary['manager_rewards'] = f"✅ 薪酬记录{data['manager_rewards']['count']}条"
        elif data['manager_rewards'].get('status') == 'no_data':
            summary['manager_rewards'] = '🔴 无薪酬记录'
        
        # 18. 主营业务
        if data['main_business'].get('status') == 'success':
            summary['main_business'] = f"✅ 主营构成{data['main_business']['count']}条"
        elif data['main_business'].get('status') == 'no_data':
            summary['main_business'] = '🔴 无主营业务数据'
        
        # 19. 港股通
        if data['hsgt_holding'].get('status') == 'success':
            summary['hsgt_holding'] = f"✅ 港股通{data['hsgt_holding']['count']}条"
        elif data['hsgt_holding'].get('status') == 'no_data':
            summary['hsgt_holding'] = '🔴 无港股通数据'
        
        # 20. 公告
        if data['announcements'].get('status') == 'success':
            summary['announcements'] = f"✅ 公告{data['announcements']['count']}条"
        elif data['announcements'].get('status') == 'no_data':
            summary['announcements'] = '🔴 无公告数据'

        # 20.5 新浪新闻
        if data.get('news_sina', {}).get('status') == 'success':
            summary['news_sina'] = f"✅ 新浪新闻{data['news_sina']['count']}条"

        # 20.6 市场快讯
        if data.get('market_news', {}).get('status') == 'success':
            summary['market_news'] = f"✅ 市场快讯{data['market_news']['count']}条"

        # 20.7 行业政策
        if data.get('industry_policy', {}).get('status') == 'success':
            summary['industry_policy'] = f"✅ 行业政策{data['industry_policy']['count']}条"

        # 21. 新闻
        if data['news']:
            summary['news'] = f"✅ 新闻{len(data['news'])}条"
        else:
            summary['news'] = '🔴 无新闻数据'

        # ==================== 新增接口摘要 ====================

        # 22. 全市场实时行情
        if data.get('realtime_list', {}).get('status') == 'success':
            summary['realtime_list'] = f"✅ 全市场行情{data['realtime_list']['count']}条"

        # 23. 质押明细
        if data.get('pledge_detail', {}).get('status') == 'success':
            summary['pledge_detail'] = f"✅ 质押明细{data['pledge_detail']['count']}条"

        # 24. 融资融券明细
        if data.get('margin_detail', {}).get('status') == 'success':
            summary['margin_detail'] = f"✅ 融资融券明细{data['margin_detail']['count']}条"

        # 25. 港股通十大成交
        if data.get('ggt_top10', {}).get('status') == 'success':
            summary['ggt_top10'] = f"✅ 港股通十大{data['ggt_top10']['count']}条"

        # 26. 沪深港通持股明细
        if data.get('hk_hold', {}).get('status') == 'success':
            summary['hk_hold'] = f"✅ 沪深港通持股{data['hk_hold']['count']}条"

        # 27. 沪深港通资金流向
        if data.get('moneyflow_hsgt', {}).get('status') == 'success':
            summary['moneyflow_hsgt'] = f"✅ 资金流向{data['moneyflow_hsgt']['count']}条"

        # 28. 涨跌停数据（同花顺）
        if data.get('limit_list_ths', {}).get('status') == 'success':
            summary['limit_list_ths'] = f"✅ 涨跌停THS{data['limit_list_ths']['count']}条"

        # 29. 东方财富个股新闻
        if data.get('news_em', {}).get('status') == 'success':
            summary['news_em'] = f"✅ 东财新闻{data['news_em']['count']}条"

        # 30. 巨潮个股公告
        if data.get('cninfo_announcement', {}).get('status') == 'success':
            summary['cninfo_announcement'] = f"✅ 巨潮公告{data['cninfo_announcement']['count']}条"

        # 31. 巨潮个股新闻
        if data.get('cninfo_news', {}).get('status') == 'success':
            summary['cninfo_news'] = f"✅ 巨潮新闻{data['cninfo_news']['count']}条"

        # 32. 巨潮研报摘要
        if data.get('cninfo_research', {}).get('status') == 'success':
            summary['cninfo_research'] = f"✅ 巨潮研报{data['cninfo_research']['count']}条"

        return summary


# 全局实例
_comprehensive_service = None

def get_comprehensive_service():
    """获取综合数据服务实例"""
    global _comprehensive_service
    if _comprehensive_service is None:
        _comprehensive_service = ComprehensiveStockDataService()
    return _comprehensive_service
