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



