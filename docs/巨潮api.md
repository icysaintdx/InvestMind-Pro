# 巨潮资讯网 API 文档

本文档整理自巨潮资讯网 WebAPI 接口文档。

**数据来源:** http://webapi.cninfo.com.cn  
**文档更新时间:** 2025-12-30  
**API总数:** 56个

---

## 目录

1. [公共数据](#公共数据) (7个API)
2. [股票数据](#股票数据) (11个API)
3. [财务数据](#财务数据) (12个API)
4. [交易数据](#交易数据) (7个API)
5. [股东数据](#股东数据) (6个API)
6. [分红配股数据](#分红配股数据) (4个API)
7. [指数数据](#指数数据) (3个API)
8. [基金数据](#基金数据) (3个API)
9. [债券数据](#债券数据) (3个API)

---

## 通用参数说明

| 参数 | 说明 |
|-----|------|
| format | 结果格式：xml/json/csv/dbf |
| @column | 选择返回字段，逗号分隔 |
| @limit | 限制返回条数 |
| @orderby | 排序：字段:asc/desc |

---

## 公共数据 (7个API)

| # | API名称 | 接口 | 说明 |
|---|--------|------|------|
| 1 | 交易日历数据 | p_public0001 | 查询交易日历 |
| 2 | 行业分类数据 | p_public0002 | 中上协/申万/新财富行业分类 |
| 3 | 地区分类数据 | p_public0003 | 省市区地区分类 |
| 4 | 证券类别编码 | p_public0004 | 证券类别编码 |
| 5 | 公共编码数据 | p_public0005 | 公共编码 |
| 6 | 人民币汇率中间价 | p_public0006 | 汇率数据 |
| 7 | 机构信息数据 | p_public0007 | 机构信息 |

---

## 股票数据 (11个API)

| # | API名称 | 接口 | 说明 |
|---|--------|------|------|
| 8 | 股票背景资料 | p_stock0001 | 股票基本背景 |
| 9 | 板块成份股 | p_stock0002 | 板块成份股列表 |
| 10 | 股票所属板块 | p_stock0004 | 股票所属板块 |
| 11 | 公司基本信息 | p_stock0005 | 公司详细信息 |
| 12 | 股票基本信息 | p_stock0006 | 股票发行上市信息 |
| 13 | 管理人员任职 | p_stock0007 | 高管任职情况 |
| 14 | 机构信息变更 | p_stock0008 | 机构变更记录 |
| 15 | 简称变更 | p_stock0009 | 证券简称变更 |
| 16 | 行业归属变动 | p_stock0010 | 行业变动记录 |
| 17 | 上市状态变动 | p_stock0011 | 上市状态变动 |
| 18 | 行业收入数据 | p_stock0012 | 主要行业收入 |

---

## 财务数据 (12个API)

| # | API名称 | 接口 | 说明 |
|---|--------|------|------|
| 19 | 定期报告预披露 | p_stock2001 | 报告预披露时间 |
| 20 | 业绩预告 | p_stock2002 | 业绩预告数据 |
| 21 | 审计意见 | p_stock2003 | 定期报告审计意见 |
| 22 | 资产负债表 | p_stock2101 | 个股资产负债表 |
| 23 | 利润表 | p_stock2102 | 个股利润表 |
| 24 | 现金流量表 | p_stock2103 | 个股现金流量表 |
| 25 | 财务指标表 | p_stock2104 | 个股财务指标 |
| 26 | 金融类资产负债表 | p_stock2201 | 金融类公司专用 |
| 27 | 金融类利润表 | p_stock2202 | 金融类公司专用 |
| 28 | 金融类现金流量表 | p_stock2203 | 金融类公司专用 |
| 29 | 业绩快报 | p_stock2004 | 业绩快报数据 |
| 30 | 个股指标快速版 | p_stock2387 | 快速获取财务指标 |

---

## 交易数据 (7个API)

| # | API名称 | 接口 | 说明 |
|---|--------|------|------|
| 31 | 日行情数据 | p_stock1001 | 个股日K线数据 |
| 32 | 周行情数据 | p_stock1002 | 个股周K线数据 |
| 33 | 月行情数据 | p_stock1003 | 个股月K线数据 |
| 34 | 停复牌信息 | p_stock1004 | 停复牌记录 |
| 35 | 涨跌停统计 | p_stock1005 | 涨跌停统计 |
| 36 | 大宗交易 | p_stock1006 | 大宗交易数据 |
| 37 | 融资融券 | p_stock1007 | 融资融券数据 |

---

## 股东数据 (6个API)

| # | API名称 | 接口 | 说明 |
|---|--------|------|------|
| 38 | 十大股东 | p_stock3001 | 十大股东数据 |
| 39 | 十大流通股东 | p_stock3002 | 十大流通股东 |
| 40 | 股东户数 | p_stock3003 | 股东户数统计 |
| 41 | 实际控制人 | p_stock3004 | 实际控制人信息 |
| 42 | 股本结构 | p_stock3005 | 股本结构数据 |
| 43 | 限售股解禁 | p_stock3006 | 限售股解禁数据 |

---

## 分红配股数据 (4个API)

| # | API名称 | 接口 | 说明 |
|---|--------|------|------|
| 44 | 分红送转 | p_stock4001 | 分红送转数据 |
| 45 | 配股数据 | p_stock4002 | 配股信息 |
| 46 | 增发数据 | p_stock4003 | 增发信息 |
| 47 | 股票回购 | p_stock4004 | 回购数据 |

---

## 指数数据 (3个API)

| # | API名称 | 接口 | 说明 |
|---|--------|------|------|
| 48 | 指数基本信息 | p_index0001 | 指数基本信息 |
| 49 | 指数日行情 | p_index0002 | 指数日K线数据 |
| 50 | 指数成份股 | p_index0003 | 指数成份股列表 |

---

## 基金数据 (3个API)

| # | API名称 | 接口 | 说明 |
|---|--------|------|------|
| 51 | 基金基本信息 | p_fund0001 | 基金基本信息 |
| 52 | 基金日行情 | p_fund0002 | 基金日K线数据 |
| 53 | 基金净值 | p_fund0003 | 基金净值数据 |

---

## 债券数据 (3个API)

| # | API名称 | 接口 | 说明 |
|---|--------|------|------|
| 54 | 债券基本信息 | p_bond0001 | 债券基本信息 |
| 55 | 债券日行情 | p_bond0002 | 债券日K线数据 |
| 56 | 可转债数据 | p_bond0003 | 可转债信息 |

---

## 详细API说明

### 日行情数据 (p_stock1001)
**URL:** http://webapi.cninfo.com.cn/api/stock/p_stock1001

| 输入参数 | 说明 |
|---------|------|
| scode | 股票代码(必填,≤50只,逗号分隔) |
| sdate | 开始日期 YYYY-MM-DD |
| edate | 结束日期 YYYY-MM-DD |

| 输出参数 | 说明 |
|---------|------|
| TRADEDATE | 交易日期 |
| OPEN | 开盘价(元) |
| HIGH | 最高价(元) |
| LOW | 最低价(元) |
| CLOSE | 收盘价(元) |
| PRECLOSE | 前收盘价(元) |
| CHANGE | 涨跌额(元) |
| CHANGEPCT | 涨跌幅(%) |
| VOLUME | 成交量(股) |
| AMOUNT | 成交额(元) |
| TURNOVERRATE | 换手率(%) |
| TOTALMV | 总市值(元) |
| FLOATMV | 流通市值(元) |

---

### 资产负债表 (p_stock2101)
**URL:** http://webapi.cninfo.com.cn/api/stock/p_stock2101

| 输入参数 | 说明 |
|---------|------|
| scode | 股票代码(必填,≤50只) |
| sdate | 开始日期 |
| edate | 结束日期 |

| 输出参数 | 说明 |
|---------|------|
| TOTALASSETS | 资产总计(元) |
| TOTALLIAB | 负债合计(元) |
| TOTALEQUITY | 所有者权益合计(元) |
| MONETARYFUNDS | 货币资金(元) |
| ACCOUNTSRECEIV | 应收账款(元) |
| INVENTORY | 存货(元) |
| FIXEDASSETS | 固定资产(元) |
| INTANGIBLEASSETS | 无形资产(元) |
| GOODWILL | 商誉(元) |
| SHORTTERMLOAN | 短期借款(元) |
| LONGTERMLOAN | 长期借款(元) |
| SHARECAPITAL | 股本(元) |
| CAPITALRESERVE | 资本公积(元) |
| RETAINEDEARNINGS | 未分配利润(元) |

---

### 利润表 (p_stock2102)
**URL:** http://webapi.cninfo.com.cn/api/stock/p_stock2102

| 输出参数 | 说明 |
|---------|------|
| TOTALREVENUE | 营业总收入(元) |
| REVENUE | 营业收入(元) |
| OPERATINGCOST | 营业成本(元) |
| SELLINGEXP | 销售费用(元) |
| ADMINEXP | 管理费用(元) |
| RDEXP | 研发费用(元) |
| FINANCEEXP | 财务费用(元) |
| OPERATINGPROFIT | 营业利润(元) |
| TOTALPROFIT | 利润总额(元) |
| NETPROFIT | 净利润(元) |
| NETPROFITPARENT | 归母净利润(元) |
| BASICEPS | 基本每股收益(元/股) |

---

### 财务指标表 (p_stock2104)
**URL:** http://webapi.cninfo.com.cn/api/stock/p_stock2104

| 输出参数 | 说明 |
|---------|------|
| BASICEPS | 基本每股收益(元/股) |
| BVPS | 每股净资产(元/股) |
| CFPS | 每股经营现金流(元/股) |
| ROE | 净资产收益率(%) |
| GROSSMARGIN | 销售毛利率(%) |
| NETMARGIN | 销售净利率(%) |
| CURRENTRATIO | 流动比率 |
| QUICKRATIO | 速动比率 |
| DEBTTOASSETS | 资产负债率(%) |

---

### 十大股东 (p_stock3001)
**URL:** http://webapi.cninfo.com.cn/api/stock/p_stock3001

| 输入参数 | 说明 |
|---------|------|
| scode | 股票代码(必填) |
| rdate | 报告期 |

| 输出参数 | 说明 |
|---------|------|
| RDATE | 报告期 |
| SHNAME | 股东名称 |
| SHTYPE | 股东类型 |
| HOLDNUM | 持股数量(股) |
| HOLDPCT | 持股比例(%) |
| HOLDCHANGE | 持股变动(股) |
| SHARETYPE | 股份类型 |

---

### 分红送转 (p_stock4001)
**URL:** http://webapi.cninfo.com.cn/api/stock/p_stock4001

| 输入参数 | 说明 |
|---------|------|
| scode | 股票代码 |
| rdate | 报告期 |

| 输出参数 | 说明 |
|---------|------|
| RDATE | 报告期 |
| NOTICEDATE | 公告日期 |
| EXDIVDATE | 除权除息日 |
| REGDATE | 股权登记日 |
| CASHDIV | 每股现金分红(元) |
| STOCKDIV | 每股送股(股) |
| STOCKTRANS | 每股转增(股) |
| DIVTOTAL | 分红总额(元) |

---

### 业绩预告 (p_stock2002)
**URL:** http://webapi.cninfo.com.cn/api/stock/p_stock2002

| 输入参数 | 说明 |
|---------|------|
| scode | 股票代码 |
| rdate | 报告期 |

| 输出参数 | 说明 |
|---------|------|
| NOTICEDATE | 公告日期 |
| FORECASTTYPE | 预告类型 |
| FORECASTCONTENT | 预告内容 |
| NETPROFITMIN | 净利润下限(元) |
| NETPROFITMAX | 净利润上限(元) |
| CHANGEPCTMIN | 变动幅度下限(%) |
| CHANGEPCTMAX | 变动幅度上限(%) |

**预告类型说明:**
- 预增：净利润同比增长50%以上
- 预减：净利润同比下降50%以上
- 扭亏：上年亏损，本期盈利
- 首亏：上年盈利，本期亏损
- 续盈：连续盈利
- 续亏：连续亏损
- 略增：净利润同比增长0-50%
- 略减：净利润同比下降0-50%

---

## 使用示例

### Python调用示例

```python
import requests

# API基础URL
BASE_URL = "http://webapi.cninfo.com.cn/api/stock"

# 获取日行情数据
def get_daily_quote(scode, sdate, edate):
    url = f"{BASE_URL}/p_stock1001"
    params = {
        "scode": scode,
        "sdate": sdate,
        "edate": edate,
        "format": "json"
    }
    response = requests.get(url, params=params)
    return response.json()

# 获取财务指标
def get_financial_indicators(scode, rdate):
    url = f"{BASE_URL}/p_stock2104"
    params = {
        "scode": scode,
        "sdate": rdate,
        "edate": rdate,
        "format": "json"
    }
    response = requests.get(url, params=params)
    return response.json()

# 示例调用
if __name__ == "__main__":
    # 获取贵州茅台日行情
    data = get_daily_quote("600519", "2024-01-01", "2024-12-31")
    print(data)
    
    # 获取财务指标
    indicators = get_financial_indicators("600519", "2024-09-30")
    print(indicators)
```

---

## 注意事项

1. **请求限制**: 每个API最大返回记录数为20000条
2. **股票代码**: 大部分API支持批量查询，用逗号分隔，但有数量限制(通常≤50或≤300只)
3. **日期格式**: 统一使用 YYYY-MM-DD 格式
4. **市场代码**: SZ表示深圳，SH表示上海
5. **报告期格式**: 使用季度末日期，如2024-03-31、2024-06-30、2024-09-30、2024-12-31
6. **数据更新**: 行情数据通常T+1更新，财务数据在定期报告披露后更新

---

## 相关链接

- 巨潮资讯网: http://www.cninfo.com.cn
- WebAPI文档: http://webapi.cninfo.com.cn
- 数据服务: http://webapi.cninfo.com.cn/#/datalist

---

*文档整理完成于 2025-12-30*








# 示例

接口英文名称：	p_info3005
接口中文名称：	公告分类信息
URL用例：	https://webapi.cninfo.com.cn/api/info/p_info3005
接口说明：	函数说明：取公告分类内容。 请求方式：GET 和 POST
最大记录数：	20000
输入参数值
英文名称	中文名称	类型	是否必填	说明
sortcode	分类编码	string	否	只能查询一个分类代码
parentcode	父类编码	string	否	传入父类编码，可以查询对应的所属分类编码，顶级分类为01
format	结果集格式	string	否	设置结果返回的格式，可选的有xml、json、csv、dbf
@column	结果列选择	string	否	选择结果集中所需要的字段，多列用逗号分隔，如@column=a,b
@limit	结果条数限制	int	否	设置结果返回的条数
@orderby	结果集排序	string	否	设置结果集的格式，如 @orderby=id:desc @orderby=id:asc
输出参数值
英文名称	中文名称	类型	单位	说明
SORTCODE	类目编码	VARCHAR		
PARENTCODE	父类编码	VARCHAR		
SORTNAME	类目名称	VARCHAR		
F001D	启用时间	DATE		
F002D	停用时间	DATE		
错误码示例
错误码	错误信息	说明
-1	系统繁忙，此时请开发者稍候再试	系统繁忙，此时请开发者稍候再试
200	success	success
401	未经授权的访问	未经授权的访问
402	不合法的参数	不合法的参数
403	脚本服务器异常	脚本服务器异常
404	token 无效	token 无效
405	token过期	token过期
406	用户已被禁用	用户已被禁用
407	免费试用次数已用完	免费试用次数已用完
408	用户没有余额	用户没有余额
409	验证权限错误	验证权限错误
410	验证权限异常	验证权限异常
411	获取用户信息失败	获取用户信息失败
412	包时长已超期	包时长已超期


## 代码示例

### Web Api

#-*- coding: UTF-8 -*-

import json
import urllib
import requests
import datetime

####用于获取token
def gettoken(client_id,client_secret):
    url='http://webapi.cninfo.com.cn/api-cloud-platform/oauth2/token'
    post_data="grant_type=client_credentials&client_id=%s&client_secret=%s"%(client_id,client_secret)
    post_data={"grant_type":"client_credentials",
               "client_id":client_id,
               "client_secret":client_secret
               }
    req = requests.post(url, data=post_data)
    tokendic = json.loads(req.text)
    return tokendic['access_token']

####用于解析接口返回内容
def getPage(url):
    response = urllib.request.urlopen(url)
    return response.read().decode('utf-8')

token = gettoken('xxxxxxxxx','xxxxxxxxx') ##请在平台注册后并填入个人中心-我的凭证中的Access Key，Access Secret
url = 'http://webapi.cninfo.com.cn/api/public/p_public0005?subtype=002&access_token='+token
print(url)
result = json.loads(getPage(url))
for i in range(len(result['records'])):
    print (result['records'][i]['PARENTCODE'],result['records'][i]['SORTCODE'],result['records'][i]['SORTNAME'],result['records'][i]['F002V'])


#### Python

#-*- coding: UTF-8 -*-

import json
import urllib
import requests
import datetime

####用于获取token
def gettoken(client_id,client_secret):
    url='http://webapi.cninfo.com.cn/api-cloud-platform/oauth2/token'
    post_data="grant_type=client_credentials&client_id=%s&client_secret=%s"%(client_id,client_secret)
    post_data={"grant_type":"client_credentials",
               "client_id":client_id,
               "client_secret":client_secret
               }
    req = requests.post(url, data=post_data)
    tokendic = json.loads(req.text)
    return tokendic['access_token']

####用于解析接口返回内容
def getPage(url):
    response = urllib.request.urlopen(url)
    return response.read().decode('utf-8')

token = gettoken('xxxxxxxxx','xxxxxxxxx') ##请在平台注册后并填入个人中心-我的凭证中的Access Key，Access Secret
url = 'http://webapi.cninfo.com.cn/api/public/p_public0005?subtype=002&access_token='+token
print(url)
result = json.loads(getPage(url))
for i in range(len(result['records'])):
    print (result['records'][i]['PARENTCODE'],result['records'][i]['SORTCODE'],result['records'][i]['SORTNAME'],result['records'][i]['F002V'])


    