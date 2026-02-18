# 巨潮资讯网 API 文档

本文档整理自巨潮资讯网 WebAPI 接口文档。

**数据来源:** http://webapi.cninfo.com.cn
**文档更新时间:** 2025-12-30
**API总数:** 56个

---

## 免费API测试结果 (2025-12-30)

### 可用的免费API (11个)

| API Code | 名称 | 记录数示例 | 说明 |
|----------|------|-----------|------|
| p_stock2100 | 公司基本信息 | 1 | 机构名称、法人代表、注册地址、主营业务等 |
| p_stock2101 | 股票基本信息 | 1 | 证券代码、上市日期、交易市场、面值等 |
| p_stock0004 | 股票所属板块 | 100 | 市场分类、行业分类、概念板块等 |
| p_stock2102 | 管理人员任职情况 | 14 | 高管姓名、职务、任职日期、个人简历等 |
| p_stock2117 | 上市状态变动情况 | 12568 | 上市、退市、暂停上市等状态变动 |
| p_stock2107 | 公司员工情况 | 2 | 员工总数、学历分布、职能分布等 |
| p_info3005 | 公告分类信息 | 31 | 公告类目编码和名称 |
| p_info3015 | 公告基本信息 | 1824 | 公告标题、日期、PDF地址等 |
| p_public0005 | 公共编码数据 | 33 | 各类编码定义 |
| p_public0006 | 人民币汇率中间价 | 4529 | 历史汇率数据 |
| p_public0007 | 机构信息数据 | 20000 | 机构基本信息 |

### 需要VIP权限的API

| API Code | 名称 | 错误码 | 说明 |
|----------|------|--------|------|
| p_stock2108 | 机构基本信息变更 | 416 | 需升级为VIP用户 |
| p_stock2109 | 证券简称变更 | 416 | 需升级为VIP用户 |
| p_stock2110 | 行业归属变动 | 416 | 需升级为VIP用户 |
| p_company3201 | 股票背景资料 | 415 | 需购买包时长服务 |

### 返回502错误的API

| API Code | 名称 | 说明 |
|----------|------|------|
| p_public0001 | 交易日历数据 | 可能需要特定参数或权限 |
| p_public0002 | 行业分类数据 | 可能需要特定参数或权限 |
| p_public0003 | 地区分类数据 | 可能需要特定参数或权限 |
| p_public0004 | 板块成份股数据 | 可能需要特定参数或权限 |

### 频率限制测试结果

- **无明显频率限制**: 连续10次快速请求全部成功
- **并发请求**: 5个并发请求全部成功
- **响应时间**: 约0.07-0.16秒/请求
- **建议间隔**: 0.3秒 (保守估计)

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




应该是免费的服务接口 如下


股票-基本信息
45
上架时间：2024-08-06供应商：深证信
AB股沪深北市场公司行为基本信息基础服务VIP服务
包含上市公司机构名称、证券简称、法人代表、注册地址、办公地址、主营业务、经营范围、中介结构、董秘、证代等机构信息、以及证券类别、交易市场、上市日期等证券基本信息。

包含接口: 
公司基本信息
API Code: p_stock2100
接口说明: 公司基本信息数据。 请求方式：GET 和 POST
输入参数值:
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	是	输入不超过50只股票代码，用逗号分隔；如： 000001,600000
输出参数值:
英文名称	中文名称	类型	是否必填	说明
ORGID	机构ID	varchar(11)	否	
ORGNAME	机构名称	varchar(100)	否	
SECCODE	证券代码	varchar(10)	否	
SECNAME	证券简称	varchar(40)	否	
F001V	英文名称	varchar(100)	否	
F002V	英文简称	varchar(40)	否	
F003V	法人代表	varchar(40)	否	
F004V	注册地址	varchar(100)	否	
F005V	办公地址	varchar(150)	否	
F006V	邮政编码	varchar(10)	否	
F007N	注册资金	numeric(14,4)	否	
F008V	货币编码	varchar(12)	否	
F009V	货币名称	varchar(60)	否	
F010D	成立日期	DATE	否	
F011V	机构网址	varchar(80)	否	
F012V	电子信箱	varchar(80)	否	
F013V	联系电话	varchar(60)	否	
F014V	联系传真	varchar(60)	否	
F015V	主营业务	varchar(500)	否	
F016V	经营范围	varchar(4000)	否	
F017V	机构简介/公司成立概况	varchar(2000)	否	
F018V	董事会秘书	varchar(40)	否	
F019V	董秘联系电话	varchar(60)	否	
F020V	董秘联系传真	varchar(60)	否	
F021V	董秘电子邮箱	varchar(80)	否	
F022V	证券事务代表	varchar(40)	否	
F023V	上市状态编码	varchar(12)	否	
F024V	上市状态	varchar(60)	否	
F025V	所属省份编码	varchar(12)	否	
F026V	所属省份	varchar(60)	否	
F027V	所属城市编码	varchar(12)	否	
F028V	所属城市	varchar(60)	否	
F029V	中上协一级行业编码	varchar(12)	否	
F030V	中上协一级行业名称	varchar(60)	否	
F031V	中上协二级行业编码	varchar(60)	否	
F032V	中上协二级行业名称	varchar(60)	否	
F033V	申万行业分类一级编码	varchar(60)	否	
F034V	申万行业分类一级名称	varchar(60)	否	
F035V	申万行业分类二级编码	varchar(60)	否	
F036V	申万行业分类二级名称	varchar(60)	否	
F037V	申万行业分类三级编码	varchar(60)	否	
F038V	申万行业分类三级名称	varchar(60)	否	
F039V	会计师事务所	varchar(200)	否	
F040V	律师事务所	varchar(200)	否	
F041V	董事长	varchar(60)	否	
F042V	总经理	varchar(60)	否	
F043V	公司独立董事(现任)	varchar(100)	否	多名
F044V	入选指数	varchar(1000)	否	多个
F045V	最新报告预约日期	varchar(50)	否	
F046V	保荐机构	varchar(500)	否	多个
F047V	主承销商	varchar(500)	否	
F048V	PEVC标记	varchar(12)	否	
F049V	注册国家	varchar(200)	否	
F050V	统一社会信用代码	varchar(60)	否	
F051V	工商ID	varchar(60)	否	
F052V	可转债	varchar(100)	否	
F053V	CDR	varchar(100)	否	
F054V	企业规模	varchar(20)	否	
股票基本信息
API Code: p_stock2101
接口说明: 取股票基本信息表 请求方式：GET 和 POST
输入参数值:
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	否	输入不超过50只股票代码，用逗号分隔；如： 000001,600000
输出参数值:
英文名称	中文名称	类型	是否必填	说明
ORGNAME	机构名称	varchar	否	
SECCODE	证券代码	varchar	否	
SECNAME	证券简称	varchar	否	
F001V	拼音简称	varchar	否	
F002V	证券类别编码	varchar	否	
F003V	证券类别	varchar	否	
F004V	交易市场编码	varchar	否	
F005V	交易市场	varchar	否	
F006D	上市日期	datetime	否	
F007N	初始上市数量	decimal	否	单位：股
F008V	代码属性编码	varchar	否	
F009V	代码属性	varchar	否	
F010V	上市状态编码	varchar	否	
F011V	上市状态	varchar	否	
F012N	面值	decimal	否	单位：元
F013V	ISIN	varchar	否	
股票所属板块
API Code: p_stock0004
接口说明:
输入参数值:
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	是	输入不超过300只股票代码，用逗号分隔；如： 000001,600000
typecode	类别代码	string	否	可以传入多个类别代码，用逗号分隔， 编码：137001 市场分类 137002 中上协行业分类 137004 申银万国行业分类 137005 新财富行业分类 137006 地区省市分类 137007 指数成份股 137008 概念板块
输出参数值:
英文名称	中文名称	类型	是否必填	说明
SECCODE	证券代码	varchar	否	
SECNAME	证券简称	varchar	否	
F001V	分类标准编码	varchar	否	
F002V	分类标准	varchar	否	
F003V	板块编码	varchar	否	
F004V	板块一类名称	varchar	否	
F005V	板块二类名称	varchar	否	
F006V	板块三类名称	varchar	否	
F007V	板块四类名称	varchar	否	
F008V	板块五类名称	varchar	否	
F009V	板块一类编码	varchar	否	
F010V	板块二类编码	varchar	否	
F011V	板块三类编码	varchar	否	
F012V	板块四类编码	varchar	否	
F013V	板块五类编码	varchar	否	
板块成份股数据
API Code: p_public0004
接口说明: 取板块的成份股列表 返回指定属于板块的所有证券列表,板块包括地区分类，行业分类，指数分类,市场分类等 请求方式：GET 和 POST
输入参数值:
英文名称	中文名称	类型	是否必填	说明
platetype	分类代码类型	string	是	137001 市场分类 137002 中上协行业分类 137003 巨潮行业分类 137004 申银万国行业分类 137005 新财富行业分类 137006 地区省市分类 137007 指数成份股 137008 概念板块 不允许多选，一次只能查一种类型的分类 不允许为空
platecode	板块代码	string	否	行业代码、地区代码、指数代码请查询上面分类数据查询API获得 市板代码定义： 沪市：012001 深市主板：012002 深市创：012015 不允许多选 只能传同一种类型的代码，不能地区、行业、指数、市场混着传；
abtype	AB股类型	string	否	A：A 股，B：B股
输出参数值:
英文名称	中文名称	类型	是否必填	说明
SECCODE	证券代码	varchar	否	
SECNAME	证券简称	varchar	否	
F001V	分类标准编码	varchar	否	
F002V	分类标准	varchar	否	
F003V	板块编码	varchar	否	
F004V	板块一类名称	varchar	否	
F005V	板块二类名称	varchar	否	
F006V	板块三类名称	varchar	否	
F007V	板块四类名称	varchar	否	
F008V	板块五类名称	varchar	否	
F009V	板块一类编码	varchar	否	
F010V	板块二类编码	varchar	否	
F011V	板块三类编码	varchar	否	
F012V	板块四类编码	varchar	否	
F013V	板块五类编码	varchar	否	
STARTDATE	生效日期	date	否	
股票背景资料
API Code: p_company3201
接口说明: 股票背景资料
输入参数值:
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	否	为空取所有公司背景
page	page	int	否	
pagesize	pagesize	int	否	
输出参数值:
英文名称	中文名称	类型	是否必填	说明
SECCODE	证券代码	VARCHAR(20)	否	
SECNAME	证券简称	VARCHAR(60)	否	
F001V	公司背景	VARCHAR(2000)	否	
RECTIME	数据时间	DATETIME	否	
F002V	资讯标题	VARCHAR(100)	否	
公司管理人员任职情况
API Code: p_stock2102
接口说明: 取公司管理人员任职情况和部份个人简介 请求方式：GET 和 POST
输入参数值:
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	是	输入不超过50只股票代码，用逗号分隔；如： 000001,600000
state	状态	int	否	为空则取数有数据，输入1则取最新一任期管理人员
输出参数值:
英文名称	中文名称	类型	是否必填	说明
ORGNAME	机构名称	VARCHAR	否	
SECCODE	证券代码	VARCHAR	否	
SECNAME	证券简称	VARCHAR	否	
DECLAREDATE	公告日期	DATE	否	
F001V	个人ID	VARCHAR	否	
F002V	姓名	VARCHAR	否	
F007D	任职日期	DATE	否	
F008D	离职日期	DATE	否	
F009V	职务名称	VARCHAR	否	
F010V	性别	VARCHAR	否	
F011V	教育程度	VARCHAR	否	
F012V	出生年份	VARCHAR	否	
F013V	国籍	VARCHAR	否	
F014V	职务类别编码	VARCHAR	否	
F015V	职务类别	VARCHAR	否	
F016V	职务编码	VARCHAR	否	
F017V	最高学历	VARCHAR	否	
F019V	个人简历	VARCHAR	否	
F020C	是否在职	char	否	0-否，1-是
机构基本信息变更情况
API Code: p_stock2108
接口说明: 机构基本信息变更情况
输入参数值:
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	是	示例：scode=000002
sdate	开始公布日期	string	否	支持格式：20161101 或2016-11-01 或2016/11/01
edate	结束公布日期	int	否	支持格式：20161101 或2016-11-01 或2016/11/01
输出参数值:
英文名称	中文名称	类型	是否必填	说明
SECCODE	证券代码	varchar(10)	否	
SECNAME	证券简称	varchar(40)	否	
VARYDATE	公布日期	DATE	否	
TYPENAME	变更事项	VARCHAR(60)	否	对应公共编码0116，机构名称、注册地址、联系方式等
TYPECODE	变更事项编码	VARCHAR(12)	否	
F001V	变更后（中文名称）	VARCHAR(100)	否	
F002V	变更后（英文名称）	VARCHAR(150)	否	
F003V	变更前（中文名称）	VARCHAR(100)	否	
F004V	变更前（英文名称）	VARCHAR(150)	否	
F005V	变更原因	VARCHAR(255)	否	
F006D	生效日期	date	否	
证券简称变更情况
API Code: p_stock2109
接口说明:
输入参数值:
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	是	示例：scode=000002
sdate	开始日期	string	否	STARTDATE
edate	结束日期	string	否	STARTDATE
输出参数值:
英文名称	中文名称	类型	是否必填	说明
暂无数据
上市公司行业归属的变动情况
API Code: p_stock2110
接口说明: 上市公司行业归属的变动情况
输入参数值:
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	是	示例：000002
sdate	开始变动日期	string	否	支持格式：20161101 或2016-11-01 或2016/11/01
edate	结束变动日期	string	否	支持格式：20161101 或2016-11-01 或2016/11/01
输出参数值:
英文名称	中文名称	类型	是否必填	说明
ORGNAME	机构名称	VARCHAR(100)	否	
SECCODE	证券代码	VARCHAR(10)	否	
SECNAME	新证券简称	VARCHAR(40)	否	通过公共编码表选择采集；对应的总类编码为‘008’
VARYDATE	变更日期	DATE	否	
F001V	分类标准编码	VARCHAR(12)	否	
F002V	分类标准	VARCHAR(60)	否	
F003V	行业编码	VARCHAR(12)	否	
F004V	行业门类	VARCHAR(60)	否	
F005V	行业次类	VARCHAR(60)	否	
F006V	行业大类	VARCHAR(60)	否	
F007V	行业中类	VARCHAR(60)	否	
F008C	最新记录标识	CHAR(1)	否	
公司上市状态变动情况表
API Code: p_stock2117
接口说明:
输入参数值:
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	否	股票代码
sign	上市状态	string	否	上市状态，须先访问公共信息中的公共编码数据（p_public0006）接口，令subtype=013，获取相应的上市状态编码
type	变更类型	string	否	变更类型，须先访问公共信息中的公共编码数据（p_public0006）接口，令subtype=031，获取变更类型编码
输出参数值:
英文名称	中文名称	类型	是否必填	说明
SECCODE	证券代码	varchar(10)	否	
SECNAME	证券简称	varchar(40)	否	
ORGNAME	机构名称	varchar(100)	否	
DECLAREDATE	公告日期	datetime	否	
VARYDATE	变更日期	date	否	
F002V	上市状态	varchar(60)	否	
F004V	变更原因	varchar(500)	否	
F006V	变更类型	varchar(60)	否	
公司员工情况表
API Code: p_stock2107
接口说明: 公司员工情况表
输入参数值:
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	是	输入不超过50只股票代码，用逗号分隔；如： 000001,600000
sdate	开始日期	string	否	支持格式示例：20181101 或2018-11-01 或2018/11/01
edate	结束日期	string	否	支持格式示例：20181101 或2018-11-01 或2018/11/01
state	最新标识	string	否	当state=1取最新标识的所有数据
输出参数值:
英文名称	中文名称	类型	是否必填	说明
ORGID	公司ID	varchar(11)	否	
ORGNAME	公司名称	varchar(100)	否	
SECCODE	证券代码	varchar(10)	否	
SECNAME	证券简称	varchar(40)	否	
ENDDATE	截止日期	datetime	否	
DECLAREDATE	公告日期	datetime	否	程序自动默认为录入当日，可修改
STAFFNUM	员工总数	decimal(8)	否	单位:人;在职员工
F006C	最新记录标识	char(1)	否	0-否,1-是;程序自动根据截止日期判断,将最新一期记录设为1,其余设为0
F003N	博士人数	int	否	
F004N	硕士人数	int	否	
F005N	本科人数	int	否	
F007N	大专人数	int	否	
F008N	高中及以下人数(其他)	int	否	采集单独披露的高中及以下人数和其他分类，高中、中专、初中等分别披露时，加总采集
F009N	生产人员	int	否	
F010N	销售人员	int	否	
F011N	技术人员	int	否	
F012N	财务人员	int	否	
F013N	行政人员	int	否	
F014N	其他人员	int	否	
股票-公司公告
47
上架时间：2021-09-25供应商：深证信
AB股沪深北市场公告资讯基础服务
巨潮网上市公司相关公告PDF全文，权威、实时、高效。

包含接口: 
公告分类信息
API Code: p_info3005
接口说明: 函数说明：取公告分类内容。 请求方式：GET 和 POST
输入参数值:
英文名称	中文名称	类型	是否必填	说明
sortcode	分类编码	string	否	只能查询一个分类代码
parentcode	父类编码	string	否	传入父类编码，可以查询对应的所属分类编码，顶级分类为01
输出参数值:
英文名称	中文名称	类型	是否必填	说明
SORTCODE	类目编码	VARCHAR	否	
PARENTCODE	父类编码	VARCHAR	否	
SORTNAME	类目名称	VARCHAR	否	
F001D	启用时间	DATE	否	
F002D	停用时间	DATE	否	
公告基本信息
API Code: p_info3015
接口说明: 获取公告信息 请求方式：GET 和 POST 注意事项：为保证响应时间，暂定API的每次返回记录数最多为20000条，请使用者注意 因公告数量较多，同一个类别的公告一次只能请求一天的数据，以保证API的响应时间 如果当天公告数量超出20000条记录，想实现增量的多次提取，可以先通过查询结果集，保存该结果集中最大一个OBJECTID,用于下次调用时通过参数maxID传入该值，这样实现增量提取
输入参数值:
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	否	输入1个股票， scode和edate同时为空情况下，默认返回最近100条记录
sdate	开始查询时间	string	否	支持格式示例：20161101 或2016-11-01 或2016/11/01
edate	结束查询时间	string	否	scode和edate同时为空情况下，默认返回最近100条记录 scode为空,edate不为空时，取edate日期这一天数据
market	市场	string	否	上交所:012001 科创板:012029 深交所主板:012002 深交所创业板:012015
maxid	增量起始ID	int	否	用于增量提取数据使用
textid	正文ID	string	否	
page	page	int	否	
pagesize	pagesize	int	否	
输出参数值:
英文名称	中文名称	类型	是否必填	说明
TEXTID	正文ID	VARCHAR	否	
RECID	主体ID	VARCHAR	否	
SECCODE	证券代码	VARCHAR	否	
SECNAME	证券简称	VARCHAR	否	
F001D	公告日期	DATE	否	
F002V	公告标题	VARCHAR	否	
F003V	公告地址	VARCHAR	否	
F004V	公告格式	VARCHAR	否	
F005N	公告大小	DECIMAL	否	
F006V	信息分类	VARCHAR	否	
F007V	证券类别编码	VARCHAR	否	
F008V	证券类别名称	VARCHAR	否	
F009V	证券市场编码	VARCHAR	否	
F010V	证券市场名称	VARCHAR	否	
OBJECTID	OBJECTID	BIGINT	否	
RECTIME	发布时间	DATETIME	否





公司基本信息
API接口名称: p_stock2100
URL接口名称: http://webapi.cninfo.com.cn/api/stock/p_stock2100
请求方式方法: get,post
最大记录数: 20000
输入参数 :
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	是	输入不超过50只股票代码，用逗号分隔；如： 000001,600000
format	结果集格式	string	否	设置结果返回的格式，可选的有xml、json、csv、dbf
@column	结果列选择	string	否	选择结果集中所需要的字段，多列用逗号分隔，如@column=a,b
@limit	结果条数限制	int	否	设置结果返回的条数
@orderby	结果集排序	string	否	设置结果集的格式，如 @orderby=id:desc @orderby=id:asc
输出参数 :
英文名称	中文名称	类型	单位	说明
ORGID	机构ID	varchar(11)		
ORGNAME	机构名称	varchar(100)		
SECCODE	证券代码	varchar(10)		
SECNAME	证券简称	varchar(40)		
F001V	英文名称	varchar(100)		
F002V	英文简称	varchar(40)		
F003V	法人代表	varchar(40)		
F004V	注册地址	varchar(100)		
F005V	办公地址	varchar(150)		
F006V	邮政编码	varchar(10)		
F007N	注册资金	numeric(14,4)		
F008V	货币编码	varchar(12)		
F009V	货币名称	varchar(60)		
F010D	成立日期	DATE		
F011V	机构网址	varchar(80)		
F012V	电子信箱	varchar(80)		
F013V	联系电话	varchar(60)		
F014V	联系传真	varchar(60)		
F015V	主营业务	varchar(500)		
F016V	经营范围	varchar(4000)		
F017V	机构简介/公司成立概况	varchar(2000)		
F018V	董事会秘书	varchar(40)		
F019V	董秘联系电话	varchar(60)		
F020V	董秘联系传真	varchar(60)		
F021V	董秘电子邮箱	varchar(80)		
F022V	证券事务代表	varchar(40)		
F023V	上市状态编码	varchar(12)		
F024V	上市状态	varchar(60)		
F025V	所属省份编码	varchar(12)		
F026V	所属省份	varchar(60)		
F027V	所属城市编码	varchar(12)		
F028V	所属城市	varchar(60)		
F029V	中上协一级行业编码	varchar(12)		
F030V	中上协一级行业名称	varchar(60)		
F031V	中上协二级行业编码	varchar(60)		
F032V	中上协二级行业名称	varchar(60)		
F033V	申万行业分类一级编码	varchar(60)		
F034V	申万行业分类一级名称	varchar(60)		
F035V	申万行业分类二级编码	varchar(60)		
F036V	申万行业分类二级名称	varchar(60)		
F037V	申万行业分类三级编码	varchar(60)		
F038V	申万行业分类三级名称	varchar(60)		
F039V	会计师事务所	varchar(200)		
F040V	律师事务所	varchar(200)		
F041V	董事长	varchar(60)		
F042V	总经理	varchar(60)		
F043V	公司独立董事(现任)	varchar(100)		多名
F044V	入选指数	varchar(1000)		多个
F045V	最新报告预约日期	varchar(50)		
F046V	保荐机构	varchar(500)		多个
F047V	主承销商	varchar(500)		
F048V	PEVC标记	varchar(12)		
F049V	注册国家	varchar(200)		
F050V	统一社会信用代码	varchar(60)		
F051V	工商ID	varchar(60)		
F052V	可转债	varchar(100)		
F053V	CDR	varchar(100)		
F054V	企业规模	varchar(20)	


新闻详情
API接口名称: p_comnewsinfo
URL接口名称: http://webapi.cninfo.com.cn/api/bigdata/p_comnewsinfo
请求方式方法: get,post
最大记录数: 20000
输入参数 :
英文名称	中文名称	类型	是否必填	说明
id	新闻id	string	是	
format	结果集格式	string	否	设置结果返回的格式，可选的有xml、json、csv、dbf
输出参数 :
英文名称	中文名称	类型	单位	说明
requestId	请求编号	String		
code	状态码	Number		
description	状态码描述	String		
timestamp	响应时间戳	String		
response	响应的结果集	Object		
page	页数	String		
total_page	总页数	String		
total	总数	String		
title	标题	string		
source	作者	varchar		
polarity	正负面(-2:确定负面，-1：疑似负面，0：中性， 1：疑似正面，2：确定正面)	number		
summary	摘要	string		
create_time	发布时间	string		
keywords	关键词	Object[]		
info_flag	来源	string		
url	原文url	string		
content	正文	mediumtext		
manager	相关人物	varchar		
companyname	相关企业	varchar




新闻列表
API接口名称: p_comnewslist
URL接口名称: http://webapi.cninfo.com.cn/api/bigdata/p_comnewslist
请求方式方法: get,post
最大记录数: 20000
输入参数 :
英文名称	中文名称	类型	是否必填	说明
cid	公司id	int	否	
sdate	开始日期	string	否	形如“2018-01-01”“”
edate	结束日期	string	否	形如“2018-01-01”“”
page	当前页码	int	否	
rows	每页条数	int	否	
cname	公司名	string	否	
key	查询词	string	否	
format	结果集格式	string	否	设置结果返回的格式，可选的有xml、json、csv、dbf
输出参数 :
英文名称	中文名称	类型	单位	说明
requestId	String	请求编号		
code	Number	状态码		
description	String	状态码描述		
timestamp	String	响应时间戳		
response	Object	响应的结果集		
page	String	页数		
total_page	String	总页数		
total	String	总数		
list	Object[]	数组		
id	number	新闻id		
title	string	标题		
polarity	number	正负面		(-2:确定负面，-1：疑似负面，0：中性， 1：疑似正面，2：确定正面)
create_time	string	发布时间		
keywords	Object[]	关键词		
info_flag	string	来源		(01新闻，02论坛，03博客，04微博，0401新浪微博，0402腾讯微博，05平媒，06微信，07视频，08长微博，09APP手机，10评论回复，99搜索)





新闻数据查询
API接口名称: p_info3030
URL接口名称: http://webapi.cninfo.com.cn/api/info/p_info3030
请求方式方法: get,post
最大记录数: 20000
输入参数 :
英文名称	中文名称	类型	是否必填	说明
scode	证券代码	string	否	scode和edate同时为空情况下，默认返回最近100条记录 Scode为证券代码
sdate	结束查询日期	string	否	支持格式示例：20230301 或2023-03-01 或2023/03/01
edate	结束查询日期	string	否	scode和edate同时为空情况下，默认返回最近100条记录 scode为空
stype	新闻分类编码	string	否	2701---证券；2702---公司； 2703---快讯；2704---产经
format	结果集格式	string	否	设置结果返回的格式，可选的有xml、json、csv、dbf
@column	结果列选择	string	否	选择结果集中所需要的字段，多列用逗号分隔，如@column=a,b
@limit	结果条数限制	int	否	设置结果返回的条数
@orderby	结果集排序	string	否	设置结果集的格式，如 @orderby=id:desc @orderby=id:asc
输出参数 :
英文名称	中文名称	类型	单位	说明
DECLAREDATE	发布时间	datetime		
TEXTID	新闻ID	numeric(12,0)		
SECCODE	证券代码	varchar(10)		
F001V	数据源	varchar(50)		
F002V	关键字	varchar(200)		
F003V	新闻分类	varchar(50)		
F004V	新闻标题	varchar(255)		
F005V	发布作者	varchar(255)		
F006V	S3链接	varchar(200)		
F007V	文件类型	varchar(20)		
F008V	S3链接	varchar(200)



新闻正文查询
API接口名称: p_info3031
URL接口名称: http://webapi.cninfo.com.cn/api/info/p_info3031
请求方式方法: get,post
最大记录数: 20000
输入参数 :
英文名称	中文名称	类型	是否必填	说明
newid	新闻ID	int	是	
format	结果集格式	string	否	设置结果返回的格式，可选的有xml、json、csv、dbf
输出参数 :
英文名称	中文名称	类型	单位	说明
NEWID	新闻ID	int		
CONTENT	正文	longtext




个股研报摘要
API接口名称: p_info3097_inc
URL接口名称: http://webapi.cninfo.com.cn/api/load/p_info3097_inc
请求方式方法: get,post
最大记录数: 20000
输入参数 :
英文名称	中文名称	类型	是否必填	说明
objectid	起始记录ID	int	是	每次下载数据时，都要记录最大的一个OBJECTID，下次调用时将保存的更新的最大OBJECTID传入取增量更新数据,第一次调用可以传入0
rowcount	返回记录条数	int	否	每次获取条数不能超过2000,默认为1000
format	结果集格式	string	否	设置结果返回的格式，可选的有xml、json、csv、dbf
@column	结果列选择	string	否	选择结果集中所需要的字段，多列用逗号分隔，如@column=a,b
@limit	结果条数限制	int	否	设置结果返回的条数
@orderby	结果集排序	string	否	设置结果集的格式，如 @orderby=id:desc @orderby=id:asc
输出参数 :
英文名称	中文名称	类型	单位	说明
SECCODE	证券代码	VARCHAR(10)		
SECNAME	证券简称	VARCHAR(20)		
F001D	资讯发布日期	DATETIME		
F002V	资讯标题	VARCHAR（400）		
F003V	资讯内容	VARCHAR（4000）		
F004V	研报发布机构	VARCHAR(200)		
F005D	研报发布日期	DATE		
F007V	资讯分类名称	VARCHAR(50)		
F009V	证券类别名称	VARCHAR(50)		
F011V	证券市场名称	VARCHAR(50)		
OBJECTID	OBJECTID	BIGINT		
CHANGE_CODE	操作标识	INT		1表示插入,2表示删除,3表示修改。 通过 记录唯一标识列：ROWKEY 做增删改操作。
ROWKEY	数据行键	VARCHAR(100)		数据唯一标识列，通过该值与目标表中记录比较做增删改操作



股票基本信息
API接口名称: p_stock2101
URL接口名称: http://webapi.cninfo.com.cn/api/stock/p_stock2101
请求方式方法: get,post
最大记录数: 20000
输入参数 :
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	否	输入不超过50只股票代码，用逗号分隔；如： 000001,600000
format	结果集格式	string	否	设置结果返回的格式，可选的有xml、json、csv、dbf
@column	结果列选择	string	否	选择结果集中所需要的字段，多列用逗号分隔，如@column=a,b
@limit	结果条数限制	int	否	设置结果返回的条数
@orderby	结果集排序	string	否	设置结果集的格式，如 @orderby=id:desc @orderby=id:asc
输出参数 :
英文名称	中文名称	类型	单位	说明
ORGNAME	机构名称	varchar		
SECCODE	证券代码	varchar		
SECNAME	证券简称	varchar		
F001V	拼音简称	varchar		
F002V	证券类别编码	varchar		
F003V	证券类别	varchar		
F004V	交易市场编码	varchar		
F005V	交易市场	varchar		
F006D	上市日期	datetime		
F007N	初始上市数量	decimal		单位：股
F008V	代码属性编码	varchar		
F009V	代码属性	varchar		
F010V	上市状态编码	varchar		
F011V	上市状态	varchar		
F012N	面值	decimal		单位：元
F013V	ISIN	varchar		



公司管理人员任职情况
API接口名称: p_stock2102
URL接口名称: http://webapi.cninfo.com.cn/api/stock/p_stock2102
请求方式方法: get,post
最大记录数: 20000
输入参数 :
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	是	输入不超过50只股票代码，用逗号分隔；如： 000001,600000
state	状态	int	否	为空则取数有数据，输入1则取最新一任期管理人员
format	结果集格式	string	否	设置结果返回的格式，可选的有xml、json、csv、dbf
@column	结果列选择	string	否	选择结果集中所需要的字段，多列用逗号分隔，如@column=a,b
@limit	结果条数限制	int	否	设置结果返回的条数
@orderby	结果集排序	string	否	设置结果集的格式，如 @orderby=id:desc @orderby=id:asc
输出参数 :
英文名称	中文名称	类型	单位	说明
ORGNAME	机构名称	VARCHAR		
SECCODE	证券代码	VARCHAR		
SECNAME	证券简称	VARCHAR		
DECLAREDATE	公告日期	DATE		
F001V	个人ID	VARCHAR		
F002V	姓名	VARCHAR		
F007D	任职日期	DATE		
F008D	离职日期	DATE		
F009V	职务名称	VARCHAR		
F010V	性别	VARCHAR		
F011V	教育程度	VARCHAR		
F012V	出生年份	VARCHAR		
F013V	国籍	VARCHAR		
F014V	职务类别编码	VARCHAR		
F015V	职务类别	VARCHAR		
F016V	职务编码	VARCHAR		
F017V	最高学历	VARCHAR		
F019V	个人简历	VARCHAR		
F020C	是否在职	char		0-否，1-是



公司上市状态变动情况表
API接口名称: p_stock2117
URL接口名称: http://webapi.cninfo.com.cn/api/stock/p_stock2117
请求方式方法: get,post
最大记录数: 20000
输入参数 :
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	否	股票代码
sign	上市状态	string	否	上市状态，须先访问公共信息中的公共编码数据（p_public0006）接口，令subtype=013，获取相应的上市状态编码
type	变更类型	string	否	变更类型，须先访问公共信息中的公共编码数据（p_public0006）接口，令subtype=031，获取变更类型编码
format	结果集格式	string	否	设置结果返回的格式，可选的有xml、json、csv、dbf
@column	结果列选择	string	否	选择结果集中所需要的字段，多列用逗号分隔，如@column=a,b
@limit	结果条数限制	int	否	设置结果返回的条数
@orderby	结果集排序	string	否	设置结果集的格式，如 @orderby=id:desc @orderby=id:asc
输出参数 :
英文名称	中文名称	类型	单位	说明
SECCODE	证券代码	varchar(10)		
SECNAME	证券简称	varchar(40)		
ORGNAME	机构名称	varchar(100)		
DECLAREDATE	公告日期	datetime		
VARYDATE	变更日期	date		
F002V	上市状态	varchar(60)		
F004V	变更原因	varchar(500)		
F006V	变更类型	varchar(60)



公司员工情况表
API接口名称: p_stock2107
URL接口名称: http://webapi.cninfo.com.cn/api/stock/p_stock2107
请求方式方法: get,post
最大记录数: 20000
输入参数 :
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	是	输入不超过50只股票代码，用逗号分隔；如： 000001,600000
sdate	开始日期	string	否	支持格式示例：20181101 或2018-11-01 或2018/11/01
edate	结束日期	string	否	支持格式示例：20181101 或2018-11-01 或2018/11/01
state	最新标识	string	否	当state=1取最新标识的所有数据
format	结果集格式	string	否	设置结果返回的格式，可选的有xml、json、csv、dbf
@column	结果列选择	string	否	选择结果集中所需要的字段，多列用逗号分隔，如@column=a,b
@limit	结果条数限制	int	否	设置结果返回的条数
@orderby	结果集排序	string	否	设置结果集的格式，如 @orderby=id:desc @orderby=id:asc
输出参数 :
英文名称	中文名称	类型	单位	说明
ORGID	公司ID	varchar(11)		
ORGNAME	公司名称	varchar(100)		
SECCODE	证券代码	varchar(10)		
SECNAME	证券简称	varchar(40)		
ENDDATE	截止日期	datetime		
DECLAREDATE	公告日期	datetime		程序自动默认为录入当日，可修改
STAFFNUM	员工总数	decimal(8)		单位:人;在职员工
F006C	最新记录标识	char(1)		0-否,1-是;程序自动根据截止日期判断,将最新一期记录设为1,其余设为0
F003N	博士人数	int		
F004N	硕士人数	int		
F005N	本科人数	int		
F007N	大专人数	int		
F008N	高中及以下人数(其他)	int		采集单独披露的高中及以下人数和其他分类，高中、中专、初中等分别披露时，加总采集
F009N	生产人员	int		
F010N	销售人员	int		
F011N	技术人员	int		
F012N	财务人员	int		
F013N	行政人员	int		
F014N	其他人员	int





公告基本信息
API接口名称: p_info3015
URL接口名称: http://webapi.cninfo.com.cn/api/info/p_info3015
请求方式方法: get,post
最大记录数: 1
输入参数 :
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	否	输入1个股票， scode和edate同时为空情况下，默认返回最近100条记录
sdate	开始查询时间	string	否	支持格式示例：20161101 或2016-11-01 或2016/11/01
edate	结束查询时间	string	否	scode和edate同时为空情况下，默认返回最近100条记录 scode为空,edate不为空时，取edate日期这一天数据
market	市场	string	否	上交所:012001 科创板:012029 深交所主板:012002 深交所创业板:012015
maxid	增量起始ID	int	否	用于增量提取数据使用
textid	正文ID	string	否	
page	page	int	否	
pagesize	pagesize	int	否	
format	结果集格式	string	否	设置结果返回的格式，可选的有xml、json、csv、dbf
@column	结果列选择	string	否	选择结果集中所需要的字段，多列用逗号分隔，如@column=a,b
@limit	结果条数限制	int	否	设置结果返回的条数
@orderby	结果集排序	string	否	设置结果集的格式，如 @orderby=id:desc @orderby=id:asc
输出参数 :
英文名称	中文名称	类型	单位	说明
TEXTID	正文ID	VARCHAR		
RECID	主体ID	VARCHAR		
SECCODE	证券代码	VARCHAR		
SECNAME	证券简称	VARCHAR		
F001D	公告日期	DATE		
F002V	公告标题	VARCHAR		
F003V	公告地址	VARCHAR		
F004V	公告格式	VARCHAR		
F005N	公告大小	DECIMAL		
F006V	信息分类	VARCHAR		
F007V	证券类别编码	VARCHAR		
F008V	证券类别名称	VARCHAR		
F009V	证券市场编码	VARCHAR		
F010V	证券市场名称	VARCHAR		
OBJECTID	OBJECTID	BIGINT		
RECTIME	发布时间	DATETIME



公告基本信息
API接口名称: p_info3015_client
URL接口名称: http://webapi.cninfo.com.cn/api/info/p_info3015_client
请求方式方法: get,post
最大记录数: 1
输入参数 :
英文名称	中文名称	类型	是否必填	说明
scode	股票代码	string	否	输入1个股票，为空时取结束日期当天的所有公告
sdate	开始查询时间	string	否	支持格式示例：20161101 或2016-11-01 或2016/11/01
edate	结束查询时间	string	否	股票代码参数为空时，取结束日期全部公告数据
market	市场	string	否	可多选 012001 上交所 012002 深交所主板 012003 012015 深交所创业板
maxid	增量起始ID	int	否	用于增量提取数据使用
textid	正文ID	int	否	可为空
page	page	int	否	
pagesize	pagesize	int	否	
format	结果集格式	string	否	设置结果返回的格式，可选的有xml、json、csv、dbf
@column	结果列选择	string	否	选择结果集中所需要的字段，多列用逗号分隔，如@column=a,b
@limit	结果条数限制	int	否	设置结果返回的条数
@orderby	结果集排序	string	否	设置结果集的格式，如 @orderby=id:desc @orderby=id:asc
输出参数 :
英文名称	中文名称	类型	单位	说明
TEXTID	正文ID	VARCHAR		
RECID	主体ID	VARCHAR		
SECCODE	证券代码	VARCHAR		
SECNAME	证券简称	VARCHAR		
F001D	公告日期	DATE		
F002V	公告标题	VARCHAR		
F003V	公告地址	VARCHAR		
F004V	公告格式	VARCHAR		
F005N	公告大小	DECIMAL		
F006V	信息分类	VARCHAR		
F007V	证券类别编码	VARCHAR		
F008V	证券类别名称	VARCHAR		
F009V	证券市场编码	VARCHAR		
F010V	证券市场名称	VARCHAR		
OBJECTID	OBJECTID	BIGINT		
RECTIME	发布时间	DATETIME		
F012V	ISIN	VARCHAR		
F013V	证券全称（英文）	VARCHAR		
F014V	证券全称（中文）	VARCHAR



{
    "total": 2134,
    "records": [
        {
            "SORTCODE": "0101",
            "SORTNAME": "发表公告机构",
            "F002D": null,
            "F001D": "2006-06-15 08:51:13",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "010101",
            "SORTNAME": "监管机构",
            "F002D": null,
            "F001D": "2006-06-15 08:51:14",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "01010101",
            "SORTNAME": "中国证监会",
            "F002D": null,
            "F001D": "2006-06-15 08:51:15",
            "PARENTCODE": "010101"
        },
        {
            "SORTCODE": "010103",
            "SORTNAME": "证券服务自律机构",
            "F002D": null,
            "F001D": "2006-06-15 08:51:16",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "01010301",
            "SORTNAME": "证券交易所",
            "F002D": null,
            "F001D": "2006-06-15 08:51:17",
            "PARENTCODE": "010103"
        },
        {
            "SORTCODE": "0101030101",
            "SORTNAME": "深圳证券交易所",
            "F002D": null,
            "F001D": "2006-06-15 08:51:18",
            "PARENTCODE": "01010301"
        },
        {
            "SORTCODE": "0101030103",
            "SORTNAME": "上海证券交易所",
            "F002D": null,
            "F001D": "2006-06-15 08:51:19",
            "PARENTCODE": "01010301"
        },
        {
            "SORTCODE": "0101030105",
            "SORTNAME": "香港联合交易所",
            "F002D": null,
            "F001D": "2008-07-07 10:56:36",
            "PARENTCODE": "01010301"
        },
        {
            "SORTCODE": "0101030107",
            "SORTNAME": "北京证券交易所",
            "F002D": null,
            "F001D": "2021-12-06 08:55:27",
            "PARENTCODE": "01010301"
        },
        {
            "SORTCODE": "01010303",
            "SORTNAME": "中国证券登记结算公司",
            "F002D": null,
            "F001D": "2006-06-15 08:51:20",
            "PARENTCODE": "010103"
        },
        {
            "SORTCODE": "01010305",
            "SORTNAME": "卫星通信公司",
            "F002D": null,
            "F001D": "2006-06-15 08:51:21",
            "PARENTCODE": "010103"
        },
        {
            "SORTCODE": "01010307",
            "SORTNAME": "中国证券业协会",
            "F002D": null,
            "F001D": "2006-06-15 08:51:22",
            "PARENTCODE": "010103"
        },
        {
            "SORTCODE": "01010309",
            "SORTNAME": "期货交易所",
            "F002D": null,
            "F001D": "2006-06-15 08:51:23",
            "PARENTCODE": "010103"
        },
        {
            "SORTCODE": "0101030901",
            "SORTNAME": "上海期货交易所",
            "F002D": null,
            "F001D": "2006-06-15 08:51:24",
            "PARENTCODE": "01010309"
        },
        {
            "SORTCODE": "0101030905",
            "SORTNAME": "大连商品交易所",
            "F002D": null,
            "F001D": "2006-06-15 08:51:25",
            "PARENTCODE": "01010309"
        },
        {
            "SORTCODE": "0101030910",
            "SORTNAME": "郑州商品交易所",
            "F002D": null,
            "F001D": "2006-06-15 08:51:26",
            "PARENTCODE": "01010309"
        },
        {
            "SORTCODE": "010105",
            "SORTNAME": "证券发行机构",
            "F002D": null,
            "F001D": "2006-06-15 08:51:27",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "01010501",
            "SORTNAME": "上市公司",
            "F002D": null,
            "F001D": "2006-06-15 08:51:28",
            "PARENTCODE": "010105"
        },
        {
            "SORTCODE": "01010503",
            "SORTNAME": "上市公司董事会",
            "F002D": null,
            "F001D": "2006-06-15 08:51:29",
            "PARENTCODE": "010105"
        },
        {
            "SORTCODE": "01010505",
            "SORTNAME": "上市公司监事会",
            "F002D": null,
            "F001D": "2006-06-15 08:51:30",
            "PARENTCODE": "010105"
        },
        {
            "SORTCODE": "01010507",
            "SORTNAME": "上市公司股东大会",
            "F002D": null,
            "F001D": "2006-06-15 08:51:31",
            "PARENTCODE": "010105"
        },
        {
            "SORTCODE": "01010509",
            "SORTNAME": "基金公司",
            "F002D": null,
            "F001D": "2006-06-15 08:51:32",
            "PARENTCODE": "010105"
        },
        {
            "SORTCODE": "0101050901",
            "SORTNAME": "深市封闭式基金",
            "F002D": null,
            "F001D": "2006-06-15 08:51:33",
            "PARENTCODE": "01010509"
        },
        {
            "SORTCODE": "0101050903",
            "SORTNAME": "沪市封闭式基金",
            "F002D": null,
            "F001D": "2006-06-15 08:51:34",
            "PARENTCODE": "01010509"
        },
        {
            "SORTCODE": "0101050905",
            "SORTNAME": "开放式基金",
            "F002D": null,
            "F001D": "2006-06-15 08:51:35",
            "PARENTCODE": "01010509"
        },
        {
            "SORTCODE": "0101050907",
            "SORTNAME": "深市LOF",
            "F002D": null,
            "F001D": "2006-06-15 08:51:36",
            "PARENTCODE": "01010509"
        },
        {
            "SORTCODE": "0101050909",
            "SORTNAME": "沪市LOF",
            "F002D": null,
            "F001D": "2006-06-15 08:51:37",
            "PARENTCODE": "01010509"
        },
        {
            "SORTCODE": "0101050911",
            "SORTNAME": "深市ETF",
            "F002D": null,
            "F001D": "2006-06-15 08:51:38",
            "PARENTCODE": "01010509"
        },
        {
            "SORTCODE": "0101050913",
            "SORTNAME": "沪市ETF",
            "F002D": null,
            "F001D": "2006-06-15 08:51:39",
            "PARENTCODE": "01010509"
        },
        {
            "SORTCODE": "0101050915",
            "SORTNAME": "QDII",
            "F002D": null,
            "F001D": "2010-11-01 09:13:11",
            "PARENTCODE": "01010509"
        },
        {
            "SORTCODE": "0101050916",
            "SORTNAME": "不动产基金",
            "F002D": null,
            "F001D": "2021-03-01 14:40:23",
            "PARENTCODE": "01010509"
        },
        {
            "SORTCODE": "0101050917",
            "SORTNAME": "乐富基金",
            "F002D": null,
            "F001D": "2011-02-25 09:20:34",
            "PARENTCODE": "01010509"
        },
        {
            "SORTCODE": "01010511",
            "SORTNAME": "债券发行主体",
            "F002D": null,
            "F001D": "2006-06-15 08:51:40",
            "PARENTCODE": "010105"
        },
        {
            "SORTCODE": "0101051101",
            "SORTNAME": "财政部",
            "F002D": null,
            "F001D": "2006-06-15 08:51:41",
            "PARENTCODE": "01010511"
        },
        {
            "SORTCODE": "0101051103",
            "SORTNAME": "地方政府财政厅（财政局）",
            "F002D": null,
            "F001D": "2009-06-22 16:26:32",
            "PARENTCODE": "01010511"
        },
        {
            "SORTCODE": "0101051105",
            "SORTNAME": "中国人民银行",
            "F002D": null,
            "F001D": "2006-06-15 08:51:42",
            "PARENTCODE": "01010511"
        },
        {
            "SORTCODE": "0101051110",
            "SORTNAME": "国家开发银行",
            "F002D": null,
            "F001D": "2006-06-15 08:51:43",
            "PARENTCODE": "01010511"
        },
        {
            "SORTCODE": "0101051113",
            "SORTNAME": "中国农业银行",
            "F002D": null,
            "F001D": "2008-07-07 11:07:43",
            "PARENTCODE": "01010511"
        },
        {
            "SORTCODE": "0101051115",
            "SORTNAME": "中国进出口银行",
            "F002D": null,
            "F001D": "2008-07-07 11:09:42",
            "PARENTCODE": "01010511"
        },
        {
            "SORTCODE": "0101051199",
            "SORTNAME": "其它发行主体",
            "F002D": null,
            "F001D": "2006-06-15 08:51:44",
            "PARENTCODE": "01010511"
        },
        {
            "SORTCODE": "01010513",
            "SORTNAME": "代办股份转让公司",
            "F002D": null,
            "F001D": "2006-06-15 08:51:45",
            "PARENTCODE": "010105"
        },
        {
            "SORTCODE": "01010517",
            "SORTNAME": "香港上市公司",
            "F002D": null,
            "F001D": "2006-06-15 08:51:46",
            "PARENTCODE": "010105"
        },
        {
            "SORTCODE": "0101051701",
            "SORTNAME": "主板上市公司",
            "F002D": "2008-07-07 11:11:14",
            "F001D": "2006-06-15 08:51:47",
            "PARENTCODE": "01010517"
        },
        {
            "SORTCODE": "0101051703",
            "SORTNAME": "创业板上市公司",
            "F002D": "2008-07-07 11:11:26",
            "F001D": "2006-06-15 08:51:48",
            "PARENTCODE": "01010517"
        },
        {
            "SORTCODE": "01010519",
            "SORTNAME": "中关村股份报价转让公司",
            "F002D": null,
            "F001D": "2006-06-15 08:51:49",
            "PARENTCODE": "010105"
        },
        {
            "SORTCODE": "01010521",
            "SORTNAME": "中证指数有限公司",
            "F002D": null,
            "F001D": "2008-07-07 11:05:58",
            "PARENTCODE": "010105"
        },
        {
            "SORTCODE": "010107",
            "SORTNAME": "证券经营机构",
            "F002D": null,
            "F001D": "2006-06-15 08:51:50",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "01010701",
            "SORTNAME": "证券公司（承销商或保荐人）",
            "F002D": null,
            "F001D": "2006-06-15 08:51:51",
            "PARENTCODE": "010107"
        },
        {
            "SORTCODE": "01010703",
            "SORTNAME": "证券公司（主办券商）",
            "F002D": null,
            "F001D": "2015-01-06 17:23:27",
            "PARENTCODE": "010107"
        },
        {
            "SORTCODE": "010109",
            "SORTNAME": "证券中介机构",
            "F002D": null,
            "F001D": "2006-06-15 08:51:53",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "01010901",
            "SORTNAME": "律师事务所",
            "F002D": null,
            "F001D": "2006-06-15 08:51:54",
            "PARENTCODE": "010109"
        },
        {
            "SORTCODE": "01010903",
            "SORTNAME": "会计师事务所",
            "F002D": null,
            "F001D": "2006-06-15 08:51:55",
            "PARENTCODE": "010109"
        },
        {
            "SORTCODE": "01010905",
            "SORTNAME": "证券投资咨询公司",
            "F002D": null,
            "F001D": "2006-06-15 08:51:56",
            "PARENTCODE": "010109"
        },
        {
            "SORTCODE": "01010907",
            "SORTNAME": "资信评估机构",
            "F002D": null,
            "F001D": "2006-06-15 08:51:57",
            "PARENTCODE": "010109"
        },
        {
            "SORTCODE": "01010909",
            "SORTNAME": "资产评估机构",
            "F002D": null,
            "F001D": "2006-06-15 08:52:01",
            "PARENTCODE": "010109"
        },
        {
            "SORTCODE": "01010911",
            "SORTNAME": "基金托管人",
            "F002D": null,
            "F001D": "2006-06-15 08:52:02",
            "PARENTCODE": "010109"
        },
        {
            "SORTCODE": "010110",
            "SORTNAME": "产交所挂牌公司",
            "F002D": null,
            "F001D": "2006-08-14 15:30:24",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "01011001",
            "SORTNAME": "四川省产权交易所公司",
            "F002D": null,
            "F001D": "2006-08-14 15:31:03",
            "PARENTCODE": "010110"
        },
        {
            "SORTCODE": "010111",
            "SORTNAME": "其它机构或个人",
            "F002D": null,
            "F001D": "2006-06-15 08:52:03",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "01011101",
            "SORTNAME": "公司大股东",
            "F002D": null,
            "F001D": "2006-06-15 08:52:04",
            "PARENTCODE": "010111"
        },
        {
            "SORTCODE": "01011103",
            "SORTNAME": "董事个人",
            "F002D": null,
            "F001D": "2006-06-15 08:52:05",
            "PARENTCODE": "010111"
        },
        {
            "SORTCODE": "01011105",
            "SORTNAME": "监事个人",
            "F002D": null,
            "F001D": "2006-06-15 08:52:06",
            "PARENTCODE": "010111"
        },
        {
            "SORTCODE": "01011107",
            "SORTNAME": "独立董事个人",
            "F002D": null,
            "F001D": "2006-06-15 08:52:07",
            "PARENTCODE": "010111"
        },
        {
            "SORTCODE": "01011109",
            "SORTNAME": "收购方",
            "F002D": null,
            "F001D": "2006-06-15 08:52:08",
            "PARENTCODE": "010111"
        },
        {
            "SORTCODE": "01011111",
            "SORTNAME": "独立的第三方",
            "F002D": null,
            "F001D": "2006-06-15 08:52:09",
            "PARENTCODE": "010111"
        },
        {
            "SORTCODE": "01011113",
            "SORTNAME": "基金持有人",
            "F002D": null,
            "F001D": "2006-06-15 08:52:10",
            "PARENTCODE": "010111"
        },
        {
            "SORTCODE": "01011115",
            "SORTNAME": "基金持有人大会",
            "F002D": null,
            "F001D": "2006-06-15 08:52:11",
            "PARENTCODE": "010111"
        },
        {
            "SORTCODE": "01011199",
            "SORTNAME": "其它信息披露主体",
            "F002D": null,
            "F001D": "2006-06-15 08:52:12",
            "PARENTCODE": "010111"
        },
        {
            "SORTCODE": "010112",
            "SORTNAME": "深市公司公告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:13",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "010113",
            "SORTNAME": "沪市主板公告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:14",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "010114",
            "SORTNAME": "中小企业板公司公告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:15",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "010115",
            "SORTNAME": "创业板公司公告",
            "F002D": null,
            "F001D": "2008-03-24 14:04:16",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "010116",
            "SORTNAME": "拟上市公司公告",
            "F002D": null,
            "F001D": "2008-03-27 09:15:39",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "010117",
            "SORTNAME": "深市债券公告",
            "F002D": null,
            "F001D": "2009-06-15 16:27:51",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "010118",
            "SORTNAME": "沪市债券公告",
            "F002D": null,
            "F001D": "2009-06-15 16:28:11",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "010119",
            "SORTNAME": "深市权证公告",
            "F002D": null,
            "F001D": "2009-10-09 12:46:56",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "010120",
            "SORTNAME": "沪市权证公告",
            "F002D": null,
            "F001D": "2009-10-09 12:47:09",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "010123",
            "SORTNAME": "科创板公司公告",
            "F002D": null,
            "F001D": "2019-05-15 08:55:27",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "010124",
            "SORTNAME": "深市主板注册制",
            "F002D": null,
            "F001D": "2023-05-08 15:31:45",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "01012401",
            "SORTNAME": "深市主板IPO公告",
            "F002D": null,
            "F001D": "2023-05-08 15:31:45",
            "PARENTCODE": "010124"
        },
        {
            "SORTCODE": "01012403",
            "SORTNAME": "深市主板再融资公告",
            "F002D": null,
            "F001D": "2023-05-08 15:31:45",
            "PARENTCODE": "010124"
        },
        {
            "SORTCODE": "01012405",
            "SORTNAME": "深市主板重大资产重组公告",
            "F002D": null,
            "F001D": "2023-05-08 15:31:45",
            "PARENTCODE": "010124"
        },
        {
            "SORTCODE": "01012407",
            "SORTNAME": "深市主板转板上市公告",
            "F002D": null,
            "F001D": "2023-05-08 15:31:46",
            "PARENTCODE": "010124"
        },
        {
            "SORTCODE": "010125",
            "SORTNAME": "深市创业板注册制",
            "F002D": null,
            "F001D": "2020-07-07 15:05:56",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "01012501",
            "SORTNAME": "深市创业板IPO公告",
            "F002D": null,
            "F001D": "2020-07-07 15:05:57",
            "PARENTCODE": "010125"
        },
        {
            "SORTCODE": "01012503",
            "SORTNAME": "深市创业板再融资公告",
            "F002D": null,
            "F001D": "2020-07-07 15:05:57",
            "PARENTCODE": "010125"
        },
        {
            "SORTCODE": "01012505",
            "SORTNAME": "深市创业板重大资产重组公告",
            "F002D": null,
            "F001D": "2020-07-07 15:05:57",
            "PARENTCODE": "010125"
        },
        {
            "SORTCODE": "01012507",
            "SORTNAME": "深市创业板转板上市公告",
            "F002D": null,
            "F001D": "2022-02-22 08:55:27",
            "PARENTCODE": "010125"
        },
        {
            "SORTCODE": "010126",
            "SORTNAME": "沪市主板注册制",
            "F002D": null,
            "F001D": "2023-05-08 15:31:46",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "01012601",
            "SORTNAME": "沪市主板IPO公告",
            "F002D": null,
            "F001D": "2023-05-08 15:31:46",
            "PARENTCODE": "010126"
        },
        {
            "SORTCODE": "01012603",
            "SORTNAME": "沪市主板并购重组公告",
            "F002D": null,
            "F001D": "2023-05-08 15:31:46",
            "PARENTCODE": "010126"
        },
        {
            "SORTCODE": "01012605",
            "SORTNAME": "沪市主板再融资公告",
            "F002D": null,
            "F001D": "2023-05-08 15:31:46",
            "PARENTCODE": "010126"
        },
        {
            "SORTCODE": "01012607",
            "SORTNAME": "沪市主板转板上市公告",
            "F002D": null,
            "F001D": "2023-05-08 15:31:46",
            "PARENTCODE": "010126"
        },
        {
            "SORTCODE": "010127",
            "SORTNAME": "沪市科创板注册制",
            "F002D": null,
            "F001D": "2020-07-07 15:05:57",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "01012701",
            "SORTNAME": "沪市科创板IPO公告",
            "F002D": null,
            "F001D": "2020-07-07 15:05:57",
            "PARENTCODE": "010127"
        },
        {
            "SORTCODE": "01012703",
            "SORTNAME": "沪市科创板并购重组公告",
            "F002D": null,
            "F001D": "2020-07-07 15:05:57",
            "PARENTCODE": "010127"
        },
        {
            "SORTCODE": "01012705",
            "SORTNAME": "沪市科创板再融资公告",
            "F002D": null,
            "F001D": "2021-06-12 09:38:50",
            "PARENTCODE": "010127"
        },
        {
            "SORTCODE": "01012707",
            "SORTNAME": "沪市科创板转板上市公告",
            "F002D": null,
            "F001D": "2022-02-22 08:55:27",
            "PARENTCODE": "010127"
        },
        {
            "SORTCODE": "010129",
            "SORTNAME": "北交所公司公告",
            "F002D": null,
            "F001D": "2021-12-06 08:55:27",
            "PARENTCODE": "0101"
        },
        {
            "SORTCODE": "0102",
            "SORTNAME": "首次公开发行及上市",
            "F002D": null,
            "F001D": "2006-06-15 08:52:16",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "010201",
            "SORTNAME": "发行获准公告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:17",
            "PARENTCODE": "0102"
        },
        {
            "SORTCODE": "010203",
            "SORTNAME": "招股说明书",
            "F002D": null,
            "F001D": "2006-06-15 08:52:18",
            "PARENTCODE": "0102"
        },
        {
            "SORTCODE": "01020301",
            "SORTNAME": "招股说明书全文",
            "F002D": null,
            "F001D": "2006-06-15 08:52:19",
            "PARENTCODE": "010203"
        },
        {
            "SORTCODE": "01020303",
            "SORTNAME": "招股意向书全文",
            "F002D": null,
            "F001D": "2008-07-07 11:13:47",
            "PARENTCODE": "010203"
        },
        {
            "SORTCODE": "01020320",
            "SORTNAME": "招股说明书摘要",
            "F002D": null,
            "F001D": "2006-06-15 08:52:20",
            "PARENTCODE": "010203"
        },
        {
            "SORTCODE": "01020321",
            "SORTNAME": "招股意向书摘要",
            "F002D": null,
            "F001D": "2008-07-07 11:14:37",
            "PARENTCODE": "010203"
        },
        {
            "SORTCODE": "010205",
            "SORTNAME": "发行公告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:21",
            "PARENTCODE": "0102"
        },
        {
            "SORTCODE": "01020501",
            "SORTNAME": "网下配售和网上定价发行公告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:22",
            "PARENTCODE": "010205"
        },
        {
            "SORTCODE": "01020510",
            "SORTNAME": "网下发行公告",
            "F002D": null,
            "F001D": "2009-07-17 19:16:16",
            "PARENTCODE": "010205"
        },
        {
            "SORTCODE": "01020520",
            "SORTNAME": "网上网下发行公告",
            "F002D": null,
            "F001D": "2009-07-17 19:16:23",
            "PARENTCODE": "010205"
        },
        {
            "SORTCODE": "010207",
            "SORTNAME": "发行提示性公告",
            "F002D": null,
            "F001D": "2009-07-17 19:17:49",
            "PARENTCODE": "0102"
        },
        {
            "SORTCODE": "010209",
            "SORTNAME": "发行价格确定公告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:26",
            "PARENTCODE": "0102"
        },
        {
            "SORTCODE": "01020901",
            "SORTNAME": "发行定价公告",
            "F002D": null,
            "F001D": "2009-07-17 19:19:17",
            "PARENTCODE": "010209"
        },
        {
            "SORTCODE": "01020910",
            "SORTNAME": "初步询价及推介公告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:28",
            "PARENTCODE": "010209"
        },
        {
            "SORTCODE": "01020920",
            "SORTNAME": "询价区间公告",
            "F002D": null,
            "F001D": "2009-07-17 19:20:09",
            "PARENTCODE": "010209"
        },
        {
            "SORTCODE": "01020930",
            "SORTNAME": "初步询价结果及定价公告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:30",
            "PARENTCODE": "010209"
        },
        {
            "SORTCODE": "010211",
            "SORTNAME": "发行结果公告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:31",
            "PARENTCODE": "0102"
        },
        {
            "SORTCODE": "01021101",
            "SORTNAME": "发行中签率(结果)公告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:32",
            "PARENTCODE": "010211"
        },
        {
            "SORTCODE": "01021110",
            "SORTNAME": "网下配售结果公告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:33",
            "PARENTCODE": "010211"
        },
        {
            "SORTCODE": "01021120",
            "SORTNAME": "摇号结果公告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:34",
            "PARENTCODE": "010211"
        },
        {
            "SORTCODE": "010213",
            "SORTNAME": "上市公告书",
            "F002D": null,
            "F001D": "2006-06-15 08:52:35",
            "PARENTCODE": "0102"
        },
        {
            "SORTCODE": "010215",
            "SORTNAME": "首次发行配套文件",
            "F002D": null,
            "F001D": "2006-06-15 08:52:36",
            "PARENTCODE": "0102"
        },
        {
            "SORTCODE": "010299",
            "SORTNAME": "其它发行事项公告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:37",
            "PARENTCODE": "0102"
        },
        {
            "SORTCODE": "01029901",
            "SORTNAME": "网上路演推介公告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:38",
            "PARENTCODE": "010299"
        },
        {
            "SORTCODE": "01029910",
            "SORTNAME": "公司成立公告",
            "F002D": null,
            "F001D": "2009-07-17 19:25:59",
            "PARENTCODE": "010299"
        },
        {
            "SORTCODE": "0103",
            "SORTNAME": "定期报告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:40",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "010301",
            "SORTNAME": "年度报告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:41",
            "PARENTCODE": "0103"
        },
        {
            "SORTCODE": "01030101",
            "SORTNAME": "年度报告正文",
            "F002D": null,
            "F001D": "2006-06-15 08:52:42",
            "PARENTCODE": "010301"
        },
        {
            "SORTCODE": "01030110",
            "SORTNAME": "年度报告摘要",
            "F002D": null,
            "F001D": "2006-06-15 08:52:43",
            "PARENTCODE": "010301"
        },
        {
            "SORTCODE": "01030120",
            "SORTNAME": "年报英文",
            "F002D": null,
            "F001D": "2006-06-15 08:52:44",
            "PARENTCODE": "010301"
        },
        {
            "SORTCODE": "01030130",
            "SORTNAME": "年报补充报告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:45",
            "PARENTCODE": "010301"
        },
        {
            "SORTCODE": "01030140",
            "SORTNAME": "年报更正报告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:46",
            "PARENTCODE": "010301"
        },
        {
            "SORTCODE": "010303",
            "SORTNAME": "半年度报告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:47",
            "PARENTCODE": "0103"
        },
        {
            "SORTCODE": "01030301",
            "SORTNAME": "半年度报告正文",
            "F002D": null,
            "F001D": "2006-06-15 08:52:48",
            "PARENTCODE": "010303"
        },
        {
            "SORTCODE": "01030310",
            "SORTNAME": "半年度报告摘要",
            "F002D": null,
            "F001D": "2006-06-15 08:52:49",
            "PARENTCODE": "010303"
        },
        {
            "SORTCODE": "01030320",
            "SORTNAME": "半年报英文",
            "F002D": null,
            "F001D": "2006-06-15 08:52:50",
            "PARENTCODE": "010303"
        },
        {
            "SORTCODE": "01030330",
            "SORTNAME": "半年报补充报告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:51",
            "PARENTCODE": "010303"
        },
        {
            "SORTCODE": "01030340",
            "SORTNAME": "半年报更正报告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:52",
            "PARENTCODE": "010303"
        },
        {
            "SORTCODE": "010305",
            "SORTNAME": "一季度报告",
            "F002D": null,
            "F001D": "2006-06-15 08:52:53",
            "PARENTCODE": "0103"
        },
        {
            "SORTCODE": "01030501",
            "SORTNAME": "一季度报告正文",
            "F002D": null,
            "F001D": "2006-06-15 08:53:01",
            "PARENTCODE": "010305"
        },
        {
            "SORTCODE": "01030510",
            "SORTNAME": "一季度报告摘要",
            "F002D": null,
            "F001D": "2006-06-15 08:53:02",
            "PARENTCODE": "010305"
        },
        {
            "SORTCODE": "01030520",
            "SORTNAME": "一季度报报英文",
            "F002D": null,
            "F001D": "2006-06-15 08:53:03",
            "PARENTCODE": "010305"
        },
        {
            "SORTCODE": "01030530",
            "SORTNAME": "一季度报告补充报告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:04",
            "PARENTCODE": "010305"
        },
        {
            "SORTCODE": "01030540",
            "SORTNAME": "一季度报告更正报告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:05",
            "PARENTCODE": "010305"
        },
        {
            "SORTCODE": "010307",
            "SORTNAME": "三季度报告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:06",
            "PARENTCODE": "0103"
        },
        {
            "SORTCODE": "01030701",
            "SORTNAME": "三季度报告正文",
            "F002D": null,
            "F001D": "2006-06-15 08:53:07",
            "PARENTCODE": "010307"
        },
        {
            "SORTCODE": "01030710",
            "SORTNAME": "三季度报告摘要",
            "F002D": null,
            "F001D": "2006-06-15 08:53:08",
            "PARENTCODE": "010307"
        },
        {
            "SORTCODE": "01030720",
            "SORTNAME": "三季度报报英文",
            "F002D": null,
            "F001D": "2006-06-15 08:53:09",
            "PARENTCODE": "010307"
        },
        {
            "SORTCODE": "01030730",
            "SORTNAME": "三季度报告补充报告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:10",
            "PARENTCODE": "010307"
        },
        {
            "SORTCODE": "01030740",
            "SORTNAME": "三季度报告更正报告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:11",
            "PARENTCODE": "010307"
        },
        {
            "SORTCODE": "010309",
            "SORTNAME": "经营报告",
            "F002D": "2013-08-21 15:16:53",
            "F001D": "2006-06-15 08:53:12",
            "PARENTCODE": "0103"
        },
        {
            "SORTCODE": "0105",
            "SORTNAME": "配股",
            "F002D": null,
            "F001D": "2006-06-15 08:53:13",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "010501",
            "SORTNAME": "配股预案",
            "F002D": null,
            "F001D": "2006-06-15 08:53:14",
            "PARENTCODE": "0105"
        },
        {
            "SORTCODE": "01050101",
            "SORTNAME": "配股初次预案",
            "F002D": null,
            "F001D": "2006-06-15 08:53:15",
            "PARENTCODE": "010501"
        },
        {
            "SORTCODE": "01050110",
            "SORTNAME": "配股预案修改",
            "F002D": null,
            "F001D": "2006-06-15 08:53:16",
            "PARENTCODE": "010501"
        },
        {
            "SORTCODE": "01050120",
            "SORTNAME": "配发议案取消",
            "F002D": null,
            "F001D": "2006-06-15 08:53:17",
            "PARENTCODE": "010501"
        },
        {
            "SORTCODE": "010503",
            "SORTNAME": "配股获准公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:18",
            "PARENTCODE": "0105"
        },
        {
            "SORTCODE": "010505",
            "SORTNAME": "配股说明书",
            "F002D": null,
            "F001D": "2006-06-15 08:53:19",
            "PARENTCODE": "0105"
        },
        {
            "SORTCODE": "010507",
            "SORTNAME": "配股提示性公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:20",
            "PARENTCODE": "0105"
        },
        {
            "SORTCODE": "010509",
            "SORTNAME": "股份变动及配股上市公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:21",
            "PARENTCODE": "0105"
        },
        {
            "SORTCODE": "010511",
            "SORTNAME": "配股发行结果公告",
            "F002D": null,
            "F001D": "2008-05-14 16:37:45",
            "PARENTCODE": "0105"
        },
        {
            "SORTCODE": "0107",
            "SORTNAME": "增发",
            "F002D": null,
            "F001D": "2006-06-15 08:53:22",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "010701",
            "SORTNAME": "增发预案",
            "F002D": null,
            "F001D": "2006-06-15 08:53:23",
            "PARENTCODE": "0107"
        },
        {
            "SORTCODE": "01070101",
            "SORTNAME": "增发初次预案",
            "F002D": null,
            "F001D": "2006-06-15 08:53:24",
            "PARENTCODE": "010701"
        },
        {
            "SORTCODE": "01070110",
            "SORTNAME": "增发预案修改",
            "F002D": null,
            "F001D": "2006-06-15 08:53:25",
            "PARENTCODE": "010701"
        },
        {
            "SORTCODE": "01070120",
            "SORTNAME": "增发议案取消",
            "F002D": null,
            "F001D": "2006-06-15 08:53:26",
            "PARENTCODE": "010701"
        },
        {
            "SORTCODE": "010703",
            "SORTNAME": "增发获准公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:27",
            "PARENTCODE": "0107"
        },
        {
            "SORTCODE": "010704",
            "SORTNAME": "增发未获准公告",
            "F002D": null,
            "F001D": "2007-01-30 10:22:44",
            "PARENTCODE": "0107"
        },
        {
            "SORTCODE": "010705",
            "SORTNAME": "增发说明书",
            "F002D": null,
            "F001D": "2006-06-15 08:53:28",
            "PARENTCODE": "0107"
        },
        {
            "SORTCODE": "010707",
            "SORTNAME": "发行公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:29",
            "PARENTCODE": "0107"
        },
        {
            "SORTCODE": "01070701",
            "SORTNAME": "网上发行公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:30",
            "PARENTCODE": "010707"
        },
        {
            "SORTCODE": "01070710",
            "SORTNAME": "网下发行公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:31",
            "PARENTCODE": "010707"
        },
        {
            "SORTCODE": "01070720",
            "SORTNAME": "机构投资者预约公告",
            "F002D": null,
            "F001D": "2009-07-17 19:23:19",
            "PARENTCODE": "010707"
        },
        {
            "SORTCODE": "010709",
            "SORTNAME": "询价区间公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:33",
            "PARENTCODE": "0107"
        },
        {
            "SORTCODE": "010711",
            "SORTNAME": "增发结果公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:34",
            "PARENTCODE": "0107"
        },
        {
            "SORTCODE": "01071101",
            "SORTNAME": "增发结果公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:35",
            "PARENTCODE": "010711"
        },
        {
            "SORTCODE": "01071103",
            "SORTNAME": "增发中签率公告",
            "F002D": null,
            "F001D": "2008-05-14 16:36:46",
            "PARENTCODE": "010711"
        },
        {
            "SORTCODE": "01071110",
            "SORTNAME": "增发余额包销公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:36",
            "PARENTCODE": "010711"
        },
        {
            "SORTCODE": "010713",
            "SORTNAME": "增发上市",
            "F002D": null,
            "F001D": "2006-06-15 08:53:37",
            "PARENTCODE": "0107"
        },
        {
            "SORTCODE": "01071301",
            "SORTNAME": "股份变动及增发上市公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:38",
            "PARENTCODE": "010713"
        },
        {
            "SORTCODE": "010715",
            "SORTNAME": "增发配套文件",
            "F002D": null,
            "F001D": "2006-06-15 08:53:39",
            "PARENTCODE": "0107"
        },
        {
            "SORTCODE": "010799",
            "SORTNAME": "增发其它公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:40",
            "PARENTCODE": "0107"
        },
        {
            "SORTCODE": "01079901",
            "SORTNAME": "增发路演推介公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:41",
            "PARENTCODE": "010799"
        },
        {
            "SORTCODE": "01079999",
            "SORTNAME": "其它增发事项公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:42",
            "PARENTCODE": "010799"
        },
        {
            "SORTCODE": "0109",
            "SORTNAME": "可转换债券",
            "F002D": null,
            "F001D": "2006-06-15 08:53:43",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "010901",
            "SORTNAME": "可转债发行预案",
            "F002D": null,
            "F001D": "2006-06-15 08:53:44",
            "PARENTCODE": "0109"
        },
        {
            "SORTCODE": "01090101",
            "SORTNAME": "可转债发行初次预案",
            "F002D": null,
            "F001D": "2006-06-15 08:53:45",
            "PARENTCODE": "010901"
        },
        {
            "SORTCODE": "01090110",
            "SORTNAME": "可转债发行预案修改",
            "F002D": null,
            "F001D": "2006-06-15 08:53:46",
            "PARENTCODE": "010901"
        },
        {
            "SORTCODE": "01090120",
            "SORTNAME": "可转债发行议案取消",
            "F002D": null,
            "F001D": "2006-06-15 08:53:47",
            "PARENTCODE": "010901"
        },
        {
            "SORTCODE": "010903",
            "SORTNAME": "可转债发行获准公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:48",
            "PARENTCODE": "0109"
        },
        {
            "SORTCODE": "010905",
            "SORTNAME": "可转债募集说明书",
            "F002D": null,
            "F001D": "2006-06-15 08:53:49",
            "PARENTCODE": "0109"
        },
        {
            "SORTCODE": "010907",
            "SORTNAME": "可转债发行公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:50",
            "PARENTCODE": "0109"
        },
        {
            "SORTCODE": "01090701",
            "SORTNAME": "可转债网上发行公告",
            "F002D": null,
            "F001D": "2009-07-17 19:29:08",
            "PARENTCODE": "010907"
        },
        {
            "SORTCODE": "01090710",
            "SORTNAME": "可转债网下发行公告",
            "F002D": null,
            "F001D": "2009-07-17 19:29:25",
            "PARENTCODE": "010907"
        },
        {
            "SORTCODE": "01090720",
            "SORTNAME": "可转债网上（下）发行公告",
            "F002D": null,
            "F001D": "2009-07-17 19:29:32",
            "PARENTCODE": "010907"
        },
        {
            "SORTCODE": "010909",
            "SORTNAME": "可转债发行提示公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:54",
            "PARENTCODE": "0109"
        },
        {
            "SORTCODE": "010911",
            "SORTNAME": "可转债发行结果公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:55",
            "PARENTCODE": "0109"
        },
        {
            "SORTCODE": "01091101",
            "SORTNAME": "可转债中签结果公告",
            "F002D": null,
            "F001D": "2009-07-17 19:31:01",
            "PARENTCODE": "010911"
        },
        {
            "SORTCODE": "01091110",
            "SORTNAME": "可转债其它发行结果公告",
            "F002D": null,
            "F001D": "2009-07-17 19:31:07",
            "PARENTCODE": "010911"
        },
        {
            "SORTCODE": "010913",
            "SORTNAME": "可转债上市公告",
            "F002D": null,
            "F001D": "2006-06-15 08:53:58",
            "PARENTCODE": "0109"
        },
        {
            "SORTCODE": "010915",
            "SORTNAME": "转股事项",
            "F002D": null,
            "F001D": "2006-06-15 08:53:59",
            "PARENTCODE": "0109"
        },
        {
            "SORTCODE": "01091501",
            "SORTNAME": "可转债开始转股的公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:01",
            "PARENTCODE": "010915"
        },
        {
            "SORTCODE": "01091510",
            "SORTNAME": "可转债每季度转股情况的公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:02",
            "PARENTCODE": "010915"
        },
        {
            "SORTCODE": "01091520",
            "SORTNAME": "可转债停止转股的公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:03",
            "PARENTCODE": "010915"
        },
        {
            "SORTCODE": "01091530",
            "SORTNAME": "可转债调整转股价格的公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:04",
            "PARENTCODE": "010915"
        },
        {
            "SORTCODE": "01091540",
            "SORTNAME": "可转债停止交易的公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:05",
            "PARENTCODE": "010915"
        },
        {
            "SORTCODE": "010917",
            "SORTNAME": "回售事项",
            "F002D": null,
            "F001D": "2006-06-15 08:54:06",
            "PARENTCODE": "0109"
        },
        {
            "SORTCODE": "01091701",
            "SORTNAME": "可转债回售公告",
            "F002D": "2008-07-07 11:18:36",
            "F001D": "2006-06-15 08:54:07",
            "PARENTCODE": "010917"
        },
        {
            "SORTCODE": "01091710",
            "SORTNAME": "可转债回售结果公告",
            "F002D": "2008-07-07 11:18:44",
            "F001D": "2006-06-15 08:54:08",
            "PARENTCODE": "010917"
        },
        {
            "SORTCODE": "010919",
            "SORTNAME": "赎回事项",
            "F002D": null,
            "F001D": "2006-06-15 08:54:09",
            "PARENTCODE": "0109"
        },
        {
            "SORTCODE": "01091901",
            "SORTNAME": "可转债赎回公告",
            "F002D": null,
            "F001D": "2015-01-06 17:23:02",
            "PARENTCODE": "010919"
        },
        {
            "SORTCODE": "01091910",
            "SORTNAME": "可转债赎回结果公告",
            "F002D": null,
            "F001D": "2015-01-06 17:23:10",
            "PARENTCODE": "010919"
        },
        {
            "SORTCODE": "010921",
            "SORTNAME": "付息事项",
            "F002D": null,
            "F001D": "2006-06-15 08:54:12",
            "PARENTCODE": "0109"
        },
        {
            "SORTCODE": "01092101",
            "SORTNAME": "可转债付息公告",
            "F002D": "2008-07-07 11:19:13",
            "F001D": "2006-06-15 08:54:13",
            "PARENTCODE": "010921"
        },
        {
            "SORTCODE": "010923",
            "SORTNAME": "可转债发行配套文件",
            "F002D": null,
            "F001D": "2006-06-15 08:54:14",
            "PARENTCODE": "0109"
        },
        {
            "SORTCODE": "010999",
            "SORTNAME": "可转债其它公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:15",
            "PARENTCODE": "0109"
        },
        {
            "SORTCODE": "01099901",
            "SORTNAME": "可转债路演推介公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:16",
            "PARENTCODE": "010999"
        },
        {
            "SORTCODE": "01099999",
            "SORTNAME": "可转债其它事项公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:17",
            "PARENTCODE": "010999"
        },
        {
            "SORTCODE": "0110",
            "SORTNAME": "权证相关公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:18",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "011001",
            "SORTNAME": "权证公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:19",
            "PARENTCODE": "0110"
        },
        {
            "SORTCODE": "01100101",
            "SORTNAME": "权证创设公告",
            "F002D": null,
            "F001D": "2008-07-07 11:27:21",
            "PARENTCODE": "011001"
        },
        {
            "SORTCODE": "01100103",
            "SORTNAME": "权证注销公告",
            "F002D": null,
            "F001D": "2008-07-07 11:27:36",
            "PARENTCODE": "011001"
        },
        {
            "SORTCODE": "011003",
            "SORTNAME": "权证交易公开信息",
            "F002D": null,
            "F001D": "2006-06-15 08:54:20",
            "PARENTCODE": "0110"
        },
        {
            "SORTCODE": "011005",
            "SORTNAME": "权证超比例持有人信息",
            "F002D": null,
            "F001D": "2006-06-15 08:54:21",
            "PARENTCODE": "0110"
        },
        {
            "SORTCODE": "011007",
            "SORTNAME": "权证发行结果公告",
            "F002D": null,
            "F001D": "2008-05-14 16:39:24",
            "PARENTCODE": "0110"
        },
        {
            "SORTCODE": "011009",
            "SORTNAME": "权证行权价变更公告",
            "F002D": null,
            "F001D": "2008-09-22 16:40:23",
            "PARENTCODE": "0110"
        },
        {
            "SORTCODE": "011011",
            "SORTNAME": "权证其他公告",
            "F002D": null,
            "F001D": "2008-10-10 11:33:21",
            "PARENTCODE": "0110"
        },
        {
            "SORTCODE": "0111",
            "SORTNAME": "其它融资",
            "F002D": null,
            "F001D": "2006-06-15 08:54:22",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "011101",
            "SORTNAME": "发行企业债券",
            "F002D": null,
            "F001D": "2006-06-15 08:54:23",
            "PARENTCODE": "0111"
        },
        {
            "SORTCODE": "01110101",
            "SORTNAME": "企业债发行公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:24",
            "PARENTCODE": "011101"
        },
        {
            "SORTCODE": "01110103",
            "SORTNAME": "企业债发行获准公告",
            "F002D": null,
            "F001D": "2007-01-30 10:24:04",
            "PARENTCODE": "011101"
        },
        {
            "SORTCODE": "01110110",
            "SORTNAME": "企业债招募说明书",
            "F002D": null,
            "F001D": "2007-01-30 14:29:01",
            "PARENTCODE": "011101"
        },
        {
            "SORTCODE": "01110120",
            "SORTNAME": "企业债其它事项公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:26",
            "PARENTCODE": "011101"
        },
        {
            "SORTCODE": "011103",
            "SORTNAME": "其它融资事项",
            "F002D": null,
            "F001D": "2006-06-15 08:54:27",
            "PARENTCODE": "0111"
        },
        {
            "SORTCODE": "01110301",
            "SORTNAME": "其它融资（ADR、海外上市等）预案",
            "F002D": null,
            "F001D": "2006-06-15 08:54:28",
            "PARENTCODE": "011103"
        },
        {
            "SORTCODE": "01110310",
            "SORTNAME": "其它融资（ADR、海外上市等）获准公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:29",
            "PARENTCODE": "011103"
        },
        {
            "SORTCODE": "01110320",
            "SORTNAME": "其它融资（ADR、海外上市等）事项公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:30",
            "PARENTCODE": "011103"
        },
        {
            "SORTCODE": "0113",
            "SORTNAME": "权益分派与限制出售股份上市",
            "F002D": null,
            "F001D": "2006-06-15 08:54:32",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "011301",
            "SORTNAME": "权益分派预案及实施",
            "F002D": null,
            "F001D": "2006-06-15 08:54:33",
            "PARENTCODE": "0113"
        },
        {
            "SORTCODE": "01130101",
            "SORTNAME": "利润分配及公积金转增股本预案",
            "F002D": null,
            "F001D": "2006-06-15 08:54:34",
            "PARENTCODE": "011301"
        },
        {
            "SORTCODE": "01130110",
            "SORTNAME": "修改利润分配及公积金转增股本预案",
            "F002D": null,
            "F001D": "2006-06-15 08:54:35",
            "PARENTCODE": "011301"
        },
        {
            "SORTCODE": "01130120",
            "SORTNAME": "利润分配及公积金转增股本实施公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:36",
            "PARENTCODE": "011301"
        },
        {
            "SORTCODE": "011303",
            "SORTNAME": "限制出售股份上市",
            "F002D": null,
            "F001D": "2006-06-15 08:54:37",
            "PARENTCODE": "0113"
        },
        {
            "SORTCODE": "01130301",
            "SORTNAME": "职工股上市公告",
            "F002D": null,
            "F001D": "2009-07-17 19:31:44",
            "PARENTCODE": "011303"
        },
        {
            "SORTCODE": "01130303",
            "SORTNAME": "首发机构配售股份上市公告",
            "F002D": null,
            "F001D": "2008-07-07 11:32:02",
            "PARENTCODE": "011303"
        },
        {
            "SORTCODE": "01130310",
            "SORTNAME": "机构配售股份上市公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:39",
            "PARENTCODE": "011303"
        },
        {
            "SORTCODE": "01130320",
            "SORTNAME": "转配股上市公告",
            "F002D": null,
            "F001D": "2009-07-17 19:32:09",
            "PARENTCODE": "011303"
        },
        {
            "SORTCODE": "01130330",
            "SORTNAME": "外资股限制股份上市公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:41",
            "PARENTCODE": "011303"
        },
        {
            "SORTCODE": "01130335",
            "SORTNAME": "股改限售股份上市公告",
            "F002D": null,
            "F001D": "2007-01-30 10:25:09",
            "PARENTCODE": "011303"
        },
        {
            "SORTCODE": "01130340",
            "SORTNAME": "其它限制股份上市公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:42",
            "PARENTCODE": "011303"
        },
        {
            "SORTCODE": "011305",
            "SORTNAME": "股权分置改革",
            "F002D": null,
            "F001D": "2006-06-15 08:54:43",
            "PARENTCODE": "0113"
        },
        {
            "SORTCODE": "0115",
            "SORTNAME": "股权变动",
            "F002D": null,
            "F001D": "2006-06-15 08:54:44",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "011501",
            "SORTNAME": "持股变动",
            "F002D": null,
            "F001D": "2006-06-15 08:54:45",
            "PARENTCODE": "0115"
        },
        {
            "SORTCODE": "01150101",
            "SORTNAME": "持股变动提示性公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:46",
            "PARENTCODE": "011501"
        },
        {
            "SORTCODE": "01150110",
            "SORTNAME": "权益变动报告书",
            "F002D": null,
            "F001D": "2006-06-15 08:54:47",
            "PARENTCODE": "011501"
        },
        {
            "SORTCODE": "01150120",
            "SORTNAME": "上市公司关于股权转让的提示性公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:48",
            "PARENTCODE": "011501"
        },
        {
            "SORTCODE": "01150130",
            "SORTNAME": "上市公司关于股权转让的公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:49",
            "PARENTCODE": "011501"
        },
        {
            "SORTCODE": "01150140",
            "SORTNAME": "持股5％以上股东通过竞价系统增（减）1％的公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:50",
            "PARENTCODE": "011501"
        },
        {
            "SORTCODE": "01150150",
            "SORTNAME": "股权拍卖公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:51",
            "PARENTCODE": "011501"
        },
        {
            "SORTCODE": "01150160",
            "SORTNAME": "限售股份持有人出售股份情况",
            "F002D": null,
            "F001D": "2007-01-30 10:26:18",
            "PARENTCODE": "011501"
        },
        {
            "SORTCODE": "01150199",
            "SORTNAME": "其它持股变动公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:52",
            "PARENTCODE": "011501"
        },
        {
            "SORTCODE": "011503",
            "SORTNAME": "股权收购",
            "F002D": null,
            "F001D": "2006-06-15 08:54:53",
            "PARENTCODE": "0115"
        },
        {
            "SORTCODE": "01150301",
            "SORTNAME": "股权收购的提示性公告",
            "F002D": null,
            "F001D": "2006-06-15 08:54:54",
            "PARENTCODE": "011503"
        },
        {
            "SORTCODE": "01150310",
            "SORTNAME": "上市公司收购报告书摘要",
            "F002D": null,
            "F001D": "2006-06-15 08:54:55",
            "PARENTCODE": "011503"
        },
        {
            "SORTCODE": "01150320",
            "SORTNAME": "上市公司收购报告书",
            "F002D": null,
            "F001D": "2006-06-15 08:54:56",
            "PARENTCODE": "011503"
        },
        {
            "SORTCODE": "01150330",
            "SORTNAME": "被收购公司董事会报告书",
            "F002D": null,
            "F001D": "2006-06-15 08:54:57",
            "PARENTCODE": "011503"
        },
        {
            "SORTCODE": "01150340",
            "SORTNAME": "有关收购的中介机构意见",
            "F002D": null,
            "F001D": "2006-06-15 08:54:58",
            "PARENTCODE": "011503"
        },
        {
            "SORTCODE": "011505",
            "SORTNAME": "要约收购",
            "F002D": null,
            "F001D": "2006-06-15 08:54:59",
            "PARENTCODE": "0115"
        },
        {
            "SORTCODE": "01150501",
            "SORTNAME": "要约收购的提示性公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:01",
            "PARENTCODE": "011505"
        },
        {
            "SORTCODE": "01150510",
            "SORTNAME": "要约收购报告书摘要",
            "F002D": null,
            "F001D": "2006-06-15 08:55:02",
            "PARENTCODE": "011505"
        },
        {
            "SORTCODE": "01150520",
            "SORTNAME": "要约收购报告书",
            "F002D": null,
            "F001D": "2006-06-15 08:55:03",
            "PARENTCODE": "011505"
        },
        {
            "SORTCODE": "01150530",
            "SORTNAME": "要约期间公告及要约结果公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:04",
            "PARENTCODE": "011505"
        },
        {
            "SORTCODE": "01150540",
            "SORTNAME": "相关中介机构的报告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:05",
            "PARENTCODE": "011505"
        },
        {
            "SORTCODE": "01150550",
            "SORTNAME": "豁免要约收购公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:06",
            "PARENTCODE": "011505"
        },
        {
            "SORTCODE": "011507",
            "SORTNAME": "股权变动进展",
            "F002D": null,
            "F001D": "2006-06-15 08:55:07",
            "PARENTCODE": "0115"
        },
        {
            "SORTCODE": "01150701",
            "SORTNAME": "股权转让获准公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:08",
            "PARENTCODE": "011507"
        },
        {
            "SORTCODE": "01150710",
            "SORTNAME": "股权托管公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:09",
            "PARENTCODE": "011507"
        },
        {
            "SORTCODE": "01150720",
            "SORTNAME": "股权转让进展公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:10",
            "PARENTCODE": "011507"
        },
        {
            "SORTCODE": "01150730",
            "SORTNAME": "股份过户（登记）公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:11",
            "PARENTCODE": "011507"
        },
        {
            "SORTCODE": "01150740",
            "SORTNAME": "中止或取消股权转让协议公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:12",
            "PARENTCODE": "011507"
        },
        {
            "SORTCODE": "011509",
            "SORTNAME": "国有股配售事项",
            "F002D": null,
            "F001D": "2006-06-15 08:55:13",
            "PARENTCODE": "0115"
        },
        {
            "SORTCODE": "01150901",
            "SORTNAME": "国有股配售预案",
            "F002D": null,
            "F001D": "2006-06-15 08:55:14",
            "PARENTCODE": "011509"
        },
        {
            "SORTCODE": "01150910",
            "SORTNAME": "国有股配售公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:15",
            "PARENTCODE": "011509"
        },
        {
            "SORTCODE": "011511",
            "SORTNAME": "吸收合并",
            "F002D": null,
            "F001D": "2006-06-15 08:55:16",
            "PARENTCODE": "0115"
        },
        {
            "SORTCODE": "01151101",
            "SORTNAME": "吸收合并获准公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:17",
            "PARENTCODE": "011511"
        },
        {
            "SORTCODE": "01151110",
            "SORTNAME": "吸收合并提示公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:18",
            "PARENTCODE": "011511"
        },
        {
            "SORTCODE": "01151120",
            "SORTNAME": "吸收合并进展公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:19",
            "PARENTCODE": "011511"
        },
        {
            "SORTCODE": "01151130",
            "SORTNAME": "吸收合并实施公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:20",
            "PARENTCODE": "011511"
        },
        {
            "SORTCODE": "01151199",
            "SORTNAME": "吸收合并其它说明公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:21",
            "PARENTCODE": "011511"
        },
        {
            "SORTCODE": "011513",
            "SORTNAME": "公司减资、分立事项",
            "F002D": null,
            "F001D": "2006-06-15 08:55:22",
            "PARENTCODE": "0115"
        },
        {
            "SORTCODE": "01151301",
            "SORTNAME": "股份回购预案",
            "F002D": null,
            "F001D": "2006-06-15 08:55:23",
            "PARENTCODE": "011513"
        },
        {
            "SORTCODE": "01151310",
            "SORTNAME": "股份回购进展公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:24",
            "PARENTCODE": "011513"
        },
        {
            "SORTCODE": "01151320",
            "SORTNAME": "公司减资公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:25",
            "PARENTCODE": "011513"
        },
        {
            "SORTCODE": "01151330",
            "SORTNAME": "公司分立公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:26",
            "PARENTCODE": "011513"
        },
        {
            "SORTCODE": "0117",
            "SORTNAME": "交易",
            "F002D": null,
            "F001D": "2006-06-15 08:55:27",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "011701",
            "SORTNAME": "收购出售资产",
            "F002D": null,
            "F001D": "2006-06-15 08:55:28",
            "PARENTCODE": "0117"
        },
        {
            "SORTCODE": "01170101",
            "SORTNAME": "收购、出售资产提示性公告",
            "F002D": null,
            "F001D": "2015-01-06 17:06:45",
            "PARENTCODE": "011701"
        },
        {
            "SORTCODE": "01170110",
            "SORTNAME": "收购、出售资产公告",
            "F002D": null,
            "F001D": "2015-01-06 17:06:52",
            "PARENTCODE": "011701"
        },
        {
            "SORTCODE": "01170120",
            "SORTNAME": "收购、出售资产进展公告",
            "F002D": null,
            "F001D": "2015-01-06 17:06:58",
            "PARENTCODE": "011701"
        },
        {
            "SORTCODE": "011702",
            "SORTNAME": "资产置换",
            "F002D": null,
            "F001D": "2006-06-30 10:07:58",
            "PARENTCODE": "0117"
        },
        {
            "SORTCODE": "011703",
            "SORTNAME": "债务重组",
            "F002D": null,
            "F001D": "2006-06-15 08:55:32",
            "PARENTCODE": "0117"
        },
        {
            "SORTCODE": "01170301",
            "SORTNAME": "债务重组提示性公告",
            "F002D": "2008-07-07 14:31:58",
            "F001D": "2006-06-15 08:55:33",
            "PARENTCODE": "011703"
        },
        {
            "SORTCODE": "01170310",
            "SORTNAME": "债务重组公告",
            "F002D": "2008-07-07 14:32:04",
            "F001D": "2006-06-15 08:55:34",
            "PARENTCODE": "011703"
        },
        {
            "SORTCODE": "01170320",
            "SORTNAME": "债务重组进展公告",
            "F002D": "2008-07-07 14:32:10",
            "F001D": "2006-06-15 08:55:35",
            "PARENTCODE": "011703"
        },
        {
            "SORTCODE": "011705",
            "SORTNAME": "对外投资",
            "F002D": null,
            "F001D": "2006-06-15 08:55:36",
            "PARENTCODE": "0117"
        },
        {
            "SORTCODE": "01170501",
            "SORTNAME": "对外投资提示性公告",
            "F002D": "2008-07-07 14:32:16",
            "F001D": "2006-06-15 08:55:37",
            "PARENTCODE": "011705"
        },
        {
            "SORTCODE": "01170510",
            "SORTNAME": "对外投资公告",
            "F002D": null,
            "F001D": "2015-01-06 17:07:09",
            "PARENTCODE": "011705"
        },
        {
            "SORTCODE": "01170520",
            "SORTNAME": "对外投资进展公告",
            "F002D": null,
            "F001D": "2015-01-06 17:07:16",
            "PARENTCODE": "011705"
        },
        {
            "SORTCODE": "01170530",
            "SORTNAME": "委托理财公告",
            "F002D": null,
            "F001D": "2006-06-15 08:55:40",
            "PARENTCODE": "011705"
        },
        {
            "SORTCODE": "011707",
            "SORTNAME": "委（受）托经营、承包、租赁",
            "F002D": null,
            "F001D": "2006-06-15 08:55:41",
            "PARENTCODE": "0117"
        },
        {
            "SORTCODE": "01170701",
            "SORTNAME": "委托经营事项公告",
            "F002D": "2008-07-07 14:33:21",
            "F001D": "2006-06-15 08:55:42",
            "PARENTCODE": "011707"
        },
        {
            "SORTCODE": "01170710",
            "SORTNAME": "受托经营事项公告",
            "F002D": "2008-07-07 14:33:28",
            "F001D": "2006-06-15 08:55:43",
            "PARENTCODE": "011707"
        },
        {
            "SORTCODE": "01170720",
            "SORTNAME": "承包事项公告",
            "F002D": "2008-07-07 14:33:34",
            "F001D": "2006-06-15 08:55:44",
            "PARENTCODE": "011707"
        },
        {
            "SORTCODE": "01170730",
            "SORTNAME": "租赁事项公告",
            "F002D": "2008-07-07 14:33:40",
            "F001D": "2006-06-15 08:55:45",
            "PARENTCODE": "011707"
        },
        {
            "SORTCODE": "011709",
            "SORTNAME": "借贷",
            "F002D": null,
            "F001D": "2006-06-15 08:55:46",
            "PARENTCODE": "0117"
        },
        {
            "SORTCODE": "01170901",
            "SORTNAME": "大额借款事项",
            "F002D": null,
            "F001D": "2015-01-06 17:22:11",
            "PARENTCODE": "011709"
        },
        {
            "SORTCODE": "01170910",
            "SORTNAME": "授信额度事项",
            "F002D": null,
            "F001D": "2015-01-06 17:22:21",
            "PARENTCODE": "011709"
        },
        {
            "SORTCODE": "01170999",
            "SORTNAME": "其它借贷事项",
            "F002D": null,
            "F001D": "2015-01-06 17:22:34",
            "PARENTCODE": "011709"
        },
        {
            "SORTCODE": "011711",
            "SORTNAME": "担保",
            "F002D": null,
            "F001D": "2006-06-15 08:55:50",
            "PARENTCODE": "0117"
        },
        {
            "SORTCODE": "01171101",
            "SORTNAME": "公司为他人提供担保公告",
            "F002D": null,
            "F001D": "2015-01-06 17:22:42",
            "PARENTCODE": "011711"
        },
        {
            "SORTCODE": "01171110",
            "SORTNAME": "履行担保义务公告",
            "F002D": "2008-07-07 14:36:41",
            "F001D": "2006-06-15 08:55:52",
            "PARENTCODE": "011711"
        },
        {
            "SORTCODE": "01171120",
            "SORTNAME": "到期担保义务无法解除公告",
            "F002D": "2008-07-07 14:36:47",
            "F001D": "2006-06-15 08:55:53",
            "PARENTCODE": "011711"
        },
        {
            "SORTCODE": "01171130",
            "SORTNAME": "解除担保责任公告",
            "F002D": "2008-07-07 14:36:54",
            "F001D": "2006-06-15 08:55:54",
            "PARENTCODE": "011711"
        },
        {
            "SORTCODE": "011713",
            "SORTNAME": "提供财务资助",
            "F002D": null,
            "F001D": "2006-06-15 08:55:55",
            "PARENTCODE": "0117"
        },
        {
            "SORTCODE": "01171301",
            "SORTNAME": "承担费用公告",
            "F002D": "2008-07-07 14:37:05",
            "F001D": "2006-06-15 08:55:56",
            "PARENTCODE": "011713"
        },
        {
            "SORTCODE": "01171310",
            "SORTNAME": "提供资金公告",
            "F002D": null,
            "F001D": "2015-01-06 17:22:50",
            "PARENTCODE": "011713"
        },
        {
            "SORTCODE": "011715",
            "SORTNAME": "赠与",
            "F002D": null,
            "F001D": "2006-06-15 08:55:58",
            "PARENTCODE": "0117"
        },
        {
            "SORTCODE": "01171501",
            "SORTNAME": "接受赠与公告",
            "F002D": "2008-07-07 14:37:19",
            "F001D": "2006-06-15 08:55:59",
            "PARENTCODE": "011715"
        },
        {
            "SORTCODE": "01171510",
            "SORTNAME": "提供赠与公告",
            "F002D": "2008-07-07 14:37:26",
            "F001D": "2006-06-15 08:56:01",
            "PARENTCODE": "011715"
        },
        {
            "SORTCODE": "011717",
            "SORTNAME": "研究与开发项目的转移",
            "F002D": null,
            "F001D": "2006-06-15 08:56:02",
            "PARENTCODE": "0117"
        },
        {
            "SORTCODE": "01171701",
            "SORTNAME": "研究项目的转移公告",
            "F002D": "2008-07-07 14:37:33",
            "F001D": "2006-06-15 08:56:03",
            "PARENTCODE": "011717"
        },
        {
            "SORTCODE": "01171710",
            "SORTNAME": "开发项目的转移公告",
            "F002D": "2008-07-07 14:37:39",
            "F001D": "2006-06-15 08:56:04",
            "PARENTCODE": "011717"
        },
        {
            "SORTCODE": "011719",
            "SORTNAME": "持续性关联交易",
            "F002D": null,
            "F001D": "2006-06-15 08:56:05",
            "PARENTCODE": "0117"
        },
        {
            "SORTCODE": "01171901",
            "SORTNAME": "购买原材料、动力、燃料的关联交易公告",
            "F002D": "2008-07-07 14:38:33",
            "F001D": "2006-06-15 08:56:06",
            "PARENTCODE": "011719"
        },
        {
            "SORTCODE": "01171910",
            "SORTNAME": "销售产成品、商品的关联交易公告",
            "F002D": "2008-07-07 14:38:41",
            "F001D": "2006-06-15 08:56:07",
            "PARENTCODE": "011719"
        },
        {
            "SORTCODE": "01171920",
            "SORTNAME": "提供和接受劳务的关联交易公告",
            "F002D": "2008-07-07 14:38:47",
            "F001D": "2006-06-15 08:56:08",
            "PARENTCODE": "011719"
        },
        {
            "SORTCODE": "01171930",
            "SORTNAME": "提供和接受销售代理的关联交易公告",
            "F002D": "2008-07-07 14:38:55",
            "F001D": "2006-06-15 08:56:09",
            "PARENTCODE": "011719"
        },
        {
            "SORTCODE": "011721",
            "SORTNAME": "股东资金占用与还款",
            "F002D": null,
            "F001D": "2006-06-15 08:56:11",
            "PARENTCODE": "0117"
        },
        {
            "SORTCODE": "011799",
            "SORTNAME": "其它交易事项公告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:10",
            "PARENTCODE": "0117"
        },
        {
            "SORTCODE": "0119",
            "SORTNAME": "股东大会",
            "F002D": null,
            "F001D": "2006-06-15 08:56:12",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "011901",
            "SORTNAME": "股东大会通知及提示",
            "F002D": null,
            "F001D": "2006-06-15 08:56:13",
            "PARENTCODE": "0119"
        },
        {
            "SORTCODE": "01190101",
            "SORTNAME": "董事会决议召开年度股东大会通知及提示",
            "F002D": null,
            "F001D": "2006-06-15 08:56:14",
            "PARENTCODE": "011901"
        },
        {
            "SORTCODE": "01190110",
            "SORTNAME": "召开临时股东大会的通知及提示",
            "F002D": null,
            "F001D": "2006-06-15 08:56:15",
            "PARENTCODE": "011901"
        },
        {
            "SORTCODE": "01190120",
            "SORTNAME": "监事会提议召开临时股东大会的通知",
            "F002D": "2007-01-31 10:52:46",
            "F001D": "2006-06-15 08:56:16",
            "PARENTCODE": "011901"
        },
        {
            "SORTCODE": "01190130",
            "SORTNAME": "股东自行提议召开临时股东大会的通知",
            "F002D": "2007-01-31 10:53:01",
            "F001D": "2006-06-15 08:56:17",
            "PARENTCODE": "011901"
        },
        {
            "SORTCODE": "011903",
            "SORTNAME": "股东大会相关事项变更",
            "F002D": null,
            "F001D": "2006-06-15 08:56:18",
            "PARENTCODE": "0119"
        },
        {
            "SORTCODE": "01190301",
            "SORTNAME": "增加股东大会议案公告",
            "F002D": null,
            "F001D": "2015-01-06 17:32:28",
            "PARENTCODE": "011903"
        },
        {
            "SORTCODE": "01190310",
            "SORTNAME": "变更股东大会议案公告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:20",
            "PARENTCODE": "011903"
        },
        {
            "SORTCODE": "01190320",
            "SORTNAME": "变更股东大会时间公告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:21",
            "PARENTCODE": "011903"
        },
        {
            "SORTCODE": "01190330",
            "SORTNAME": "变更股东大会地点公告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:22",
            "PARENTCODE": "011903"
        },
        {
            "SORTCODE": "01190340",
            "SORTNAME": "取消股东大会公告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:23",
            "PARENTCODE": "011903"
        },
        {
            "SORTCODE": "01190350",
            "SORTNAME": "取消股东大会议案公告",
            "F002D": "2007-01-31 10:19:13",
            "F001D": "2006-06-15 08:56:24",
            "PARENTCODE": "011903"
        },
        {
            "SORTCODE": "011905",
            "SORTNAME": "股东大会决议公告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:25",
            "PARENTCODE": "0119"
        },
        {
            "SORTCODE": "01190501",
            "SORTNAME": "正常股东大会决议公告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:26",
            "PARENTCODE": "011905"
        },
        {
            "SORTCODE": "01190510",
            "SORTNAME": "增加、变更或否决议案的决议公告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:27",
            "PARENTCODE": "011905"
        },
        {
            "SORTCODE": "011906",
            "SORTNAME": "股东大会资料",
            "F002D": null,
            "F001D": "2006-06-15 08:56:28",
            "PARENTCODE": "0119"
        },
        {
            "SORTCODE": "011999",
            "SORTNAME": "股东大会其它公告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:29",
            "PARENTCODE": "0119"
        },
        {
            "SORTCODE": "01199901",
            "SORTNAME": "股东大会法律意见书",
            "F002D": null,
            "F001D": "2006-06-15 08:56:30",
            "PARENTCODE": "011999"
        },
        {
            "SORTCODE": "01199910",
            "SORTNAME": "未能如期刊登股东大会决议公告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:31",
            "PARENTCODE": "011999"
        },
        {
            "SORTCODE": "01199920",
            "SORTNAME": "征集投票权公告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:32",
            "PARENTCODE": "011999"
        },
        {
            "SORTCODE": "0120",
            "SORTNAME": "投资者关系信息",
            "F002D": null,
            "F001D": "2012-07-07 10:46:54",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "012001",
            "SORTNAME": "调研活动",
            "F002D": null,
            "F001D": "2012-07-07 10:47:35",
            "PARENTCODE": "0120"
        },
        {
            "SORTCODE": "012002",
            "SORTNAME": "活动通知（媒体采访）",
            "F002D": null,
            "F001D": "2012-07-07 10:48:01",
            "PARENTCODE": "0120"
        },
        {
            "SORTCODE": "012003",
            "SORTNAME": "业绩说明会（路演活动）",
            "F002D": null,
            "F001D": "2012-07-07 10:48:20",
            "PARENTCODE": "0120"
        },
        {
            "SORTCODE": "012004",
            "SORTNAME": "管理制度",
            "F002D": null,
            "F001D": "2012-07-07 10:48:34",
            "PARENTCODE": "0120"
        },
        {
            "SORTCODE": "0121",
            "SORTNAME": "澄清、风险提示、业绩预告事项",
            "F002D": null,
            "F001D": "2006-06-15 08:56:33",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "012101",
            "SORTNAME": "澄清公告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:34",
            "PARENTCODE": "0121"
        },
        {
            "SORTCODE": "012102",
            "SORTNAME": "致歉公告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:35",
            "PARENTCODE": "0121"
        },
        {
            "SORTCODE": "012103",
            "SORTNAME": "股票交易异常波动风险提示",
            "F002D": null,
            "F001D": "2006-06-15 08:56:36",
            "PARENTCODE": "0121"
        },
        {
            "SORTCODE": "01210301",
            "SORTNAME": "连续三个交易日达到涨幅限制公告",
            "F002D": null,
            "F001D": "2015-01-06 17:32:39",
            "PARENTCODE": "012103"
        },
        {
            "SORTCODE": "01210310",
            "SORTNAME": "连续三个交易日达到跌幅限制公告",
            "F002D": "2008-07-07 14:39:51",
            "F001D": "2006-06-15 08:56:38",
            "PARENTCODE": "012103"
        },
        {
            "SORTCODE": "01210320",
            "SORTNAME": "连续五个交易日列入公开信息公告",
            "F002D": "2008-07-07 14:39:58",
            "F001D": "2006-06-15 08:56:39",
            "PARENTCODE": "012103"
        },
        {
            "SORTCODE": "01210330",
            "SORTNAME": "振幅连续三个交易日达到15％公告",
            "F002D": "2008-07-07 14:40:11",
            "F001D": "2006-06-15 08:56:40",
            "PARENTCODE": "012103"
        },
        {
            "SORTCODE": "01210340",
            "SORTNAME": "日均成交金额连续五个交易日逐日增加50％",
            "F002D": "2008-07-07 14:40:19",
            "F001D": "2006-06-15 08:56:41",
            "PARENTCODE": "012103"
        },
        {
            "SORTCODE": "01210399",
            "SORTNAME": "中国证监会或交易所认为属于异常波动的其它情况公告",
            "F002D": null,
            "F001D": "2015-01-06 17:32:48",
            "PARENTCODE": "012103"
        },
        {
            "SORTCODE": "012105",
            "SORTNAME": "暂停上市风险提示",
            "F002D": null,
            "F001D": "2006-06-15 08:56:43",
            "PARENTCODE": "0121"
        },
        {
            "SORTCODE": "012107",
            "SORTNAME": "退市风险提示",
            "F002D": null,
            "F001D": "2006-06-15 08:56:44",
            "PARENTCODE": "0121"
        },
        {
            "SORTCODE": "012109",
            "SORTNAME": "其它风险提示",
            "F002D": null,
            "F001D": "2006-06-15 08:56:45",
            "PARENTCODE": "0121"
        },
        {
            "SORTCODE": "01210901",
            "SORTNAME": "重大经营性或非经营性亏损",
            "F002D": "2008-07-07 14:42:05",
            "F001D": "2006-06-15 08:56:46",
            "PARENTCODE": "012109"
        },
        {
            "SORTCODE": "01210910",
            "SORTNAME": "预计出现资不抵债",
            "F002D": "2008-07-07 14:42:16",
            "F001D": "2006-06-15 08:56:47",
            "PARENTCODE": "012109"
        },
        {
            "SORTCODE": "01210920",
            "SORTNAME": "发生重大债务或未清偿到期重大债务",
            "F002D": "2008-07-07 14:42:24",
            "F001D": "2006-06-15 08:56:48",
            "PARENTCODE": "012109"
        },
        {
            "SORTCODE": "01210930",
            "SORTNAME": "被担保人出现影响还款能力事项",
            "F002D": "2008-07-07 14:42:32",
            "F001D": "2006-06-15 08:56:49",
            "PARENTCODE": "012109"
        },
        {
            "SORTCODE": "01210940",
            "SORTNAME": "股价风险提示",
            "F002D": "2008-07-07 14:42:40",
            "F001D": "2006-06-15 08:56:50",
            "PARENTCODE": "012109"
        },
        {
            "SORTCODE": "01210950",
            "SORTNAME": "涉讼风险提示",
            "F002D": "2008-07-07 14:42:48",
            "F001D": "2006-06-15 08:56:51",
            "PARENTCODE": "012109"
        },
        {
            "SORTCODE": "01210960",
            "SORTNAME": "意外风险提示",
            "F002D": "2008-07-07 14:42:54",
            "F001D": "2006-06-15 08:56:52",
            "PARENTCODE": "012109"
        },
        {
            "SORTCODE": "01210970",
            "SORTNAME": "重组风险提示",
            "F002D": null,
            "F001D": "2015-01-06 17:24:43",
            "PARENTCODE": "012109"
        },
        {
            "SORTCODE": "01210980",
            "SORTNAME": "异常审计意见解决情况进展公告",
            "F002D": "2008-07-07 14:43:08",
            "F001D": "2006-06-15 08:56:54",
            "PARENTCODE": "012109"
        },
        {
            "SORTCODE": "01210990",
            "SORTNAME": "减资弥补亏损的特别风险提示",
            "F002D": "2008-07-07 14:43:14",
            "F001D": "2007-01-30 10:27:10",
            "PARENTCODE": "012109"
        },
        {
            "SORTCODE": "012111",
            "SORTNAME": "业绩预告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:55",
            "PARENTCODE": "0121"
        },
        {
            "SORTCODE": "01211101",
            "SORTNAME": "预计盈利公告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:56",
            "PARENTCODE": "012111"
        },
        {
            "SORTCODE": "01211110",
            "SORTNAME": "预计亏损公告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:57",
            "PARENTCODE": "012111"
        },
        {
            "SORTCODE": "01211115",
            "SORTNAME": "预计减亏公告",
            "F002D": null,
            "F001D": "2008-07-07 14:44:37",
            "PARENTCODE": "012111"
        },
        {
            "SORTCODE": "01211120",
            "SORTNAME": "业绩大幅增加公告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:58",
            "PARENTCODE": "012111"
        },
        {
            "SORTCODE": "01211130",
            "SORTNAME": "业绩大幅减少公告",
            "F002D": null,
            "F001D": "2006-06-15 08:56:59",
            "PARENTCODE": "012111"
        },
        {
            "SORTCODE": "01211140",
            "SORTNAME": "无法预计公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:01",
            "PARENTCODE": "012111"
        },
        {
            "SORTCODE": "01211150",
            "SORTNAME": "盈利预测及调整公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:02",
            "PARENTCODE": "012111"
        },
        {
            "SORTCODE": "01211160",
            "SORTNAME": "业绩快报",
            "F002D": null,
            "F001D": "2006-06-15 08:57:03",
            "PARENTCODE": "012111"
        },
        {
            "SORTCODE": "0122",
            "SORTNAME": "沪市投资者关系信息",
            "F002D": null,
            "F001D": "2021-12-06 08:55:27",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "0123",
            "SORTNAME": "其它重大事项",
            "F002D": null,
            "F001D": "2006-06-15 08:57:04",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "012301",
            "SORTNAME": "公司基本信息变更",
            "F002D": null,
            "F001D": "2006-06-15 08:57:05",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "01230101",
            "SORTNAME": "公司章程变更公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:06",
            "PARENTCODE": "012301"
        },
        {
            "SORTCODE": "01230103",
            "SORTNAME": "保荐人或保荐机构变更公告",
            "F002D": null,
            "F001D": "2008-05-14 16:40:20",
            "PARENTCODE": "012301"
        },
        {
            "SORTCODE": "01230110",
            "SORTNAME": "公司注册资本变更公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:07",
            "PARENTCODE": "012301"
        },
        {
            "SORTCODE": "01230120",
            "SORTNAME": "公司注册地变更公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:08",
            "PARENTCODE": "012301"
        },
        {
            "SORTCODE": "01230130",
            "SORTNAME": "公司名称变更公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:09",
            "PARENTCODE": "012301"
        },
        {
            "SORTCODE": "01230140",
            "SORTNAME": "公司经营方针重大变化",
            "F002D": "2008-07-07 14:45:49",
            "F001D": "2006-06-15 08:57:10",
            "PARENTCODE": "012301"
        },
        {
            "SORTCODE": "01230150",
            "SORTNAME": "公司经营范围重大变化",
            "F002D": null,
            "F001D": "2006-06-15 08:57:11",
            "PARENTCODE": "012301"
        },
        {
            "SORTCODE": "01230160",
            "SORTNAME": "公司股份性质变更公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:12",
            "PARENTCODE": "012301"
        },
        {
            "SORTCODE": "01230170",
            "SORTNAME": "公司中介机构变更",
            "F002D": null,
            "F001D": "2006-06-15 08:57:13",
            "PARENTCODE": "012301"
        },
        {
            "SORTCODE": "0123017001",
            "SORTNAME": "续聘中介机构",
            "F002D": null,
            "F001D": "2007-01-30 10:28:05",
            "PARENTCODE": "01230170"
        },
        {
            "SORTCODE": "01230180",
            "SORTNAME": "公司办公地址变更",
            "F002D": null,
            "F001D": "2007-01-30 10:29:58",
            "PARENTCODE": "012301"
        },
        {
            "SORTCODE": "01230199",
            "SORTNAME": "公司其它基本信息变更",
            "F002D": null,
            "F001D": "2006-06-15 08:57:14",
            "PARENTCODE": "012301"
        },
        {
            "SORTCODE": "012303",
            "SORTNAME": "变更董事、监事及高管",
            "F002D": null,
            "F001D": "2006-06-15 08:57:15",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "01230301",
            "SORTNAME": "变更董事公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:16",
            "PARENTCODE": "012303"
        },
        {
            "SORTCODE": "01230310",
            "SORTNAME": "变更监事公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:17",
            "PARENTCODE": "012303"
        },
        {
            "SORTCODE": "01230315",
            "SORTNAME": "变更独立董事公告",
            "F002D": null,
            "F001D": "2008-07-07 14:46:22",
            "PARENTCODE": "012303"
        },
        {
            "SORTCODE": "01230320",
            "SORTNAME": "变更高级管理人员公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:18",
            "PARENTCODE": "012303"
        },
        {
            "SORTCODE": "01230330",
            "SORTNAME": "独立董事声明公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:19",
            "PARENTCODE": "012303"
        },
        {
            "SORTCODE": "01230340",
            "SORTNAME": "独立董事候选人声明",
            "F002D": null,
            "F001D": "2015-01-06 17:24:55",
            "PARENTCODE": "012303"
        },
        {
            "SORTCODE": "01230350",
            "SORTNAME": "高管人员持股变更公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:21",
            "PARENTCODE": "012303"
        },
        {
            "SORTCODE": "012305",
            "SORTNAME": "经营环境重大变化",
            "F002D": null,
            "F001D": "2006-06-15 08:57:22",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "01230501",
            "SORTNAME": "获得财政补贴公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:23",
            "PARENTCODE": "012305"
        },
        {
            "SORTCODE": "01230510",
            "SORTNAME": "税费变化公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:24",
            "PARENTCODE": "012305"
        },
        {
            "SORTCODE": "01230520",
            "SORTNAME": "通过资格认证公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:25",
            "PARENTCODE": "012305"
        },
        {
            "SORTCODE": "01230530",
            "SORTNAME": "政策变更公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:26",
            "PARENTCODE": "012305"
        },
        {
            "SORTCODE": "01230540",
            "SORTNAME": "价格调整公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:27",
            "PARENTCODE": "012305"
        },
        {
            "SORTCODE": "01230550",
            "SORTNAME": "业务停顿公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:28",
            "PARENTCODE": "012305"
        },
        {
            "SORTCODE": "01230560",
            "SORTNAME": "子公司注销",
            "F002D": null,
            "F001D": "2007-01-30 10:29:26",
            "PARENTCODE": "012305"
        },
        {
            "SORTCODE": "01230599",
            "SORTNAME": "经营环境其它重大变化公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:29",
            "PARENTCODE": "012305"
        },
        {
            "SORTCODE": "012307",
            "SORTNAME": "股份质押、冻结",
            "F002D": null,
            "F001D": "2006-06-15 08:57:30",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "01230701",
            "SORTNAME": "股份质押公告",
            "F002D": null,
            "F001D": "2015-01-06 17:25:08",
            "PARENTCODE": "012307"
        },
        {
            "SORTCODE": "01230710",
            "SORTNAME": "股份冻结公告",
            "F002D": null,
            "F001D": "2015-01-06 17:25:16",
            "PARENTCODE": "012307"
        },
        {
            "SORTCODE": "01230720",
            "SORTNAME": "股份质押解除公告",
            "F002D": null,
            "F001D": "2015-01-06 17:25:24",
            "PARENTCODE": "012307"
        },
        {
            "SORTCODE": "01230730",
            "SORTNAME": "股份解冻公告",
            "F002D": null,
            "F001D": "2015-01-06 17:25:32",
            "PARENTCODE": "012307"
        },
        {
            "SORTCODE": "012309",
            "SORTNAME": "重大诉讼",
            "F002D": null,
            "F001D": "2006-06-15 08:57:35",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "01230901",
            "SORTNAME": "重大诉讼公告",
            "F002D": null,
            "F001D": "2015-01-06 17:25:43",
            "PARENTCODE": "012309"
        },
        {
            "SORTCODE": "01230910",
            "SORTNAME": "诉讼事项进展公告",
            "F002D": null,
            "F001D": "2015-01-06 17:25:55",
            "PARENTCODE": "012309"
        },
        {
            "SORTCODE": "01230920",
            "SORTNAME": "诉讼判决公告",
            "F002D": null,
            "F001D": "2015-01-06 17:26:04",
            "PARENTCODE": "012309"
        },
        {
            "SORTCODE": "01230930",
            "SORTNAME": "判决执行公告",
            "F002D": null,
            "F001D": "2015-01-06 17:26:10",
            "PARENTCODE": "012309"
        },
        {
            "SORTCODE": "012311",
            "SORTNAME": "重大仲裁",
            "F002D": null,
            "F001D": "2006-06-15 08:57:40",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "01231101",
            "SORTNAME": "重大仲裁公告",
            "F002D": null,
            "F001D": "2015-01-06 17:26:39",
            "PARENTCODE": "012311"
        },
        {
            "SORTCODE": "01231110",
            "SORTNAME": "仲裁事项进展公告",
            "F002D": null,
            "F001D": "2015-01-06 17:26:26",
            "PARENTCODE": "012311"
        },
        {
            "SORTCODE": "01231120",
            "SORTNAME": "仲裁事项裁决公告",
            "F002D": null,
            "F001D": "2015-01-06 17:26:46",
            "PARENTCODE": "012311"
        },
        {
            "SORTCODE": "01231130",
            "SORTNAME": "裁决执行公告",
            "F002D": null,
            "F001D": "2015-01-06 17:31:50",
            "PARENTCODE": "012311"
        },
        {
            "SORTCODE": "012313",
            "SORTNAME": "重大损失",
            "F002D": null,
            "F001D": "2006-06-15 08:57:45",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "01231301",
            "SORTNAME": "大额银行退票",
            "F002D": "2008-07-07 14:52:18",
            "F001D": "2006-06-15 08:57:46",
            "PARENTCODE": "012313"
        },
        {
            "SORTCODE": "01231310",
            "SORTNAME": "遭受不可抗力重大损失",
            "F002D": "2008-07-07 14:52:25",
            "F001D": "2006-06-15 08:57:47",
            "PARENTCODE": "012313"
        },
        {
            "SORTCODE": "01231320",
            "SORTNAME": "可能依法承担的赔偿责任",
            "F002D": "2008-07-07 14:52:32",
            "F001D": "2006-06-15 08:57:48",
            "PARENTCODE": "012313"
        },
        {
            "SORTCODE": "01231330",
            "SORTNAME": "主要债务人进入破产程序",
            "F002D": "2008-07-07 14:52:40",
            "F001D": "2006-06-15 08:57:49",
            "PARENTCODE": "012313"
        },
        {
            "SORTCODE": "012315",
            "SORTNAME": "募集资金使用",
            "F002D": null,
            "F001D": "2006-06-15 08:57:50",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "01231501",
            "SORTNAME": "变更募股资金用途公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:51",
            "PARENTCODE": "012315"
        },
        {
            "SORTCODE": "01231510",
            "SORTNAME": "募集资金使用进展情况公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:52",
            "PARENTCODE": "012315"
        },
        {
            "SORTCODE": "01231520",
            "SORTNAME": "前次募集资金使用情况公告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:53",
            "PARENTCODE": "012315"
        },
        {
            "SORTCODE": "01231530",
            "SORTNAME": "募集资金使用专项报告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:54",
            "PARENTCODE": "012315"
        },
        {
            "SORTCODE": "01231540",
            "SORTNAME": "回访报告",
            "F002D": null,
            "F001D": "2006-06-15 08:57:55",
            "PARENTCODE": "012315"
        },
        {
            "SORTCODE": "01231550",
            "SORTNAME": "签订募集资金监管协议",
            "F002D": null,
            "F001D": "2007-01-30 10:30:20",
            "PARENTCODE": "012315"
        },
        {
            "SORTCODE": "012317",
            "SORTNAME": "公司处罚、整改及自查",
            "F002D": null,
            "F001D": "2006-06-15 08:58:01",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "01231701",
            "SORTNAME": "因涉嫌违反证券法规被监管机构调查或正受到处罚",
            "F002D": null,
            "F001D": "2015-01-06 17:02:36",
            "PARENTCODE": "012317"
        },
        {
            "SORTCODE": "01231710",
            "SORTNAME": "重大行政处罚",
            "F002D": null,
            "F001D": "2015-01-06 17:03:15",
            "PARENTCODE": "012317"
        },
        {
            "SORTCODE": "01231720",
            "SORTNAME": "公开谴责",
            "F002D": "2008-07-07 14:53:37",
            "F001D": "2006-06-15 08:58:04",
            "PARENTCODE": "012317"
        },
        {
            "SORTCODE": "01231730",
            "SORTNAME": "公司高管人员受处罚",
            "F002D": "2008-07-07 14:53:46",
            "F001D": "2006-06-15 08:58:05",
            "PARENTCODE": "012317"
        },
        {
            "SORTCODE": "01231740",
            "SORTNAME": "公开批评",
            "F002D": "2008-07-07 14:53:59",
            "F001D": "2006-06-15 08:58:06",
            "PARENTCODE": "012317"
        },
        {
            "SORTCODE": "01231750",
            "SORTNAME": "内部通报批评",
            "F002D": "2008-07-07 14:54:30",
            "F001D": "2006-06-15 08:58:07",
            "PARENTCODE": "012317"
        },
        {
            "SORTCODE": "01231760",
            "SORTNAME": "整改报告",
            "F002D": null,
            "F001D": "2015-01-06 17:03:32",
            "PARENTCODE": "012317"
        },
        {
            "SORTCODE": "01231770",
            "SORTNAME": "自查报告",
            "F002D": "2008-07-07 14:54:46",
            "F001D": "2006-06-15 08:58:09",
            "PARENTCODE": "012317"
        },
        {
            "SORTCODE": "01231780",
            "SORTNAME": "建立现代企业制度的自查报告",
            "F002D": "2008-07-07 14:54:55",
            "F001D": "2006-06-15 08:58:10",
            "PARENTCODE": "012317"
        },
        {
            "SORTCODE": "01231790",
            "SORTNAME": "公司接受调查的提示公告",
            "F002D": "2008-07-07 14:55:03",
            "F001D": "2006-06-15 08:58:11",
            "PARENTCODE": "012317"
        },
        {
            "SORTCODE": "012319",
            "SORTNAME": "破产、清算事项",
            "F002D": null,
            "F001D": "2006-06-15 08:58:12",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "01231901",
            "SORTNAME": "上市公司进入破产、清算状态",
            "F002D": "2008-07-07 14:55:19",
            "F001D": "2006-06-15 08:58:13",
            "PARENTCODE": "012319"
        },
        {
            "SORTCODE": "01231910",
            "SORTNAME": "法院发布受理破产公告",
            "F002D": "2008-07-07 14:55:26",
            "F001D": "2006-06-15 08:58:14",
            "PARENTCODE": "012319"
        },
        {
            "SORTCODE": "01231920",
            "SORTNAME": "法院发布终结破产程序公告",
            "F002D": "2008-07-07 14:55:35",
            "F001D": "2006-06-15 08:58:15",
            "PARENTCODE": "012319"
        },
        {
            "SORTCODE": "01231930",
            "SORTNAME": "法院宣告破产的公告",
            "F002D": "2008-07-07 14:55:47",
            "F001D": "2006-06-15 08:58:16",
            "PARENTCODE": "012319"
        },
        {
            "SORTCODE": "01231940",
            "SORTNAME": "上市公司申请破产公告",
            "F002D": "2008-07-07 14:55:59",
            "F001D": "2006-06-15 08:58:17",
            "PARENTCODE": "012319"
        },
        {
            "SORTCODE": "01231950",
            "SORTNAME": "上市公司公告法院受理破产的公告",
            "F002D": "2008-07-07 14:56:09",
            "F001D": "2006-06-15 08:58:18",
            "PARENTCODE": "012319"
        },
        {
            "SORTCODE": "01231960",
            "SORTNAME": "上市公司公告法院终结破产程序公告",
            "F002D": "2008-07-07 14:56:23",
            "F001D": "2006-06-15 08:58:19",
            "PARENTCODE": "012319"
        },
        {
            "SORTCODE": "01231970",
            "SORTNAME": "破产清算进展",
            "F002D": null,
            "F001D": "2015-01-06 17:32:58",
            "PARENTCODE": "012319"
        },
        {
            "SORTCODE": "012321",
            "SORTNAME": "决议被依法撤销事项",
            "F002D": null,
            "F001D": "2006-06-15 08:58:20",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "01232101",
            "SORTNAME": "股东大会决议被依法撤销",
            "F002D": null,
            "F001D": "2006-06-15 08:58:21",
            "PARENTCODE": "012321"
        },
        {
            "SORTCODE": "01232110",
            "SORTNAME": "董事会决议被依法撤销",
            "F002D": null,
            "F001D": "2006-06-15 08:58:22",
            "PARENTCODE": "012321"
        },
        {
            "SORTCODE": "012323",
            "SORTNAME": "换股",
            "F002D": null,
            "F001D": "2006-06-15 08:58:23",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "01232301",
            "SORTNAME": "换购说明书",
            "F002D": null,
            "F001D": "2006-06-15 08:58:24",
            "PARENTCODE": "012323"
        },
        {
            "SORTCODE": "01232310",
            "SORTNAME": "换购公告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:25",
            "PARENTCODE": "012323"
        },
        {
            "SORTCODE": "012325",
            "SORTNAME": "股权激励",
            "F002D": null,
            "F001D": "2006-06-29 11:13:31",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "012327",
            "SORTNAME": "重大合同",
            "F002D": null,
            "F001D": "2006-12-07 12:23:03",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "012329",
            "SORTNAME": "调研信息",
            "F002D": null,
            "F001D": "2021-12-06 08:55:27",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "012330",
            "SORTNAME": "环境与社会责任报告",
            "F002D": null,
            "F001D": "2022-04-21 00:00:00",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "01233001",
            "SORTNAME": "环境社会责任及公司管治报告",
            "F002D": null,
            "F001D": "2023-05-15 00:00:00",
            "PARENTCODE": "012330"
        },
        {
            "SORTCODE": "01233010",
            "SORTNAME": "社会责任报告",
            "F002D": null,
            "F001D": "2023-05-15 00:00:00",
            "PARENTCODE": "012330"
        },
        {
            "SORTCODE": "01233015",
            "SORTNAME": "可持续发展报告",
            "F002D": null,
            "F001D": "2023-05-15 00:00:00",
            "PARENTCODE": "012330"
        },
        {
            "SORTCODE": "01233020",
            "SORTNAME": "环境信息披露报告",
            "F002D": null,
            "F001D": "2023-05-15 00:00:00",
            "PARENTCODE": "012330"
        },
        {
            "SORTCODE": "012331",
            "SORTNAME": "做市交易业务",
            "F002D": null,
            "F001D": "2024-04-10 00:00:00",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "012333",
            "SORTNAME": "质量回报双提升",
            "F002D": null,
            "F001D": "2024-09-11 15:00:00",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "012399",
            "SORTNAME": "其它事项公告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:26",
            "PARENTCODE": "0123"
        },
        {
            "SORTCODE": "01239901",
            "SORTNAME": "其它董事会（决议）公告",
            "F002D": null,
            "F001D": "2015-01-06 17:06:25",
            "PARENTCODE": "012399"
        },
        {
            "SORTCODE": "01239910",
            "SORTNAME": "其它监事会（决议）公告",
            "F002D": null,
            "F001D": "2015-01-06 17:06:34",
            "PARENTCODE": "012399"
        },
        {
            "SORTCODE": "01239930",
            "SORTNAME": "其它证券市场公告",
            "F002D": null,
            "F001D": "2015-01-06 00:00:00",
            "PARENTCODE": "012399"
        },
        {
            "SORTCODE": "01239999",
            "SORTNAME": "其它临时公告",
            "F002D": null,
            "F001D": "2015-01-06 17:33:15",
            "PARENTCODE": "012399"
        },
        {
            "SORTCODE": "0125",
            "SORTNAME": "特别处理和退市",
            "F002D": null,
            "F001D": "2006-06-15 08:58:30",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "012501",
            "SORTNAME": "特别处理",
            "F002D": null,
            "F001D": "2006-06-15 08:58:31",
            "PARENTCODE": "0125"
        },
        {
            "SORTCODE": "01250101",
            "SORTNAME": "实施特别处理公告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:32",
            "PARENTCODE": "012501"
        },
        {
            "SORTCODE": "01250110",
            "SORTNAME": "实施警示终止上市风险的特别处理公告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:33",
            "PARENTCODE": "012501"
        },
        {
            "SORTCODE": "01250120",
            "SORTNAME": "撤销特别处理公告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:34",
            "PARENTCODE": "012501"
        },
        {
            "SORTCODE": "012503",
            "SORTNAME": "暂停上市",
            "F002D": null,
            "F001D": "2006-06-15 08:58:35",
            "PARENTCODE": "0125"
        },
        {
            "SORTCODE": "01250301",
            "SORTNAME": "暂停上市提示公告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:36",
            "PARENTCODE": "012503"
        },
        {
            "SORTCODE": "01250310",
            "SORTNAME": "暂停上市前的停牌公告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:37",
            "PARENTCODE": "012503"
        },
        {
            "SORTCODE": "01250320",
            "SORTNAME": "暂停特别转让公告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:38",
            "PARENTCODE": "012503"
        },
        {
            "SORTCODE": "01250330",
            "SORTNAME": "恢复特别转让公告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:39",
            "PARENTCODE": "012503"
        },
        {
            "SORTCODE": "01250340",
            "SORTNAME": "暂停上市公告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:40",
            "PARENTCODE": "012503"
        },
        {
            "SORTCODE": "012505",
            "SORTNAME": "恢复上市",
            "F002D": null,
            "F001D": "2006-06-15 08:58:41",
            "PARENTCODE": "0125"
        },
        {
            "SORTCODE": "01250501",
            "SORTNAME": "宽限期申请的相关公告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:42",
            "PARENTCODE": "012505"
        },
        {
            "SORTCODE": "01250510",
            "SORTNAME": "恢复上市申请",
            "F002D": null,
            "F001D": "2006-06-15 08:58:43",
            "PARENTCODE": "012505"
        },
        {
            "SORTCODE": "01250520",
            "SORTNAME": "恢复上市推荐书",
            "F002D": null,
            "F001D": "2006-06-15 08:58:44",
            "PARENTCODE": "012505"
        },
        {
            "SORTCODE": "01250530",
            "SORTNAME": "恢复上市进展公告",
            "F002D": null,
            "F001D": "2008-05-14 16:38:52",
            "PARENTCODE": "012505"
        },
        {
            "SORTCODE": "012507",
            "SORTNAME": "终止上市",
            "F002D": null,
            "F001D": "2006-06-15 08:58:45",
            "PARENTCODE": "0125"
        },
        {
            "SORTCODE": "01250701",
            "SORTNAME": "终止上市提示公告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:46",
            "PARENTCODE": "012507"
        },
        {
            "SORTCODE": "01250710",
            "SORTNAME": "终止上市公告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:47",
            "PARENTCODE": "012507"
        },
        {
            "SORTCODE": "012509",
            "SORTNAME": "退市期公司公告",
            "F002D": null,
            "F001D": "2012-12-22 10:21:03",
            "PARENTCODE": "0125"
        },
        {
            "SORTCODE": "0127",
            "SORTNAME": "补充及更正",
            "F002D": null,
            "F001D": "2006-06-15 08:58:48",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "012701",
            "SORTNAME": "定期报告补充、更正",
            "F002D": null,
            "F001D": "2006-06-15 08:58:49",
            "PARENTCODE": "0127"
        },
        {
            "SORTCODE": "01270101",
            "SORTNAME": "定期报告的补充公告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:50",
            "PARENTCODE": "012701"
        },
        {
            "SORTCODE": "01270110",
            "SORTNAME": "定期报告的更正公告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:51",
            "PARENTCODE": "012701"
        },
        {
            "SORTCODE": "012703",
            "SORTNAME": "临时报告补充、更正",
            "F002D": null,
            "F001D": "2006-06-15 08:58:52",
            "PARENTCODE": "0127"
        },
        {
            "SORTCODE": "01270301",
            "SORTNAME": "临时报告补充公告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:53",
            "PARENTCODE": "012703"
        },
        {
            "SORTCODE": "01270310",
            "SORTNAME": "临时报告更正公告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:54",
            "PARENTCODE": "012703"
        },
        {
            "SORTCODE": "012799",
            "SORTNAME": "其它补充、更正公告",
            "F002D": "2008-07-07 14:57:57",
            "F001D": "2006-06-15 08:58:55",
            "PARENTCODE": "0127"
        },
        {
            "SORTCODE": "01279901",
            "SORTNAME": "误导公告",
            "F002D": "2008-07-07 14:57:57",
            "F001D": "2006-06-15 08:58:56",
            "PARENTCODE": "012799"
        },
        {
            "SORTCODE": "01279910",
            "SORTNAME": "遗漏公告",
            "F002D": "2008-07-07 14:57:57",
            "F001D": "2006-06-15 08:58:57",
            "PARENTCODE": "012799"
        },
        {
            "SORTCODE": "01279920",
            "SORTNAME": "技术性差错公告",
            "F002D": "2008-07-07 14:57:57",
            "F001D": "2006-06-15 08:58:58",
            "PARENTCODE": "012799"
        },
        {
            "SORTCODE": "0129",
            "SORTNAME": "中介机构报告",
            "F002D": null,
            "F001D": "2006-06-15 08:58:59",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "012901",
            "SORTNAME": "独立财务顾问报告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:01",
            "PARENTCODE": "0129"
        },
        {
            "SORTCODE": "012903",
            "SORTNAME": "法律意见书",
            "F002D": null,
            "F001D": "2006-06-15 08:59:02",
            "PARENTCODE": "0129"
        },
        {
            "SORTCODE": "012905",
            "SORTNAME": "资产评估报告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:03",
            "PARENTCODE": "0129"
        },
        {
            "SORTCODE": "012907",
            "SORTNAME": "项目可行性分析报告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:04",
            "PARENTCODE": "0129"
        },
        {
            "SORTCODE": "012909",
            "SORTNAME": "证券咨询机构投资分析报告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:05",
            "PARENTCODE": "0129"
        },
        {
            "SORTCODE": "012911",
            "SORTNAME": "保荐意见书",
            "F002D": null,
            "F001D": "2006-06-26 09:27:18",
            "PARENTCODE": "0129"
        },
        {
            "SORTCODE": "012913",
            "SORTNAME": "审计报告",
            "F002D": null,
            "F001D": "2007-01-30 10:31:09",
            "PARENTCODE": "0129"
        },
        {
            "SORTCODE": "012915",
            "SORTNAME": "财务顾问持续督导意见",
            "F002D": null,
            "F001D": "2012-07-10 11:17:16",
            "PARENTCODE": "0129"
        },
        {
            "SORTCODE": "012917",
            "SORTNAME": "保荐机构持续督导意见",
            "F002D": null,
            "F001D": "2012-07-10 11:17:37",
            "PARENTCODE": "0129"
        },
        {
            "SORTCODE": "0131",
            "SORTNAME": "上市公司制度",
            "F002D": null,
            "F001D": "2006-06-15 08:59:06",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "013101",
            "SORTNAME": "公司章程",
            "F002D": null,
            "F001D": "2006-06-15 08:59:07",
            "PARENTCODE": "0131"
        },
        {
            "SORTCODE": "013103",
            "SORTNAME": "股东大会与监事会",
            "F002D": null,
            "F001D": "2006-06-15 08:59:08",
            "PARENTCODE": "0131"
        },
        {
            "SORTCODE": "01310301",
            "SORTNAME": "股东大会议事规则",
            "F002D": null,
            "F001D": "2006-06-15 08:59:09",
            "PARENTCODE": "013103"
        },
        {
            "SORTCODE": "01310310",
            "SORTNAME": "监事会议事规则",
            "F002D": null,
            "F001D": "2006-06-15 08:59:10",
            "PARENTCODE": "013103"
        },
        {
            "SORTCODE": "013105",
            "SORTNAME": "董事与董事会",
            "F002D": null,
            "F001D": "2006-06-15 08:59:11",
            "PARENTCODE": "0131"
        },
        {
            "SORTCODE": "01310501",
            "SORTNAME": "董事会议事规则",
            "F002D": null,
            "F001D": "2006-06-15 08:59:12",
            "PARENTCODE": "013105"
        },
        {
            "SORTCODE": "01310505",
            "SORTNAME": "董事会战略委员会议事规则",
            "F002D": null,
            "F001D": "2006-06-15 08:59:13",
            "PARENTCODE": "013105"
        },
        {
            "SORTCODE": "01310510",
            "SORTNAME": "董事会提名委员会议事规则",
            "F002D": null,
            "F001D": "2006-06-15 08:59:14",
            "PARENTCODE": "013105"
        },
        {
            "SORTCODE": "01310515",
            "SORTNAME": "董事会审计委员会议事规则",
            "F002D": null,
            "F001D": "2006-06-15 08:59:15",
            "PARENTCODE": "013105"
        },
        {
            "SORTCODE": "01310520",
            "SORTNAME": "董事会薪酬与考核委员会议事规则",
            "F002D": null,
            "F001D": "2006-06-15 08:59:16",
            "PARENTCODE": "013105"
        },
        {
            "SORTCODE": "01310525",
            "SORTNAME": "董事会战略委员会实施细则",
            "F002D": null,
            "F001D": "2006-06-15 08:59:17",
            "PARENTCODE": "013105"
        },
        {
            "SORTCODE": "01310530",
            "SORTNAME": "董事会薪酬与考核委员会实施细则",
            "F002D": null,
            "F001D": "2006-06-15 08:59:18",
            "PARENTCODE": "013105"
        },
        {
            "SORTCODE": "01310535",
            "SORTNAME": "董事会薪酬与考核委员会实施细则",
            "F002D": "2013-07-26 08:49:38",
            "F001D": "2006-06-15 08:59:19",
            "PARENTCODE": "013105"
        },
        {
            "SORTCODE": "01310540",
            "SORTNAME": "董事会投资审查与决策程序的规定",
            "F002D": null,
            "F001D": "2006-06-15 08:59:20",
            "PARENTCODE": "013105"
        },
        {
            "SORTCODE": "01310545",
            "SORTNAME": "独立董事工作制度",
            "F002D": null,
            "F001D": "2006-06-15 08:59:21",
            "PARENTCODE": "013105"
        },
        {
            "SORTCODE": "01310550",
            "SORTNAME": "独立董事候选人及提名人声明",
            "F002D": null,
            "F001D": "2006-06-15 08:59:22",
            "PARENTCODE": "013105"
        },
        {
            "SORTCODE": "01310555",
            "SORTNAME": "独立董事声明及承诺书",
            "F002D": null,
            "F001D": "2006-06-15 08:59:23",
            "PARENTCODE": "013105"
        },
        {
            "SORTCODE": "01310560",
            "SORTNAME": "独立董事履历表",
            "F002D": null,
            "F001D": "2006-06-15 08:59:24",
            "PARENTCODE": "013105"
        },
        {
            "SORTCODE": "01310565",
            "SORTNAME": "独立董事意见",
            "F002D": null,
            "F001D": "2006-06-15 08:59:25",
            "PARENTCODE": "013105"
        },
        {
            "SORTCODE": "013199",
            "SORTNAME": "其它治理准则",
            "F002D": null,
            "F001D": "2006-06-15 08:59:26",
            "PARENTCODE": "0131"
        },
        {
            "SORTCODE": "01319901",
            "SORTNAME": "信息披露管理办法",
            "F002D": null,
            "F001D": "2006-06-15 08:59:27",
            "PARENTCODE": "013199"
        },
        {
            "SORTCODE": "01319910",
            "SORTNAME": "总裁工作细则",
            "F002D": null,
            "F001D": "2006-06-15 08:59:28",
            "PARENTCODE": "013199"
        },
        {
            "SORTCODE": "01319915",
            "SORTNAME": "反舞弊制度",
            "F002D": null,
            "F001D": "2023-05-15 00:00:00",
            "PARENTCODE": "013199"
        },
        {
            "SORTCODE": "01319920",
            "SORTNAME": "社会责任管理制度",
            "F002D": null,
            "F001D": "2023-06-06 00:00:00",
            "PARENTCODE": "013199"
        },
        {
            "SORTCODE": "0133",
            "SORTNAME": "基金招募及设立",
            "F002D": null,
            "F001D": "2006-06-15 08:59:29",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "013301",
            "SORTNAME": "招募说明书",
            "F002D": null,
            "F001D": "2006-06-15 08:59:30",
            "PARENTCODE": "0133"
        },
        {
            "SORTCODE": "013303",
            "SORTNAME": "发行公告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:31",
            "PARENTCODE": "0133"
        },
        {
            "SORTCODE": "013305",
            "SORTNAME": "基金募集期变动公告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:32",
            "PARENTCODE": "0133"
        },
        {
            "SORTCODE": "013307",
            "SORTNAME": "发行结果公告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:33",
            "PARENTCODE": "0133"
        },
        {
            "SORTCODE": "013309",
            "SORTNAME": "基金成立或基金合同生效公告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:34",
            "PARENTCODE": "0133"
        },
        {
            "SORTCODE": "013311",
            "SORTNAME": "基金份额上市交易公告书",
            "F002D": null,
            "F001D": "2006-06-15 08:59:35",
            "PARENTCODE": "0133"
        },
        {
            "SORTCODE": "013313",
            "SORTNAME": "基金合同",
            "F002D": null,
            "F001D": "2006-06-15 08:59:36",
            "PARENTCODE": "0133"
        },
        {
            "SORTCODE": "013399",
            "SORTNAME": "其它发行事项公告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:37",
            "PARENTCODE": "0133"
        },
        {
            "SORTCODE": "0135",
            "SORTNAME": "基金定期报告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:38",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "013501",
            "SORTNAME": "年度报告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:39",
            "PARENTCODE": "0135"
        },
        {
            "SORTCODE": "013503",
            "SORTNAME": "半年度报告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:40",
            "PARENTCODE": "0135"
        },
        {
            "SORTCODE": "013505",
            "SORTNAME": "季度报告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:41",
            "PARENTCODE": "0135"
        },
        {
            "SORTCODE": "013507",
            "SORTNAME": "投资组合报告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:42",
            "PARENTCODE": "0135"
        },
        {
            "SORTCODE": "013509",
            "SORTNAME": "基金资产净值公告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:43",
            "PARENTCODE": "0135"
        },
        {
            "SORTCODE": "013511",
            "SORTNAME": "公开说明书（开放基金）",
            "F002D": null,
            "F001D": "2006-06-15 08:59:44",
            "PARENTCODE": "0135"
        },
        {
            "SORTCODE": "013599",
            "SORTNAME": "其它报告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:45",
            "PARENTCODE": "0135"
        },
        {
            "SORTCODE": "0137",
            "SORTNAME": "基金临时报告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:46",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "013701",
            "SORTNAME": "召开基金持有人大会的通知",
            "F002D": null,
            "F001D": "2006-06-15 08:59:47",
            "PARENTCODE": "0137"
        },
        {
            "SORTCODE": "013702",
            "SORTNAME": "基金份额持有人大会表决结果的公告",
            "F002D": null,
            "F001D": "2007-01-30 10:31:34",
            "PARENTCODE": "0137"
        },
        {
            "SORTCODE": "013703",
            "SORTNAME": "申购及赎回事项",
            "F002D": null,
            "F001D": "2006-06-15 08:59:48",
            "PARENTCODE": "0137"
        },
        {
            "SORTCODE": "01370301",
            "SORTNAME": "开放式基金开始办理申购、赎回；",
            "F002D": null,
            "F001D": "2015-01-06 17:23:42",
            "PARENTCODE": "013703"
        },
        {
            "SORTCODE": "01370305",
            "SORTNAME": "开放式基金申购、赎回费率及其收费方式发生变更",
            "F002D": null,
            "F001D": "2015-01-06 17:23:51",
            "PARENTCODE": "013703"
        },
        {
            "SORTCODE": "01370310",
            "SORTNAME": "开放式基金发生巨额赎回并延期支付；",
            "F002D": "2008-07-07 14:59:30",
            "F001D": "2006-06-15 08:59:51",
            "PARENTCODE": "013703"
        },
        {
            "SORTCODE": "01370315",
            "SORTNAME": "开放式基金连续发生巨额赎回并暂停接受赎回申请",
            "F002D": "2008-07-07 14:59:39",
            "F001D": "2006-06-15 08:59:52",
            "PARENTCODE": "013703"
        },
        {
            "SORTCODE": "01370320",
            "SORTNAME": "开放式基金暂停接受申购、赎回申请后重新接受申购、赎回",
            "F002D": null,
            "F001D": "2015-01-06 17:24:04",
            "PARENTCODE": "013703"
        },
        {
            "SORTCODE": "013705",
            "SORTNAME": "基金管理人、基金托管人的基金托管部门的重大人事变动",
            "F002D": null,
            "F001D": "2006-06-15 08:59:54",
            "PARENTCODE": "0137"
        },
        {
            "SORTCODE": "013707",
            "SORTNAME": "基金管理人股东及其出资比例发生变更",
            "F002D": null,
            "F001D": "2006-06-15 08:59:55",
            "PARENTCODE": "0137"
        },
        {
            "SORTCODE": "013709",
            "SORTNAME": "基金管理人、基金托管人或其高管人员受调查或处罚",
            "F002D": null,
            "F001D": "2006-06-15 08:59:56",
            "PARENTCODE": "0137"
        },
        {
            "SORTCODE": "013711",
            "SORTNAME": "重大诉讼、仲裁事项",
            "F002D": null,
            "F001D": "2006-06-15 08:59:57",
            "PARENTCODE": "0137"
        },
        {
            "SORTCODE": "013713",
            "SORTNAME": "基金收益分配事项",
            "F002D": null,
            "F001D": "2006-06-15 08:59:58",
            "PARENTCODE": "0137"
        },
        {
            "SORTCODE": "013715",
            "SORTNAME": "重大关联交易事项",
            "F002D": null,
            "F001D": "2006-06-15 08:59:59",
            "PARENTCODE": "0137"
        },
        {
            "SORTCODE": "013717",
            "SORTNAME": "基金份额净值计价错误公告",
            "F002D": null,
            "F001D": "2006-06-15 08:59:59",
            "PARENTCODE": "0137"
        },
        {
            "SORTCODE": "013719",
            "SORTNAME": "基金提前中止",
            "F002D": null,
            "F001D": "2006-06-15 09:00:01",
            "PARENTCODE": "0137"
        },
        {
            "SORTCODE": "013721",
            "SORTNAME": "延长基金合同期限",
            "F002D": null,
            "F001D": "2006-06-15 09:00:02",
            "PARENTCODE": "0137"
        },
        {
            "SORTCODE": "013723",
            "SORTNAME": "转换基金运作方式",
            "F002D": null,
            "F001D": "2006-06-15 09:00:03",
            "PARENTCODE": "0137"
        },
        {
            "SORTCODE": "013725",
            "SORTNAME": "各类变更公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:04",
            "PARENTCODE": "0137"
        },
        {
            "SORTCODE": "01372501",
            "SORTNAME": "基金管理人或基金托管人变更",
            "F002D": null,
            "F001D": "2015-01-06 17:24:22",
            "PARENTCODE": "013725"
        },
        {
            "SORTCODE": "01372505",
            "SORTNAME": "基金管理人、基金托管人的法定名称、住所发生变更",
            "F002D": "2008-07-07 15:00:15",
            "F001D": "2006-06-15 09:00:06",
            "PARENTCODE": "013725"
        },
        {
            "SORTCODE": "01372510",
            "SORTNAME": "管理费、托管费等费用计提标准、计提方式和费率发生变更",
            "F002D": "2008-07-07 15:00:22",
            "F001D": "2006-06-15 09:00:07",
            "PARENTCODE": "013725"
        },
        {
            "SORTCODE": "01372515",
            "SORTNAME": "基金改聘会计师事务所",
            "F002D": "2008-07-07 15:00:32",
            "F001D": "2006-06-15 09:00:08",
            "PARENTCODE": "013725"
        },
        {
            "SORTCODE": "01372520",
            "SORTNAME": "变更基金份额发售机构",
            "F002D": null,
            "F001D": "2015-01-06 17:24:33",
            "PARENTCODE": "013725"
        },
        {
            "SORTCODE": "01372525",
            "SORTNAME": "基金更换注册登记机构",
            "F002D": "2008-07-07 15:00:47",
            "F001D": "2006-06-15 09:00:10",
            "PARENTCODE": "013725"
        },
        {
            "SORTCODE": "013727",
            "SORTNAME": "澄清公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:11",
            "PARENTCODE": "0137"
        },
        {
            "SORTCODE": "013799",
            "SORTNAME": "其它重大事项",
            "F002D": null,
            "F001D": "2006-06-15 09:00:12",
            "PARENTCODE": "0137"
        },
        {
            "SORTCODE": "0139",
            "SORTNAME": "债券公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:13",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "013901",
            "SORTNAME": "债券发行上市",
            "F002D": null,
            "F001D": "2006-06-15 09:00:14",
            "PARENTCODE": "0139"
        },
        {
            "SORTCODE": "013903",
            "SORTNAME": "债券定期公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:15",
            "PARENTCODE": "0139"
        },
        {
            "SORTCODE": "013904",
            "SORTNAME": "债券付息公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:16",
            "PARENTCODE": "0139"
        },
        {
            "SORTCODE": "013905",
            "SORTNAME": "债券到期兑付、停止交易公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:17",
            "PARENTCODE": "0139"
        },
        {
            "SORTCODE": "013906",
            "SORTNAME": "债权人相关公告",
            "F002D": null,
            "F001D": "2024-09-12 00:00:00",
            "PARENTCODE": "0139"
        },
        {
            "SORTCODE": "013999",
            "SORTNAME": "债券其它公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:18",
            "PARENTCODE": "0139"
        },
        {
            "SORTCODE": "0141",
            "SORTNAME": "交易所、结算公司公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:19",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "014101",
            "SORTNAME": "主板停复牌公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:20",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014102",
            "SORTNAME": "中小盘企业板停复牌公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:21",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014103",
            "SORTNAME": "主板公开信息",
            "F002D": null,
            "F001D": "2006-06-15 09:00:22",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014104",
            "SORTNAME": "中小盘企业板公开信息",
            "F002D": null,
            "F001D": "2006-06-15 09:00:23",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014105",
            "SORTNAME": "大宗交易公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:24",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014106",
            "SORTNAME": "中小盘企业板其他公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:25",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014107",
            "SORTNAME": "业务通知",
            "F002D": null,
            "F001D": "2006-06-15 09:00:26",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014108",
            "SORTNAME": "基金公开信息",
            "F002D": null,
            "F001D": "2007-05-31 16:42:30",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014109",
            "SORTNAME": "内部批评",
            "F002D": null,
            "F001D": "2006-06-15 09:00:27",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014111",
            "SORTNAME": "公开谴责",
            "F002D": null,
            "F001D": "2006-06-15 09:00:28",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014113",
            "SORTNAME": "处罚",
            "F002D": null,
            "F001D": "2006-06-15 09:00:29",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014115",
            "SORTNAME": "结算业务公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:30",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014117",
            "SORTNAME": "公司管理部业务通知",
            "F002D": "2008-07-07 15:01:22",
            "F001D": "2006-06-15 09:00:31",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014119",
            "SORTNAME": "市场行情",
            "F002D": null,
            "F001D": "2006-06-15 09:00:32",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014120",
            "SORTNAME": "创业板市场行情",
            "F002D": null,
            "F001D": "2009-04-10 19:03:38",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014121",
            "SORTNAME": "市场概况",
            "F002D": null,
            "F001D": "2006-06-15 09:00:33",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014122",
            "SORTNAME": "创业板市场总貌",
            "F002D": null,
            "F001D": "2009-04-10 19:04:43",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014123",
            "SORTNAME": "重大事项停牌公告",
            "F002D": null,
            "F001D": "2007-01-30 10:21:31",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014124",
            "SORTNAME": "创业板停复牌公告",
            "F002D": null,
            "F001D": "2008-03-24 14:04:42",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014125",
            "SORTNAME": "创业板公开信息",
            "F002D": null,
            "F001D": "2008-03-24 14:05:54",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014127",
            "SORTNAME": "创业板其他公告",
            "F002D": null,
            "F001D": "2008-03-24 14:06:37",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014129",
            "SORTNAME": "交易风险提示",
            "F002D": null,
            "F001D": "2008-05-14 16:46:07",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014131",
            "SORTNAME": "科创板停复牌公告",
            "F002D": null,
            "F001D": "2019-05-15 08:55:27",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014133",
            "SORTNAME": "北交所停复牌公告",
            "F002D": null,
            "F001D": "2021-12-06 08:55:27",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "014199",
            "SORTNAME": "其它公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:34",
            "PARENTCODE": "0141"
        },
        {
            "SORTCODE": "0143",
            "SORTNAME": "代办股份转让公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:35",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "014301",
            "SORTNAME": "证券业协会公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:36",
            "PARENTCODE": "0143"
        },
        {
            "SORTCODE": "014303",
            "SORTNAME": "主办券商",
            "F002D": null,
            "F001D": "2006-06-15 09:00:37",
            "PARENTCODE": "0143"
        },
        {
            "SORTCODE": "01430301",
            "SORTNAME": "主办券商临时公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:38",
            "PARENTCODE": "014303"
        },
        {
            "SORTCODE": "01430305",
            "SORTNAME": "主办券商分析报告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:39",
            "PARENTCODE": "014303"
        },
        {
            "SORTCODE": "014305",
            "SORTNAME": "业务通知",
            "F002D": null,
            "F001D": "2006-06-15 09:00:40",
            "PARENTCODE": "0143"
        },
        {
            "SORTCODE": "0145",
            "SORTNAME": "特殊公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:41",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "014501",
            "SORTNAME": "历史公告摘要",
            "F002D": null,
            "F001D": "2006-06-15 09:00:42",
            "PARENTCODE": "0145"
        },
        {
            "SORTCODE": "0147",
            "SORTNAME": "股份报价转让系统公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:43",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "014701",
            "SORTNAME": "证券业协会公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:44",
            "PARENTCODE": "0147"
        },
        {
            "SORTCODE": "01470101",
            "SORTNAME": "业务通知",
            "F002D": null,
            "F001D": "2006-06-15 09:00:45",
            "PARENTCODE": "014701"
        },
        {
            "SORTCODE": "01470103",
            "SORTNAME": "违规处罚",
            "F002D": null,
            "F001D": "2006-06-15 09:00:46",
            "PARENTCODE": "014701"
        },
        {
            "SORTCODE": "01470109",
            "SORTNAME": "证监会、深交所业务通知",
            "F002D": null,
            "F001D": "2009-05-14 18:27:55",
            "PARENTCODE": "014701"
        },
        {
            "SORTCODE": "014703",
            "SORTNAME": "主办券商公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:47",
            "PARENTCODE": "0147"
        },
        {
            "SORTCODE": "014705",
            "SORTNAME": "分析报告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:48",
            "PARENTCODE": "0147"
        },
        {
            "SORTCODE": "014707",
            "SORTNAME": "公司公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:49",
            "PARENTCODE": "0147"
        },
        {
            "SORTCODE": "01470701",
            "SORTNAME": "临时公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:50",
            "PARENTCODE": "014707"
        },
        {
            "SORTCODE": "01470702",
            "SORTNAME": "定期报告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:51",
            "PARENTCODE": "014707"
        },
        {
            "SORTCODE": "0149",
            "SORTNAME": "产权公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:52",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "014901",
            "SORTNAME": "临时公告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:53",
            "PARENTCODE": "0149"
        },
        {
            "SORTCODE": "014902",
            "SORTNAME": "定期报告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:54",
            "PARENTCODE": "0149"
        },
        {
            "SORTCODE": "014903",
            "SORTNAME": "分析报告",
            "F002D": null,
            "F001D": "2006-06-15 09:00:55",
            "PARENTCODE": "0149"
        },
        {
            "SORTCODE": "014904",
            "SORTNAME": "非上市公司动态",
            "F002D": null,
            "F001D": "2009-11-20 10:39:14",
            "PARENTCODE": "0149"
        },
        {
            "SORTCODE": "014905",
            "SORTNAME": "非上市公司决议",
            "F002D": null,
            "F001D": "2009-11-20 10:39:34",
            "PARENTCODE": "0149"
        },
        {
            "SORTCODE": "014906",
            "SORTNAME": "非上市公司财务报告",
            "F002D": null,
            "F001D": "2009-11-20 10:39:52",
            "PARENTCODE": "0149"
        },
        {
            "SORTCODE": "0151",
            "SORTNAME": "注册期发行与上市",
            "F002D": null,
            "F001D": "2020-07-07 15:05:57",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "015101",
            "SORTNAME": "申报稿",
            "F002D": null,
            "F001D": "2020-07-07 15:05:57",
            "PARENTCODE": "0151"
        },
        {
            "SORTCODE": "015103",
            "SORTNAME": "上会稿",
            "F002D": null,
            "F001D": "2020-07-07 15:05:57",
            "PARENTCODE": "0151"
        },
        {
            "SORTCODE": "015105",
            "SORTNAME": "注册稿",
            "F002D": null,
            "F001D": "2020-07-07 15:05:58",
            "PARENTCODE": "0151"
        },
        {
            "SORTCODE": "015107",
            "SORTNAME": "问询与回复",
            "F002D": null,
            "F001D": "2020-07-07 15:05:58",
            "PARENTCODE": "0151"
        },
        {
            "SORTCODE": "015109",
            "SORTNAME": "封卷稿",
            "F002D": null,
            "F001D": "2022-02-22 08:55:27",
            "PARENTCODE": "0151"
        },
        {
            "SORTCODE": "0199",
            "SORTNAME": "紧急公告",
            "F002D": null,
            "F001D": "2006-06-28 10:33:48",
            "PARENTCODE": "01"
        },
        {
            "SORTCODE": "019901",
            "SORTNAME": "创业板紧急公告",
            "F002D": null,
            "F001D": "2008-03-24 14:06:52",
            "PARENTCODE": "0199"
        },
        {
            "SORTCODE": "02",
            "SORTNAME": "港股公告",
            "F002D": null,
            "F001D": "2010-02-16 17:24:43",
            "PARENTCODE": null
        },
        {
            "SORTCODE": "10000",
            "SORTNAME": "公告及通告",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "40"
        },
        {
            "SORTCODE": "11000",
            "SORTNAME": "关连交易",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "10000"
        },
        {
            "SORTCODE": "11100",
            "SORTNAME": "核数师或独立非执行董事未能确认有关持续关连交易的事宜",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "11000"
        },
        {
            "SORTCODE": "11200",
            "SORTNAME": "关连交易",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "11000"
        },
        {
            "SORTCODE": "11300",
            "SORTNAME": "持续关连交易",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "11000"
        },
        {
            "SORTCODE": "11400",
            "SORTNAME": "担保有形资产净值或溢利",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "11000"
        },
        {
            "SORTCODE": "11500",
            "SORTNAME": "就关连交易规定所授予的豁免",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "11000"
        },
        {
            "SORTCODE": "12000",
            "SORTNAME": "公司状况变动及委员会／公司变动",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "10000"
        },
        {
            "SORTCODE": "12050",
            "SORTNAME": "更改公司网址",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12100",
            "SORTNAME": "修订宪章文件",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12150",
            "SORTNAME": "更换核数师",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12200",
            "SORTNAME": "更改不同类别股份的权利",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12250",
            "SORTNAME": "更换合规顾问",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12300",
            "SORTNAME": "更换监察主任",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12350",
            "SORTNAME": "更换董事或重要行政职能或职责的变更",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12400",
            "SORTNAME": "更改财政年度结算日期",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12450",
            "SORTNAME": "更换合资格会计师(2009年1月1日前)",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12500",
            "SORTNAME": "更改注册地或办事处、香港业务注册地或香港接收法律程序文件代表",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12550",
            "SORTNAME": "更换公司秘书",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12600",
            "SORTNAME": "更换监事",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12650",
            "SORTNAME": "更换审核委员会成员",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12700",
            "SORTNAME": "更改公司名称",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12750",
            "SORTNAME": "未能符合审核委员会的规定",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12800",
            "SORTNAME": "未能符合监察主任的规定",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12850",
            "SORTNAME": "未能符合独立非执行董事规定或独立非执行董事未能符合独立性指引",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12900",
            "SORTNAME": "未能符合合资格会计师的规定(2009年1月1日前)",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12950",
            "SORTNAME": "董事或监事履历详情的变更",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12951",
            "SORTNAME": "更换行政总裁",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12952",
            "SORTNAME": "董事名单和他们的地位和作用",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12953",
            "SORTNAME": "未能符合薪酬委员会的规定",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12954",
            "SORTNAME": "审核委员会的职权范围",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12955",
            "SORTNAME": "提名委员会的职权范围",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12956",
            "SORTNAME": "薪酬委员会的职权范围",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12957",
            "SORTNAME": "更换薪酬委员会成员",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12958",
            "SORTNAME": "其他董事会辖下之委员会的职权范围",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "12959",
            "SORTNAME": "更换股份过户登记处/登记代理",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "12000"
        },
        {
            "SORTCODE": "13000",
            "SORTNAME": "财务资料",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "10000"
        },
        {
            "SORTCODE": "13100",
            "SORTNAME": "向实体提供垫款",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "13000"
        },
        {
            "SORTCODE": "13150",
            "SORTNAME": "董事会召开日期",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "13000"
        },
        {
            "SORTCODE": "13200",
            "SORTNAME": "延迟发表业绩公告",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "13000"
        },
        {
            "SORTCODE": "13250",
            "SORTNAME": "股息或分派",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "13000"
        },
        {
            "SORTCODE": "13251",
            "SORTNAME": "股息或分派（公告表格）",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "13000"
        },
        {
            "SORTCODE": "13300",
            "SORTNAME": "末期业绩",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "13000"
        },
        {
            "SORTCODE": "13350",
            "SORTNAME": "向联属公司提供财务资助及/或作出担保",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "13000"
        },
        {
            "SORTCODE": "13400",
            "SORTNAME": "中期业绩",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "13000"
        },
        {
            "SORTCODE": "13450",
            "SORTNAME": "资产净值",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "13000"
        },
        {
            "SORTCODE": "13500",
            "SORTNAME": "盈利警告",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "13000"
        },
        {
            "SORTCODE": "13550",
            "SORTNAME": "核数师发出「非标准报告」",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "13000"
        },
        {
            "SORTCODE": "13600",
            "SORTNAME": "季度业绩",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "13000"
        },
        {
            "SORTCODE": "13650",
            "SORTNAME": "附属公司的业绩",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "13000"
        },
        {
            "SORTCODE": "13700",
            "SORTNAME": "修订已刊发初步业绩的资料",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "13000"
        },
        {
            "SORTCODE": "13750",
            "SORTNAME": "修正重大错误而作出的前期调整",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "13000"
        },
        {
            "SORTCODE": "13800",
            "SORTNAME": "修改已刊发的财务报表及报告",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "13000"
        },
        {
            "SORTCODE": "14000",
            "SORTNAME": "会议／表决",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "10000"
        },
        {
            "SORTCODE": "14100",
            "SORTNAME": "更改表决意向",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "14000"
        },
        {
            "SORTCODE": "14200",
            "SORTNAME": "在发出通函后的重大资料",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "14000"
        },
        {
            "SORTCODE": "14300",
            "SORTNAME": "由股东提名董事",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "14000"
        },
        {
            "SORTCODE": "14400",
            "SORTNAME": "股东周年大会通告",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "14000"
        },
        {
            "SORTCODE": "14500",
            "SORTNAME": "股东特别大会通告",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "14000"
        },
        {
            "SORTCODE": "14600",
            "SORTNAME": "在股东批准的情况下重选或委任董事",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "14000"
        },
        {
            "SORTCODE": "14700",
            "SORTNAME": "股东周年大会的结果",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "14000"
        },
        {
            "SORTCODE": "14800",
            "SORTNAME": "股东特别大会的结果",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "14000"
        },
        {
            "SORTCODE": "14900",
            "SORTNAME": "投票表决的结果(2009年1月1日前)",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "14000"
        },
        {
            "SORTCODE": "15000",
            "SORTNAME": "新上市（上市发行人／新申请人）",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "10000"
        },
        {
            "SORTCODE": "15100",
            "SORTNAME": "配发结果",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "15000"
        },
        {
            "SORTCODE": "15200",
            "SORTNAME": "正式通告",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "15000"
        },
        {
            "SORTCODE": "15300",
            "SORTNAME": "以介绍形式上市的证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "15000"
        },
        {
            "SORTCODE": "15400",
            "SORTNAME": "供认购或投标发售的行使价",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "15000"
        },
        {
            "SORTCODE": "15500",
            "SORTNAME": "有关首次公开招股的补充资料",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "15000"
        },
        {
            "SORTCODE": "15600",
            "SORTNAME": "由GEM转往主板上市",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "15000"
        },
        {
            "SORTCODE": "15700",
            "SORTNAME": "混合媒介要约",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "15000"
        },
        {
            "SORTCODE": "16000",
            "SORTNAME": "须予公布的交易",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "10000"
        },
        {
            "SORTCODE": "16100",
            "SORTNAME": "在完成须予公布的交易方面出现延误",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "16000"
        },
        {
            "SORTCODE": "16200",
            "SORTNAME": "须予披露的交易",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "16000"
        },
        {
            "SORTCODE": "16300",
            "SORTNAME": "主要交易",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "16000"
        },
        {
            "SORTCODE": "16400",
            "SORTNAME": "反收购",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "16000"
        },
        {
            "SORTCODE": "16500",
            "SORTNAME": "股份交易",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "16000"
        },
        {
            "SORTCODE": "16600",
            "SORTNAME": "终止交易",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "16000"
        },
        {
            "SORTCODE": "16700",
            "SORTNAME": "条款上的更改",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "16000"
        },
        {
            "SORTCODE": "16800",
            "SORTNAME": "非常重大的收购事项",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "16000"
        },
        {
            "SORTCODE": "16900",
            "SORTNAME": "非常重大的出售事项",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "16000"
        },
        {
            "SORTCODE": "17000",
            "SORTNAME": "重组／股权变动／主要改动／公众持股量／上市地位",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "10000"
        },
        {
            "SORTCODE": "17100",
            "SORTNAME": "《收购守则》所指的受要约公司刊发的公告",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17150",
            "SORTNAME": "《收购守则》所指的要约公司刊发的公告",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17200",
            "SORTNAME": "股权出现变动",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17250",
            "SORTNAME": "股东抵押股份",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17300",
            "SORTNAME": "股权集中",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17350",
            "SORTNAME": "董事于《标准守则》所载的禁售期内买卖证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17400",
            "SORTNAME": "主要业务活动出现根本转变(2009年1月1日前)",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17450",
            "SORTNAME": "集团重组或协议安排",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17500",
            "SORTNAME": "证券缺乏公开市场",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17550",
            "SORTNAME": "于海外交易所或证券市场上市",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17600",
            "SORTNAME": "私有化/撤销或取消证券上市",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17650",
            "SORTNAME": "复牌",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17700",
            "SORTNAME": "分拆",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17750",
            "SORTNAME": "资产充足度及/或业务充足度及/或发行人成为现金资产公司",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17800",
            "SORTNAME": "公众持股量充足度",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17850",
            "SORTNAME": "停牌",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17900",
            "SORTNAME": "发行人、其控股公司或主要附属公司结束营业及清盘",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17950",
            "SORTNAME": "主要业务活动出现转变",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "17960",
            "SORTNAME": "短暂停牌",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "17000"
        },
        {
            "SORTCODE": "18",
            "SORTNAME": "基金",
            "F002D": null,
            "F001D": "2022-02-14 00:00:00",
            "PARENTCODE": "0"
        },
        {
            "SORTCODE": "18000",
            "SORTNAME": "证券／股本",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "10000"
        },
        {
            "SORTCODE": "1801",
            "SORTNAME": "基金招募设立",
            "F002D": null,
            "F001D": "2022-02-14 00:00:00",
            "PARENTCODE": "18"
        },
        {
            "SORTCODE": "180101",
            "SORTNAME": "招募说明书",
            "F002D": null,
            "F001D": "2024-02-01 00:00:00",
            "PARENTCODE": "1801"
        },
        {
            "SORTCODE": "180102",
            "SORTNAME": "基金合同",
            "F002D": null,
            "F001D": "2024-02-01 00:00:00",
            "PARENTCODE": "1801"
        },
        {
            "SORTCODE": "180103",
            "SORTNAME": "基金合同更新",
            "F002D": null,
            "F001D": "2024-02-01 00:00:00",
            "PARENTCODE": "1801"
        },
        {
            "SORTCODE": "180104",
            "SORTNAME": "资料概要",
            "F002D": null,
            "F001D": "2024-02-01 00:00:00",
            "PARENTCODE": "1801"
        },
        {
            "SORTCODE": "180105",
            "SORTNAME": "招募说明书更新",
            "F002D": null,
            "F001D": "2024-04-15 00:00:00",
            "PARENTCODE": "1801"
        },
        {
            "SORTCODE": "180106",
            "SORTNAME": "资料概要更新",
            "F002D": null,
            "F001D": "2024-04-15 00:00:00",
            "PARENTCODE": "1801"
        },
        {
            "SORTCODE": "180199",
            "SORTNAME": "其他招募发行公告",
            "F002D": null,
            "F001D": "2024-07-19 00:00:00",
            "PARENTCODE": "1801"
        },
        {
            "SORTCODE": "1802",
            "SORTNAME": "基金定期报告",
            "F002D": null,
            "F001D": "2022-02-14 00:00:00",
            "PARENTCODE": "18"
        },
        {
            "SORTCODE": "180201",
            "SORTNAME": "基金一季报",
            "F002D": null,
            "F001D": "2024-01-01 00:00:00",
            "PARENTCODE": "1802"
        },
        {
            "SORTCODE": "180202",
            "SORTNAME": "基金二季报",
            "F002D": null,
            "F001D": "2024-01-01 00:00:00",
            "PARENTCODE": "1802"
        },
        {
            "SORTCODE": "180203",
            "SORTNAME": "基金三季报",
            "F002D": null,
            "F001D": "2024-01-01 00:00:00",
            "PARENTCODE": "1802"
        },
        {
            "SORTCODE": "180204",
            "SORTNAME": "基金四季报",
            "F002D": null,
            "F001D": "2024-01-01 00:00:00",
            "PARENTCODE": "1802"
        },
        {
            "SORTCODE": "180205",
            "SORTNAME": "基金半年报",
            "F002D": null,
            "F001D": "2024-01-01 00:00:00",
            "PARENTCODE": "1802"
        },
        {
            "SORTCODE": "180206",
            "SORTNAME": "基金年报",
            "F002D": null,
            "F001D": "2024-01-01 00:00:00",
            "PARENTCODE": "1802"
        },
        {
            "SORTCODE": "180299",
            "SORTNAME": "其他定期报告公告",
            "F002D": null,
            "F001D": "2024-04-15 00:00:00",
            "PARENTCODE": "1802"
        },
        {
            "SORTCODE": "1803",
            "SORTNAME": "基金持有人大会",
            "F002D": null,
            "F001D": "2022-02-14 00:00:00",
            "PARENTCODE": "18"
        },
        {
            "SORTCODE": "1804",
            "SORTNAME": "基金申购赎回转换",
            "F002D": null,
            "F001D": "2022-02-14 00:00:00",
            "PARENTCODE": "18"
        },
        {
            "SORTCODE": "1805",
            "SORTNAME": "基金分红分拆合并",
            "F002D": null,
            "F001D": "2022-02-14 00:00:00",
            "PARENTCODE": "18"
        },
        {
            "SORTCODE": "1806",
            "SORTNAME": "基金净值",
            "F002D": null,
            "F001D": "2022-02-14 00:00:00",
            "PARENTCODE": "18"
        },
        {
            "SORTCODE": "1807",
            "SORTNAME": "基金管理人员变更",
            "F002D": null,
            "F001D": "2022-02-14 00:00:00",
            "PARENTCODE": "18"
        },
        {
            "SORTCODE": "1808",
            "SORTNAME": "基金运行通知",
            "F002D": null,
            "F001D": "2022-02-14 00:00:00",
            "PARENTCODE": "18"
        },
        {
            "SORTCODE": "1809",
            "SORTNAME": "基金提醒澄清说明",
            "F002D": null,
            "F001D": "2022-02-14 00:00:00",
            "PARENTCODE": "18"
        },
        {
            "SORTCODE": "1810",
            "SORTNAME": "基金投资",
            "F002D": null,
            "F001D": "2022-02-14 00:00:00",
            "PARENTCODE": "18"
        },
        {
            "SORTCODE": "18100",
            "SORTNAME": "根据《公司股份回购守则》发出的公告",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "1811",
            "SORTNAME": "基金公司动态",
            "F002D": null,
            "F001D": "2022-02-14 00:00:00",
            "PARENTCODE": "18"
        },
        {
            "SORTCODE": "18110",
            "SORTNAME": "红股或红利（公告表格）",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "1812",
            "SORTNAME": "基金二级交易",
            "F002D": null,
            "F001D": "2022-02-14 00:00:00",
            "PARENTCODE": "18"
        },
        {
            "SORTCODE": "18120",
            "SORTNAME": "资本重组",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "1813",
            "SORTNAME": "基金销售及代销",
            "F002D": null,
            "F001D": "2022-02-14 00:00:00",
            "PARENTCODE": "18"
        },
        {
            "SORTCODE": "1814",
            "SORTNAME": "基金费率调整",
            "F002D": null,
            "F001D": "2022-02-14 00:00:00",
            "PARENTCODE": "18"
        },
        {
            "SORTCODE": "18140",
            "SORTNAME": "资本化发行",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "1815",
            "SORTNAME": "基金其他公告",
            "F002D": null,
            "F001D": "2022-02-14 00:00:00",
            "PARENTCODE": "18"
        },
        {
            "SORTCODE": "1816",
            "SORTNAME": "基金停复牌",
            "F002D": null,
            "F001D": "2024-08-07 00:00:00",
            "PARENTCODE": "18"
        },
        {
            "SORTCODE": "18160",
            "SORTNAME": "更改每手买卖单位",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "181601",
            "SORTNAME": "风险提示停复牌",
            "F002D": null,
            "F001D": "2024-08-07 00:00:00",
            "PARENTCODE": "1816"
        },
        {
            "SORTCODE": "181602",
            "SORTNAME": "持有人会议停复牌",
            "F002D": null,
            "F001D": "2024-08-07 00:00:00",
            "PARENTCODE": "1816"
        },
        {
            "SORTCODE": "181603",
            "SORTNAME": "上交所基金临时停牌",
            "F002D": null,
            "F001D": "2025-07-21 00:00:00",
            "PARENTCODE": "1816"
        },
        {
            "SORTCODE": "181604",
            "SORTNAME": "深交所基金临时停牌",
            "F002D": null,
            "F001D": "2025-07-21 00:00:00",
            "PARENTCODE": "1816"
        },
        {
            "SORTCODE": "181605",
            "SORTNAME": "北交所基金临时停牌",
            "F002D": null,
            "F001D": "2025-08-07 00:00:00",
            "PARENTCODE": "1816"
        },
        {
            "SORTCODE": "181699",
            "SORTNAME": "其他停复牌",
            "F002D": null,
            "F001D": "2024-08-07 00:00:00",
            "PARENTCODE": "1816"
        },
        {
            "SORTCODE": "1817",
            "SORTNAME": "REITs反馈意见及回复",
            "F002D": null,
            "F001D": "2025-06-18 00:00:00",
            "PARENTCODE": "18"
        },
        {
            "SORTCODE": "18180",
            "SORTNAME": "更改证券条款或随附于证券的权利",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18200",
            "SORTNAME": "更改股息支付日期",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18220",
            "SORTNAME": "暂停办理过户登记手续或更改暂停办理过户日期",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18240",
            "SORTNAME": "代价发行",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18260",
            "SORTNAME": "转换证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18280",
            "SORTNAME": "出售未能联络到的股东股份的意向",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18300",
            "SORTNAME": "发行可转换证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18320",
            "SORTNAME": "发行债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18340",
            "SORTNAME": "发行优先股",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18360",
            "SORTNAME": "主要附属公司发行证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18380",
            "SORTNAME": "根据一般性授权发行股份",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18400",
            "SORTNAME": "根据特定授权发行股份",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18420",
            "SORTNAME": "发行权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18440",
            "SORTNAME": "已发行股本变动",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18460",
            "SORTNAME": "公开招股",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18480",
            "SORTNAME": "配售",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18500",
            "SORTNAME": "供股",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18520",
            "SORTNAME": "股份计划",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18540",
            "SORTNAME": "交易安排（更改每手买卖单位除外）",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18560",
            "SORTNAME": "根据一般性授权出售或转让库存股份",
            "F002D": null,
            "F001D": "2024-10-13 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "18580",
            "SORTNAME": "根据特定授权出售或转让库存股份",
            "F002D": null,
            "F001D": "2024-10-13 00:00:00",
            "PARENTCODE": "18000"
        },
        {
            "SORTCODE": "19",
            "SORTNAME": "银行间债券",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "0"
        },
        {
            "SORTCODE": "19000",
            "SORTNAME": "杂项",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "10000"
        },
        {
            "SORTCODE": "1901",
            "SORTNAME": "发行情况报告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1902",
            "SORTNAME": "发行披露",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1903",
            "SORTNAME": "债券发行",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1904",
            "SORTNAME": "评级报告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1905",
            "SORTNAME": "兑付注销",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1906",
            "SORTNAME": "付息兑付",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1907",
            "SORTNAME": "重大事项",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1908",
            "SORTNAME": "财务报告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1909",
            "SORTNAME": "信用评级",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1910",
            "SORTNAME": "专项品种",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "19100",
            "SORTNAME": "违反借贷协议",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "1911",
            "SORTNAME": "重大事项及其他",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1912",
            "SORTNAME": "发行与付息兑付",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1913",
            "SORTNAME": "债券交易流通要素公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1914",
            "SORTNAME": "托管业务公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1915",
            "SORTNAME": "国债公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "19150",
            "SORTNAME": "澄清新闻报道或报告-附带意见",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "1916",
            "SORTNAME": "交易流通要素公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1917",
            "SORTNAME": "银行对公大额存单的发行公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1918",
            "SORTNAME": "上市流通公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1919",
            "SORTNAME": "地方债公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1920",
            "SORTNAME": "债券信息披露",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "19200",
            "SORTNAME": "澄清新闻报道或报告-标准内容或超级内容",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "1921",
            "SORTNAME": "利率定价自律",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1922",
            "SORTNAME": "信息披露",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1923",
            "SORTNAME": "编码管理",
            "F002D": null,
            "F001D": "2025-11-26 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1924",
            "SORTNAME": "市场公告",
            "F002D": null,
            "F001D": "2025-11-26 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "1925",
            "SORTNAME": "专题",
            "F002D": null,
            "F001D": "2025-11-26 00:00:00",
            "PARENTCODE": "19"
        },
        {
            "SORTCODE": "19250",
            "SORTNAME": "延迟发送通函或其他文件",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19300",
            "SORTNAME": "附有特定履行契诺的借贷协议",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19350",
            "SORTNAME": "有关期权事宜",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19400",
            "SORTNAME": "有关集体投资计划事宜",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19450",
            "SORTNAME": "其他(2014年4月1日前)",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19500",
            "SORTNAME": "海外监管公告(2014年4月1日前)",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19550",
            "SORTNAME": "股价敏感资料(2013年1月1日前)",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19600",
            "SORTNAME": "不寻常价格/成交量变动-附带意见",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19650",
            "SORTNAME": "不寻常价格/成交量变动-标准内容或超级内容",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19700",
            "SORTNAME": "上市发行人所从事的矿业活动",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19750",
            "SORTNAME": "内幕消息",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19760",
            "SORTNAME": "其他-业务发展最新情况",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19770",
            "SORTNAME": "其他-企业管治相关事宜",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19780",
            "SORTNAME": "其他-诉讼",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19790",
            "SORTNAME": "其他-杂项",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19800",
            "SORTNAME": "其他-营运业绩最新情况",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19810",
            "SORTNAME": "海外监管公告-董事会/监事会决议",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19820",
            "SORTNAME": "海外监管公告-业务发展最新情况",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19830",
            "SORTNAME": "海外监管公告-企业管治相关事宜",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19840",
            "SORTNAME": "海外监管公告-证券发行及相关事宜",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19850",
            "SORTNAME": "海外监管公告-其他",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19860",
            "SORTNAME": "海外监管公告-营运业绩最新情况",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "19870",
            "SORTNAME": "海外监管公告-库存股份出售或转让及相关事宜",
            "F002D": null,
            "F001D": "2024-10-13 00:00:00",
            "PARENTCODE": "19000"
        },
        {
            "SORTCODE": "20",
            "SORTNAME": "监管动态",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "0"
        },
        {
            "SORTCODE": "20000",
            "SORTNAME": "通函",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "40"
        },
        {
            "SORTCODE": "2001",
            "SORTNAME": "上交所一般公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2002",
            "SORTNAME": "上交所上市退市公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2003",
            "SORTNAME": "上交所交易监管动态",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2004",
            "SORTNAME": "上交所交易监管纪律处分",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2005",
            "SORTNAME": "上交所公司监管动态",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2006",
            "SORTNAME": "中国证监会公司令",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2007",
            "SORTNAME": "中国证监会公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2008",
            "SORTNAME": "中国证监会发行部行政监管措施",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2009",
            "SORTNAME": "中国证监会新闻发布会",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2010",
            "SORTNAME": "中国证监会机关部门最新更新",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2011",
            "SORTNAME": "中国证监会派出机构最新更新",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2012",
            "SORTNAME": "中国证监会要闻",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2013",
            "SORTNAME": "证监会令",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2014",
            "SORTNAME": "证监会公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2015",
            "SORTNAME": "证监会要闻",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2016",
            "SORTNAME": "行政处罚决定",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2017",
            "SORTNAME": "行政复议",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2018",
            "SORTNAME": "行政许可批复",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2019",
            "SORTNAME": "市场禁入决定",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2020",
            "SORTNAME": "中证协通知公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2021",
            "SORTNAME": "北交所公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2022",
            "SORTNAME": "北交所要闻",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2023",
            "SORTNAME": "深交所上市公司公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2024",
            "SORTNAME": "深交所中介机构监管",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2025",
            "SORTNAME": "深交所会员及其他交易参与人监管",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2026",
            "SORTNAME": "深交所停复牌公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2027",
            "SORTNAME": "深交所固收产品公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2028",
            "SORTNAME": "深交所基金公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2029",
            "SORTNAME": "深交所复核决定",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2030",
            "SORTNAME": "深交所监管动态",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2031",
            "SORTNAME": "深交所融资融券业务公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2032",
            "SORTNAME": "深交所通知公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2033",
            "SORTNAME": "深交所限制交易决定",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2034",
            "SORTNAME": "结算公司总部通知",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2035",
            "SORTNAME": "上海分公司通知",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2036",
            "SORTNAME": "深圳分公司通知",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2037",
            "SORTNAME": "北京分公司通知",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2038",
            "SORTNAME": "其他监管动态",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2039",
            "SORTNAME": "上交所融资融券",
            "F002D": null,
            "F001D": "2023-03-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2040",
            "SORTNAME": "北交所融资融券",
            "F002D": null,
            "F001D": "2023-03-18 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2041",
            "SORTNAME": "辖区监管动态",
            "F002D": null,
            "F001D": "2024-02-01 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2042",
            "SORTNAME": "香港子公司通知",
            "F002D": null,
            "F001D": "2024-02-01 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2043",
            "SORTNAME": "上交所停复牌公告",
            "F002D": null,
            "F001D": "2024-09-09 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2044",
            "SORTNAME": "上交所港股通公告",
            "F002D": null,
            "F001D": "2025-04-10 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2045",
            "SORTNAME": "深交所港股通公告",
            "F002D": null,
            "F001D": "2025-04-10 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2046",
            "SORTNAME": "港交所陆股通公告",
            "F002D": null,
            "F001D": "2025-04-10 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2047",
            "SORTNAME": "港交所陆股通交易告示",
            "F002D": null,
            "F001D": "2025-04-10 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2048",
            "SORTNAME": "深交所存托凭证最新信息",
            "F002D": null,
            "F001D": "2025-05-22 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2049",
            "SORTNAME": "深交所存托凭证业务规则",
            "F002D": null,
            "F001D": "2025-05-22 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2050",
            "SORTNAME": "深交所存托凭证业务指南",
            "F002D": null,
            "F001D": "2025-05-22 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2051",
            "SORTNAME": "上交所存托凭证最新信息",
            "F002D": null,
            "F001D": "2025-05-22 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2052",
            "SORTNAME": "上交所存托凭证业务规则",
            "F002D": null,
            "F001D": "2025-05-22 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "2053",
            "SORTNAME": "上交所存托凭证业务指南",
            "F002D": null,
            "F001D": "2025-05-22 00:00:00",
            "PARENTCODE": "20"
        },
        {
            "SORTCODE": "21",
            "SORTNAME": "IPO预披露信息",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "0"
        },
        {
            "SORTCODE": "21000",
            "SORTNAME": "关连交易",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "20000"
        },
        {
            "SORTCODE": "2101",
            "SORTNAME": "北交所审核公告通知上市委会议公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2102",
            "SORTNAME": "北交所审核公告通知上市委会议结果公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2103",
            "SORTNAME": "北交所公开发行信息披露",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2104",
            "SORTNAME": "北交所审核信息披露",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2105",
            "SORTNAME": "北交所审核公告通知注册结果",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2106",
            "SORTNAME": "北交所审核公告通知终止审核",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2107",
            "SORTNAME": "发审会公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2108",
            "SORTNAME": "审核反馈意见",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2109",
            "SORTNAME": "审核预披露招股书",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2110",
            "SORTNAME": "科创板信息披露",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "21100",
            "SORTNAME": "关连交易",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "21000"
        },
        {
            "SORTCODE": "2111",
            "SORTNAME": "创业板预披露",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2112",
            "SORTNAME": "其他预披露",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2113",
            "SORTNAME": "预披露招股说明书",
            "F002D": null,
            "F001D": "2023-03-01 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2114",
            "SORTNAME": "预披露发行保荐书",
            "F002D": null,
            "F001D": "2023-03-01 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2115",
            "SORTNAME": "预披露上市保荐书",
            "F002D": null,
            "F001D": "2023-03-01 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2116",
            "SORTNAME": "预披露审计报告",
            "F002D": null,
            "F001D": "2023-03-01 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2117",
            "SORTNAME": "预披露法律意见书",
            "F002D": null,
            "F001D": "2023-03-01 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2118",
            "SORTNAME": "预披露问询与回复",
            "F002D": null,
            "F001D": "2023-03-01 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2119",
            "SORTNAME": "深交所IPO申报稿",
            "F002D": null,
            "F001D": "2024-06-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2120",
            "SORTNAME": "深交所IPO上会稿",
            "F002D": null,
            "F001D": "2024-06-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "21200",
            "SORTNAME": "持续关连交易",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "21000"
        },
        {
            "SORTCODE": "2121",
            "SORTNAME": "深交所IPO注册稿",
            "F002D": null,
            "F001D": "2024-06-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2122",
            "SORTNAME": "深交所IPO问询与回复",
            "F002D": null,
            "F001D": "2024-06-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2123",
            "SORTNAME": "上交所发行上市申报稿",
            "F002D": null,
            "F001D": "2024-06-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2124",
            "SORTNAME": "上交所发行上市上会稿",
            "F002D": null,
            "F001D": "2024-06-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2125",
            "SORTNAME": "上交所发行上市注册稿",
            "F002D": null,
            "F001D": "2024-06-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2126",
            "SORTNAME": "上交所发行上市问询与回复",
            "F002D": null,
            "F001D": "2024-06-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2127",
            "SORTNAME": "北交所审核信息披露申报稿",
            "F002D": null,
            "F001D": "2024-06-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2128",
            "SORTNAME": "北交所审核信息披露上会稿",
            "F002D": null,
            "F001D": "2024-06-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2129",
            "SORTNAME": "北交所审核信息披露注册稿",
            "F002D": null,
            "F001D": "2024-06-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "2130",
            "SORTNAME": "北交所审核信息披露问询与回复",
            "F002D": null,
            "F001D": "2024-06-18 00:00:00",
            "PARENTCODE": "21"
        },
        {
            "SORTCODE": "22",
            "SORTNAME": "辅导企业公告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "0"
        },
        {
            "SORTCODE": "22000",
            "SORTNAME": "公司状况变动及委员会／公司变动",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "20000"
        },
        {
            "SORTCODE": "2201",
            "SORTNAME": "挂牌公司辅导信息",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "22"
        },
        {
            "SORTCODE": "2202",
            "SORTNAME": "终止辅导信息",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "22"
        },
        {
            "SORTCODE": "2203",
            "SORTNAME": "辅导企业信息",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "22"
        },
        {
            "SORTCODE": "2204",
            "SORTNAME": "辅导企业基本情况",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "22"
        },
        {
            "SORTCODE": "2205",
            "SORTNAME": "辅导信息动态",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "22"
        },
        {
            "SORTCODE": "2206",
            "SORTNAME": "辅导备案信息",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "22"
        },
        {
            "SORTCODE": "2207",
            "SORTNAME": "辅导备案报告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "22"
        },
        {
            "SORTCODE": "2208",
            "SORTNAME": "辅导工作总结报告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "22"
        },
        {
            "SORTCODE": "2209",
            "SORTNAME": "辅导工作报告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "22"
        },
        {
            "SORTCODE": "2210",
            "SORTNAME": "辅导工作进展报告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "22"
        },
        {
            "SORTCODE": "22100",
            "SORTNAME": "修订宪章文件",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "22000"
        },
        {
            "SORTCODE": "2211",
            "SORTNAME": "辅导情况报告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "22"
        },
        {
            "SORTCODE": "2212",
            "SORTNAME": "辅导进展情况报告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "22"
        },
        {
            "SORTCODE": "2213",
            "SORTNAME": "其他辅导信息",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "22"
        },
        {
            "SORTCODE": "23",
            "SORTNAME": "港股IPO预披露",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "0"
        },
        {
            "SORTCODE": "23000",
            "SORTNAME": "会议／表决",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "20000"
        },
        {
            "SORTCODE": "2301",
            "SORTNAME": "处理中",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "23"
        },
        {
            "SORTCODE": "2302",
            "SORTNAME": "没有进展,失效",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "23"
        },
        {
            "SORTCODE": "2303",
            "SORTNAME": "没有进展,撤回",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "23"
        },
        {
            "SORTCODE": "2304",
            "SORTNAME": "没有进展,被拒绝",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "23"
        },
        {
            "SORTCODE": "23100",
            "SORTNAME": "更改表决意向",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "23000"
        },
        {
            "SORTCODE": "23200",
            "SORTNAME": "发出通函后的重大资料",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "23000"
        },
        {
            "SORTCODE": "23300",
            "SORTNAME": "由股东提名董事",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "23000"
        },
        {
            "SORTCODE": "23400",
            "SORTNAME": "在股东批准的情况下重选或委任董事",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "23000"
        },
        {
            "SORTCODE": "23500",
            "SORTNAME": "在股东批准的情况下更换核数师",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "23000"
        },
        {
            "SORTCODE": "24",
            "SORTNAME": "交易所监管函件",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "0"
        },
        {
            "SORTCODE": "24000",
            "SORTNAME": "须予公布的交易",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "20000"
        },
        {
            "SORTCODE": "2401",
            "SORTNAME": "三季报问询函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2402",
            "SORTNAME": "交易所通报批评",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2403",
            "SORTNAME": "公司部函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2404",
            "SORTNAME": "公开认定不适合担任上市公司董事会秘书",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2405",
            "SORTNAME": "公开认定不适合担任上市公司董监高（不含董秘）",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2406",
            "SORTNAME": "公开谴责",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2407",
            "SORTNAME": "关注函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2408",
            "SORTNAME": "关注函（会计师事务所模板）",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2409",
            "SORTNAME": "内部批评",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2410",
            "SORTNAME": "半年报问询函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "24100",
            "SORTNAME": "须予披露的交易(2009年1月1日前)",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "24000"
        },
        {
            "SORTCODE": "2411",
            "SORTNAME": "向中介机构发函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2412",
            "SORTNAME": "定期报告事后审核意见函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2413",
            "SORTNAME": "定期报告信息披露监管问询函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2414",
            "SORTNAME": "年报审核问询函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2415",
            "SORTNAME": "年报问询函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2416",
            "SORTNAME": "并购重组审核意见函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2417",
            "SORTNAME": "暂停或者限制交易权限",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2418",
            "SORTNAME": "监管关注",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2419",
            "SORTNAME": "监管关注函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2420",
            "SORTNAME": "监管函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "24200",
            "SORTNAME": "主要交易",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "24000"
        },
        {
            "SORTCODE": "2421",
            "SORTNAME": "监管函（会计师事务所模板）",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2422",
            "SORTNAME": "监管工作函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2423",
            "SORTNAME": "监管警示函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2424",
            "SORTNAME": "第三季报审查问询函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2425",
            "SORTNAME": "许可类重组问询函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2426",
            "SORTNAME": "违法违规线索评估分析报告",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2427",
            "SORTNAME": "通报批评",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2428",
            "SORTNAME": "重大资产重组预案审核意见函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2429",
            "SORTNAME": "问询函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "2430",
            "SORTNAME": "非许可类重组问询函",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "24300",
            "SORTNAME": "反收购",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "24000"
        },
        {
            "SORTCODE": "2431",
            "SORTNAME": "其他函件",
            "F002D": null,
            "F001D": "2022-02-18 00:00:00",
            "PARENTCODE": "24"
        },
        {
            "SORTCODE": "24400",
            "SORTNAME": "非常重大的收购事项",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "24000"
        },
        {
            "SORTCODE": "24500",
            "SORTNAME": "非常重大的出售事项",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "24000"
        },
        {
            "SORTCODE": "25",
            "SORTNAME": "深证信新债券公告分类",
            "F002D": null,
            "F001D": "2022-06-08 00:00:00",
            "PARENTCODE": "0"
        },
        {
            "SORTCODE": "25000",
            "SORTNAME": "重组／股权改动／主要改动／公众持股量／上市地位",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "20000"
        },
        {
            "SORTCODE": "2501",
            "SORTNAME": "发行上市",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "25"
        },
        {
            "SORTCODE": "250101",
            "SORTNAME": "发行公告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2501"
        },
        {
            "SORTCODE": "250102",
            "SORTNAME": "发行结果",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2501"
        },
        {
            "SORTCODE": "250103",
            "SORTNAME": "募集公告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2501"
        },
        {
            "SORTCODE": "250104",
            "SORTNAME": "法律意见书",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2501"
        },
        {
            "SORTCODE": "250105",
            "SORTNAME": "承销分销",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2501"
        },
        {
            "SORTCODE": "250106",
            "SORTNAME": "推迟取消发行",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2501"
        },
        {
            "SORTCODE": "250107",
            "SORTNAME": "上市公告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2501"
        },
        {
            "SORTCODE": "250108",
            "SORTNAME": "注册发行",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2501"
        },
        {
            "SORTCODE": "250109",
            "SORTNAME": "延长发行",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2501"
        },
        {
            "SORTCODE": "250110",
            "SORTNAME": "发行中介报告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2501"
        },
        {
            "SORTCODE": "250111",
            "SORTNAME": "招标发行相关",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2501"
        },
        {
            "SORTCODE": "250112",
            "SORTNAME": "发行事项调整",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2501"
        },
        {
            "SORTCODE": "250113",
            "SORTNAME": "其他发行相关",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2501"
        },
        {
            "SORTCODE": "2502",
            "SORTNAME": "信用评级",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "25"
        },
        {
            "SORTCODE": "250201",
            "SORTNAME": "信用评级",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2502"
        },
        {
            "SORTCODE": "250202",
            "SORTNAME": "评级下调",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2502"
        },
        {
            "SORTCODE": "250203",
            "SORTNAME": "评级展望负面",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2502"
        },
        {
            "SORTCODE": "250204",
            "SORTNAME": "推迟评级",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2502"
        },
        {
            "SORTCODE": "250205",
            "SORTNAME": "终止评级",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2502"
        },
        {
            "SORTCODE": "250206",
            "SORTNAME": "评级关注",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2502"
        },
        {
            "SORTCODE": "250207",
            "SORTNAME": "评级调整",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2502"
        },
        {
            "SORTCODE": "250208",
            "SORTNAME": "评级机构变化",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2502"
        },
        {
            "SORTCODE": "250209",
            "SORTNAME": "评级展望变动",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2502"
        },
        {
            "SORTCODE": "2503",
            "SORTNAME": "债券兑付",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "25"
        },
        {
            "SORTCODE": "250301",
            "SORTNAME": "付息兑付",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2503"
        },
        {
            "SORTCODE": "250302",
            "SORTNAME": "提前还本",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2503"
        },
        {
            "SORTCODE": "250303",
            "SORTNAME": "债券违约",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2503"
        },
        {
            "SORTCODE": "250304",
            "SORTNAME": "利率相关",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2503"
        },
        {
            "SORTCODE": "250305",
            "SORTNAME": "ABS报告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2503"
        },
        {
            "SORTCODE": "250306",
            "SORTNAME": "偿付不确定",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2503"
        },
        {
            "SORTCODE": "250307",
            "SORTNAME": "分期还本",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2503"
        },
        {
            "SORTCODE": "250308",
            "SORTNAME": "债券展期",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2503"
        },
        {
            "SORTCODE": "2504",
            "SORTNAME": "财务报告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "25"
        },
        {
            "SORTCODE": "250401",
            "SORTNAME": "业绩预告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2504"
        },
        {
            "SORTCODE": "250402",
            "SORTNAME": "业绩亏损或下滑",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2504"
        },
        {
            "SORTCODE": "250403",
            "SORTNAME": "季报",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2504"
        },
        {
            "SORTCODE": "250404",
            "SORTNAME": "中报",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2504"
        },
        {
            "SORTCODE": "250405",
            "SORTNAME": "年报",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2504"
        },
        {
            "SORTCODE": "250406",
            "SORTNAME": "补充披露",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2504"
        },
        {
            "SORTCODE": "250407",
            "SORTNAME": "财务其他",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2504"
        },
        {
            "SORTCODE": "250408",
            "SORTNAME": "审计报告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2504"
        },
        {
            "SORTCODE": "250409",
            "SORTNAME": "会计差错更正",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2504"
        },
        {
            "SORTCODE": "250410",
            "SORTNAME": "会计政策估计变更",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2504"
        },
        {
            "SORTCODE": "250411",
            "SORTNAME": "财报延期披露",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2504"
        },
        {
            "SORTCODE": "250412",
            "SORTNAME": "经营报告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2504"
        },
        {
            "SORTCODE": "2505",
            "SORTNAME": "交易提示",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "25"
        },
        {
            "SORTCODE": "250501",
            "SORTNAME": "暂停上市",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2505"
        },
        {
            "SORTCODE": "250502",
            "SORTNAME": "摘牌公告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2505"
        },
        {
            "SORTCODE": "250503",
            "SORTNAME": "债券转托管",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2505"
        },
        {
            "SORTCODE": "250504",
            "SORTNAME": "债券简称变更",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2505"
        },
        {
            "SORTCODE": "250505",
            "SORTNAME": "标准券折算比例",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2505"
        },
        {
            "SORTCODE": "250506",
            "SORTNAME": "质押式回购交易",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2505"
        },
        {
            "SORTCODE": "250507",
            "SORTNAME": "估值说明",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2505"
        },
        {
            "SORTCODE": "250508",
            "SORTNAME": "停复牌",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2505"
        },
        {
            "SORTCODE": "250509",
            "SORTNAME": "交易情况",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2505"
        },
        {
            "SORTCODE": "2506",
            "SORTNAME": "含权债相关",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "25"
        },
        {
            "SORTCODE": "250601",
            "SORTNAME": "债券回售",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2506"
        },
        {
            "SORTCODE": "250602",
            "SORTNAME": "赎回公告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2506"
        },
        {
            "SORTCODE": "250603",
            "SORTNAME": "债券调换",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2506"
        },
        {
            "SORTCODE": "250604",
            "SORTNAME": "转股事项",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2506"
        },
        {
            "SORTCODE": "250605",
            "SORTNAME": "转股价格调整",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2506"
        },
        {
            "SORTCODE": "250606",
            "SORTNAME": "债转股",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2506"
        },
        {
            "SORTCODE": "250607",
            "SORTNAME": "要约收购购回",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2506"
        },
        {
            "SORTCODE": "250608",
            "SORTNAME": "利率公告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2506"
        },
        {
            "SORTCODE": "250609",
            "SORTNAME": "权利行使",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2506"
        },
        {
            "SORTCODE": "250610",
            "SORTNAME": "提前到期",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2506"
        },
        {
            "SORTCODE": "250611",
            "SORTNAME": "存续期相关",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2506"
        },
        {
            "SORTCODE": "2507",
            "SORTNAME": "重大事项",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "25"
        },
        {
            "SORTCODE": "250701",
            "SORTNAME": "控股股东或实际控制人相关",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250702",
            "SORTNAME": "债务人变更",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250703",
            "SORTNAME": "董监高变动",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250705",
            "SORTNAME": "董监高违法违纪",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250706",
            "SORTNAME": "诉讼仲裁",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250707",
            "SORTNAME": "监管问询通报",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250708",
            "SORTNAME": "违规处罚",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250709",
            "SORTNAME": "债务逾期展期",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250710",
            "SORTNAME": "生产停产",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250711",
            "SORTNAME": "破产清算重整",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250712",
            "SORTNAME": "资产重组",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250713",
            "SORTNAME": "资产股权债权抵质押",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250714",
            "SORTNAME": "资产出售转让划转",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250715",
            "SORTNAME": "对外投资",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250716",
            "SORTNAME": "借款",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250717",
            "SORTNAME": "担保",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250718",
            "SORTNAME": "生产事故",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250719",
            "SORTNAME": "自然灾害",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250720",
            "SORTNAME": "募集资金使用",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250721",
            "SORTNAME": "债券名称变更",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250722",
            "SORTNAME": "经营范围变更",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250723",
            "SORTNAME": "偿债措施相关",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250724",
            "SORTNAME": "外部条件变化",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250725",
            "SORTNAME": "放弃债权财产",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250726",
            "SORTNAME": "减资合并分立",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250727",
            "SORTNAME": "重大损失",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250728",
            "SORTNAME": "市场传闻",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250729",
            "SORTNAME": "信用增进",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250730",
            "SORTNAME": "重大合同",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250731",
            "SORTNAME": "资产抵(质)押",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250732",
            "SORTNAME": "资产报废",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250733",
            "SORTNAME": "资产查封扣押冻结执行",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250734",
            "SORTNAME": "大额赔偿",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250735",
            "SORTNAME": "债务相关",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250736",
            "SORTNAME": "企业解散关闭",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250737",
            "SORTNAME": "业务停顿",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250738",
            "SORTNAME": "政策优惠",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250739",
            "SORTNAME": "资格取消",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250740",
            "SORTNAME": "审核不批准(不通过)",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250741",
            "SORTNAME": "事项中止终止",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250742",
            "SORTNAME": "投资理财",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250743",
            "SORTNAME": "否决议案",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250744",
            "SORTNAME": "股份增减持",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250745",
            "SORTNAME": "股份股权冻结",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250746",
            "SORTNAME": "资产股权拍卖处置",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250747",
            "SORTNAME": "澄清公告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250748",
            "SORTNAME": "致歉公告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250749",
            "SORTNAME": "其他重要风险事项",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250751",
            "SORTNAME": "股份回购",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250752",
            "SORTNAME": "股权激励",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250753",
            "SORTNAME": "低押质押解除",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250754",
            "SORTNAME": "冻结解除",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250755",
            "SORTNAME": "员工持股计划",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250756",
            "SORTNAME": "债务重组",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250757",
            "SORTNAME": "监管关注",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250758",
            "SORTNAME": "监管警示",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250759",
            "SORTNAME": "公开认定",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250760",
            "SORTNAME": "通报批评",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250761",
            "SORTNAME": "公开谴责",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250762",
            "SORTNAME": "自律处分",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250763",
            "SORTNAME": "立案调查",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250765",
            "SORTNAME": "行政处罚",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250766",
            "SORTNAME": "市场禁入",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250768",
            "SORTNAME": "募集资金置换",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250769",
            "SORTNAME": "股权变动",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250771",
            "SORTNAME": "债券转让",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250772",
            "SORTNAME": "自查报告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250773",
            "SORTNAME": "异常波动",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250774",
            "SORTNAME": "股份变动",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250775",
            "SORTNAME": "经营情况说明",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250776",
            "SORTNAME": "问题整改",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250777",
            "SORTNAME": "债券增减持",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250778",
            "SORTNAME": "发行人分红派息",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250779",
            "SORTNAME": "关联交易",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250780",
            "SORTNAME": "偿债能力分析",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250781",
            "SORTNAME": "行政申请审批",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250782",
            "SORTNAME": "信托计划相关",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250783",
            "SORTNAME": "资产支持计划",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250784",
            "SORTNAME": "公益活动",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250785",
            "SORTNAME": "回报承诺",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250786",
            "SORTNAME": "境外交易所公告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "250799",
            "SORTNAME": "其他重大事项",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2507"
        },
        {
            "SORTCODE": "2508",
            "SORTNAME": "公司或债券持有人大会",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "25"
        },
        {
            "SORTCODE": "250801",
            "SORTNAME": "持有人会议",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2508"
        },
        {
            "SORTCODE": "250802",
            "SORTNAME": "公司董事会",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2508"
        },
        {
            "SORTCODE": "250803",
            "SORTNAME": "公司监事会",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2508"
        },
        {
            "SORTCODE": "250804",
            "SORTNAME": "公司股东大会",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2508"
        },
        {
            "SORTCODE": "250805",
            "SORTNAME": "职工大会",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2508"
        },
        {
            "SORTCODE": "2509",
            "SORTNAME": "中介机构",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "25"
        },
        {
            "SORTCODE": "250901",
            "SORTNAME": "中介机构变更",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2509"
        },
        {
            "SORTCODE": "2510",
            "SORTNAME": "受托管理及代理报告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "25"
        },
        {
            "SORTCODE": "25100",
            "SORTNAME": "《收购守则》所指的受要约公司发出的文件",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "25000"
        },
        {
            "SORTCODE": "251001",
            "SORTNAME": "受托管理报告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2510"
        },
        {
            "SORTCODE": "251002",
            "SORTNAME": "代理管理报告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2510"
        },
        {
            "SORTCODE": "2511",
            "SORTNAME": "中介机构专项意见",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "25"
        },
        {
            "SORTCODE": "251101",
            "SORTNAME": "会计事务所专项意见",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2511"
        },
        {
            "SORTCODE": "251102",
            "SORTNAME": "律师事务所专项意见",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2511"
        },
        {
            "SORTCODE": "251103",
            "SORTNAME": "其他中介机构报告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2511"
        },
        {
            "SORTCODE": "2512",
            "SORTNAME": "公司资料与制度",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "25"
        },
        {
            "SORTCODE": "251201",
            "SORTNAME": "公司资料变更",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2512"
        },
        {
            "SORTCODE": "251202",
            "SORTNAME": "公司制度",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2512"
        },
        {
            "SORTCODE": "251203",
            "SORTNAME": "投资者关系相关",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2512"
        },
        {
            "SORTCODE": "2513",
            "SORTNAME": "环境社会公司治理报告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "25"
        },
        {
            "SORTCODE": "251301",
            "SORTNAME": "ESG报告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2513"
        },
        {
            "SORTCODE": "251302",
            "SORTNAME": "社会责任报告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2513"
        },
        {
            "SORTCODE": "251303",
            "SORTNAME": "可持续发展报告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2513"
        },
        {
            "SORTCODE": "251304",
            "SORTNAME": "环境信息披露报告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2513"
        },
        {
            "SORTCODE": "25200",
            "SORTNAME": "《收购守则》所指的要约公司发出的文件",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "25000"
        },
        {
            "SORTCODE": "25300",
            "SORTNAME": "主要业务活动出现根本转变",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "25000"
        },
        {
            "SORTCODE": "25400",
            "SORTNAME": "私有化/撤销证券上市",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "25000"
        },
        {
            "SORTCODE": "25500",
            "SORTNAME": "有关矿务公司开发天然资源用以拓展或更改现有活动的建议",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "25000"
        },
        {
            "SORTCODE": "25600",
            "SORTNAME": "分拆",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "25000"
        },
        {
            "SORTCODE": "2599",
            "SORTNAME": "其它",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "25"
        },
        {
            "SORTCODE": "259901",
            "SORTNAME": "其他公告",
            "F002D": null,
            "F001D": "2022-09-21 00:00:00",
            "PARENTCODE": "2599"
        },
        {
            "SORTCODE": "26000",
            "SORTNAME": "证券／股本",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "20000"
        },
        {
            "SORTCODE": "2601",
            "SORTNAME": "上交所临时停牌",
            "F002D": null,
            "F001D": "2022-06-08 00:00:00",
            "PARENTCODE": "26"
        },
        {
            "SORTCODE": "2602",
            "SORTNAME": "北交所临时停牌",
            "F002D": null,
            "F001D": "2022-06-08 00:00:00",
            "PARENTCODE": "26"
        },
        {
            "SORTCODE": "2603",
            "SORTNAME": "深交所临时停牌",
            "F002D": null,
            "F001D": "2022-06-08 00:00:00",
            "PARENTCODE": "26"
        },
        {
            "SORTCODE": "2604",
            "SORTNAME": "深交所融资融券业务公告",
            "F002D": null,
            "F001D": "2022-06-08 00:00:00",
            "PARENTCODE": "26"
        },
        {
            "SORTCODE": "26100",
            "SORTNAME": "资本化发行",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "26150",
            "SORTNAME": "更改证券条款或随附于证券的权利",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "26200",
            "SORTNAME": "根据《公司股份回购守则》刊发的文件",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "26250",
            "SORTNAME": "交换证券或取代原证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "26300",
            "SORTNAME": "回购股份的说明函件",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "26350",
            "SORTNAME": "一般性授权",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "26400",
            "SORTNAME": "发行可转换证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "26450",
            "SORTNAME": "发行债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "26500",
            "SORTNAME": "发行优先股",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "26550",
            "SORTNAME": "主要附属公司发行证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "26600",
            "SORTNAME": "于上市后六个月内发行证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "26650",
            "SORTNAME": "发行股份",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "26700",
            "SORTNAME": "发行权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "26750",
            "SORTNAME": "公开招股",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "26800",
            "SORTNAME": "供股",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "26850",
            "SORTNAME": "股份计划",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "26900",
            "SORTNAME": "于上市后六个月内出售或转让库存股份",
            "F002D": null,
            "F001D": "2024-10-13 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "26950",
            "SORTNAME": "出售或转让库存股份",
            "F002D": null,
            "F001D": "2024-10-13 00:00:00",
            "PARENTCODE": "26000"
        },
        {
            "SORTCODE": "27",
            "SORTNAME": "全景资讯",
            "F002D": null,
            "F001D": "2023-04-01 00:00:00",
            "PARENTCODE": "0"
        },
        {
            "SORTCODE": "27000",
            "SORTNAME": "杂项",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "20000"
        },
        {
            "SORTCODE": "2701",
            "SORTNAME": "证券",
            "F002D": null,
            "F001D": "2023-04-01 00:00:00",
            "PARENTCODE": "27"
        },
        {
            "SORTCODE": "2702",
            "SORTNAME": "公司",
            "F002D": null,
            "F001D": "2023-04-01 00:00:00",
            "PARENTCODE": "27"
        },
        {
            "SORTCODE": "2703",
            "SORTNAME": "快讯",
            "F002D": null,
            "F001D": "2023-04-01 00:00:00",
            "PARENTCODE": "27"
        },
        {
            "SORTCODE": "2704",
            "SORTNAME": "产经",
            "F002D": null,
            "F001D": "2023-04-01 00:00:00",
            "PARENTCODE": "27"
        },
        {
            "SORTCODE": "27100",
            "SORTNAME": "有关集体投资计划事宜",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "27000"
        },
        {
            "SORTCODE": "27900",
            "SORTNAME": "其他",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "27000"
        },
        {
            "SORTCODE": "28",
            "SORTNAME": "英文监管动态",
            "F002D": null,
            "F001D": "2022-04-06 00:00:00",
            "PARENTCODE": "0"
        },
        {
            "SORTCODE": "2801",
            "SORTNAME": "CCDC News",
            "F002D": null,
            "F001D": "2022-04-06 00:00:00",
            "PARENTCODE": "28"
        },
        {
            "SORTCODE": "2802",
            "SORTNAME": "CFXC News",
            "F002D": null,
            "F001D": "2022-04-06 00:00:00",
            "PARENTCODE": "28"
        },
        {
            "SORTCODE": "2803",
            "SORTNAME": "CSDC News",
            "F002D": null,
            "F001D": "2022-04-06 00:00:00",
            "PARENTCODE": "28"
        },
        {
            "SORTCODE": "2804",
            "SORTNAME": "CSRC News",
            "F002D": null,
            "F001D": "2022-04-06 00:00:00",
            "PARENTCODE": "28"
        },
        {
            "SORTCODE": "2805",
            "SORTNAME": "PBC News",
            "F002D": null,
            "F001D": "2022-04-06 00:00:00",
            "PARENTCODE": "28"
        },
        {
            "SORTCODE": "2806",
            "SORTNAME": "SSE News",
            "F002D": null,
            "F001D": "2022-04-06 00:00:00",
            "PARENTCODE": "28"
        },
        {
            "SORTCODE": "2807",
            "SORTNAME": "SSE Rules",
            "F002D": null,
            "F001D": "2022-04-06 00:00:00",
            "PARENTCODE": "28"
        },
        {
            "SORTCODE": "2808",
            "SORTNAME": "SZSE News",
            "F002D": null,
            "F001D": "2022-04-06 00:00:00",
            "PARENTCODE": "28"
        },
        {
            "SORTCODE": "2809",
            "SORTNAME": "SZSE Rules",
            "F002D": null,
            "F001D": "2022-04-06 00:00:00",
            "PARENTCODE": "28"
        },
        {
            "SORTCODE": "29",
            "SORTNAME": "地方证监局监管动态",
            "F002D": null,
            "F001D": "2023-03-18 00:00:00",
            "PARENTCODE": "0"
        },
        {
            "SORTCODE": "2901",
            "SORTNAME": "基金监管",
            "F002D": null,
            "F001D": "2023-03-18 00:00:00",
            "PARENTCODE": "29"
        },
        {
            "SORTCODE": "2902",
            "SORTNAME": "证券服务机构监管",
            "F002D": null,
            "F001D": "2023-03-18 00:00:00",
            "PARENTCODE": "29"
        },
        {
            "SORTCODE": "2903",
            "SORTNAME": "行政执法",
            "F002D": null,
            "F001D": "2023-03-18 00:00:00",
            "PARENTCODE": "29"
        },
        {
            "SORTCODE": "2904",
            "SORTNAME": "综合政务",
            "F002D": null,
            "F001D": "2023-03-18 00:00:00",
            "PARENTCODE": "29"
        },
        {
            "SORTCODE": "2905",
            "SORTNAME": "市场数据",
            "F002D": null,
            "F001D": "2023-03-18 00:00:00",
            "PARENTCODE": "29"
        },
        {
            "SORTCODE": "2906",
            "SORTNAME": "上市公司监管",
            "F002D": null,
            "F001D": "2023-03-18 00:00:00",
            "PARENTCODE": "29"
        },
        {
            "SORTCODE": "2907",
            "SORTNAME": "证券经营机构监管",
            "F002D": null,
            "F001D": "2023-03-18 00:00:00",
            "PARENTCODE": "29"
        },
        {
            "SORTCODE": "2908",
            "SORTNAME": "期货监管",
            "F002D": null,
            "F001D": "2023-03-18 00:00:00",
            "PARENTCODE": "29"
        },
        {
            "SORTCODE": "2909",
            "SORTNAME": "公众公司监管",
            "F002D": null,
            "F001D": "2023-03-18 00:00:00",
            "PARENTCODE": "29"
        },
        {
            "SORTCODE": "2910",
            "SORTNAME": "境外机构监管",
            "F002D": null,
            "F001D": "2023-03-18 00:00:00",
            "PARENTCODE": "29"
        },
        {
            "SORTCODE": "2911",
            "SORTNAME": "其他",
            "F002D": null,
            "F001D": "2023-03-18 00:00:00",
            "PARENTCODE": "29"
        },
        {
            "SORTCODE": "30",
            "SORTNAME": "再融资/重组/转板公告",
            "F002D": null,
            "F001D": "2023-10-31 00:00:00",
            "PARENTCODE": "0"
        },
        {
            "SORTCODE": "30000",
            "SORTNAME": "上市文件",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "40"
        },
        {
            "SORTCODE": "3001",
            "SORTNAME": "再融资公告",
            "F002D": null,
            "F001D": "2023-10-31 00:00:00",
            "PARENTCODE": "30"
        },
        {
            "SORTCODE": "300101",
            "SORTNAME": "再融资申报稿",
            "F002D": null,
            "F001D": "2023-10-31 00:00:00",
            "PARENTCODE": "3001"
        },
        {
            "SORTCODE": "300102",
            "SORTNAME": "再融资注册稿（北交所）",
            "F002D": null,
            "F001D": "2023-10-31 00:00:00",
            "PARENTCODE": "3001"
        },
        {
            "SORTCODE": "300103",
            "SORTNAME": "再融资问询与回复",
            "F002D": null,
            "F001D": "2023-10-31 00:00:00",
            "PARENTCODE": "3001"
        },
        {
            "SORTCODE": "3002",
            "SORTNAME": "重组公告",
            "F002D": null,
            "F001D": "2023-10-31 00:00:00",
            "PARENTCODE": "30"
        },
        {
            "SORTCODE": "300201",
            "SORTNAME": "重组申报稿",
            "F002D": null,
            "F001D": "2023-10-31 00:00:00",
            "PARENTCODE": "3002"
        },
        {
            "SORTCODE": "300202",
            "SORTNAME": "重组上会稿",
            "F002D": null,
            "F001D": "2023-10-31 00:00:00",
            "PARENTCODE": "3002"
        },
        {
            "SORTCODE": "300203",
            "SORTNAME": "重组注册稿",
            "F002D": null,
            "F001D": "2023-10-31 00:00:00",
            "PARENTCODE": "3002"
        },
        {
            "SORTCODE": "300204",
            "SORTNAME": "重组问询与回复",
            "F002D": null,
            "F001D": "2023-10-31 00:00:00",
            "PARENTCODE": "3002"
        },
        {
            "SORTCODE": "3003",
            "SORTNAME": "转板公告",
            "F002D": null,
            "F001D": "2023-10-31 00:00:00",
            "PARENTCODE": "30"
        },
        {
            "SORTCODE": "300301",
            "SORTNAME": "转板申报稿",
            "F002D": null,
            "F001D": "2023-10-31 00:00:00",
            "PARENTCODE": "3003"
        },
        {
            "SORTCODE": "300302",
            "SORTNAME": "转板上会稿（上交所）",
            "F002D": null,
            "F001D": "2023-10-31 00:00:00",
            "PARENTCODE": "3003"
        },
        {
            "SORTCODE": "300303",
            "SORTNAME": "转板封卷稿（上交所）",
            "F002D": null,
            "F001D": "2023-10-31 00:00:00",
            "PARENTCODE": "3003"
        },
        {
            "SORTCODE": "300304",
            "SORTNAME": "转板上会稿及备案稿（深交所）",
            "F002D": null,
            "F001D": "2023-10-31 00:00:00",
            "PARENTCODE": "3003"
        },
        {
            "SORTCODE": "300305",
            "SORTNAME": "转板问询与回复",
            "F002D": null,
            "F001D": "2023-10-31 00:00:00",
            "PARENTCODE": "3003"
        },
        {
            "SORTCODE": "30100",
            "SORTNAME": "认可集体投资计划",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "30000"
        },
        {
            "SORTCODE": "30200",
            "SORTNAME": "资本化发行",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "30000"
        },
        {
            "SORTCODE": "30300",
            "SORTNAME": "按《上市规则》规定视为新上市",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "30000"
        },
        {
            "SORTCODE": "30400",
            "SORTNAME": "交换证券或取代原证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "30000"
        },
        {
            "SORTCODE": "30500",
            "SORTNAME": "介绍",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "30000"
        },
        {
            "SORTCODE": "30600",
            "SORTNAME": "发售现有证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "30000"
        },
        {
            "SORTCODE": "30700",
            "SORTNAME": "发售以供认购",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "30000"
        },
        {
            "SORTCODE": "30800",
            "SORTNAME": "公开招股",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "30000"
        },
        {
            "SORTCODE": "30900",
            "SORTNAME": "其他",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "30000"
        },
        {
            "SORTCODE": "31000",
            "SORTNAME": "配售上市后的新证券类别",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "30000"
        },
        {
            "SORTCODE": "31100",
            "SORTNAME": "供股",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "30000"
        },
        {
            "SORTCODE": "31200",
            "SORTNAME": "补充上市文件",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "30000"
        },
        {
            "SORTCODE": "35",
            "SORTNAME": "上市公司公告补充分类",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "0"
        },
        {
            "SORTCODE": "3502",
            "SORTNAME": "首次公开发行及上市（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "35"
        },
        {
            "SORTCODE": "350217",
            "SORTNAME": "超额配售选择权行使公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3502"
        },
        {
            "SORTCODE": "3503",
            "SORTNAME": "定期报告（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "35"
        },
        {
            "SORTCODE": "350308",
            "SORTNAME": "定期报告预约披露时间变更公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3503"
        },
        {
            "SORTCODE": "350311",
            "SORTNAME": "预计不能在法定期限内刊登定期报告的提示性公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3503"
        },
        {
            "SORTCODE": "350313",
            "SORTNAME": "未在法定期限内刊登定期报告的停牌公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3503"
        },
        {
            "SORTCODE": "350314",
            "SORTNAME": "董监高无法保证定期报告真实、准确、完整或者有异议的相关说明",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3503"
        },
        {
            "SORTCODE": "3505",
            "SORTNAME": "配股（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "35"
        },
        {
            "SORTCODE": "350513",
            "SORTNAME": "延长配股决议有效期议案",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3505"
        },
        {
            "SORTCODE": "350514",
            "SORTNAME": "配股证监会作出注册或者不予注册决定公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3505"
        },
        {
            "SORTCODE": "350515",
            "SORTNAME": "配股交易所审核结果公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3505"
        },
        {
            "SORTCODE": "350516",
            "SORTNAME": "交易所受理配股注册申请文件的公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3505"
        },
        {
            "SORTCODE": "350517",
            "SORTNAME": "交易所不予受理配股注册申请文件的公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3505"
        },
        {
            "SORTCODE": "350518",
            "SORTNAME": "配股注册批文后发行股份数量及价格调整公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3505"
        },
        {
            "SORTCODE": "350519",
            "SORTNAME": "撤回配股申请",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3505"
        },
        {
            "SORTCODE": "350520",
            "SORTNAME": "配股收到中国证监会终止发行注册决定",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3505"
        },
        {
            "SORTCODE": "3507",
            "SORTNAME": "增发（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "35"
        },
        {
            "SORTCODE": "350717",
            "SORTNAME": "延长向不特定对象募集股份决议有效期的议案",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "350718",
            "SORTNAME": "向不特定对象募集股份证监会作出注册或者不予注册决定公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "350719",
            "SORTNAME": "向不特定对象募集股份交易所审核结果公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "350720",
            "SORTNAME": "向不特定对象募集股份交易所受理增发注册申请文件的公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "350721",
            "SORTNAME": "向不特定对象募集股份交易所不予受理增发注册申请文件的公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "350722",
            "SORTNAME": "向不特定对象募集股份注册批文后发行股份数量及价格调整公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "350723",
            "SORTNAME": "撤回向不特定对象募集股份申请",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "350724",
            "SORTNAME": "向不特定对象募集股份收到中国证监会终止发行注册决定",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "350725",
            "SORTNAME": "延长向特定对象发行股票决议有效期的议案",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "350726",
            "SORTNAME": "向特定对象发行股票交易所审核结果公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "350727",
            "SORTNAME": "向特定对象发行股票证监会作出注册或者不予注册决定公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "350728",
            "SORTNAME": "撤回向特定对象发行股票申请",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "350729",
            "SORTNAME": "向特定对象发行股票注册批文失效公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "350730",
            "SORTNAME": "交易所受理向特定对象发股注册申请文件的公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "350731",
            "SORTNAME": "向特定对象发行股票发行情况报告书",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "350732",
            "SORTNAME": "交易所不予受理向特定对象发股注册申请文件的公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "350733",
            "SORTNAME": "向特定对象发行股票注册批文后发行股份数量及价格调整公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "350734",
            "SORTNAME": "向特定对象发行股票收到中国证监会终止发行注册决定",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3507"
        },
        {
            "SORTCODE": "3509",
            "SORTNAME": "可转换债券（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "35"
        },
        {
            "SORTCODE": "350925",
            "SORTNAME": "可转债转股数额累计达到转股前发行人总股份10%公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3509"
        },
        {
            "SORTCODE": "350926",
            "SORTNAME": "可转债摘牌公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3509"
        },
        {
            "SORTCODE": "350927",
            "SORTNAME": "可转债暂停转股的公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3509"
        },
        {
            "SORTCODE": "350928",
            "SORTNAME": "可转债恢复转股的公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3509"
        },
        {
            "SORTCODE": "350929",
            "SORTNAME": "可转债利率调整公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3509"
        },
        {
            "SORTCODE": "350930",
            "SORTNAME": "发行可转债证监会作出注册或者不予注册决定公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3509"
        },
        {
            "SORTCODE": "350931",
            "SORTNAME": "发行可转债交易所审核结果公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3509"
        },
        {
            "SORTCODE": "350932",
            "SORTNAME": "可转债持有比例变动达10%",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3509"
        },
        {
            "SORTCODE": "350933",
            "SORTNAME": "可转债信用跟踪评级报告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3509"
        },
        {
            "SORTCODE": "350934",
            "SORTNAME": "交易所受理可转债注册申请文件的公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3509"
        },
        {
            "SORTCODE": "350935",
            "SORTNAME": "可转债中止发行公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3509"
        },
        {
            "SORTCODE": "350936",
            "SORTNAME": "可转债不行使赎回权的公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3509"
        },
        {
            "SORTCODE": "350937",
            "SORTNAME": "可转债赎回延期公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3509"
        },
        {
            "SORTCODE": "350938",
            "SORTNAME": "交易所不予受理可转债注册申请文件的公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3509"
        },
        {
            "SORTCODE": "350939",
            "SORTNAME": "撤回向不特定对象发行可转债申请",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3509"
        },
        {
            "SORTCODE": "350940",
            "SORTNAME": "收到中国证监会终止发行可转债注册决定",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3509"
        },
        {
            "SORTCODE": "350941",
            "SORTNAME": "可转债本息兑付公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3509"
        },
        {
            "SORTCODE": "3511",
            "SORTNAME": "其它融资（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "35"
        },
        {
            "SORTCODE": "351103",
            "SORTNAME": "其它融资事项（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3511"
        },
        {
            "SORTCODE": "35110321",
            "SORTNAME": "信托产品融资",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351103"
        },
        {
            "SORTCODE": "35110323",
            "SORTNAME": "H股相关的股份变动",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351103"
        },
        {
            "SORTCODE": "351105",
            "SORTNAME": "发行优先股",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3511"
        },
        {
            "SORTCODE": "35110501",
            "SORTNAME": "优先股发行预案",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "35110502",
            "SORTNAME": "优先股方案修改或取消",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "35110503",
            "SORTNAME": "优先股发行交易所审核结果公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "35110504",
            "SORTNAME": "优先股发行证监会作出注册或者不予注册决定公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "35110505",
            "SORTNAME": "向特定对象发行优先股的发行情况报告书",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "35110506",
            "SORTNAME": "优先股上市（转让）公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "35110507",
            "SORTNAME": "优先股表决权恢复提示性公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "35110508",
            "SORTNAME": "优先股表决权终止提示性公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "35110509",
            "SORTNAME": "优先股付息公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "35110510",
            "SORTNAME": "优先股回售公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "35110511",
            "SORTNAME": "优先股回售结果公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "35110512",
            "SORTNAME": "优先股赎回公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "35110513",
            "SORTNAME": "优先股赎回结果公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "35110514",
            "SORTNAME": "优先股强制转换为普通股提示性公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "35110515",
            "SORTNAME": "优先股向不特定对象发行情况报告书",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "35110516",
            "SORTNAME": "优先股摘牌公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "35110517",
            "SORTNAME": "优先股停止交易公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "35110518",
            "SORTNAME": "优先股恢复交易公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351105"
        },
        {
            "SORTCODE": "351107",
            "SORTNAME": "发行全球存托凭证（GDR）",
            "F002D": null,
            "F001D": "2025-03-05 00:00:00",
            "PARENTCODE": "3511"
        },
        {
            "SORTCODE": "35110701",
            "SORTNAME": "全球存托凭证对应基础股份上市公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351107"
        },
        {
            "SORTCODE": "3513",
            "SORTNAME": "权益分派与限制出售股份上市（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "35"
        },
        {
            "SORTCODE": "351303",
            "SORTNAME": "限制出售股份上市（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3513"
        },
        {
            "SORTCODE": "35130341",
            "SORTNAME": "向特定对象发行股票的股份上市流通提示性公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351303"
        },
        {
            "SORTCODE": "35130342",
            "SORTNAME": "公开发行前已发行股份上市流通提示性公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351303"
        },
        {
            "SORTCODE": "3515",
            "SORTNAME": "股权变动（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "35"
        },
        {
            "SORTCODE": "351501",
            "SORTNAME": "持股变动（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3515"
        },
        {
            "SORTCODE": "35150170",
            "SORTNAME": "离婚、解散、分立公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351501"
        },
        {
            "SORTCODE": "35150171",
            "SORTNAME": "董事、监事和高管持股变动公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351501"
        },
        {
            "SORTCODE": "35150172",
            "SORTNAME": "减持预披露提示性公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351501"
        },
        {
            "SORTCODE": "35150173",
            "SORTNAME": "减持计划进展",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351501"
        },
        {
            "SORTCODE": "35150174",
            "SORTNAME": "大股东、董监高披露股份增持计划",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351501"
        },
        {
            "SORTCODE": "35150175",
            "SORTNAME": "大股东、董监高披露股份增持计划的进展",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351501"
        },
        {
            "SORTCODE": "35150176",
            "SORTNAME": "公开征集股权受让方",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351501"
        },
        {
            "SORTCODE": "35150177",
            "SORTNAME": "公开征集股权受让方的结果",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351501"
        },
        {
            "SORTCODE": "35150178",
            "SORTNAME": "关于公司控制权变更处于筹划阶段的提示性公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351501"
        },
        {
            "SORTCODE": "35150179",
            "SORTNAME": "控股股东或实际控制人发生变动的提示",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351501"
        },
        {
            "SORTCODE": "35150180",
            "SORTNAME": "短线交易",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351501"
        },
        {
            "SORTCODE": "35150181",
            "SORTNAME": "部分或全部特别表决权股份转换为普通股份公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351501"
        },
        {
            "SORTCODE": "35150182",
            "SORTNAME": "每份特别表决权股份的表决权数量调整公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351501"
        },
        {
            "SORTCODE": "35150183",
            "SORTNAME": "持股5%以上的股东减持后持股比例低于5%",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351501"
        },
        {
            "SORTCODE": "351505",
            "SORTNAME": "要约收购（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3515"
        },
        {
            "SORTCODE": "35150560",
            "SORTNAME": "变更要约收购条件公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351505"
        },
        {
            "SORTCODE": "35150561",
            "SORTNAME": "要约收购期满的停牌公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351505"
        },
        {
            "SORTCODE": "35150562",
            "SORTNAME": "取消要约收购公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351505"
        },
        {
            "SORTCODE": "35150563",
            "SORTNAME": "预受要约的提示性公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351505"
        },
        {
            "SORTCODE": "35150564",
            "SORTNAME": "要约收购股份清算",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351505"
        },
        {
            "SORTCODE": "351511",
            "SORTNAME": "吸收合并（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3515"
        },
        {
            "SORTCODE": "35151140",
            "SORTNAME": "现金选择权行权公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351511"
        },
        {
            "SORTCODE": "35151141",
            "SORTNAME": "现金选择权行权期间提示性",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351511"
        },
        {
            "SORTCODE": "35151142",
            "SORTNAME": "现金选择权结果公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351511"
        },
        {
            "SORTCODE": "35151143",
            "SORTNAME": "现金选择权派发公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351511"
        },
        {
            "SORTCODE": "35151144",
            "SORTNAME": "现金选择权进展公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351511"
        },
        {
            "SORTCODE": "351513",
            "SORTNAME": "公司减资、分立事项（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3515"
        },
        {
            "SORTCODE": "35151340",
            "SORTNAME": "回购股份注销完成暨股份变动公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351513"
        },
        {
            "SORTCODE": "35151341",
            "SORTNAME": "已回购股份减持结果暨股份变动公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351513"
        },
        {
            "SORTCODE": "35151342",
            "SORTNAME": "回购股份报告书",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351513"
        },
        {
            "SORTCODE": "35151343",
            "SORTNAME": "回购股份提议",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351513"
        },
        {
            "SORTCODE": "35151344",
            "SORTNAME": "回购结果暨股份变动公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351513"
        },
        {
            "SORTCODE": "35151345",
            "SORTNAME": "以集中竞价方式减持已回购股份的预披露公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351513"
        },
        {
            "SORTCODE": "35151346",
            "SORTNAME": "以集中竞价方式减持已回购股份的进展公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351513"
        },
        {
            "SORTCODE": "35151347",
            "SORTNAME": "回购股份方案变更或终止公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351513"
        },
        {
            "SORTCODE": "35151348",
            "SORTNAME": "回购前前十名股东持股情况",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351513"
        },
        {
            "SORTCODE": "35151349",
            "SORTNAME": "回购注销债权人通知公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351513"
        },
        {
            "SORTCODE": "3517",
            "SORTNAME": "交易（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "35"
        },
        {
            "SORTCODE": "351704",
            "SORTNAME": "债权重组",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3517"
        },
        {
            "SORTCODE": "351711",
            "SORTNAME": "担保（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3517"
        },
        {
            "SORTCODE": "35171140",
            "SORTNAME": "年度担保预计",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351711"
        },
        {
            "SORTCODE": "351714",
            "SORTNAME": "接受财务资助",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3517"
        },
        {
            "SORTCODE": "351719",
            "SORTNAME": "持续性关联交易（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3517"
        },
        {
            "SORTCODE": "35171940",
            "SORTNAME": "向关联人购买资产",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351719"
        },
        {
            "SORTCODE": "35171941",
            "SORTNAME": "向关联人出售资产",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351719"
        },
        {
            "SORTCODE": "35171942",
            "SORTNAME": "与关联人共同投资",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351719"
        },
        {
            "SORTCODE": "35171943",
            "SORTNAME": "向关联人提供财务资助",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351719"
        },
        {
            "SORTCODE": "35171944",
            "SORTNAME": "接受关联人财务资助",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351719"
        },
        {
            "SORTCODE": "35171945",
            "SORTNAME": "与关联人债权重组",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351719"
        },
        {
            "SORTCODE": "35171946",
            "SORTNAME": "与关联人债务重组",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351719"
        },
        {
            "SORTCODE": "35171947",
            "SORTNAME": "与关联人签订许可使用协议",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351719"
        },
        {
            "SORTCODE": "35171948",
            "SORTNAME": "日常关联交易公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351719"
        },
        {
            "SORTCODE": "35171949",
            "SORTNAME": "年度日常关联交易预计公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351719"
        },
        {
            "SORTCODE": "35171950",
            "SORTNAME": "财务公司关联交易公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351719"
        },
        {
            "SORTCODE": "351721",
            "SORTNAME": "股东资金占用与还款（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3517"
        },
        {
            "SORTCODE": "35172101",
            "SORTNAME": "清欠方案及其调整公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351721"
        },
        {
            "SORTCODE": "35172102",
            "SORTNAME": "清欠进展公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351721"
        },
        {
            "SORTCODE": "351723",
            "SORTNAME": "签订许可使用协议",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3517"
        },
        {
            "SORTCODE": "351725",
            "SORTNAME": "矿业权交易",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3517"
        },
        {
            "SORTCODE": "351727",
            "SORTNAME": "与私募基金合作投资",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3517"
        },
        {
            "SORTCODE": "3519",
            "SORTNAME": "股东大会（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "35"
        },
        {
            "SORTCODE": "351999",
            "SORTNAME": "股东大会其它公告（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3519"
        },
        {
            "SORTCODE": "35199930",
            "SORTNAME": "征集提案权公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351999"
        },
        {
            "SORTCODE": "35199940",
            "SORTNAME": "股东大会无法正常召开或无法形成决议",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "351999"
        },
        {
            "SORTCODE": "3520",
            "SORTNAME": "投资者关系信息（增补）",
            "F002D": null,
            "F001D": "2024-11-26 00:00:00",
            "PARENTCODE": "35"
        },
        {
            "SORTCODE": "352005",
            "SORTNAME": "中小投资者股东质询函回复",
            "F002D": null,
            "F001D": "2024-11-26 00:00:00",
            "PARENTCODE": "3520"
        },
        {
            "SORTCODE": "3521",
            "SORTNAME": "澄清、风险提示、业绩预告事项（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "35"
        },
        {
            "SORTCODE": "352103",
            "SORTNAME": "股票交易异常波动风险提示（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3521"
        },
        {
            "SORTCODE": "35210350",
            "SORTNAME": "上市首日风险提示及澄清公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352103"
        },
        {
            "SORTCODE": "35210360",
            "SORTNAME": "市场传闻或股价异动核查的停牌公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352103"
        },
        {
            "SORTCODE": "35210370",
            "SORTNAME": "异常波动核查结果公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352103"
        },
        {
            "SORTCODE": "35210380",
            "SORTNAME": "交易严重异常波动公告",
            "F002D": null,
            "F001D": "2024-11-26 00:00:00",
            "PARENTCODE": "352103"
        },
        {
            "SORTCODE": "352111",
            "SORTNAME": "业绩预告（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3521"
        },
        {
            "SORTCODE": "35211170",
            "SORTNAME": "业绩快报修正公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352111"
        },
        {
            "SORTCODE": "35211180",
            "SORTNAME": "业绩预告修正公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352111"
        },
        {
            "SORTCODE": "3523",
            "SORTNAME": "其它重大事项（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "35"
        },
        {
            "SORTCODE": "352301",
            "SORTNAME": "公司基本信息变更（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3523"
        },
        {
            "SORTCODE": "35230170",
            "SORTNAME": "公司中介机构变更（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352301"
        },
        {
            "SORTCODE": "3523017003",
            "SORTNAME": "会计师事务所更名",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "35230170"
        },
        {
            "SORTCODE": "352303",
            "SORTNAME": "变更董事、监事及高管（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3523"
        },
        {
            "SORTCODE": "35230360",
            "SORTNAME": "推选职工董事或者监事",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352303"
        },
        {
            "SORTCODE": "35230370",
            "SORTNAME": "变更董事会秘书",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352303"
        },
        {
            "SORTCODE": "35230380",
            "SORTNAME": "证券事务代表变更",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352303"
        },
        {
            "SORTCODE": "352305",
            "SORTNAME": "经营环境重大变化（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3523"
        },
        {
            "SORTCODE": "35230570",
            "SORTNAME": "行业变更公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352305"
        },
        {
            "SORTCODE": "35230571",
            "SORTNAME": "上市时未盈利公司实现盈利",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352305"
        },
        {
            "SORTCODE": "35230572",
            "SORTNAME": "新法律、政策可能对公司经营产生重大影响",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352305"
        },
        {
            "SORTCODE": "35230573",
            "SORTNAME": "商标、专利、技术等无形资产的取得或使用发生重大变化",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352305"
        },
        {
            "SORTCODE": "35230574",
            "SORTNAME": "新产品等研发或技术改造取得重要进展",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352305"
        },
        {
            "SORTCODE": "35230575",
            "SORTNAME": "筹划子公司在其他证券交易场所挂牌转让",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352305"
        },
        {
            "SORTCODE": "352307",
            "SORTNAME": "股份质押、冻结（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3523"
        },
        {
            "SORTCODE": "35230740",
            "SORTNAME": "股份被司法拍卖",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352307"
        },
        {
            "SORTCODE": "35230750",
            "SORTNAME": "股份司法拍卖进展",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352307"
        },
        {
            "SORTCODE": "352313",
            "SORTNAME": "重大损失（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3523"
        },
        {
            "SORTCODE": "35231340",
            "SORTNAME": "计提大额资产减值准备",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352313"
        },
        {
            "SORTCODE": "35231350",
            "SORTNAME": "计提大额资产减值准备转回",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352313"
        },
        {
            "SORTCODE": "35231360",
            "SORTNAME": "控股股东、董监高失联、被调查或其他无法履行职责公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352313"
        },
        {
            "SORTCODE": "352315",
            "SORTNAME": "募集资金使用（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3523"
        },
        {
            "SORTCODE": "35231560",
            "SORTNAME": "置换先期投入公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352315"
        },
        {
            "SORTCODE": "35231561",
            "SORTNAME": "签订或提前终止募集资金三方监管协议公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352315"
        },
        {
            "SORTCODE": "35231562",
            "SORTNAME": "募集资金暂时补充流动资金公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352315"
        },
        {
            "SORTCODE": "35231563",
            "SORTNAME": "归还补充流动资金公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352315"
        },
        {
            "SORTCODE": "35231564",
            "SORTNAME": "募集资金节余资金使用公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352315"
        },
        {
            "SORTCODE": "35231565",
            "SORTNAME": "募投项目对外转让或置换公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352315"
        },
        {
            "SORTCODE": "35231566",
            "SORTNAME": "暂时闲置的募集资金进行现金管理公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352315"
        },
        {
            "SORTCODE": "352319",
            "SORTNAME": "破产、清算事项（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3523"
        },
        {
            "SORTCODE": "35231980",
            "SORTNAME": "法院裁定批准重整计划、和解协议的公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352319"
        },
        {
            "SORTCODE": "35231981",
            "SORTNAME": "破产重整涉及的权益调整预案",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352319"
        },
        {
            "SORTCODE": "35231982",
            "SORTNAME": "发出债权人会议通知",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352319"
        },
        {
            "SORTCODE": "35231983",
            "SORTNAME": "债权人会议决议（关注复牌）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352319"
        },
        {
            "SORTCODE": "35231984",
            "SORTNAME": "破产重整权益调整方案实施公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352319"
        },
        {
            "SORTCODE": "35231985",
            "SORTNAME": "确定重整投资人公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352319"
        },
        {
            "SORTCODE": "35231986",
            "SORTNAME": "法院裁定重整计划、和解协议执行完毕的公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352319"
        },
        {
            "SORTCODE": "35231987",
            "SORTNAME": "指定破产管理人",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352319"
        },
        {
            "SORTCODE": "352325",
            "SORTNAME": "股权激励（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3523"
        },
        {
            "SORTCODE": "35232501",
            "SORTNAME": "股权激励计划草案",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232502",
            "SORTNAME": "股权激励方案调整公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232503",
            "SORTNAME": "股权激励计划授予",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232504",
            "SORTNAME": "股权激励期权授予完成公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232505",
            "SORTNAME": "股权激励限制性股票授予完成",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232506",
            "SORTNAME": "关于股权激励期权符合行权条件的公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232507",
            "SORTNAME": "股权激励期权行权公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232508",
            "SORTNAME": "股权激励获得股份解除限售公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232509",
            "SORTNAME": "股票期权行权结果",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232510",
            "SORTNAME": "拟注销股权激励授予股份、期权公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232511",
            "SORTNAME": "股权激励授予期权注销完成公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232512",
            "SORTNAME": "股权激励授予股份注销完成公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232513",
            "SORTNAME": "股权激励计划终止公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232514",
            "SORTNAME": "员工持股计划草案",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232515",
            "SORTNAME": "员工持股计划实施进展公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232516",
            "SORTNAME": "终止员工持股计划",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232517",
            "SORTNAME": "员工持股计划调整公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232518",
            "SORTNAME": "员工持股计划实施完成公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232519",
            "SORTNAME": "员工持股计划锁定期变更公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232520",
            "SORTNAME": "员工持股计划股份锁定期届满公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232521",
            "SORTNAME": "员工持股计划改变管理方式公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "35232522",
            "SORTNAME": "员工持股转让、继承、处置公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352325"
        },
        {
            "SORTCODE": "352327",
            "SORTNAME": "重大合同（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3523"
        },
        {
            "SORTCODE": "35232701",
            "SORTNAME": "生产经营方面重要合同的进展公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352327"
        },
        {
            "SORTCODE": "352332",
            "SORTNAME": "内部控制",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3523"
        },
        {
            "SORTCODE": "35233201",
            "SORTNAME": "内部控制自我评价报告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352332"
        },
        {
            "SORTCODE": "35233202",
            "SORTNAME": "内控审计报告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352332"
        },
        {
            "SORTCODE": "35233203",
            "SORTNAME": "内控实施方案",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352332"
        },
        {
            "SORTCODE": "352399",
            "SORTNAME": "其它事项公告（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3523"
        },
        {
            "SORTCODE": "35239940",
            "SORTNAME": "双提升方案公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352399"
        },
        {
            "SORTCODE": "35239941",
            "SORTNAME": "不能如期刊登临时报告的停牌公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352399"
        },
        {
            "SORTCODE": "35239942",
            "SORTNAME": "重大事项停牌公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352399"
        },
        {
            "SORTCODE": "35239943",
            "SORTNAME": "重大事项复牌公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352399"
        },
        {
            "SORTCODE": "35239944",
            "SORTNAME": "重大事项停牌进展公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352399"
        },
        {
            "SORTCODE": "35239945",
            "SORTNAME": "停牌期满申请继续停牌公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352399"
        },
        {
            "SORTCODE": "35239946",
            "SORTNAME": "自愿性信息披露公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352399"
        },
        {
            "SORTCODE": "35239947",
            "SORTNAME": "监管部门函件及回复",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352399"
        },
        {
            "SORTCODE": "3525",
            "SORTNAME": "特别处理和退市（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "35"
        },
        {
            "SORTCODE": "352509",
            "SORTNAME": "退市期公司公告（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3525"
        },
        {
            "SORTCODE": "35250901",
            "SORTNAME": "与主办券商签订协议公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352509"
        },
        {
            "SORTCODE": "35250902",
            "SORTNAME": "股票可能将被终止上市的风险提示公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352509"
        },
        {
            "SORTCODE": "35250903",
            "SORTNAME": "股票于退市整理期交易的风险提示公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352509"
        },
        {
            "SORTCODE": "35250904",
            "SORTNAME": "股票摘牌公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352509"
        },
        {
            "SORTCODE": "35250905",
            "SORTNAME": "股票进入退市整理期交易首日的风险提示公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352509"
        },
        {
            "SORTCODE": "35250906",
            "SORTNAME": "上市公司向本所申请复核的公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352509"
        },
        {
            "SORTCODE": "35250907",
            "SORTNAME": "复核申请被交易所受理或不予受理公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352509"
        },
        {
            "SORTCODE": "35250908",
            "SORTNAME": "股票可能被实施重大违法强制退市风险提示公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352509"
        },
        {
            "SORTCODE": "35250909",
            "SORTNAME": "收到重大违法强制退市事先告知书的公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352509"
        },
        {
            "SORTCODE": "35250910",
            "SORTNAME": "收到重大违法强制退市决定书的公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352509"
        },
        {
            "SORTCODE": "3527",
            "SORTNAME": "补充及更正（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "35"
        },
        {
            "SORTCODE": "352701",
            "SORTNAME": "定期报告补充、更正（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3527"
        },
        {
            "SORTCODE": "35270120",
            "SORTNAME": "会计差错更正公告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "352701"
        },
        {
            "SORTCODE": "3531",
            "SORTNAME": "上市公司制度（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "35"
        },
        {
            "SORTCODE": "353105",
            "SORTNAME": "董事与董事会（增补）",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "3531"
        },
        {
            "SORTCODE": "35310570",
            "SORTNAME": "独立董事年度述职报告",
            "F002D": null,
            "F001D": "2024-09-26 00:00:00",
            "PARENTCODE": "353105"
        },
        {
            "SORTCODE": "36",
            "SORTNAME": "期货交易所动态",
            "F002D": null,
            "F001D": "2025-11-26 00:00:00",
            "PARENTCODE": "0"
        },
        {
            "SORTCODE": "3601",
            "SORTNAME": "上海国际能源交易中心动态",
            "F002D": null,
            "F001D": "2025-11-26 00:00:00",
            "PARENTCODE": "36"
        },
        {
            "SORTCODE": "3602",
            "SORTNAME": "上海期货交易所动态",
            "F002D": null,
            "F001D": "2025-11-26 00:00:00",
            "PARENTCODE": "36"
        },
        {
            "SORTCODE": "3603",
            "SORTNAME": "大连商品交易所动态",
            "F002D": null,
            "F001D": "2025-11-26 00:00:00",
            "PARENTCODE": "36"
        },
        {
            "SORTCODE": "3604",
            "SORTNAME": "广州期货交易所动态",
            "F002D": null,
            "F001D": "2025-11-26 00:00:00",
            "PARENTCODE": "36"
        },
        {
            "SORTCODE": "3605",
            "SORTNAME": "郑州商品交易所动态",
            "F002D": null,
            "F001D": "2025-11-26 00:00:00",
            "PARENTCODE": "36"
        },
        {
            "SORTCODE": "40",
            "SORTNAME": "最新港股分类",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "0"
        },
        {
            "SORTCODE": "40000",
            "SORTNAME": "财务报表/环境、社会及管治资料",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "40"
        },
        {
            "SORTCODE": "40100",
            "SORTNAME": "年报",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "40000"
        },
        {
            "SORTCODE": "40200",
            "SORTNAME": "中期/半年度报告",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "40000"
        },
        {
            "SORTCODE": "40300",
            "SORTNAME": "季度报告",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "40000"
        },
        {
            "SORTCODE": "40400",
            "SORTNAME": "环境、社会及管治资料/报告",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "40000"
        },
        {
            "SORTCODE": "50000",
            "SORTNAME": "翌日披露报表",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "40"
        },
        {
            "SORTCODE": "50100",
            "SORTNAME": "股份购回",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "50000"
        },
        {
            "SORTCODE": "50200",
            "SORTNAME": "其他",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "50000"
        },
        {
            "SORTCODE": "50300",
            "SORTNAME": "在场内出售库存股份",
            "F002D": null,
            "F001D": "2024-10-13 00:00:00",
            "PARENTCODE": "50000"
        },
        {
            "SORTCODE": "51000",
            "SORTNAME": "股份购回报告(2009年1月1日前)",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "50000"
        },
        {
            "SORTCODE": "51500",
            "SORTNAME": "月报表",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "50000"
        },
        {
            "SORTCODE": "52000",
            "SORTNAME": "委任代表表格",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "50000"
        },
        {
            "SORTCODE": "53000",
            "SORTNAME": "公司资料报表",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "50000"
        },
        {
            "SORTCODE": "54000",
            "SORTNAME": "宪章文件",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "50000"
        },
        {
            "SORTCODE": "55000",
            "SORTNAME": "合并守则-交易披露",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "50000"
        },
        {
            "SORTCODE": "56000",
            "SORTNAME": "标题类别-展示文件",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "50000"
        },
        {
            "SORTCODE": "57000",
            "SORTNAME": "标题类别-展示文件（债务证券发行计划）",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "50000"
        },
        {
            "SORTCODE": "58000",
            "SORTNAME": "标题类别-展示文件（债务证券）",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "50000"
        },
        {
            "SORTCODE": "59000",
            "SORTNAME": "标题类别–展示文件（结构性产品）",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "50000"
        },
        {
            "SORTCODE": "70000",
            "SORTNAME": "债券及结构性产品",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "40"
        },
        {
            "SORTCODE": "70001",
            "SORTNAME": "牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "70002",
            "SORTNAME": "衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "70003",
            "SORTNAME": "股票挂钩票据",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "70004",
            "SORTNAME": "结构性产品发行人",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "70005",
            "SORTNAME": "债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "70006",
            "SORTNAME": "债务证券发行计划",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "71100",
            "SORTNAME": "每日交易报告－衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "71200",
            "SORTNAME": "上市前交易报告－衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "71300",
            "SORTNAME": "每日交易报告－股票挂钩票据",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "71400",
            "SORTNAME": "上市前交易报告－股票挂钩票据",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "71500",
            "SORTNAME": "每日交易报告－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "71600",
            "SORTNAME": "上市前交易报告－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72100",
            "SORTNAME": "附加资料－非标准型衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72150",
            "SORTNAME": "到期公告－衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72200",
            "SORTNAME": "发行公告－衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72250",
            "SORTNAME": "其他－衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72300",
            "SORTNAME": "附加资料－非标准型股票挂钩票据",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72350",
            "SORTNAME": "到期公告－股票挂钩票据",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72400",
            "SORTNAME": "发行公告－股票挂钩票据",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72450",
            "SORTNAME": "其他－股票挂钩票据",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72500",
            "SORTNAME": "附加资料－非标准型牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72550",
            "SORTNAME": "到期公告－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72600",
            "SORTNAME": "发行公告－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72650",
            "SORTNAME": "其他－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72660",
            "SORTNAME": "调整条款及细则－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72661",
            "SORTNAME": "调整条款及细则（公告表格）－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72670",
            "SORTNAME": "内幕消息－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72680",
            "SORTNAME": "流通量供应服务－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72690",
            "SORTNAME": "市场受阻事件－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72700",
            "SORTNAME": "复牌－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72710",
            "SORTNAME": "停牌－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72720",
            "SORTNAME": "短暂停牌－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72730",
            "SORTNAME": "撤销上市－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72731",
            "SORTNAME": "撤销上市（公告表格）－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72740",
            "SORTNAME": "调整条款及细则－衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72741",
            "SORTNAME": "调整条款及细则（公告表格）－衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72750",
            "SORTNAME": "内幕消息－衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72760",
            "SORTNAME": "流通量供应服务－衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72770",
            "SORTNAME": "市场受阻事件－衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72780",
            "SORTNAME": "复牌－衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72790",
            "SORTNAME": "停牌－衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72800",
            "SORTNAME": "短暂停牌－衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72810",
            "SORTNAME": "撤销上市－衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72811",
            "SORTNAME": "撤销上市（公告表格）－衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72820",
            "SORTNAME": "调整条款及细则－股票挂钩票据",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72830",
            "SORTNAME": "内幕消息－股票挂钩票据",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72840",
            "SORTNAME": "流通量供应服务－股票挂钩票据",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72850",
            "SORTNAME": "市场受阻事件－股票挂钩票据",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72860",
            "SORTNAME": "复牌－股票挂钩票据",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72870",
            "SORTNAME": "停牌－股票挂钩票据",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72880",
            "SORTNAME": "短暂停牌－股票挂钩票据",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72890",
            "SORTNAME": "撤销上市－股票挂钩票据",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72900",
            "SORTNAME": "公司资料－结构性产品发行人",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72910",
            "SORTNAME": "信贷评级－结构性产品发行人",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72920",
            "SORTNAME": "财务披露或报告－结构性产品发行人",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72930",
            "SORTNAME": "内幕消息－结构性产品发行人",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72940",
            "SORTNAME": "其他－结构性产品发行人",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72950",
            "SORTNAME": "调整条款及细则－债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72960",
            "SORTNAME": "财务报告－债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72970",
            "SORTNAME": "内幕消息－债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72980",
            "SORTNAME": "赎回或购回－债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "72990",
            "SORTNAME": "复牌－债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "73000",
            "SORTNAME": "停牌－债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "73010",
            "SORTNAME": "短暂停牌－债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "73020",
            "SORTNAME": "撤销上市－债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "73030",
            "SORTNAME": "利息派发（公告表格）－债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "73100",
            "SORTNAME": "基础上市文件－衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "73200",
            "SORTNAME": "补充上市文件－衍生权证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "73300",
            "SORTNAME": "基础上市文件－股票挂钩票据",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "73400",
            "SORTNAME": "补充上市文件－股票挂钩票据",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "73500",
            "SORTNAME": "基础上市文件－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "73600",
            "SORTNAME": "补充上市文件－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "73700",
            "SORTNAME": "剩余价值（公告表格）－牛熊证",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "74100",
            "SORTNAME": "上市通告－债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "74200",
            "SORTNAME": "其他－债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "74300",
            "SORTNAME": "海外监管公告－债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "75100",
            "SORTNAME": "发行通函或定价补充文件－债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "75200",
            "SORTNAME": "招股章程－债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "75300",
            "SORTNAME": "发行人特定报告－债务证券",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "76100",
            "SORTNAME": "财务报告-债务证券发行计划",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "76200",
            "SORTNAME": "上市通告-债务证券发行计划",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "76300",
            "SORTNAME": "内幕消息-债务证券发行计划",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "76400",
            "SORTNAME": "发行人特定报告-债务证券发行计划",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "76500",
            "SORTNAME": "发行通函-债务证券发行计划",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "76600",
            "SORTNAME": "其他-债务证券发行计划",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "76700",
            "SORTNAME": "海外监管公告-债务证券发行计划",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "70000"
        },
        {
            "SORTCODE": "80000",
            "SORTNAME": "交易所买卖基金的交易资料",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "40"
        },
        {
            "SORTCODE": "81000",
            "SORTNAME": "杠杆及反向产品的交易资料",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "80000"
        },
        {
            "SORTCODE": "90000",
            "SORTNAME": "监管者发出的公告及消息",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "40"
        },
        {
            "SORTCODE": "91000",
            "SORTNAME": "申请版本﹑整体协调人公告及聆讯后资料集",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "90000"
        },
        {
            "SORTCODE": "91100",
            "SORTNAME": "聆讯后资料集或相关材料",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "91000"
        },
        {
            "SORTCODE": "91200",
            "SORTNAME": "申请版本或相关材料",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "91000"
        },
        {
            "SORTCODE": "91300",
            "SORTNAME": "整体协调人公告或相关材料",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "91000"
        },
        {
            "SORTCODE": "99999",
            "SORTNAME": "港交所新闻",
            "F002D": null,
            "F001D": "2023-08-15 00:00:00",
            "PARENTCODE": "90000"
        },
        {
            "SORTCODE": "L",
            "SORTNAME": "法律法规披露栏目",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "0"
        },
        {
            "SORTCODE": "L01",
            "SORTNAME": "证监会",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L"
        },
        {
            "SORTCODE": "L0101",
            "SORTNAME": "令",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L01"
        },
        {
            "SORTCODE": "L0102",
            "SORTNAME": "公告",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L01"
        },
        {
            "SORTCODE": "L0103",
            "SORTNAME": "监管规则适用指引",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L01"
        },
        {
            "SORTCODE": "L02",
            "SORTNAME": "深交所",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L"
        },
        {
            "SORTCODE": "L0201",
            "SORTNAME": "本所业务规则",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L02"
        },
        {
            "SORTCODE": "L020101",
            "SORTNAME": "综合类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0201"
        },
        {
            "SORTCODE": "L020102",
            "SORTNAME": "股票类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0201"
        },
        {
            "SORTCODE": "L02010201",
            "SORTNAME": "发行上市审核",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L020102"
        },
        {
            "SORTCODE": "L02010202",
            "SORTNAME": "发行承销",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L020102"
        },
        {
            "SORTCODE": "L02010203",
            "SORTNAME": "持续监管",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L020102"
        },
        {
            "SORTCODE": "L0201020301",
            "SORTNAME": "通用",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L02010203"
        },
        {
            "SORTCODE": "L0201020302",
            "SORTNAME": "主板专用",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L02010203"
        },
        {
            "SORTCODE": "L0201020303",
            "SORTNAME": "创业板专用",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L02010203"
        },
        {
            "SORTCODE": "L02010204",
            "SORTNAME": "交易",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L020102"
        },
        {
            "SORTCODE": "L020103",
            "SORTNAME": "固收类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0201"
        },
        {
            "SORTCODE": "L02010301",
            "SORTNAME": "债券",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L020103"
        },
        {
            "SORTCODE": "L0201030101",
            "SORTNAME": "发行上市（挂牌）",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L02010301"
        },
        {
            "SORTCODE": "L0201030102",
            "SORTNAME": "持续监管",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L02010301"
        },
        {
            "SORTCODE": "L0201030103",
            "SORTNAME": "交易",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L02010301"
        },
        {
            "SORTCODE": "L02010302",
            "SORTNAME": "资产支持证券",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L020103"
        },
        {
            "SORTCODE": "L020104",
            "SORTNAME": "基金类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0201"
        },
        {
            "SORTCODE": "L02010401",
            "SORTNAME": "上市",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L020104"
        },
        {
            "SORTCODE": "L02010402",
            "SORTNAME": "交易",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L020104"
        },
        {
            "SORTCODE": "L020105",
            "SORTNAME": "基础设施REITs类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0201"
        },
        {
            "SORTCODE": "L020106",
            "SORTNAME": "衍生品类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0201"
        },
        {
            "SORTCODE": "L020107",
            "SORTNAME": "交易类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0201"
        },
        {
            "SORTCODE": "L02010701",
            "SORTNAME": "通用",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L020107"
        },
        {
            "SORTCODE": "L02010702",
            "SORTNAME": "特定业务",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L020107"
        },
        {
            "SORTCODE": "L0201070201",
            "SORTNAME": "融资融券",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L02010702"
        },
        {
            "SORTCODE": "L0201070202",
            "SORTNAME": "转融通",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L02010702"
        },
        {
            "SORTCODE": "L0201070203",
            "SORTNAME": "股票质押式回购",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L02010702"
        },
        {
            "SORTCODE": "L0201070204",
            "SORTNAME": "质押式报价回购",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L02010702"
        },
        {
            "SORTCODE": "L0201070205",
            "SORTNAME": "约定购回",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L02010702"
        },
        {
            "SORTCODE": "L0201070206",
            "SORTNAME": "协议转让",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L02010702"
        },
        {
            "SORTCODE": "L0201070207",
            "SORTNAME": "其他",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L02010702"
        },
        {
            "SORTCODE": "L020108",
            "SORTNAME": "会员管理类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0201"
        },
        {
            "SORTCODE": "L020109",
            "SORTNAME": "跨境创新类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0201"
        },
        {
            "SORTCODE": "L02010901",
            "SORTNAME": "深港通",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L020109"
        },
        {
            "SORTCODE": "L02010902",
            "SORTNAME": "试点创新企业",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L020109"
        },
        {
            "SORTCODE": "L02010903",
            "SORTNAME": "H股全流通",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L020109"
        },
        {
            "SORTCODE": "L02010904",
            "SORTNAME": "互联互通存托凭证",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L020109"
        },
        {
            "SORTCODE": "L020110",
            "SORTNAME": "纪律处分与内部救济类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0201"
        },
        {
            "SORTCODE": "L0202",
            "SORTNAME": "本所业务指南",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L02"
        },
        {
            "SORTCODE": "L020201",
            "SORTNAME": "股票类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0202"
        },
        {
            "SORTCODE": "L020202",
            "SORTNAME": "固收类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0202"
        },
        {
            "SORTCODE": "L020203",
            "SORTNAME": "基金类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0202"
        },
        {
            "SORTCODE": "L020204",
            "SORTNAME": "基础设施REITs类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0202"
        },
        {
            "SORTCODE": "L020205",
            "SORTNAME": "衍生品类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0202"
        },
        {
            "SORTCODE": "L020206",
            "SORTNAME": "会员与交易类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0202"
        },
        {
            "SORTCODE": "L020207",
            "SORTNAME": "跨境创新类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0202"
        },
        {
            "SORTCODE": "L020208",
            "SORTNAME": "其他类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0202"
        },
        {
            "SORTCODE": "L03",
            "SORTNAME": "上交所",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L"
        },
        {
            "SORTCODE": "L0301",
            "SORTNAME": "本所业务规则",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03"
        },
        {
            "SORTCODE": "L030101",
            "SORTNAME": "章程",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0301"
        },
        {
            "SORTCODE": "L030102",
            "SORTNAME": "股票",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0301"
        },
        {
            "SORTCODE": "L03010201",
            "SORTNAME": "发行上市审核",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030102"
        },
        {
            "SORTCODE": "L0301020101",
            "SORTNAME": "首发",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010201"
        },
        {
            "SORTCODE": "L0301020102",
            "SORTNAME": "再融资",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010201"
        },
        {
            "SORTCODE": "L0301020103",
            "SORTNAME": "重组",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010201"
        },
        {
            "SORTCODE": "L0301020104",
            "SORTNAME": "转板",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010201"
        },
        {
            "SORTCODE": "L03010202",
            "SORTNAME": "发行承销",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030102"
        },
        {
            "SORTCODE": "L03010203",
            "SORTNAME": "主板上市（挂牌）",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030102"
        },
        {
            "SORTCODE": "L03010204",
            "SORTNAME": "科创板上市（挂牌）",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030102"
        },
        {
            "SORTCODE": "L03010205",
            "SORTNAME": "股票交易",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030102"
        },
        {
            "SORTCODE": "L03010206",
            "SORTNAME": "试点创新企业",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030102"
        },
        {
            "SORTCODE": "L03010207",
            "SORTNAME": "股权分置改革",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030102"
        },
        {
            "SORTCODE": "L030103",
            "SORTNAME": "债券",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0301"
        },
        {
            "SORTCODE": "L03010301",
            "SORTNAME": "发行上市审核",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030103"
        },
        {
            "SORTCODE": "L03010302",
            "SORTNAME": "发行承销",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030103"
        },
        {
            "SORTCODE": "L03010303",
            "SORTNAME": "上市（挂牌）",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030103"
        },
        {
            "SORTCODE": "L0301030301",
            "SORTNAME": "公司债券上市（挂牌）",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010303"
        },
        {
            "SORTCODE": "L0301030302",
            "SORTNAME": "资产支持证券上市（挂牌）",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010303"
        },
        {
            "SORTCODE": "L03010304",
            "SORTNAME": "债券交易",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030103"
        },
        {
            "SORTCODE": "L0301030401",
            "SORTNAME": "债券交易通用",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010304"
        },
        {
            "SORTCODE": "L0301030402",
            "SORTNAME": "国债预发行",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010304"
        },
        {
            "SORTCODE": "L0301030403",
            "SORTNAME": "债券质押式三方回购",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010304"
        },
        {
            "SORTCODE": "L0301030404",
            "SORTNAME": "债券质押式协议回购",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010304"
        },
        {
            "SORTCODE": "L0301030405",
            "SORTNAME": "国债买断式回购交易",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010304"
        },
        {
            "SORTCODE": "L0301030406",
            "SORTNAME": "信用保护工具",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010304"
        },
        {
            "SORTCODE": "L03010305",
            "SORTNAME": "上市公司可转债",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030103"
        },
        {
            "SORTCODE": "L030104",
            "SORTNAME": "基金",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0301"
        },
        {
            "SORTCODE": "L03010401",
            "SORTNAME": "基金上市",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030104"
        },
        {
            "SORTCODE": "L03010402",
            "SORTNAME": "基金交易",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030104"
        },
        {
            "SORTCODE": "L030105",
            "SORTNAME": "基础设施公募REITs",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0301"
        },
        {
            "SORTCODE": "L030106",
            "SORTNAME": "期权",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0301"
        },
        {
            "SORTCODE": "L030107",
            "SORTNAME": "交易通用",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0301"
        },
        {
            "SORTCODE": "L03010701",
            "SORTNAME": "通用类",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030107"
        },
        {
            "SORTCODE": "L03010702",
            "SORTNAME": "特定业务",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030107"
        },
        {
            "SORTCODE": "L0301070201",
            "SORTNAME": "融资融券",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010702"
        },
        {
            "SORTCODE": "L0301070202",
            "SORTNAME": "转融通",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010702"
        },
        {
            "SORTCODE": "L0301070203",
            "SORTNAME": "质押式回购",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010702"
        },
        {
            "SORTCODE": "L0301070204",
            "SORTNAME": "质押式报价回购",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010702"
        },
        {
            "SORTCODE": "L0301070205",
            "SORTNAME": "约定购回",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010702"
        },
        {
            "SORTCODE": "L0301070206",
            "SORTNAME": "协议转让",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010702"
        },
        {
            "SORTCODE": "L0301070207",
            "SORTNAME": "其他",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03010702"
        },
        {
            "SORTCODE": "L030108",
            "SORTNAME": "跨境创新业务",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0301"
        },
        {
            "SORTCODE": "L03010801",
            "SORTNAME": "沪港通",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030108"
        },
        {
            "SORTCODE": "L03010802",
            "SORTNAME": "互联互通存托凭证",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030108"
        },
        {
            "SORTCODE": "L030109",
            "SORTNAME": "会员管理",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0301"
        },
        {
            "SORTCODE": "L03010901",
            "SORTNAME": "会员管理",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030109"
        },
        {
            "SORTCODE": "L03010902",
            "SORTNAME": "适当性管理",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030109"
        },
        {
            "SORTCODE": "L030110",
            "SORTNAME": "纪律处分与复核",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0301"
        },
        {
            "SORTCODE": "L030111",
            "SORTNAME": "交易收费",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0301"
        },
        {
            "SORTCODE": "L030112",
            "SORTNAME": "其他业务规则",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0301"
        },
        {
            "SORTCODE": "L0302",
            "SORTNAME": "本所业务指南与流程",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03"
        },
        {
            "SORTCODE": "L030201",
            "SORTNAME": "股票业务指南与流程",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0302"
        },
        {
            "SORTCODE": "L03020101",
            "SORTNAME": "发行上市审核业务指南",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030201"
        },
        {
            "SORTCODE": "L03020102",
            "SORTNAME": "发行承销业务指南",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030201"
        },
        {
            "SORTCODE": "L0302010201",
            "SORTNAME": "发行承销业务指南",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03020102"
        },
        {
            "SORTCODE": "L0302010202",
            "SORTNAME": "发行承销工作通知",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03020102"
        },
        {
            "SORTCODE": "L03020103",
            "SORTNAME": "主板信息披露监管业务指南",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030201"
        },
        {
            "SORTCODE": "L0302010301",
            "SORTNAME": "上市公司自律监管指南",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03020103"
        },
        {
            "SORTCODE": "L0302010302",
            "SORTNAME": "上市公司专项信息披露指南",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03020103"
        },
        {
            "SORTCODE": "L0302010302A",
            "SORTNAME": "境外发行人信息披露业务",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0302010302"
        },
        {
            "SORTCODE": "L0302010302B",
            "SORTNAME": "上市公司股权分置改革",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0302010302"
        },
        {
            "SORTCODE": "L0302010303",
            "SORTNAME": "上市公司信息披露工作通知",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03020103"
        },
        {
            "SORTCODE": "L03020104",
            "SORTNAME": "科创板信息披露监管业务指南",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030201"
        },
        {
            "SORTCODE": "L03020105",
            "SORTNAME": "交易管理业务指南与流程",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L030201"
        },
        {
            "SORTCODE": "L0302010501",
            "SORTNAME": "交易管理业务指南",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03020105"
        },
        {
            "SORTCODE": "L0302010502",
            "SORTNAME": "交易管理工作通知",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L03020105"
        },
        {
            "SORTCODE": "L030202",
            "SORTNAME": "会员管理业务指南与流程",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0302"
        },
        {
            "SORTCODE": "L030203",
            "SORTNAME": "债券业务指南与流程",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0302"
        },
        {
            "SORTCODE": "L030204",
            "SORTNAME": "基金业务指南与流程",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0302"
        },
        {
            "SORTCODE": "L030205",
            "SORTNAME": "基础设施公募REITs业务指南与流程",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0302"
        },
        {
            "SORTCODE": "L030206",
            "SORTNAME": "市场监管业务指南与流程",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0302"
        },
        {
            "SORTCODE": "L030207",
            "SORTNAME": "互联互通存托凭证业务指南与流程",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0302"
        },
        {
            "SORTCODE": "L030208",
            "SORTNAME": "股票期权业务指南与流程",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0302"
        },
        {
            "SORTCODE": "L030209",
            "SORTNAME": "协议转让业务指南与流程",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0302"
        },
        {
            "SORTCODE": "L030210",
            "SORTNAME": "其他业务指南与流程",
            "F002D": null,
            "F001D": "2025-07-22 00:00:00",
            "PARENTCODE": "L0302"
        },
        {
            "SORTCODE": "L04",
            "SORTNAME": "北交所",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L"
        },
        {
            "SORTCODE": "L0401",
            "SORTNAME": "法律规则",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L04"
        },
        {
            "SORTCODE": "L040101",
            "SORTNAME": "业务规则",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0401"
        },
        {
            "SORTCODE": "L04010101",
            "SORTNAME": "股票",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L040101"
        },
        {
            "SORTCODE": "L0401010101",
            "SORTNAME": "发行融资",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L04010101"
        },
        {
            "SORTCODE": "L0401010102",
            "SORTNAME": "持续监管",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L04010101"
        },
        {
            "SORTCODE": "L0401010103",
            "SORTNAME": "交易管理",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L04010101"
        },
        {
            "SORTCODE": "L04010102",
            "SORTNAME": "债券",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L040101"
        },
        {
            "SORTCODE": "L0401010201",
            "SORTNAME": "发行融资",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L04010102"
        },
        {
            "SORTCODE": "L0401010202",
            "SORTNAME": "持续监管",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L04010102"
        },
        {
            "SORTCODE": "L0401010203",
            "SORTNAME": "交易管理",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L04010102"
        },
        {
            "SORTCODE": "L04010103",
            "SORTNAME": "市场管理",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L040101"
        },
        {
            "SORTCODE": "L040102",
            "SORTNAME": "服务指南",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0401"
        },
        {
            "SORTCODE": "L05",
            "SORTNAME": "中国证券业协会",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L"
        },
        {
            "SORTCODE": "L0501",
            "SORTNAME": "自律规则",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L05"
        },
        {
            "SORTCODE": "L06",
            "SORTNAME": "中基协",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L"
        },
        {
            "SORTCODE": "L0601",
            "SORTNAME": "政策法规",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L06"
        },
        {
            "SORTCODE": "L060101",
            "SORTNAME": "自律规则",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0601"
        },
        {
            "SORTCODE": "L06010101",
            "SORTNAME": "自律管理",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L060101"
        },
        {
            "SORTCODE": "L06010102",
            "SORTNAME": "会员管理",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L060101"
        },
        {
            "SORTCODE": "L06010103",
            "SORTNAME": "公募基金",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L060101"
        },
        {
            "SORTCODE": "L06010104",
            "SORTNAME": "私募基金",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L060101"
        },
        {
            "SORTCODE": "L06010105",
            "SORTNAME": "资产管理",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L060101"
        },
        {
            "SORTCODE": "L06010106",
            "SORTNAME": "基金托管及服务",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L060101"
        },
        {
            "SORTCODE": "L06010107",
            "SORTNAME": "从业人员",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L060101"
        },
        {
            "SORTCODE": "L06010108",
            "SORTNAME": "信息科技",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L060101"
        },
        {
            "SORTCODE": "L06010109",
            "SORTNAME": "其他",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L060101"
        },
        {
            "SORTCODE": "L07",
            "SORTNAME": "中国结算",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L"
        },
        {
            "SORTCODE": "L0701",
            "SORTNAME": "法律规则",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L07"
        },
        {
            "SORTCODE": "L070101",
            "SORTNAME": "业务规则",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0701"
        },
        {
            "SORTCODE": "L07010101",
            "SORTNAME": "账户管理",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L070101"
        },
        {
            "SORTCODE": "L07010102",
            "SORTNAME": "登记与存管",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L070101"
        },
        {
            "SORTCODE": "L07010103",
            "SORTNAME": "清算与交收",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L070101"
        },
        {
            "SORTCODE": "L07010104",
            "SORTNAME": "证券发行",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L070101"
        },
        {
            "SORTCODE": "L07010105",
            "SORTNAME": "债券业务",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L070101"
        },
        {
            "SORTCODE": "L07010106",
            "SORTNAME": "股票期权",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L070101"
        },
        {
            "SORTCODE": "L07010107",
            "SORTNAME": "融资融券与转融通",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L070101"
        },
        {
            "SORTCODE": "L07010108",
            "SORTNAME": "基金与资产管理业务",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L070101"
        },
        {
            "SORTCODE": "L07010109",
            "SORTNAME": "涉外与跨境业务",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L070101"
        },
        {
            "SORTCODE": "L07010110",
            "SORTNAME": "协助执法",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L070101"
        },
        {
            "SORTCODE": "L07010111",
            "SORTNAME": "其他",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L070101"
        },
        {
            "SORTCODE": "L08",
            "SORTNAME": "中国银行间市场交易商协会",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L"
        },
        {
            "SORTCODE": "L0801",
            "SORTNAME": "自律",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L08"
        },
        {
            "SORTCODE": "L080101",
            "SORTNAME": "自律规则",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L0801"
        },
        {
            "SORTCODE": "L08010101",
            "SORTNAME": "会员管理类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L080101"
        },
        {
            "SORTCODE": "L08010102",
            "SORTNAME": "产品创新类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L080101"
        },
        {
            "SORTCODE": "L08010103",
            "SORTNAME": "注册发行类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L080101"
        },
        {
            "SORTCODE": "L0801010301",
            "SORTNAME": "注册类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L08010103"
        },
        {
            "SORTCODE": "L0801010302",
            "SORTNAME": "发行类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L08010103"
        },
        {
            "SORTCODE": "L08010104",
            "SORTNAME": "存续期管理",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L080101"
        },
        {
            "SORTCODE": "L08010105",
            "SORTNAME": "交易规范类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L080101"
        },
        {
            "SORTCODE": "L0801010501",
            "SORTNAME": "债券交易类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L08010105"
        },
        {
            "SORTCODE": "L0801010502",
            "SORTNAME": "衍生品业务类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L08010105"
        },
        {
            "SORTCODE": "L0801010503",
            "SORTNAME": "非金平台类",
            "F002D": null,
            "F001D": "2025-07-25 00:00:00",
            "PARENTCODE": "L08010105"
        },
        {
            "SORTCODE": "MISC",
            "SORTNAME": "杂项",
            "F002D": null,
            "F001D": "2021-06-08 00:00:00",
            "PARENTCODE": "40"
        },
        {
            "SORTCODE": "N",
            "SORTNAME": "新三板公告分类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "0"
        },
        {
            "SORTCODE": "N001",
            "SORTNAME": "定期报告类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N001001",
            "SORTNAME": "年度报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N001"
        },
        {
            "SORTCODE": "N001002",
            "SORTNAME": "半年度报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N001"
        },
        {
            "SORTCODE": "N001003",
            "SORTNAME": "一季度报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N001"
        },
        {
            "SORTCODE": "N001004",
            "SORTNAME": "三季度报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N001"
        },
        {
            "SORTCODE": "N001005",
            "SORTNAME": "会计师事务所专项说明",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N001"
        },
        {
            "SORTCODE": "N001006",
            "SORTNAME": "会计变更",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N001"
        },
        {
            "SORTCODE": "N001007",
            "SORTNAME": "会计差错更正",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N001"
        },
        {
            "SORTCODE": "N001008",
            "SORTNAME": "审查报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N001"
        },
        {
            "SORTCODE": "N001009",
            "SORTNAME": "未按期披露报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N001"
        },
        {
            "SORTCODE": "N001010",
            "SORTNAME": "内部控制评价报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N001"
        },
        {
            "SORTCODE": "N001011",
            "SORTNAME": "财务信息报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N001"
        },
        {
            "SORTCODE": "N001012",
            "SORTNAME": "月度报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N001"
        },
        {
            "SORTCODE": "N002",
            "SORTNAME": "业绩类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N002001",
            "SORTNAME": "业绩预告公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N002"
        },
        {
            "SORTCODE": "N002002",
            "SORTNAME": "业绩快报公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N002"
        },
        {
            "SORTCODE": "N002003",
            "SORTNAME": "业绩补充公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N002"
        },
        {
            "SORTCODE": "N002004",
            "SORTNAME": "业绩风险提示公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N002"
        },
        {
            "SORTCODE": "N002005",
            "SORTNAME": "经营业绩",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N002"
        },
        {
            "SORTCODE": "N002006",
            "SORTNAME": "业绩补偿",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N002"
        },
        {
            "SORTCODE": "N002007",
            "SORTNAME": "业绩说明会",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N002"
        },
        {
            "SORTCODE": "N003",
            "SORTNAME": "公司治理类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N003001",
            "SORTNAME": "董事会决议公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N003"
        },
        {
            "SORTCODE": "N003002",
            "SORTNAME": "监事会决议公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N003"
        },
        {
            "SORTCODE": "N003003",
            "SORTNAME": "职工代表大会公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N003"
        },
        {
            "SORTCODE": "N003004",
            "SORTNAME": "独立董事意见",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N003"
        },
        {
            "SORTCODE": "N003005",
            "SORTNAME": "其他关于公司治理的公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N003"
        },
        {
            "SORTCODE": "N003006",
            "SORTNAME": "股东大会通知公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N003"
        },
        {
            "SORTCODE": "N003007",
            "SORTNAME": "会议相关信息变更",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N003"
        },
        {
            "SORTCODE": "N003008",
            "SORTNAME": "（临时）股东大会",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N003"
        },
        {
            "SORTCODE": "N003009",
            "SORTNAME": "股东大会决议",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N003"
        },
        {
            "SORTCODE": "N003010",
            "SORTNAME": "其他股东大会相关公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N003"
        },
        {
            "SORTCODE": "N003011",
            "SORTNAME": "回复公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N003"
        },
        {
            "SORTCODE": "N003012",
            "SORTNAME": "律师事务所公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N003"
        },
        {
            "SORTCODE": "N003013",
            "SORTNAME": "述职报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N003"
        },
        {
            "SORTCODE": "N003014",
            "SORTNAME": "投票相关细则",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N003"
        },
        {
            "SORTCODE": "N003015",
            "SORTNAME": "问询函相关公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N003"
        },
        {
            "SORTCODE": "N003016",
            "SORTNAME": "限制消费令",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N003"
        },
        {
            "SORTCODE": "N003017",
            "SORTNAME": "自愿性公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N003"
        },
        {
            "SORTCODE": "N004",
            "SORTNAME": "公司经营类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N004001",
            "SORTNAME": "获得补贴补助公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004002",
            "SORTNAME": "资质许可特许经营权等生产经营条件相关公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004003",
            "SORTNAME": "对外投资公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004004",
            "SORTNAME": "对外提供担保公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004005",
            "SORTNAME": "关联交易",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004006",
            "SORTNAME": "购买出售资产公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004007",
            "SORTNAME": "签订重大经营合同公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004008",
            "SORTNAME": "签订战略框架协议及其进展公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004009",
            "SORTNAME": "债权债务相关公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004010",
            "SORTNAME": "子/孙公司公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004011",
            "SORTNAME": "对外捐助情况",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004012",
            "SORTNAME": "生产情况公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004013",
            "SORTNAME": "公司账款管理公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004014",
            "SORTNAME": "中标公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004015",
            "SORTNAME": "融资公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004016",
            "SORTNAME": "资金使用公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004017",
            "SORTNAME": "资金交易往来公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004018",
            "SORTNAME": "资产变动相关公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004019",
            "SORTNAME": "租入租出资产公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004020",
            "SORTNAME": "委托受托经营公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N004021",
            "SORTNAME": "其它经营类公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N004"
        },
        {
            "SORTCODE": "N005",
            "SORTNAME": "公司及董监高信息变更类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N005001",
            "SORTNAME": "变更公司全称",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N005"
        },
        {
            "SORTCODE": "N005002",
            "SORTNAME": "变更证券简称",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N005"
        },
        {
            "SORTCODE": "N005003",
            "SORTNAME": "董监高人事变动",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N005"
        },
        {
            "SORTCODE": "N005004",
            "SORTNAME": "被调出创新层的公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N005"
        },
        {
            "SORTCODE": "N005005",
            "SORTNAME": "会计师事务所变更公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N005"
        },
        {
            "SORTCODE": "N005006",
            "SORTNAME": "主营业务变更公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N005"
        },
        {
            "SORTCODE": "N005007",
            "SORTNAME": "营业执照管理",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N005"
        },
        {
            "SORTCODE": "N005008",
            "SORTNAME": "工商登记信息变更",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N005"
        },
        {
            "SORTCODE": "N005009",
            "SORTNAME": "律师事务所变更",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N005"
        },
        {
            "SORTCODE": "N006",
            "SORTNAME": "股票发行及相关业务办理类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N006001",
            "SORTNAME": "股票发行说明书",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N006"
        },
        {
            "SORTCODE": "N006002",
            "SORTNAME": "资产评估报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N006"
        },
        {
            "SORTCODE": "N006003",
            "SORTNAME": "主办券商关于定向发行的推荐工作报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N006"
        },
        {
            "SORTCODE": "N006004",
            "SORTNAME": "股票发行方案",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N006"
        },
        {
            "SORTCODE": "N006005",
            "SORTNAME": "募集资金相关公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N006"
        },
        {
            "SORTCODE": "N006006",
            "SORTNAME": "股票发行进展",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N006"
        },
        {
            "SORTCODE": "N006007",
            "SORTNAME": "股票认购公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N006"
        },
        {
            "SORTCODE": "N006008",
            "SORTNAME": "向不特定合格投资者发行并在精选层挂牌",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N006"
        },
        {
            "SORTCODE": "N006009",
            "SORTNAME": "律师关于定向发行的法律意见书",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N006"
        },
        {
            "SORTCODE": "N006010",
            "SORTNAME": "股票发行相关机构/人员变更",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N006"
        },
        {
            "SORTCODE": "N006011",
            "SORTNAME": "普通股新增股份挂牌公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N006"
        },
        {
            "SORTCODE": "N006012",
            "SORTNAME": "其他关于股票发行的公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N006"
        },
        {
            "SORTCODE": "N006013",
            "SORTNAME": "变更主办券商",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N006"
        },
        {
            "SORTCODE": "N007",
            "SORTNAME": "优先股及相关业务办理类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N007001",
            "SORTNAME": "优先股股息相关公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N007"
        },
        {
            "SORTCODE": "N007002",
            "SORTNAME": "优先股转让",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N007"
        },
        {
            "SORTCODE": "N007003",
            "SORTNAME": "优先股发行认购",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N007"
        },
        {
            "SORTCODE": "N007004",
            "SORTNAME": "优先股赎回",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N007"
        },
        {
            "SORTCODE": "N007005",
            "SORTNAME": "非公开发行优先股",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N007"
        },
        {
            "SORTCODE": "N007006",
            "SORTNAME": "优先股募集资金情况",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N007"
        },
        {
            "SORTCODE": "N007007",
            "SORTNAME": "优先股发行进展",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N007"
        },
        {
            "SORTCODE": "N007008",
            "SORTNAME": "其它关于优先股公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N007"
        },
        {
            "SORTCODE": "N007009",
            "SORTNAME": "收到股转系统优先股相关文件",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N007"
        },
        {
            "SORTCODE": "N007010",
            "SORTNAME": "优先股表决权相关公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N007"
        },
        {
            "SORTCODE": "N007011",
            "SORTNAME": "优先股风险警示公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N007"
        },
        {
            "SORTCODE": "N007012",
            "SORTNAME": "优先股权益变化公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N007"
        },
        {
            "SORTCODE": "N008",
            "SORTNAME": "固定收益类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N008001",
            "SORTNAME": "发行公司（可转换）债券",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N008"
        },
        {
            "SORTCODE": "N008002",
            "SORTNAME": "债券财务报表",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N008"
        },
        {
            "SORTCODE": "N008003",
            "SORTNAME": "可转债公告",
            "F002D": null,
            "F001D": "2024-09-09 00:00:00",
            "PARENTCODE": "N008"
        },
        {
            "SORTCODE": "N009",
            "SORTNAME": "重大资产重组类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N009001",
            "SORTNAME": "重大资产重组预案",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N009"
        },
        {
            "SORTCODE": "N009002",
            "SORTNAME": "对重组的核查意见/问询函",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N009"
        },
        {
            "SORTCODE": "N009003",
            "SORTNAME": "重大资产重组报告书",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N009"
        },
        {
            "SORTCODE": "N009004",
            "SORTNAME": "重大资产重组独立财务顾问报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N009"
        },
        {
            "SORTCODE": "N009005",
            "SORTNAME": "重大资产重组法律意见书",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N009"
        },
        {
            "SORTCODE": "N009006",
            "SORTNAME": "重大资产重组实施情况报告书",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N009"
        },
        {
            "SORTCODE": "N009007",
            "SORTNAME": "重大资产重组持续督导意见",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N009"
        },
        {
            "SORTCODE": "N009008",
            "SORTNAME": "标的资产评估/估值报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N009"
        },
        {
            "SORTCODE": "N009009",
            "SORTNAME": "中止/恢复重大资产重组的公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N009"
        },
        {
            "SORTCODE": "N009010",
            "SORTNAME": "终止重大资产重组的公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N009"
        },
        {
            "SORTCODE": "N009011",
            "SORTNAME": "重组相关证券存在异常转让情况公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N009"
        },
        {
            "SORTCODE": "N009012",
            "SORTNAME": "其他关于重大资产重组的公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N009"
        },
        {
            "SORTCODE": "N009013",
            "SORTNAME": "重大资产重组进展/情况说明",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N009"
        },
        {
            "SORTCODE": "N009014",
            "SORTNAME": "标的资产审计报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N009"
        },
        {
            "SORTCODE": "N009015",
            "SORTNAME": "标的资产盈利预测报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N009"
        },
        {
            "SORTCODE": "N010",
            "SORTNAME": "收购类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N010001",
            "SORTNAME": "权益变动报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N010"
        },
        {
            "SORTCODE": "N010002",
            "SORTNAME": "收购报告书",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N010"
        },
        {
            "SORTCODE": "N010003",
            "SORTNAME": "要约收购报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N010"
        },
        {
            "SORTCODE": "N010004",
            "SORTNAME": "实际控制人及其一致行动人变更公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N010"
        },
        {
            "SORTCODE": "N010005",
            "SORTNAME": "收购相关报告/意见/协议",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N010"
        },
        {
            "SORTCODE": "N010006",
            "SORTNAME": "收购进展公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N010"
        },
        {
            "SORTCODE": "N010007",
            "SORTNAME": "挂牌公司董事会报告书",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N010"
        },
        {
            "SORTCODE": "N010008",
            "SORTNAME": "其他关于收购的公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N010"
        },
        {
            "SORTCODE": "N010009",
            "SORTNAME": "收购资产/股权",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N010"
        },
        {
            "SORTCODE": "N010010",
            "SORTNAME": "收购人相关承诺",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N010"
        },
        {
            "SORTCODE": "N010011",
            "SORTNAME": "要约收购取得国家相关部门批准的提示性公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N010"
        },
        {
            "SORTCODE": "N010012",
            "SORTNAME": "收购人审计报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N010"
        },
        {
            "SORTCODE": "N010013",
            "SORTNAME": "因权益分派调整收购要约的提示性公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N010"
        },
        {
            "SORTCODE": "N011",
            "SORTNAME": "股权相关类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N011001",
            "SORTNAME": "股权质押公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N011"
        },
        {
            "SORTCODE": "N011002",
            "SORTNAME": "股权司法冻结公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N011"
        },
        {
            "SORTCODE": "N011003",
            "SORTNAME": "股东持股（变动）情况",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N011"
        },
        {
            "SORTCODE": "N011004",
            "SORTNAME": "持股百分之五以上股东相关公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N011"
        },
        {
            "SORTCODE": "N011005",
            "SORTNAME": "股权分置改革",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N011"
        },
        {
            "SORTCODE": "N011006",
            "SORTNAME": "股权转让",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N011"
        },
        {
            "SORTCODE": "N011007",
            "SORTNAME": "股权登记日变更",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N011"
        },
        {
            "SORTCODE": "N011008",
            "SORTNAME": "股权受限解除公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N011"
        },
        {
            "SORTCODE": "N011009",
            "SORTNAME": "股份确权",
            "F002D": null,
            "F001D": "2023-08-17 00:00:00",
            "PARENTCODE": "N011"
        },
        {
            "SORTCODE": "N012",
            "SORTNAME": "股权激励类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N012001",
            "SORTNAME": "股权激励计划",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N012"
        },
        {
            "SORTCODE": "N012002",
            "SORTNAME": "限制性股票激励计划",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N012"
        },
        {
            "SORTCODE": "N012003",
            "SORTNAME": "监事会关于股权激励计划的相关公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N012"
        },
        {
            "SORTCODE": "N012004",
            "SORTNAME": "员工持股计划类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N012"
        },
        {
            "SORTCODE": "N013",
            "SORTNAME": "股份回购类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N013001",
            "SORTNAME": "回购进展情况公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N013"
        },
        {
            "SORTCODE": "N013002",
            "SORTNAME": "回购股份方案",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N013"
        },
        {
            "SORTCODE": "N013003",
            "SORTNAME": "内幕信息知情人买卖本公司股票情况的自查报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N013"
        },
        {
            "SORTCODE": "N013004",
            "SORTNAME": "定向回购",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N013"
        },
        {
            "SORTCODE": "N013005",
            "SORTNAME": "要约回购",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N013"
        },
        {
            "SORTCODE": "N013006",
            "SORTNAME": "回购股份注销完成暨股份变动公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N013"
        },
        {
            "SORTCODE": "N013007",
            "SORTNAME": "变更或终止回购股份方案的公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N013"
        },
        {
            "SORTCODE": "N013008",
            "SORTNAME": "回购实施预告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N013"
        },
        {
            "SORTCODE": "N013009",
            "SORTNAME": "回购价格及回购数量的调整公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N013"
        },
        {
            "SORTCODE": "N013010",
            "SORTNAME": "通知债权人的情况公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N013"
        },
        {
            "SORTCODE": "N013011",
            "SORTNAME": "回购股份结果公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N013"
        },
        {
            "SORTCODE": "N013012",
            "SORTNAME": "主办券商关于股份回购相关合法合规意见",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N013"
        },
        {
            "SORTCODE": "N013013",
            "SORTNAME": "开始接受要约申报的提示性公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N013"
        },
        {
            "SORTCODE": "N013014",
            "SORTNAME": "竞价/做市方式回购",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N013"
        },
        {
            "SORTCODE": "N013015",
            "SORTNAME": "其他关于股份回购的公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N013"
        },
        {
            "SORTCODE": "N013016",
            "SORTNAME": "回购相关风险提示公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N013"
        },
        {
            "SORTCODE": "N014",
            "SORTNAME": "风险事项类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N014001",
            "SORTNAME": "涉及仲裁及进展",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014002",
            "SORTNAME": "重大亏损重大损失或承担重大赔偿责任",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014003",
            "SORTNAME": "主要资产被查封扣押冻结等受限类公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014004",
            "SORTNAME": "破产清算类公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014005",
            "SORTNAME": "澄清公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014006",
            "SORTNAME": "董事长实际控制人等无法履职或取得联系",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014007",
            "SORTNAME": "未弥补亏损达到（超过）实收资本总额三分之一",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014008",
            "SORTNAME": "涉及诉讼及进展",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014009",
            "SORTNAME": "挂牌公司及关联方涉嫌违法违规被立案调查或收到行政处罚自律监管",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014010",
            "SORTNAME": "警示函",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014011",
            "SORTNAME": "口头警告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014012",
            "SORTNAME": "处分决定书",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014013",
            "SORTNAME": "公司风险提示性公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014014",
            "SORTNAME": "各大风险类型说明",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014015",
            "SORTNAME": "风险处置预案",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014016",
            "SORTNAME": "风险事项说明",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014017",
            "SORTNAME": "风险管理",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014018",
            "SORTNAME": "风险消除公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014019",
            "SORTNAME": "公司涉嫌违法违规的情况及整改情况公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N014020",
            "SORTNAME": "股票异常波动公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N014"
        },
        {
            "SORTCODE": "N015",
            "SORTNAME": "诚信情况类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N015001",
            "SORTNAME": "承诺新增公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N015"
        },
        {
            "SORTCODE": "N015002",
            "SORTNAME": "承诺履行相关公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N015"
        },
        {
            "SORTCODE": "N015003",
            "SORTNAME": "失信相关公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N015"
        },
        {
            "SORTCODE": "N015004",
            "SORTNAME": "承诺事项/进展公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N015"
        },
        {
            "SORTCODE": "N015005",
            "SORTNAME": "承诺管理制度",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N015"
        },
        {
            "SORTCODE": "N015006",
            "SORTNAME": "回购承诺",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N015"
        },
        {
            "SORTCODE": "N015007",
            "SORTNAME": "书面承诺相关公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N015"
        },
        {
            "SORTCODE": "N015008",
            "SORTNAME": "不买卖股票承诺",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N015"
        },
        {
            "SORTCODE": "N015009",
            "SORTNAME": "业绩承诺",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N015"
        },
        {
            "SORTCODE": "N015010",
            "SORTNAME": "其他关于诚信情况的公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N015"
        },
        {
            "SORTCODE": "N016",
            "SORTNAME": "交易上市类",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N016001",
            "SORTNAME": "股票限售公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N016"
        },
        {
            "SORTCODE": "N016002",
            "SORTNAME": "股票转让",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N016"
        },
        {
            "SORTCODE": "N016003",
            "SORTNAME": "股票停牌",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N016"
        },
        {
            "SORTCODE": "N016004",
            "SORTNAME": "股票复牌",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N016"
        },
        {
            "SORTCODE": "N016005",
            "SORTNAME": "被实行风险警示的公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N016"
        },
        {
            "SORTCODE": "N016006",
            "SORTNAME": "撤销风险警示的公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N016"
        },
        {
            "SORTCODE": "N016007",
            "SORTNAME": "两网及退市公司股票转让方式变更公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N016"
        },
        {
            "SORTCODE": "N016008",
            "SORTNAME": "可能被终止挂牌的风险提示公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N016"
        },
        {
            "SORTCODE": "N016009",
            "SORTNAME": "拟申请终止挂牌公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N016"
        },
        {
            "SORTCODE": "N016010",
            "SORTNAME": "股东权益保护措施",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N016"
        },
        {
            "SORTCODE": "N016011",
            "SORTNAME": "复核公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N016"
        },
        {
            "SORTCODE": "N016012",
            "SORTNAME": "终止挂牌进展公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N016"
        },
        {
            "SORTCODE": "N016013",
            "SORTNAME": "投资者保护措施",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N016"
        },
        {
            "SORTCODE": "N016014",
            "SORTNAME": "主动终止挂牌公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N016"
        },
        {
            "SORTCODE": "N016015",
            "SORTNAME": "被强制终止挂牌的公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N016"
        },
        {
            "SORTCODE": "N016016",
            "SORTNAME": "其他关于终止挂牌的公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N016"
        },
        {
            "SORTCODE": "N017",
            "SORTNAME": "做市类公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N017001",
            "SORTNAME": "股票回售",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N017"
        },
        {
            "SORTCODE": "N017002",
            "SORTNAME": "股票转售",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N017"
        },
        {
            "SORTCODE": "N017003",
            "SORTNAME": "为挂牌公司提供做市报价服务的公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N017"
        },
        {
            "SORTCODE": "N017004",
            "SORTNAME": "退出为挂牌公司提供做市报价服务的公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N017"
        },
        {
            "SORTCODE": "N017005",
            "SORTNAME": "股票暂停转让",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N017"
        },
        {
            "SORTCODE": "N017006",
            "SORTNAME": "股票暂停交易",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N017"
        },
        {
            "SORTCODE": "N017007",
            "SORTNAME": "变更股票转让方式",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N017"
        },
        {
            "SORTCODE": "N017008",
            "SORTNAME": "做市商数量不足",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N017"
        },
        {
            "SORTCODE": "N017009",
            "SORTNAME": "做市商数量恢复",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N017"
        },
        {
            "SORTCODE": "N018",
            "SORTNAME": "主办券商公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N018001",
            "SORTNAME": "主办券商风险提示公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N018"
        },
        {
            "SORTCODE": "N018002",
            "SORTNAME": "持续督导协议",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N018"
        },
        {
            "SORTCODE": "N018003",
            "SORTNAME": "托管协议",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N018"
        },
        {
            "SORTCODE": "N018004",
            "SORTNAME": "主办券商推荐工作报告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N018"
        },
        {
            "SORTCODE": "N018005",
            "SORTNAME": "内部鉴证",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N018"
        },
        {
            "SORTCODE": "N018006",
            "SORTNAME": "主办券商其他公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N018"
        },
        {
            "SORTCODE": "N019",
            "SORTNAME": "权益分派",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N019001",
            "SORTNAME": "权益分派预案公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N019"
        },
        {
            "SORTCODE": "N019002",
            "SORTNAME": "权益分派实施公告（全部或部分代派）",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N019"
        },
        {
            "SORTCODE": "N019003",
            "SORTNAME": "权益分派实施公告（全部自派）",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N019"
        },
        {
            "SORTCODE": "N019004",
            "SORTNAME": "因股本变动调整权益分派比例的公告（分派总额不变）",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N019"
        },
        {
            "SORTCODE": "N019005",
            "SORTNAME": "权益分派终止/延期公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N019"
        },
        {
            "SORTCODE": "N019006",
            "SORTNAME": "资本公积",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N019"
        },
        {
            "SORTCODE": "N019007",
            "SORTNAME": "权益分派",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N019"
        },
        {
            "SORTCODE": "N019008",
            "SORTNAME": "股息派发方案",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N019"
        },
        {
            "SORTCODE": "N019009",
            "SORTNAME": "因会计差错更正调整权益分派",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N019"
        },
        {
            "SORTCODE": "N019010",
            "SORTNAME": "利润分配方案",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N019"
        },
        {
            "SORTCODE": "N019011",
            "SORTNAME": "未按期实施权益分派的致歉公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N019"
        },
        {
            "SORTCODE": "N020",
            "SORTNAME": "章程制度",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N020001",
            "SORTNAME": "公司内部章程",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N020"
        },
        {
            "SORTCODE": "N020002",
            "SORTNAME": "对外担保制度",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N020"
        },
        {
            "SORTCODE": "N020003",
            "SORTNAME": "管理制度",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N020"
        },
        {
            "SORTCODE": "N020004",
            "SORTNAME": "薪酬制度",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N020"
        },
        {
            "SORTCODE": "N020005",
            "SORTNAME": "信息披露制度",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N020"
        },
        {
            "SORTCODE": "N020006",
            "SORTNAME": "绩效考核制度",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N020"
        },
        {
            "SORTCODE": "N020007",
            "SORTNAME": "责任追究制度",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N020"
        },
        {
            "SORTCODE": "N020008",
            "SORTNAME": "内部审计制度",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N020"
        },
        {
            "SORTCODE": "N020009",
            "SORTNAME": "实施细则",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N020"
        },
        {
            "SORTCODE": "N020010",
            "SORTNAME": "工作议事相关规则",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N020"
        },
        {
            "SORTCODE": "N020011",
            "SORTNAME": "相关制度变更公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N020"
        },
        {
            "SORTCODE": "N021",
            "SORTNAME": "其他",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N"
        },
        {
            "SORTCODE": "N021001",
            "SORTNAME": "其他公告",
            "F002D": null,
            "F001D": "2021-11-17 00:00:00",
            "PARENTCODE": "N021"
        }
    ],
    "resultmsg": "success",
    "count": 2134,
    "resultcode": 200,
    "FromCahce": true
}