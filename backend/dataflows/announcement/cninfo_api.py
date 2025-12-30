# -*- coding: utf-8 -*-
"""
巨潮资讯网官方API客户端
基于 webapi.cninfo.com.cn 官方接口

认证方式：
- 使用 Access Key 和 Access Secret 通过 OAuth2 获取 access_token
- 然后在请求中携带 access_token 参数

使用方式：
1. 在 .env 中配置 CNINFO_ACCESS_KEY, CNINFO_ACCESS_SECRET
2. 或在 backend/config/cninfo_config.json 中配置
"""

import os
import json
import time
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

import httpx

from backend.utils.logging_config import get_logger

logger = get_logger("cninfo_api")

# 配置文件路径
CONFIG_FILE_PATH = Path(__file__).parent.parent.parent / 'config' / 'cninfo_config.json'

# API基础URL
API_BASE_URL = "http://webapi.cninfo.com.cn"
TOKEN_URL = "http://webapi.cninfo.com.cn/api-cloud-platform/oauth2/token"


class CninfoConfig:
    """巨潮API配置管理"""

    _config_cache: Dict[str, Any] = {}
    _config_loaded: bool = False

    @classmethod
    def _load_config_file(cls) -> Dict[str, Any]:
        """从配置文件加载配置"""
        if CONFIG_FILE_PATH.exists():
            try:
                with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载巨潮配置文件失败: {e}")
        return {}

    @classmethod
    def _get_config(cls, key: str, default: str = '') -> str:
        """获取配置值，优先从配置文件读取，其次从环境变量"""
        if not cls._config_loaded:
            cls._config_cache = cls._load_config_file()
            cls._config_loaded = True

        if key in cls._config_cache:
            return cls._config_cache[key]

        return os.getenv(key, default)

    @classmethod
    def reload_config(cls):
        """重新加载配置"""
        cls._config_cache = cls._load_config_file()
        cls._config_loaded = True
        logger.info("巨潮配置已重新加载")

    @classmethod
    def save_config(cls, config: Dict[str, Any]) -> bool:
        """保存配置到文件"""
        try:
            CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            existing_config = cls._load_config_file()
            existing_config.update(config)

            with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(existing_config, f, ensure_ascii=False, indent=2)

            cls._config_cache = existing_config
            cls._config_loaded = True
            logger.info(f"巨潮配置已保存到: {CONFIG_FILE_PATH}")
            return True
        except Exception as e:
            logger.error(f"保存巨潮配置失败: {e}")
            return False

    @classmethod
    def is_configured(cls) -> bool:
        """检查是否已配置"""
        return bool(cls._get_config('CNINFO_ACCESS_KEY', '') and cls._get_config('CNINFO_ACCESS_SECRET', ''))

    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """获取所有配置（脱敏）"""
        return {
            'CNINFO_ACCESS_KEY': cls._get_config('CNINFO_ACCESS_KEY', '')[:8] + '***' if cls._get_config('CNINFO_ACCESS_KEY', '') else '',
            'CNINFO_ACCESS_SECRET': '******' if cls._get_config('CNINFO_ACCESS_SECRET', '') else '',
            'configured': cls.is_configured()
        }


class CninfoApiClient:
    """巨潮资讯网官方API客户端"""

    def __init__(self):
        self.base_url = API_BASE_URL
        self.config = CninfoConfig
        self._client: Optional[httpx.AsyncClient] = None
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        """关闭客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _get_access_token(self) -> str:
        """获取OAuth2 access_token"""
        # 检查缓存的token是否有效
        if self._access_token and self._token_expires and datetime.now() < self._token_expires:
            return self._access_token

        access_key = self.config._get_config('CNINFO_ACCESS_KEY', '')
        access_secret = self.config._get_config('CNINFO_ACCESS_SECRET', '')

        if not access_key or not access_secret:
            raise ValueError("巨潮API未配置Access Key或Access Secret")

        client = await self._get_client()
        post_data = {
            'grant_type': 'client_credentials',
            'client_id': access_key,
            'client_secret': access_secret
        }

        response = await client.post(TOKEN_URL, data=post_data)
        if response.status_code == 200:
            result = response.json()
            self._access_token = result.get('access_token', '')
            # Token有效期通常是7200秒(2小时)，我们设置为1.5小时后过期
            self._token_expires = datetime.now() + timedelta(hours=1, minutes=30)
            logger.info("巨潮API Token获取成功")
            return self._access_token
        else:
            raise ValueError(f"获取巨潮API Token失败: {response.text}")

    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """发送API请求"""
        if not self.config.is_configured():
            return {'success': False, 'error': '巨潮API未配置，请先配置 CNINFO_ACCESS_KEY 和 CNINFO_ACCESS_SECRET'}

        try:
            # 获取access_token
            access_token = await self._get_access_token()

            url = f"{self.base_url}{endpoint}"
            client = await self._get_client()

            # 构建请求参数
            request_params = params.copy() if params else {}
            request_params['access_token'] = access_token

            # 发送GET请求
            response = await client.get(url, params=request_params)

            if response.status_code == 200:
                result = response.json()
                if result.get('resultcode') == 200:
                    return {
                        'success': True,
                        'data': result.get('records', []),
                        'total': len(result.get('records', []))
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('resultmsg', '未知错误'),
                        'code': result.get('resultcode')
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP错误: {response.status_code}',
                    'status_code': response.status_code
                }
        except Exception as e:
            logger.error(f"巨潮API请求失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 公共数据接口 ====================

    async def get_trade_calendar(
        self,
        start_date: str,
        end_date: str,
        market: str = 'SZ'
    ) -> Dict[str, Any]:
        """
        获取交易日历 [免费可用]

        Args:
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            market: 市场 SZ/SH
        """
        return await self._request('/api/stock/p_public0001', {
            'sdate': start_date,
            'edate': end_date,
            'market': market
        })

    async def get_industry_classification(
        self,
        ind_code: str = '',
        ind_type: str = '137004'  # 默认申万行业
    ) -> Dict[str, Any]:
        """
        获取行业分类 [免费可用]

        Args:
            ind_code: 行业代码
            ind_type: 分类标准 137002中上协/137004申万/137005新财富
        """
        return await self._request('/api/stock/p_public0002', {
            'indcode': ind_code,
            'indtype': ind_type
        })

    # ==================== 公告信息接口 (免费可用) ====================

    async def get_announcement_categories(
        self,
        sort_code: str = '',
        parent_code: str = '01'
    ) -> Dict[str, Any]:
        """
        获取公告分类信息 [免费可用]

        Args:
            sort_code: 分类编码
            parent_code: 父类编码，顶级分类为01
        """
        params = {}
        if sort_code:
            params['sortcode'] = sort_code
        if parent_code:
            params['parentcode'] = parent_code
        return await self._request('/api/info/p_info3005', params)

    # ==================== 股票数据接口 (需要付费权限) ====================

    async def get_stock_info(
        self,
        stock_codes: List[str],
        market: str = ''
    ) -> Dict[str, Any]:
        """
        获取股票背景资料

        Args:
            stock_codes: 股票代码列表（最多300只）
            market: 市场 SZ/SH
        """
        codes = ','.join(stock_codes[:300])
        params = {'scode': codes}
        if market:
            params['market'] = market
        return await self._request('/api/stock/p_stock0001', params)

    async def get_company_info(self, stock_codes: List[str]) -> Dict[str, Any]:
        """
        获取公司基本信息

        Args:
            stock_codes: 股票代码列表（最多300只）
        """
        codes = ','.join(stock_codes[:300])
        return await self._request('/api/stock/p_stock0005', {'scode': codes})

    async def get_stock_basic_info(
        self,
        stock_codes: List[str],
        market: str = ''
    ) -> Dict[str, Any]:
        """
        获取股票基本信息

        Args:
            stock_codes: 股票代码列表（最多300只）
            market: 市场 SZ/SH
        """
        codes = ','.join(stock_codes[:300])
        params = {'scode': codes}
        if market:
            params['market'] = market
        return await self._request('/api/stock/p_stock0006', params)

    async def get_stock_sector(
        self,
        stock_codes: List[str],
        type_code: str = '137004'  # 默认申万行业
    ) -> Dict[str, Any]:
        """
        获取股票所属板块

        Args:
            stock_codes: 股票代码列表（最多300只）
            type_code: 分类标准
        """
        codes = ','.join(stock_codes[:300])
        return await self._request('/api/stock/p_stock0004', {
            'scode': codes,
            'typecode': type_code
        })

    # ==================== 财务数据接口 ====================

    async def get_performance_forecast(
        self,
        stock_codes: List[str] = None,
        report_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取业绩预告

        Args:
            stock_codes: 股票代码列表
            report_date: 报告期 YYYY-MM-DD
        """
        params = {}
        if stock_codes:
            params['scode'] = ','.join(stock_codes[:300])
        if report_date:
            params['rdate'] = report_date
        return await self._request('/api/stock/p_stock2002', params)

    async def get_performance_express(
        self,
        stock_codes: List[str] = None,
        report_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取业绩快报

        Args:
            stock_codes: 股票代码列表
            report_date: 报告期 YYYY-MM-DD
        """
        params = {}
        if stock_codes:
            params['scode'] = ','.join(stock_codes[:300])
        if report_date:
            params['rdate'] = report_date
        return await self._request('/api/stock/p_stock2004', params)

    async def get_balance_sheet(
        self,
        stock_codes: List[str],
        start_date: str = '',
        end_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取资产负债表

        Args:
            stock_codes: 股票代码列表（最多50只）
            start_date: 开始日期
            end_date: 结束日期
        """
        codes = ','.join(stock_codes[:50])
        params = {'scode': codes}
        if start_date:
            params['sdate'] = start_date
        if end_date:
            params['edate'] = end_date
        return await self._request('/api/stock/p_stock2101', params)

    async def get_income_statement(
        self,
        stock_codes: List[str],
        start_date: str = '',
        end_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取利润表

        Args:
            stock_codes: 股票代码列表（最多50只）
            start_date: 开始日期
            end_date: 结束日期
        """
        codes = ','.join(stock_codes[:50])
        params = {'scode': codes}
        if start_date:
            params['sdate'] = start_date
        if end_date:
            params['edate'] = end_date
        return await self._request('/api/stock/p_stock2102', params)

    async def get_cash_flow(
        self,
        stock_codes: List[str],
        start_date: str = '',
        end_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取现金流量表

        Args:
            stock_codes: 股票代码列表（最多50只）
            start_date: 开始日期
            end_date: 结束日期
        """
        codes = ','.join(stock_codes[:50])
        params = {'scode': codes}
        if start_date:
            params['sdate'] = start_date
        if end_date:
            params['edate'] = end_date
        return await self._request('/api/stock/p_stock2103', params)

    async def get_financial_indicators(
        self,
        stock_codes: List[str],
        start_date: str = '',
        end_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取财务指标

        Args:
            stock_codes: 股票代码列表（最多50只）
            start_date: 开始日期
            end_date: 结束日期
        """
        codes = ','.join(stock_codes[:50])
        params = {'scode': codes}
        if start_date:
            params['sdate'] = start_date
        if end_date:
            params['edate'] = end_date
        return await self._request('/api/stock/p_stock2104', params)

    async def get_quick_indicators(
        self,
        stock_codes: List[str],
        report_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取个股指标快速版

        Args:
            stock_codes: 股票代码列表（最多300只）
            report_date: 报告期
        """
        codes = ','.join(stock_codes[:300])
        params = {'scode': codes}
        if report_date:
            params['rdate'] = report_date
        return await self._request('/api/stock/p_stock2387', params)

    # ==================== 交易数据接口 ====================

    async def get_daily_quote(
        self,
        stock_codes: List[str],
        start_date: str = '',
        end_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取日行情数据

        Args:
            stock_codes: 股票代码列表（最多50只）
            start_date: 开始日期
            end_date: 结束日期
        """
        codes = ','.join(stock_codes[:50])
        params = {'scode': codes}
        if start_date:
            params['sdate'] = start_date
        if end_date:
            params['edate'] = end_date
        return await self._request('/api/stock/p_stock1001', params)

    async def get_suspend_resume(
        self,
        stock_codes: List[str] = None,
        start_date: str = '',
        end_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取停复牌信息

        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
        """
        params = {}
        if stock_codes:
            params['scode'] = ','.join(stock_codes[:300])
        if start_date:
            params['sdate'] = start_date
        if end_date:
            params['edate'] = end_date
        return await self._request('/api/stock/p_stock1004', params)

    async def get_limit_stats(
        self,
        stock_codes: List[str] = None,
        start_date: str = '',
        end_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取涨跌停统计

        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
        """
        params = {}
        if stock_codes:
            params['scode'] = ','.join(stock_codes[:300])
        if start_date:
            params['sdate'] = start_date
        if end_date:
            params['edate'] = end_date
        return await self._request('/api/stock/p_stock1005', params)

    async def get_block_trade(
        self,
        stock_codes: List[str] = None,
        start_date: str = '',
        end_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取大宗交易数据

        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
        """
        params = {}
        if stock_codes:
            params['scode'] = ','.join(stock_codes[:300])
        if start_date:
            params['sdate'] = start_date
        if end_date:
            params['edate'] = end_date
        return await self._request('/api/stock/p_stock1006', params)

    async def get_margin_trading(
        self,
        stock_codes: List[str] = None,
        start_date: str = '',
        end_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取融资融券数据

        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
        """
        params = {}
        if stock_codes:
            params['scode'] = ','.join(stock_codes[:300])
        if start_date:
            params['sdate'] = start_date
        if end_date:
            params['edate'] = end_date
        return await self._request('/api/stock/p_stock1007', params)

    # ==================== 股东数据接口 ====================

    async def get_shareholder_count(
        self,
        stock_codes: List[str],
        report_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取股东户数

        Args:
            stock_codes: 股票代码列表
            report_date: 报告期
        """
        codes = ','.join(stock_codes[:300])
        params = {'scode': codes}
        if report_date:
            params['rdate'] = report_date
        return await self._request('/api/stock/p_stock3001', params)

    async def get_top_shareholders(
        self,
        stock_codes: List[str],
        report_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取十大股东

        Args:
            stock_codes: 股票代码列表
            report_date: 报告期
        """
        codes = ','.join(stock_codes[:300])
        params = {'scode': codes}
        if report_date:
            params['rdate'] = report_date
        return await self._request('/api/stock/p_stock3002', params)

    # ==================== 分红配股接口 ====================

    async def get_dividend(
        self,
        stock_codes: List[str] = None,
        start_date: str = '',
        end_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取分红数据

        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
        """
        params = {}
        if stock_codes:
            params['scode'] = ','.join(stock_codes[:300])
        if start_date:
            params['sdate'] = start_date
        if end_date:
            params['edate'] = end_date
        return await self._request('/api/stock/p_stock4001', params)


# 全局实例
_cninfo_client: Optional[CninfoApiClient] = None


def get_cninfo_api_client() -> CninfoApiClient:
    """获取巨潮API客户端实例"""
    global _cninfo_client
    if _cninfo_client is None:
        _cninfo_client = CninfoApiClient()
    return _cninfo_client


async def test_cninfo_api():
    """测试巨潮API"""
    client = get_cninfo_api_client()

    print("=" * 50)
    print("巨潮API配置状态:")
    print(json.dumps(CninfoConfig.get_all_config(), indent=2, ensure_ascii=False))
    print("=" * 50)

    if not CninfoConfig.is_configured():
        print("❌ 巨潮API未配置，请先配置 CNINFO_ACCESS_TOKEN")
        print("\n配置方式:")
        print("1. 在 .env 文件中添加: CNINFO_ACCESS_TOKEN=your_token")
        print("2. 或在 backend/config/cninfo_config.json 中配置")
        return

    # 测试获取股票信息
    print("\n测试获取股票信息 (600519 贵州茅台)...")
    result = await client.get_stock_info(['600519'])
    if result['success']:
        print(f"✅ 成功获取 {result['total']} 条记录")
        if result['data']:
            print(json.dumps(result['data'][0], indent=2, ensure_ascii=False))
    else:
        print(f"❌ 失败: {result.get('error')}")

    # 测试获取业绩预告
    print("\n测试获取业绩预告...")
    result = await client.get_performance_forecast(['600519'])
    if result['success']:
        print(f"✅ 成功获取 {result['total']} 条记录")
    else:
        print(f"❌ 失败: {result.get('error')}")

    await client.close()
    print("\n测试完成!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_cninfo_api())
