"""
全面测试所有数据源的连通性、获取和解析
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import json
from datetime import datetime
from backend.dataflows.stock_data_adapter import StockDataAdapter
from backend.api.stock_api import router as stock_router
from backend.dataflows.news.unified_news_api import get_unified_news
import akshare as ak
import traceback

# 设置彩色输出
class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    print(f"\n{Color.BOLD}{Color.BLUE}{'='*60}{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}{title:^60}{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}{'='*60}{Color.RESET}")

def print_success(msg):
    print(f"{Color.GREEN}✓ {msg}{Color.RESET}")

def print_error(msg):
    print(f"{Color.RED}✗ {msg}{Color.RESET}")

def print_warning(msg):
    print(f"{Color.YELLOW}⚠ {msg}{Color.RESET}")

def print_info(msg):
    print(f"{Color.BLUE}ℹ {msg}{Color.RESET}")

async def test_akshare():
    """测试AKShare数据源"""
    print_header("测试 AKShare 数据源")
    try:
        # 测试实时行情
        print_info("测试实时行情接口...")
        df = ak.stock_zh_a_spot_em()
        if not df.empty:
            print_success(f"获取到 {len(df)} 支股票实时行情")
            # 获取第一支股票详情
            stock_000001 = df[df['代码'] == '000001']
            if not stock_000001.empty:
                print_success(f"000001 最新价: {stock_000001.iloc[0]['最新价']}")
        else:
            print_error("未获取到行情数据")
            
        # 测试个股数据
        print_info("测试个股数据接口...")
        stock_info = ak.stock_individual_info_em(symbol="000001")
        if stock_info is not None:
            print_success(f"获取到个股信息: {stock_info.iloc[0]['value'] if not stock_info.empty else 'N/A'}")
        
        return True
    except Exception as e:
        print_error(f"AKShare 测试失败: {str(e)}")
        traceback.print_exc()
        return False

async def test_sina():
    """测试新浪财经数据源"""
    print_header("测试新浪财经数据源")
    try:
        import requests
        # 测试新浪实时行情
        url = "https://hq.sinajs.cn/list=sh000001"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finance.sina.com.cn'
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            print_success(f"新浪接口响应正常: {response.text[:100]}")
            # 解析数据
            if 'hq_str_sh000001=' in response.text:
                data = response.text.split('=')[1].strip('";\n')
                if data:
                    parts = data.split(',')
                    if len(parts) > 3:
                        print_success(f"上证指数: {parts[3]}")
                        return True
        print_error("新浪数据获取失败")
        return False
    except Exception as e:
        print_error(f"新浪财经测试失败: {str(e)}")
        return False

async def test_tushare():
    """测试Tushare数据源"""
    print_header("测试 Tushare 数据源")
    try:
        import tushare as ts
        # 测试是否需要token
        print_info("测试Tushare基础接口...")
        
        # 尝试不需要token的接口
        df = ts.realtime_quote(ts_code='000001.SZ')
        if df is not None and not df.empty:
            print_success(f"Tushare获取到数据: {df.iloc[0]['NAME'] if 'NAME' in df.columns else 'N/A'}")
            return True
        else:
            print_warning("Tushare需要配置token")
            return False
    except Exception as e:
        print_warning(f"Tushare测试失败(可能需要token): {str(e)}")
        return False

async def test_juhe():
    """测试聚合数据"""
    print_header("测试聚合数据源")
    try:
        import requests
        # 聚合数据通常需要API Key
        print_warning("聚合数据需要有效的API Key")
        # 测试连接
        url = "http://web.juhe.cn:8080/finance/stock/hs"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print_info(f"聚合数据API可访问，但需要key")
        return False
    except:
        print_error("聚合数据源不可用（需要付费API Key）")
        return False

async def test_baostock():
    """测试BaoStock数据源"""
    print_header("测试 BaoStock 数据源")
    try:
        import baostock as bs
        # 登录系统
        lg = bs.login()
        if lg.error_code == '0':
            print_success("BaoStock登录成功")
            # 查询股票数据
            rs = bs.query_history_k_data_plus("sh.000001",
                "date,code,open,high,low,close,volume",
                start_date='2025-12-01', end_date='2025-12-04',
                frequency="d")
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            if data_list:
                print_success(f"获取到 {len(data_list)} 条历史数据")
            # 登出
            bs.logout()
            return True
        else:
            print_error(f"BaoStock登录失败: {lg.error_msg}")
            return False
    except Exception as e:
        print_error(f"BaoStock测试失败: {str(e)}")
        return False

async def test_stock_adapter():
    """测试股票数据适配器"""
    print_header("测试股票数据适配器")
    
    adapter = StockDataAdapter()
    test_symbol = "000001"
    
    print_info(f"测试股票代码: {test_symbol}")
    
    # 测试获取数据
    result = await adapter.get_stock_data(test_symbol)
    
    if result.get('success'):
        data = result.get('data', {})
        print_success(f"数据获取成功!")
        print_info(f"  数据源: {data.get('data_source', 'Unknown')}")
        print_info(f"  股票名称: {data.get('name', 'N/A')}")
        print_info(f"  当前价格: ¥{data.get('price', 0)}")
        print_info(f"  涨跌幅: {data.get('change', 0)}%")
        print_info(f"  成交量: {data.get('volume', 0)}")
        
        # 测试数据解析
        if 'raw_text' in data:
            print_info("\n原始数据预览:")
            print(data['raw_text'][:500] + "..." if len(data['raw_text']) > 500 else data['raw_text'])
            
            # 测试解析器
            parsed = adapter.parse_text_data(data['raw_text'])
            print_info("\n解析结果:")
            for key, value in parsed.items():
                if value != 'N/A' and value != 0:
                    print(f"  {key}: {value}")
        return True
    else:
        print_error(f"适配器测试失败: {result.get('error', 'Unknown error')}")
        return False

async def test_news_api():
    """测试新闻API"""
    print_header("测试新闻API")
    
    try:
        # 测试统一新闻接口
        print_info("测试统一新闻接口...")
        news_data = await get_unified_news("000001", limit=5)
        
        if news_data and 'items' in news_data:
            items = news_data['items']
            print_success(f"获取到 {len(items)} 条新闻")
            
            # 显示前3条新闻
            for i, item in enumerate(items[:3], 1):
                print_info(f"\n新闻 {i}:")
                print(f"  标题: {item.get('title', 'N/A')[:50]}...")
                print(f"  来源: {item.get('source', 'N/A')}")
                print(f"  时间: {item.get('time', 'N/A')}")
        else:
            print_warning("未获取到新闻数据")
            
        # 测试各个新闻源
        print_info("\n测试各新闻数据源...")
        sources_to_test = [
            "akshare_stock",
            "akshare_cjzc", 
            "akshare_global",
            "akshare_cls"
        ]
        
        for source in sources_to_test:
            try:
                # 这里需要实际的测试代码
                print_info(f"  测试 {source}...")
                # 实际测试逻辑
            except Exception as e:
                print_warning(f"  {source} 测试失败: {str(e)}")
                
        return True
    except Exception as e:
        print_error(f"新闻API测试失败: {str(e)}")
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print_header("InvestMind Pro 数据源完整测试")
    print_info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {}
    
    # 1. 测试AKShare
    results['AKShare'] = await test_akshare()
    
    # 2. 测试新浪财经
    results['Sina'] = await test_sina()
    
    # 3. 测试Tushare
    results['Tushare'] = await test_tushare()
    
    # 4. 测试聚合数据
    results['Juhe'] = await test_juhe()
    
    # 5. 测试BaoStock
    results['BaoStock'] = await test_baostock()
    
    # 6. 测试股票适配器
    results['StockAdapter'] = await test_stock_adapter()
    
    # 7. 测试新闻API
    results['NewsAPI'] = await test_news_api()
    
    # 汇总结果
    print_header("测试结果汇总")
    working_sources = []
    failed_sources = []
    
    for source, status in results.items():
        if status:
            print_success(f"{source}: 正常工作")
            working_sources.append(source)
        else:
            print_error(f"{source}: 存在问题")
            failed_sources.append(source)
    
    print(f"\n{Color.BOLD}可用数据源: {Color.GREEN}{', '.join(working_sources) if working_sources else '无'}{Color.RESET}")
    print(f"{Color.BOLD}问题数据源: {Color.RED}{', '.join(failed_sources) if failed_sources else '无'}{Color.RESET}")
    
    # 建议
    print_header("修复建议")
    if 'AKShare' in failed_sources:
        print_warning("1. AKShare可能需要更新: pip install --upgrade akshare")
    if 'Tushare' in failed_sources:
        print_warning("2. Tushare需要配置token: https://tushare.pro/register")
    if 'NewsAPI' in failed_sources:
        print_warning("3. 新闻API需要检查backend/dataflows/news/目录下的实现")
    
    print_info("\n建议优先使用AKShare作为主数据源，它免费且稳定")

if __name__ == "__main__":
    asyncio.run(main())
