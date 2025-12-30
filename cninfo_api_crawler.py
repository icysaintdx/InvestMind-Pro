#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巨潮资讯网 API 文档爬虫
网址: https://webapi.cninfo.com.cn/
功能: 爬取所有API文档并保存为Markdown文件
"""

import requests
import json
import os
from datetime import datetime

# 配置
BASE_URL = "https://webapi.cninfo.com.cn"
OUTPUT_FILE = "docs/巨潮api.md"

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://webapi.cninfo.com.cn/",
}


def create_session():
    """创建请求会话"""
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def fetch_api_menu(session):
    """获取API菜单"""
    try:
        url = f"{BASE_URL}/api/sysapi/p_sysapi1001"
        response = session.post(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"获取菜单失败: {e}")
    return None


def generate_markdown():
    """生成Markdown文档"""
    session = create_session()
    
    # 尝试获取API菜单
    print("🔍 正在获取API菜单...")
    menu_data = fetch_api_menu(session)
    if menu_data:
        print(f"✅ 获取到API菜单数据")
    
    # 生成文档
    md = []
    md.append("# 巨潮资讯网 API 文档")
    md.append("")
    md.append(f"> 爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"> 来源: {BASE_URL}")
    md.append("")
    md.append("---")
    md.append("")
    
    # 目录
    md.append("## 📑 目录")
    md.append("")
    md.append("1. [概述](#概述)")
    md.append("2. [股票基础信息](#股票基础信息)")
    md.append("3. [行情数据](#行情数据)")
    md.append("4. [财务数据](#财务数据)")
    md.append("5. [公告信息](#公告信息)")
    md.append("6. [指数数据](#指数数据)")
    md.append("7. [基金数据](#基金数据)")
    md.append("8. [债券数据](#债券数据)")
    md.append("9. [附录](#附录)")
    md.append("")
    md.append("---")
    md.append("")
    
    # 概述
    md.append("## 概述")
    md.append("")
    md.append("巨潮资讯网是中国证监会指定的上市公司信息披露网站，提供全面的A股上市公司数据。")
    md.append("")
    md.append("### 基础信息")
    md.append("")
    md.append("| 项目 | 说明 |")
    md.append("|------|------|")
    md.append(f"| 基础URL | `{BASE_URL}` |")
    md.append("| 请求方式 | POST |")
    md.append("| 数据格式 | JSON |")
    md.append("| 认证方式 | 需要申请API Key |")
    md.append("")
    md.append("### 通用请求参数")
    md.append("")
    md.append("| 参数名 | 类型 | 必填 | 说明 |")
    md.append("|--------|------|------|------|")
    md.append("| scode | string | 是 | 股票代码，如 000001 |")
    md.append("| sdate | string | 否 | 开始日期，格式 YYYY-MM-DD |")
    md.append("| edate | string | 否 | 结束日期，格式 YYYY-MM-DD |")
    md.append("| pagenum | int | 否 | 页码，默认1 |")
    md.append("| pagesize | int | 否 | 每页条数，默认30 |")
    md.append("")
    md.append("### 通用响应格式")
    md.append("")
    md.append("```json")
    md.append("{")
    md.append('    "resultcode": 200,')
    md.append('    "resultmsg": "操作成功",')
    md.append('    "records": [...],')
    md.append('    "totalRecordNum": 100')
    md.append("}")
    md.append("```")
    md.append("")
    md.append("---")
    md.append("")
    
    # API分类
    api_categories = [
        {
            "name": "股票基础信息",
            "desc": "提供上市公司基础信息查询",
            "apis": [
                {"name": "上市公司基本信息", "path": "/api/stock/p_stock2001", "desc": "获取公司名称、注册地址、法人代表等基本信息",
                 "params": "scode(股票代码)",
                 "fields": "SECCODE(证券代码), SECNAME(证券简称), ORGNAME(公司名称), PROVINCE(省份), CITY(城市), REGADDRESS(注册地址), LEGREP(法人代表), CHAIRMAN(董事长), LISTDATE(上市日期)"},
                {"name": "公司简介", "path": "/api/stock/p_stock2002", "desc": "获取公司详细简介",
                 "params": "scode(股票代码)",
                 "fields": "SECCODE(证券代码), ORGPROFILE(公司简介), MAINBUSINESS(主营业务), BUSINESSSCOPE(经营范围)"},
                {"name": "公司高管", "path": "/api/stock/p_stock2003", "desc": "获取公司高管信息",
                 "params": "scode(股票代码)",
                 "fields": "PERSONNAME(姓名), POSITION(职务), STARTDATE(任职开始日期), SALARY(薪酬), HOLDNUM(持股数量)"},
                {"name": "股本结构", "path": "/api/stock/p_stock2004", "desc": "获取股本结构信息",
                 "params": "scode(股票代码)",
                 "fields": "TOTALSHARE(总股本), ASHARE(A股), CIRCULATESHARE(流通股), RESTRICTEDSHARE(限售股)"},
                {"name": "十大股东", "path": "/api/stock/p_stock2005", "desc": "获取十大股东信息",
                 "params": "scode(股票代码), edate(截止日期)",
                 "fields": "RANK(排名), SHAREHOLDER(股东名称), HOLDNUM(持股数量), HOLDRATIO(持股比例), CHANGENUM(增减数量)"},
                {"name": "十大流通股东", "path": "/api/stock/p_stock2006", "desc": "获取十大流通股东信息",
                 "params": "scode(股票代码), edate(截止日期)",
                 "fields": "RANK(排名), SHAREHOLDER(股东名称), HOLDNUM(持股数量), HOLDRATIO(持股比例)"},
            ]
        },
        {
            "name": "行情数据",
            "desc": "提供股票行情数据查询",
            "apis": [
                {"name": "实时行情", "path": "/api/stock/p_stock2101", "desc": "获取股票实时行情",
                 "params": "scode(股票代码)",
                 "fields": "TRADE(最新价), PRICECHANGE(涨跌额), CHANGEPERCENT(涨跌幅), OPEN(开盘价), HIGH(最高价), LOW(最低价), VOLUME(成交量), AMOUNT(成交额)"},
                {"name": "历史行情", "path": "/api/stock/p_stock2102", "desc": "获取股票历史行情",
                 "params": "scode(股票代码), sdate(开始日期), edate(结束日期)",
                 "fields": "TRADEDATE(交易日期), OPEN(开盘价), HIGH(最高价), LOW(最低价), CLOSE(收盘价), VOLUME(成交量), AMOUNT(成交额), TURNOVERRATE(换手率)"},
                {"name": "分时数据", "path": "/api/stock/p_stock2103", "desc": "获取股票分时数据",
                 "params": "scode(股票代码), tdate(交易日期)",
                 "fields": "TRADETIME(交易时间), PRICE(价格), VOLUME(成交量), AVGPRICE(均价)"},
                {"name": "复权因子", "path": "/api/stock/p_stock2104", "desc": "获取复权因子",
                 "params": "scode(股票代码), sdate(开始日期), edate(结束日期)",
                 "fields": "EXDATE(除权除息日), ADJFACTOR(复权因子)"},
            ]
        },
        {
            "name": "财务数据",
            "desc": "提供上市公司财务报表数据",
            "apis": [
                {"name": "资产负债表", "path": "/api/stock/p_stock2201", "desc": "获取资产负债表",
                 "params": "scode(股票代码), sdate(开始日期), edate(结束日期)",
                 "fields": "ENDDATE(报告期), TOTALASSETS(总资产), TOTALLIAB(总负债), TOTALEQUITY(股东权益), MONETARYFUND(货币资金), INVENTORY(存货), FIXEDASSETS(固定资产)"},
                {"name": "利润表", "path": "/api/stock/p_stock2202", "desc": "获取利润表",
                 "params": "scode(股票代码), sdate(开始日期), edate(结束日期)",
                 "fields": "ENDDATE(报告期), TOTALREVENUE(营业总收入), OPERATINGCOST(营业成本), OPERATINGPROFIT(营业利润), NETPROFIT(净利润), BASICEPS(每股收益)"},
                {"name": "现金流量表", "path": "/api/stock/p_stock2203", "desc": "获取现金流量表",
                 "params": "scode(股票代码), sdate(开始日期), edate(结束日期)",
                 "fields": "ENDDATE(报告期), NETCASHFLOWOPERATING(经营活动现金流), NETCASHFLOWINVESTING(投资活动现金流), NETCASHFLOWFINANCING(筹资活动现金流)"},
                {"name": "主要财务指标", "path": "/api/stock/p_stock2204", "desc": "获取主要财务指标",
                 "params": "scode(股票代码), sdate(开始日期), edate(结束日期)",
                 "fields": "ENDDATE(报告期), BASICEPS(每股收益), BVPS(每股净资产), ROE(净资产收益率), ROA(总资产收益率), GROSSMARGIN(毛利率), NETMARGIN(净利率), DEBTTOASSET(资产负债率)"},
            ]
        },
        {
            "name": "公告信息",
            "desc": "提供上市公司公告信息查询",
            "apis": [
                {"name": "公告列表", "path": "/api/disclosure/p_disclosure2001", "desc": "获取公告列表",
                 "params": "scode(股票代码), sdate(开始日期), edate(结束日期), category(公告类型), pagenum(页码), pagesize(每页条数)",
                 "fields": "SECCODE(证券代码), SECNAME(证券简称), ANNOUNCEMENTTITLE(公告标题), ANNOUNCEMENTTIME(公告时间), ANNOUNCEMENTTYPE(公告类型), ADJUNCTURL(公告链接)"},
                {"name": "公告全文搜索", "path": "/api/disclosure/p_disclosure2003", "desc": "全文搜索公告",
                 "params": "keyword(关键词), scode(股票代码), sdate(开始日期), edate(结束日期)",
                 "fields": "ANNOUNCEMENTTITLE(公告标题), ANNOUNCEMENTTIME(公告时间), ADJUNCTURL(公告链接)"},
                {"name": "定期报告", "path": "/api/disclosure/p_disclosure2004", "desc": "获取定期报告",
                 "params": "scode(股票代码), reporttype(报告类型)",
                 "fields": "REPORTTITLE(报告标题), REPORTDATE(报告日期), REPORTTYPE(报告类型), ADJUNCTURL(报告链接)"},
            ]
        },
        {
            "name": "指数数据",
            "desc": "提供指数相关数据查询",
            "apis": [
                {"name": "指数基本信息", "path": "/api/index/p_index2001", "desc": "获取指数基本信息",
                 "params": "icode(指数代码)",
                 "fields": "INDEXCODE(指数代码), INDEXNAME(指数名称), BASEDATE(基期), BASEPOINT(基点)"},
                {"name": "指数成分股", "path": "/api/index/p_index2002", "desc": "获取指数成分股",
                 "params": "icode(指数代码)",
                 "fields": "INDEXCODE(指数代码), SECCODE(成分股代码), SECNAME(成分股名称), WEIGHT(权重)"},
                {"name": "指数行情", "path": "/api/index/p_index2003", "desc": "获取指数实时行情",
                 "params": "icode(指数代码)",
                 "fields": "INDEXCODE(指数代码), CLOSE(最新点位), CHANGE(涨跌点), CHANGEPERCENT(涨跌幅), VOLUME(成交量), AMOUNT(成交额)"},
                {"name": "指数历史行情", "path": "/api/index/p_index2004", "desc": "获取指数历史行情",
                 "params": "icode(指数代码), sdate(开始日期), edate(结束日期)",
                 "fields": "TRADEDATE(交易日期), OPEN(开盘), HIGH(最高), LOW(最低), CLOSE(收盘), VOLUME(成交量), AMOUNT(成交额)"},
            ]
        },
        {
            "name": "基金数据",
            "desc": "提供基金相关数据查询",
            "apis": [
                {"name": "基金基本信息", "path": "/api/fund/p_fund2001", "desc": "获取基金基本信息",
                 "params": "fcode(基金代码)",
                 "fields": "FUNDCODE(基金代码), FUNDNAME(基金名称), FUNDTYPE(基金类型), SETUPDATE(成立日期), FUNDMANAGER(基金经理)"},
                {"name": "基金净值", "path": "/api/fund/p_fund2002", "desc": "获取基金净值",
                 "params": "fcode(基金代码), sdate(开始日期), edate(结束日期)",
                 "fields": "FUNDCODE(基金代码), NAVDATE(净值日期), NAV(单位净值), ACCNAV(累计净值), DAYCHANGE(日涨跌幅)"},
                {"name": "基金持仓", "path": "/api/fund/p_fund2003", "desc": "获取基金持仓",
                 "params": "fcode(基金代码)",
                 "fields": "FUNDCODE(基金代码), SECCODE(持仓股票代码), SECNAME(持仓股票名称), HOLDNUM(持仓数量), HOLDVALUE(持仓市值), HOLDRATIO(持仓比例)"},
                {"name": "基金分红", "path": "/api/fund/p_fund2004", "desc": "获取基金分红",
                 "params": "fcode(基金代码)",
                 "fields": "FUNDCODE(基金代码), EXDATE(除息日), DIVIDEND(每份分红)"},
            ]
        },
        {
            "name": "债券数据",
            "desc": "提供债券相关数据查询",
            "apis": [
                {"name": "债券基本信息", "path": "/api/bond/p_bond2001", "desc": "获取债券基本信息",
                 "params": "bcode(债券代码)",
                 "fields": "BONDCODE(债券代码), BONDNAME(债券名称), BONDTYPE(债券类型), ISSUEDATE(发行日期), MATURITYDATE(到期日期), COUPONRATE(票面利率)"},
                {"name": "债券行情", "path": "/api/bond/p_bond2002", "desc": "获取债券行情",
                 "params": "bcode(债券代码), sdate(开始日期), edate(结束日期)",
                 "fields": "BONDCODE(债券代码), TRADEDATE(交易日期), CLOSE(收盘价), YIELD(到期收益率)"},
                {"name": "可转债信息", "path": "/api/bond/p_bond2003", "desc": "获取可转债信息",
                 "params": "bcode(债券代码)",
                 "fields": "BONDCODE(债券代码), BONDNAME(债券名称), STOCKCODE(正股代码), STOCKNAME(正股名称), CONVPRICE(转股价), CONVVALUE(转股价值), PREMIUM(溢价率)"},
            ]
        },
    ]
    
    # 生成各分类文档
    for category in api_categories:
        print(f"📝 正在处理: {category['name']}")
        
        md.append(f"## {category['name']}")
        md.append("")
        md.append(f"> {category['desc']}")
        md.append("")
        
        for api in category["apis"]:
            md.append(f"### {api['name']}")
            md.append("")
            md.append(f"**接口路径**: `{api['path']}`")
            md.append("")
            md.append(f"**请求方式**: `POST`")
            md.append("")
            md.append(f"**功能说明**: {api['desc']}")
            md.append("")
            md.append(f"**请求参数**: {api['params']}")
            md.append("")
            md.append(f"**响应字段**: {api['fields']}")
            md.append("")
            md.append("---")
            md.append("")
    
    # 附录
    md.append("## 附录")
    md.append("")
    md.append("### 股票代码规则")
    md.append("")
    md.append("| 交易所 | 代码前缀 | 示例 |")
    md.append("|--------|----------|------|")
    md.append("| 上海证券交易所 | 6开头 | 600000 |")
    md.append("| 深圳证券交易所 | 0开头 | 000001 |")
    md.append("| 创业板 | 3开头 | 300001 |")
    md.append("| 科创板 | 688开头 | 688001 |")
    md.append("| 北交所 | 8开头 | 830001 |")
    md.append("")
    md.append("### 公告类型代码")
    md.append("")
    md.append("| 代码 | 类型 |")
    md.append("|------|------|")
    md.append("| category_ndbg_szsh | 年度报告 |")
    md.append("| category_bndbg_szsh | 半年度报告 |")
    md.append("| category_yjdbg_szsh | 一季度报告 |")
    md.append("| category_sjdbg_szsh | 三季度报告 |")
    md.append("| category_ipo_szsh | IPO公告 |")
    md.append("| category_zf_szsh | 增发公告 |")
    md.append("| category_pg_szsh | 配股公告 |")
    md.append("| category_gqbd_szsh | 股权变动 |")
    md.append("| category_gddh_szsh | 股东大会 |")
    md.append("")
    md.append("### 错误码说明")
    md.append("")
    md.append("| 错误码 | 说明 |")
    md.append("|--------|------|")
    md.append("| 200 | 成功 |")
    md.append("| 400 | 请求参数错误 |")
    md.append("| 401 | 未授权 |")
    md.append("| 403 | 禁止访问 |")
    md.append("| 404 | 接口不存在 |")
    md.append("| 451 | Token无效或过期 |")
    md.append("| 500 | 服务器内部错误 |")
    md.append("| 502 | 网关错误 |")
    md.append("")
    md.append("### 相关链接")
    md.append("")
    md.append("- [巨潮资讯网官网](http://www.cninfo.com.cn/)")
    md.append("- [巨潮资讯网API平台](https://webapi.cninfo.com.cn/)")
    md.append("- [深圳证券交易所](http://www.szse.cn/)")
    md.append("- [上海证券交易所](http://www.sse.com.cn/)")
    md.append("")
    md.append("---")
    md.append("")
    md.append(f"*文档生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    return "\n".join(md)


def main():
    """主函数"""
    print("=" * 60)
    print("巨潮资讯网 API 文档爬虫")
    print("=" * 60)
    print()
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # 生成文档
    print("🚀 开始生成API文档...")
    print()
    
    md_content = generate_markdown()
    
    # 保存文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print()
    print("=" * 60)
    print(f"✅ 文档已保存到: {OUTPUT_FILE}")
    print(f"📄 文件大小: {os.path.getsize(OUTPUT_FILE) / 1024:.2f} KB")
    print("=" * 60)


if __name__ == "__main__":
    main()