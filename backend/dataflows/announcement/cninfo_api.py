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

免费API列表 (2025-12-30 测试验证):
=================================
股票-基本信息 (产品45):
  - p_stock2100: 公司基本信息 ✓
  - p_stock2101: 股票基本信息 ✓ (注意: 这是股票基本信息，不是利润表)
  - p_stock0004: 股票所属板块 ✓
  - p_stock2102: 公司管理人员任职情况 ✓ (注意: 这是管理人员，不是利润表)
  - p_stock2117: 公司上市状态变动情况 ✓
  - p_stock2107: 公司员工情况表 ✓

股票-公司公告 (产品47):
  - p_info3005: 公告分类信息 ✓
  - p_info3015: 公告基本信息 ✓

公共数据:
  - p_public0005: 公共编码数据 ✓
  - p_public0006: 人民币汇率中间价 ✓
  - p_public0007: 机构信息数据 ✓

需要VIP权限的API:
  - p_stock2108: 机构基本信息变更情况 (416 VIP接口)
  - p_stock2109: 证券简称变更情况 (416 VIP接口)
  - p_stock2110: 上市公司行业归属变动 (416 VIP接口)
  - p_company3201: 股票背景资料 (415 需购买包时长)

返回502错误的API (可能需要特定参数或权限):
  - p_public0001: 交易日历数据
  - p_public0002: 行业分类数据
  - p_public0003: 地区分类数据
  - p_public0004: 板块成份股数据

频率限制: 无明显限制，建议间隔0.3秒
响应时间: 约0.07-0.16秒/请求
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

    async def get_public_codes(
        self,
        subtype: str = ''
    ) -> Dict[str, Any]:
        """
        获取公共编码数据 [免费可用]

        Args:
            subtype: 子类型编码
        """
        params = {}
        if subtype:
            params['subtype'] = subtype
        return await self._request('/api/public/p_public0005', params)

    async def get_exchange_rate(self) -> Dict[str, Any]:
        """
        获取人民币汇率中间价 [免费可用]
        """
        return await self._request('/api/public/p_public0006', {})

    async def get_institution_info(self) -> Dict[str, Any]:
        """
        获取机构信息数据 [免费可用]
        """
        return await self._request('/api/public/p_public0007', {})

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

    async def get_announcement_info(
        self,
        stock_code: str = '',
        start_date: str = '',
        end_date: str = '',
        market: str = '',
        max_id: int = None,
        text_id: str = '',
        page: int = None,
        page_size: int = None
    ) -> Dict[str, Any]:
        """
        获取公告基本信息 [免费可用]

        Args:
            stock_code: 股票代码（单个）
            start_date: 开始查询时间 YYYY-MM-DD
            end_date: 结束查询时间 YYYY-MM-DD
            market: 市场 (上交所:012001, 科创板:012029, 深交所主板:012002, 深交所创业板:012015)
            max_id: 增量起始ID，用于增量提取数据
            text_id: 正文ID
            page: 页码
            page_size: 每页大小
        """
        params = {}
        if stock_code:
            params['scode'] = stock_code
        if start_date:
            params['sdate'] = start_date
        if end_date:
            params['edate'] = end_date
        if market:
            params['market'] = market
        if max_id is not None:
            params['maxid'] = max_id
        if text_id:
            params['textid'] = text_id
        if page is not None:
            params['page'] = page
        if page_size is not None:
            params['pagesize'] = page_size
        return await self._request('/api/info/p_info3015', params)

    # ==================== 股票基本信息接口 (免费可用) ====================

    async def get_company_basic_info(self, stock_codes: List[str]) -> Dict[str, Any]:
        """
        获取公司基本信息 [免费可用] - p_stock2100

        包含：机构名称、证券简称、法人代表、注册地址、办公地址、主营业务、
        经营范围、中介机构、董秘、证代等机构信息，以及证券类别、交易市场、上市日期等

        Args:
            stock_codes: 股票代码列表（最多50只）
        """
        codes = ','.join(stock_codes[:50])
        return await self._request('/api/stock/p_stock2100', {'scode': codes})

    async def get_stock_basic_info(self, stock_codes: List[str] = None) -> Dict[str, Any]:
        """
        获取股票基本信息 [免费可用] - p_stock2101

        包含：机构名称、证券代码、证券简称、拼音简称、证券类别、交易市场、
        上市日期、初始上市数量、代码属性、上市状态、面值、ISIN等

        Args:
            stock_codes: 股票代码列表（最多50只），为空则获取全部
        """
        params = {}
        if stock_codes:
            codes = ','.join(stock_codes[:50])
            params['scode'] = codes
        return await self._request('/api/stock/p_stock2101', params)

    async def get_stock_sector(
        self,
        stock_codes: List[str],
        type_code: str = ''
    ) -> Dict[str, Any]:
        """
        获取股票所属板块 [免费可用] - p_stock0004

        Args:
            stock_codes: 股票代码列表（最多300只）
            type_code: 类别代码 (137001市场分类, 137002中上协行业, 137004申万行业,
                       137005新财富行业, 137006地区省市, 137007指数成份股, 137008概念板块)
        """
        codes = ','.join(stock_codes[:300])
        params = {'scode': codes}
        if type_code:
            params['typecode'] = type_code
        return await self._request('/api/stock/p_stock0004', params)

    async def get_management_personnel(
        self,
        stock_codes: List[str],
        state: int = None
    ) -> Dict[str, Any]:
        """
        获取公司管理人员任职情况 [免费可用] - p_stock2102

        Args:
            stock_codes: 股票代码列表（最多50只）
            state: 状态，为空取所有数据，输入1则取最新一任期管理人员
        """
        codes = ','.join(stock_codes[:50])
        params = {'scode': codes}
        if state is not None:
            params['state'] = state
        return await self._request('/api/stock/p_stock2102', params)

    async def get_listing_status_changes(
        self,
        stock_code: str = '',
        sign: str = '',
        change_type: str = ''
    ) -> Dict[str, Any]:
        """
        获取公司上市状态变动情况 [免费可用] - p_stock2117

        Args:
            stock_code: 股票代码
            sign: 上市状态编码 (通过p_public0006接口subtype=013获取)
            change_type: 变更类型编码 (通过p_public0006接口subtype=031获取)
        """
        params = {}
        if stock_code:
            params['scode'] = stock_code
        if sign:
            params['sign'] = sign
        if change_type:
            params['type'] = change_type
        return await self._request('/api/stock/p_stock2117', params)

    async def get_employee_info(
        self,
        stock_codes: List[str],
        start_date: str = '',
        end_date: str = '',
        state: str = ''
    ) -> Dict[str, Any]:
        """
        获取公司员工情况表 [免费可用] - p_stock2107

        Args:
            stock_codes: 股票代码列表（最多50只）
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            state: 最新标识，当state=1取最新标识的所有数据
        """
        codes = ','.join(stock_codes[:50])
        params = {'scode': codes}
        if start_date:
            params['sdate'] = start_date
        if end_date:
            params['edate'] = end_date
        if state:
            params['state'] = state
        return await self._request('/api/stock/p_stock2107', params)

    # ==================== 以下接口需要VIP权限或付费 ====================
    # 注意: 以下接口在免费账户下会返回 416 (VIP接口) 或 502 错误

    async def get_stock_background(
        self,
        stock_codes: List[str] = None
    ) -> Dict[str, Any]:
        """
        获取股票背景资料 [需要付费] - p_company3201

        Args:
            stock_codes: 股票代码列表
        """
        params = {}
        if stock_codes:
            codes = ','.join(stock_codes[:50])
            params['scode'] = codes
        return await self._request('/api/stock/p_company3201', params)

    async def get_institution_changes(
        self,
        stock_code: str,
        start_date: str = '',
        end_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取机构基本信息变更情况 [需要VIP] - p_stock2108

        Args:
            stock_code: 股票代码
            start_date: 开始公布日期
            end_date: 结束公布日期
        """
        params = {'scode': stock_code}
        if start_date:
            params['sdate'] = start_date
        if end_date:
            params['edate'] = end_date
        return await self._request('/api/stock/p_stock2108', params)

    async def get_name_changes(
        self,
        stock_code: str,
        start_date: str = '',
        end_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取证券简称变更情况 [需要VIP] - p_stock2109

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        """
        params = {'scode': stock_code}
        if start_date:
            params['sdate'] = start_date
        if end_date:
            params['edate'] = end_date
        return await self._request('/api/stock/p_stock2109', params)

    async def get_industry_changes(
        self,
        stock_code: str,
        start_date: str = '',
        end_date: str = ''
    ) -> Dict[str, Any]:
        """
        获取上市公司行业归属变动情况 [需要VIP] - p_stock2110

        Args:
            stock_code: 股票代码
            start_date: 开始变动日期
            end_date: 结束变动日期
        """
        params = {'scode': stock_code}
        if start_date:
            params['sdate'] = start_date
        if end_date:
            params['edate'] = end_date
        return await self._request('/api/stock/p_stock2110', params)

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

    # ==================== 新闻资讯接口 ====================

    async def get_news_list(
        self,
        stock_code: str = '',
        start_date: str = '',
        end_date: str = '',
        news_type: str = '',
        limit: int = None
    ) -> Dict[str, Any]:
        """
        获取新闻数据查询 - p_info3030

        Args:
            stock_code: 证券代码
            start_date: 开始查询日期 YYYY-MM-DD
            end_date: 结束查询日期 YYYY-MM-DD
            news_type: 新闻分类编码 (2701-证券, 2702-公司, 2703-快讯, 2704-产经)
            limit: 返回条数限制

        Returns:
            新闻列表，包含：发布时间、新闻ID、证券代码、数据源、关键字、新闻分类、新闻标题、发布作者等
        """
        params = {}
        if stock_code:
            params['scode'] = stock_code
        if start_date:
            params['sdate'] = start_date
        if end_date:
            params['edate'] = end_date
        if news_type:
            params['stype'] = news_type
        if limit:
            params['@limit'] = limit
        return await self._request('/api/info/p_info3030', params)

    async def get_news_content(self, news_id: int) -> Dict[str, Any]:
        """
        获取新闻正文查询 - p_info3031

        Args:
            news_id: 新闻ID (从p_info3030获取的TEXTID)

        Returns:
            新闻正文内容
        """
        params = {'newid': news_id}
        return await self._request('/api/info/p_info3031', params)

    async def get_company_news_list(
        self,
        company_id: int = None,
        company_name: str = '',
        keyword: str = '',
        start_date: str = '',
        end_date: str = '',
        page: int = 1,
        rows: int = 100
    ) -> Dict[str, Any]:
        """
        获取公司新闻列表 - p_comnewslist (bigdata接口)

        Args:
            company_id: 公司ID
            company_name: 公司名称
            keyword: 查询关键词
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            page: 当前页码
            rows: 每页条数

        Returns:
            新闻列表，包含：新闻id、标题、正负面情绪、发布时间、关键词、来源等
        """
        params = {'page': page, 'rows': rows}
        if company_id:
            params['cid'] = company_id
        if company_name:
            params['cname'] = company_name
        if keyword:
            params['key'] = keyword
        if start_date:
            params['sdate'] = start_date
        if end_date:
            params['edate'] = end_date
        return await self._request('/api/bigdata/p_comnewslist', params)

    async def get_company_news_detail(self, news_id: str) -> Dict[str, Any]:
        """
        获取新闻详情 - p_comnewsinfo (bigdata接口)

        Args:
            news_id: 新闻ID

        Returns:
            新闻详情，包含：标题、作者、正负面情绪、摘要、发布时间、关键词、来源、原文URL、正文、相关人物、相关企业
        """
        params = {'id': news_id}
        return await self._request('/api/bigdata/p_comnewsinfo', params)

    async def get_research_report_summary(
        self,
        object_id: int = 0,
        row_count: int = 1000
    ) -> Dict[str, Any]:
        """
        获取个股研报摘要 - p_info3097_inc

        Args:
            object_id: 起始记录ID，用于增量获取。第一次调用传入0，后续传入上次返回的最大OBJECTID
            row_count: 返回记录条数，最大2000，默认1000

        Returns:
            研报摘要列表，包含：证券代码、证券简称、资讯发布日期、资讯标题、资讯内容、
            研报发布机构、研报发布日期、资讯分类名称、证券类别名称、证券市场名称等
        """
        params = {
            'objectid': object_id,
            'rowcount': min(row_count, 2000)
        }
        return await self._request('/api/load/p_info3097_inc', params)


# 全局实例
_cninfo_client: Optional[CninfoApiClient] = None


def get_cninfo_api_client() -> CninfoApiClient:
    """获取巨潮API客户端实例"""
    global _cninfo_client
    if _cninfo_client is None:
        _cninfo_client = CninfoApiClient()
    return _cninfo_client


async def test_cninfo_api():
    """测试巨潮API - 免费接口"""
    client = get_cninfo_api_client()

    print("=" * 60)
    print("巨潮资讯网API测试 - 免费接口")
    print("=" * 60)
    print("配置状态:")
    print(json.dumps(CninfoConfig.get_all_config(), indent=2, ensure_ascii=False))
    print("=" * 60)

    if not CninfoConfig.is_configured():
        print("巨潮API未配置，请先配置 CNINFO_ACCESS_KEY 和 CNINFO_ACCESS_SECRET")
        print("\n配置方式:")
        print("1. 在 .env 文件中添加:")
        print("   CNINFO_ACCESS_KEY=your_access_key")
        print("   CNINFO_ACCESS_SECRET=your_access_secret")
        print("2. 或在 backend/config/cninfo_config.json 中配置")
        return

    test_stock = '000001'  # 平安银行
    results = []

    # 测试免费API
    print("\n测试免费API接口...")
    print("-" * 60)

    # 1. 公司基本信息
    print(f"\n1. 公司基本信息 (p_stock2100) - {test_stock}")
    result = await client.get_company_basic_info([test_stock])
    if result['success']:
        print(f"   OK - {result['total']} 条记录")
        if result['data']:
            data = result['data'][0]
            print(f"   公司: {data.get('ORGNAME', 'N/A')}")
            print(f"   简称: {data.get('SECNAME', 'N/A')}")
        results.append(('p_stock2100', True))
    else:
        print(f"   ERROR - {result.get('error')}")
        results.append(('p_stock2100', False))

    # 2. 股票基本信息
    print(f"\n2. 股票基本信息 (p_stock2101) - {test_stock}")
    result = await client.get_stock_basic_info([test_stock])
    if result['success']:
        print(f"   OK - {result['total']} 条记录")
        if result['data']:
            data = result['data'][0]
            print(f"   上市日期: {data.get('F006D', 'N/A')}")
            print(f"   交易市场: {data.get('F005V', 'N/A')}")
        results.append(('p_stock2101', True))
    else:
        print(f"   ERROR - {result.get('error')}")
        results.append(('p_stock2101', False))

    # 3. 股票所属板块
    print(f"\n3. 股票所属板块 (p_stock0004) - {test_stock}")
    result = await client.get_stock_sector([test_stock])
    if result['success']:
        print(f"   OK - {result['total']} 条记录")
        results.append(('p_stock0004', True))
    else:
        print(f"   ERROR - {result.get('error')}")
        results.append(('p_stock0004', False))

    # 4. 管理人员任职情况
    print(f"\n4. 管理人员任职情况 (p_stock2102) - {test_stock}")
    result = await client.get_management_personnel([test_stock], state=1)
    if result['success']:
        print(f"   OK - {result['total']} 条记录")
        results.append(('p_stock2102', True))
    else:
        print(f"   ERROR - {result.get('error')}")
        results.append(('p_stock2102', False))

    # 5. 上市状态变动
    print("\n5. 上市状态变动 (p_stock2117)")
    result = await client.get_listing_status_changes()
    if result['success']:
        print(f"   OK - {result['total']} 条记录")
        results.append(('p_stock2117', True))
    else:
        print(f"   ERROR - {result.get('error')}")
        results.append(('p_stock2117', False))

    # 6. 员工情况
    print(f"\n6. 员工情况 (p_stock2107) - {test_stock}")
    result = await client.get_employee_info([test_stock], state='1')
    if result['success']:
        print(f"   OK - {result['total']} 条记录")
        if result['data']:
            data = result['data'][0]
            print(f"   员工总数: {data.get('STAFFNUM', 'N/A')}")
        results.append(('p_stock2107', True))
    else:
        print(f"   ERROR - {result.get('error')}")
        results.append(('p_stock2107', False))

    # 7. 公告分类信息
    print("\n7. 公告分类信息 (p_info3005)")
    result = await client.get_announcement_categories()
    if result['success']:
        print(f"   OK - {result['total']} 条记录")
        results.append(('p_info3005', True))
    else:
        print(f"   ERROR - {result.get('error')}")
        results.append(('p_info3005', False))

    # 8. 公告基本信息
    print(f"\n8. 公告基本信息 (p_info3015) - {test_stock}")
    result = await client.get_announcement_info(stock_code=test_stock)
    if result['success']:
        print(f"   OK - {result['total']} 条记录")
        if result['data']:
            data = result['data'][0]
            print(f"   最新公告: {data.get('F002V', 'N/A')[:50]}...")
        results.append(('p_info3015', True))
    else:
        print(f"   ERROR - {result.get('error')}")
        results.append(('p_info3015', False))

    # 9. 公共编码数据
    print("\n9. 公共编码数据 (p_public0005)")
    result = await client.get_public_codes(subtype='002')
    if result['success']:
        print(f"   OK - {result['total']} 条记录")
        results.append(('p_public0005', True))
    else:
        print(f"   ERROR - {result.get('error')}")
        results.append(('p_public0005', False))

    # 10. 人民币汇率
    print("\n10. 人民币汇率中间价 (p_public0006)")
    result = await client.get_exchange_rate()
    if result['success']:
        print(f"   OK - {result['total']} 条记录")
        results.append(('p_public0006', True))
    else:
        print(f"   ERROR - {result.get('error')}")
        results.append(('p_public0006', False))

    # 11. 机构信息
    print("\n11. 机构信息数据 (p_public0007)")
    result = await client.get_institution_info()
    if result['success']:
        print(f"   OK - {result['total']} 条记录")
        results.append(('p_public0007', True))
    else:
        print(f"   ERROR - {result.get('error')}")
        results.append(('p_public0007', False))

    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    ok_count = sum(1 for _, ok in results if ok)
    print(f"成功: {ok_count}/{len(results)}")
    print("\n可用的免费API:")
    for name, ok in results:
        status = "OK" if ok else "ERROR"
        print(f"  - {name}: {status}")

    await client.close()
    print("\n测试完成!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_cninfo_api())
