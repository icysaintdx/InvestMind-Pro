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

所有API都支持以下通用参数：

| 参数 | 说明 |
|-----|------|
| format | 结果格式：xml/json/csv/dbf |
| @column | 选择返回字段，逗号分隔 |
| @limit | 限制返回条数 |
| @orderby | 排序：字段:asc/desc |

---

## 公共数据

### 1. 交易日历数据
**API:** p_public0001 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_public0001

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| sdate | 开始日期 YYYY-MM-DD | TRADEDATE | 交易日期 |
| edate | 结束日期 YYYY-MM-DD | MARKET | 市场代码 |
| market | SZ深圳/SH上海 | ISOPEN | 是否交易(1/0) |

### 2. 行业分类数据
**API:** p_public0002 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_public0002

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| indcode | 行业代码 | INDCODE | 行业代码 |
| indtype | 137002中上协/137004申万/137005新财富 | INDNAME | 行业名称 |
| | | PARENTCODE | 父类编码 |
| | | LEVEL | 层级 |

### 3. 地区分类数据
**API:** p_public0003 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_public0003

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| areaid | 地区编码(0为省级) | SORTCODE | 地区编码 |
| | | SORTNAME | 地区名称 |
| | | PARENTCODE | 父类编码 |

### 4. 证券类别编码数据
**API:** p_public0004 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_public0004

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| typecode | 类别代码 | TYPECODE | 类别代码 |
| | | TYPENAME | 类别名称 |

### 5. 公共编码数据
**API:** p_public0005 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_public0005

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| codetype | 编码类型 | CODETYPE | 编码类型 |
| | | CODE | 编码 |
| | | CODENAME | 编码名称 |

### 6. 人民币汇率中间价
**API:** p_public0006 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_public0006

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| sdate | 开始日期 | TRADEDATE | 交易日期 |
| edate | 结束日期 | CURRENCY | 货币代码 |
| currency | 货币代码 | RATE | 汇率中间价 |

### 7. 机构信息数据
**API:** p_public0007 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_public0007

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| orgcode | 机构代码 | ORGCODE | 机构代码 |
| orgtype | 机构类型 | ORGNAME | 机构名称 |

---

## 股票数据

### 8. 股票背景资料
**API:** p_stock0001 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock0001

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| scode | 股票代码(≤300只) | SECCODE | 证券代码 |
| market | SZ/SH | SECNAME | 证券简称 |
| | | ORGNAME | 公司名称 |
| | | LISTDATE | 上市日期 |

### 9. 板块成份股数据
**API:** p_stock0002 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock0002

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| platecode | 板块代码(必填) | PLATECODE | 板块代码 |
| | | PLATENAME | 板块名称 |
| | | SECCODE | 证券代码 |
| | | SECNAME | 证券简称 |

### 10. 股票所属板块
**API:** p_stock0004 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock0004

| 输入参数 | 说明 |
|---------|------|
| scode | 股票代码(必填,≤300只) |
| typecode | 137001市场/137002中上协/137004申万/137005新财富/137006地区/137007指数成份/137008概念 |

### 11. 公司基本信息
**API:** p_stock0005 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock0005

| 输出参数 | 说明 |
|---------|------|
| SECCODE/SECNAME | 证券代码/简称 |
| ORGNAME | 公司名称 |
| REGCAPITAL | 注册资本(万元) |
| REGADDRESS | 注册地址 |
| TEL/FAX/EMAIL | 电话/传真/邮箱 |
| WEBSITE | 公司网址 |
| LEGALREP/CHAIRMAN/SECRETARY | 法人/董事长/董秘 |
| MAINBUSINESS | 主营业务 |
| INTRODUCTION | 公司简介 |

### 12. 股票基本信息
**API:** p_stock0006 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock0006

| 输出参数 | 说明 |
|---------|------|
| SECCODE/SECNAME | 证券代码/简称 |
| MARKET/SECTYPE | 市场代码/证券类型 |
| LISTDATE/DELISTDATE | 上市/退市日期 |
| IPODATE/IPOPRICE/IPOSHARES | 发行日期/价格/数量 |
| TOTALSHARES/FLOATSHARES | 总股本/流通股本 |
| PARVALUE | 面值(元) |

### 13-18. 其他股票数据API
- **p_stock0007** - 公司管理人员任职情况
- **p_stock0008** - 机构基本信息变更情况
- **p_stock0009** - 证券简称变更情况
- **p_stock0010** - 上市公司行业归属变动情况
- **p_stock0011** - 公司上市状态变动情况表
- **p_stock0012** - 公司主要行业收入数据

---

## 财务数据

### 19. 定期报告预披露时间
**API:** p_stock2001 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock2001

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| scode | 股票代码 | RDATE | 报告期 |
| rdate | 报告期 | PREDATE | 预披露日期 |
| | | ACTUALDATE | 实际披露日期 |

### 20. 上市公司业绩预告
**API:** p_stock2002 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock2002

| 输出参数 | 说明 |
|---------|------|
| NOTICEDATE | 公告日期 |
| FORECASTTYPE | 预告类型(预增/预减/扭亏/首亏/续盈/续亏/略增/略减) |
| FORECASTCONTENT | 预告内容 |
| NETPROFITMIN/MAX | 净利润下限/上限(元) |
| CHANGEPCTMIN/MAX | 变动幅度下限/上限(%) |

### 21. 定期报告审计意见
**API:** p_stock2003 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock2003

### 22. 个股报告期资产负债表
**API:** p_stock2101 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock2101

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

### 23. 个股报告期利润表
**API:** p_stock2102 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock2102

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

### 24. 个股报告期现金流量表
**API:** p_stock2103 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock2103

| 输出参数 | 说明 |
|---------|------|
| NETCASHOPERATING | 经营活动产生的现金流量净额(元) |
| NETCASHINVESTING | 投资活动产生的现金流量净额(元) |
| NETCASHFINANCING | 筹资活动产生的现金流量净额(元) |
| NETCASHINCREASE | 现金及现金等价物净增加额(元) |
| CASHENDING | 期末现金及现金等价物余额(元) |

### 25. 个股报告期指标表
**API:** p_stock2104 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock2104

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

### 26-28. 金融类财务报表2007版
- **p_stock2201** - 金融类资产负债表
- **p_stock2202** - 金融类利润表
- **p_stock2203** - 金融类现金流量表

适用于银行、证券、保险等金融类上市公司。

### 29. 业绩快报
**API:** p_stock2004 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock2004

### 30. 个股指标快速版
**API:** p_stock2387 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock2387

---

## 交易数据

### 31. 个股日行情数据
**API:** p_stock1001 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock1001

| 输入参数 | 说明 |
|---------|------|
| scode | 股票代码(必填,≤50只) |
| sdate/edate | 开始/结束日期 |

| 输出参数 | 说明 |
|---------|------|
| TRADEDATE | 交易日期 |
| OPEN/HIGH/LOW/CLOSE | 开盘/最高/最低/收盘价(元) |
| PRECLOSE | 前收盘价(元) |
| CHANGE | 涨跌额(元) |
| CHANGEPCT | 涨跌幅(%) |
| VOLUME | 成交量(股) |
| AMOUNT | 成交额(元) |
| TURNOVERRATE | 换手率(%) |
| TOTALMV/FLOATMV | 总市值/流通市值(元) |

### 32-33. 周/月行情数据
- **p_stock1002** - 个股周行情数据
- **p_stock1003** - 个股月行情数据

### 34. 停复牌信息
**API:** p_stock1004 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock1004

| 输出参数 | 说明 |
|---------|------|
| SUSPENDDATE | 停牌日期 |
| RESUMEDATE | 复牌日期 |
| SUSPENDREASON | 停牌原因 |
| SUSPENDTYPE | 停牌类型 |

### 35. 涨跌停统计
**API:** p_stock1005 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock1005

| 输出参数 | 说明 |
|---------|------|
| TRADEDATE | 交易日期 |
| LIMITTYPE | 涨跌停类型 |
| LIMITDAYS | 连续涨跌停天数 |

### 36. 大宗交易数据
**API:** p_stock1006 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock1006

| 输出参数 | 说明 |
|---------|------|
| TRADEDATE | 交易日期 |
| PRICE | 成交价(元) |
| VOLUME | 成交量(股) |
| AMOUNT | 成交额(元) |
| BUYER | 买方营业部 |
| SELLER | 卖方营业部 |
| PREMIUM | 溢价率(%) |

### 37. 融资融券数据
**API:** p_stock1007 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock1007

| 输出参数 | 说明 |
|---------|------|
| TRADEDATE | 交易日期 |
| RZYE | 融资余额(元) |
| RZMRE | 融资买入额(元) |
| RZCHE | 融资偿还额(元) |
| RQYL | 融券余量(股) |
| RQMCL | 融券卖出量(股) |
| RZRQYE | 融资融券余额(元) |

---

## 股东数据

### 38. 十大股东数据
**API:** p_stock3001 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock3001

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| scode | 股票代码(必填) | RDATE | 报告期 |
| rdate | 报告期 | SHNAME | 股东名称 |
| | | SHTYPE | 股东类型 |
| | | HOLDNUM | 持股数量(股) |
| | | HOLDPCT | 持股比例(%) |
| | | HOLDCHANGE | 持股变动(股) |
| | | SHARETYPE | 股份类型 |

### 39. 十大流通股东数据
**API:** p_stock3002 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock3002

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| scode | 股票代码(必填) | RDATE | 报告期 |
| rdate | 报告期 | SHNAME | 股东名称 |
| | | SHTYPE | 股东类型 |
| | | HOLDNUM | 持股数量(股) |
| | | HOLDPCT | 持股比例(%) |
| | | HOLDCHANGE | 持股变动(股) |

### 40. 股东户数数据
**API:** p_stock3003 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock3003

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| scode | 股票代码(必填) | RDATE | 报告期 |
| rdate | 报告期 | SHNUM | 股东户数 |
| | | SHNUMCHANGE | 股东户数变动 |
| | | SHNUMCHANGEPCT | 股东户数变动比例(%) |
| | | AVGHOLD | 户均持股数(股) |

### 41. 实际控制人数据
**API:** p_stock3004 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock3004

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| scode | 股票代码(必填) | RDATE | 报告期 |
| rdate | 报告期 | CONTROLLERNAME | 实际控制人名称 |
| | | CONTROLLERTYPE | 实际控制人类型 |
| | | CONTROLPCT | 控制比例(%) |
| | | CONTROLPATH | 控制路径 |

### 42. 股本结构数据
**API:** p_stock3005 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock3005

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| scode | 股票代码(必填) | CHANGEDATE | 变动日期 |
| sdate/edate | 开始/结束日期 | CHANGEREASON | 变动原因 |
| | | TOTALSHARES | 总股本(股) |
| | | FLOATASHARES | 流通A股(股) |
| | | LIMITEDSHARES | 限售股(股) |

### 43. 限售股解禁数据
**API:** p_stock3006 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock3006

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| scode | 股票代码 | UNLOCKDATE | 解禁日期 |
| sdate/edate | 开始/结束日期 | UNLOCKSHARES | 解禁数量(股) |
| | | UNLOCKPCT | 解禁比例(%) |
| | | UNLOCKTYPE | 解禁类型 |
| | | SHNAME | 股东名称 |

---

## 分红配股数据

### 44. 分红送转数据
**API:** p_stock4001 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock4001

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| scode | 股票代码 | RDATE | 报告期 |
| rdate | 报告期 | NOTICEDATE | 公告日期 |
| | | EXDIVDATE | 除权除息日 |
| | | REGDATE | 股权登记日 |
| | | CASHDIV | 每股现金分红(元) |
| | | STOCKDIV | 每股送股(股) |
| | | STOCKTRANS | 每股转增(股) |
| | | DIVTOTAL | 分红总额(元) |

### 45. 配股数据
**API:** p_stock4002 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock4002

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| scode | 股票代码 | NOTICEDATE | 公告日期 |
| sdate/edate | 开始/结束日期 | ALLOTPRICE | 配股价格(元) |
| | | ALLOTRATIO | 配股比例 |
| | | ALLOTSHARES | 配股数量(股) |
| | | ALLOTAMOUNT | 配股金额(元) |
| | | REGDATE | 股权登记日 |
| | | EXRIGHTDATE | 除权日 |
| | | PAYDATE | 缴款日期 |

### 46. 增发数据
**API:** p_stock4003 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock4003

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| scode | 股票代码 | NOTICEDATE | 公告日期 |
| sdate/edate | 开始/结束日期 | ISSUEPRICE | 发行价格(元) |
| | | ISSUESHARES | 发行数量(股) |
| | | ISSUEAMOUNT | 募集资金(元) |
| | | ISSUETYPE | 发行类型 |
| | | LISTDATE | 上市日期 |

### 47. 股票回购数据
**API:** p_stock4004 | **URL:** http://webapi.cninfo.com.cn/api/stock/p_stock4004

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| scode | 股票代码 | NOTICEDATE | 公告日期 |
| sdate/edate | 开始/结束日期 | BUYBACKSHARES | 回购数量(股) |
| | | BUYBACKAMOUNT | 回购金额(元) |
| | | BUYBACKPRICE | 回购价格(元) |
| | | BUYBACKPURPOSE | 回购目的 |

---

## 指数数据

### 48. 指数基本信息
**API:** p_index0001 | **URL:** http://webapi.cninfo.com.cn/api/index/p_index0001

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| indexcode | 指数代码 | INDEXCODE | 指数代码 |
| market | SZ/SH | INDEXNAME | 指数名称 |
| | | MARKET | 市场代码 |
| | | BASEDATE | 基期日期 |
| | | BASEPOINT | 基点 |
| | | PUBLISHDATE | 发布日期 |

### 49. 指数日行情数据
**API:** p_index0002 | **URL:** http://webapi.cninfo.com.cn/api/index/p_index0002

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| indexcode | 指数代码(必填) | TRADEDATE | 交易日期 |
| sdate/edate | 开始/结束日期 | OPEN/HIGH/LOW/CLOSE | 开高低收 |
| | | PRECLOSE | 前收盘 |
| | | CHANGE | 涨跌额 |
| | | CHANGEPCT | 涨跌幅(%) |
| | | VOLUME | 成交量(股) |
| | | AMOUNT | 成交额(元) |

### 50. 指数成份股数据
**API:** p_index0003 | **URL:** http://webapi.cninfo.com.cn/api/index/p_index0003

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| indexcode | 指数代码(必填) | INDEXCODE | 指数代码 |
| | | INDEXNAME | 指数名称 |
| | | SECCODE | 成份股代码 |
| | | SECNAME | 成份股简称 |
| | | WEIGHT | 权重(%) |

---

## 基金数据

### 51. 基金基本信息
**API:** p_fund0001 | **URL:** http://webapi.cninfo.com.cn/api/fund/p_fund0001

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| fundcode | 基金代码 | FUNDCODE | 基金代码 |
| market | SZ/SH | FUNDNAME | 基金名称 |
| | | FUNDTYPE | 基金类型 |
| | | SETUPDATE | 成立日期 |
| | | LISTDATE | 上市日期 |
| | | MANAGER | 基金管理人 |
| | | CUSTODIAN | 基金托管人 |

### 52. 基金日行情数据
**API:** p_fund0002 | **URL:** http://webapi.cninfo.com.cn/api/fund/p_fund0002

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| fundcode | 基金代码(必填) | TRADEDATE | 交易日期 |
| sdate/edate | 开始/结束日期 | OPEN/HIGH/LOW/CLOSE | 开高低收(元) |
| | | PRECLOSE | 前收盘价(元) |
| | | CHANGE | 涨跌额(元) |
| | | CHANGEPCT | 涨跌幅(%) |
| | | VOLUME | 成交量(份) |
| | | AMOUNT | 成交额(元) |

### 53. 基金净值数据
**API:** p_fund0003 | **URL:** http://webapi.cninfo.com.cn/api/fund/p_fund0003

| 输入参数 | 说明 | 输出参数 | 说明 |
|---------|------|---------|------|
| fundcode | 基金代码(必填) |