股票数据开发文档
接口地址： http://web.juhe.cn/finance/stock/hs
返回格式： json
请求方式： http get
请求示例： http://web.juhe.cn/finance/stock/hs
接口备注： 数据仅供参考，不作投资使用，每5分钟更新一次；不支持对外展示，只支持自用学习研究。
请求Header：
名称
Content-Type
值
application/x-www-form-urlencoded
请求参数说明：
名称
gid
类型
string
必填
否
说明
股票编号，上海股市以sh开头，深圳股市以sz开头
如：sh601009（type为0或者1时gid不传）
key
 type
返回参数说明：
名称
String
 int
类型
见JSON返回示例
是
否
说明
APP Key
 0代表上证综合指数，1代表深证成份指数(输入此字段时,gid
字段不起作用)
JSON返回示例：
/*股票编号*/
 /*涨跌百分比*/
 /*涨跌额*/
 /*股票名称*/
 /*今日开盘价*/
 /*昨日收盘价*/
 /*当前价格*/
 /*今日最高价*/
 /*今日最低价*/
 /*竞买价*/
 /*竞卖价*/
 /*成交量*/
 /*成交金额*/
 /*买一*/
 /*买一报价*/
 /*买二*/
 /*买二报价*/
 /*买三*/
 /*买三报价*/
 /*买四*/
 /*买四报价*/
 /*买五*/
 /*买五报价*/
 /*卖一*/
 /*卖一报价*/
 /*卖二*/
 /*卖二报价*/
 /*卖三*/
 /*卖三报价*/
 /*卖四*/
 /*卖四报价*/
 /*卖五*/
 /*卖五报价*/
 /*日期*/
 /*时间*/
 {
 "resultcode":"200", /*返回码，200:正常*/
 "reason":"SUCCESSED!",
 "result":[
 {
    "data":{
                "gid":"sh601009",                                
                "increPer": "9.91",                               
                "increase": "43.99",                             
                "name":"南京银行",                                
                "todayStartPri":"8.26",                                
                "yestodEndPri":"8.26",                                
                "nowPri":"8.37",                                
                "todayMax":"8.55",                                
                "todayMin":"8.25",                                
                "competitivePri":"8.37",                        
                "reservePri":"8.38",                                
                "traNumber":"34501453",                                
                "traAmount":"290889560",                        
                "buyOne":"10870",                                
                "buyOnePri":"8.37",                                
                "buyTwo":"177241",                                
                "buyTwoPri":"8.36",                                
                "buyThree":"92600",                                
                "buyThreePri":"8.35",                                
                "buyFour":"87200"                                
                "buyFourPri":"8.34",                                
                "buyFive":"113700",                                
                "buyFivePri":"8.42",                                
                "sellOne":"47556",                                
                "sellOnePri":"8.38",                                
                "sellTwo":"103057",                                
                "sellTwoPri":"8.39",                                
                "sellThree":"186689",                                
                "sellThreePri":"8.40",                                
                "sellFour":"49000",                                
                "sellFourPri":"8.41",                                
                "sellFive":"214535",                                
                "sellFivePri":"15.21",                                
                "date":"2012-12-11",                                
                "time":"15:03:06",                                
    },
 "dapandata":{
                                "dot":"7.690",/*当前价格*/
                                "name":"南京银行",
                                "nowPic":"-0.070",/*涨量*/
                                "rate":"-0.90",/*涨幅(%)*/
                                "traAmount":"17265",/*成交额(万)*/
                                "traNumber":"223355"/*成交量*/
                        },
    "gopicture":{
        "minurl":"http://image.sinajs.cn/newchart/min/n/sh601009.gif",/*分时K线图*/
        "dayurl":"http://image.sinajs.cn/newchart/daily/n/sh601009.gif",/*日K线图*/
        "weekurl":"http://image.sinajs.cn/newchart/weekly/n/sh601009.gif",/*周K线图*/
        "monthurl":"http://image.sinajs.cn/newchart/monthly/n/sh601009.gif"/*月K线图*/
    }
 }]
 }----------------------------------深（上）证指数示例-----------------------------------------------------------------
{
    "error_code": 0
    "reason": "SUCCESSED!",
    "result": {
        "dealNum": "24388041799",/*成交量(手)*/
        "dealPri": "340674441059.270",/*成交额*/
        "highPri": "10357.417",/*最高*/
        "increPer": "-0.46",/*涨跌百分比*/
         "increase": "-43.756",/*涨跌幅*/
        "lowpri": "10121.741",/*最低*/
        "name": "深证成指",/*名称*/
        "nowpri": "10270.855",/*当前价格*/
        "openPri": "10200.547",/*今开*/
        "time": "2015-09-22 14:45:25",/*时间*/
        "yesPri": "10176.727"/*昨收*/
    },
 }
 2、错误码参照
服务级错误码参照(error_code)：    [顶部]
错误码
202101
 202102
说明
参数错误
查询不到结果
202103
系统级错误码参照：
错误码 说明
10001
 10002
错误的请求KEY
该KEY无请求权限
网络异常
旧版本(resultcode)
 101
 102
 10003
 10004
 10005
 10007
 10008
 10009
 10011
 10012
 10013
 10014
 10020
 KEY过期
错误的OPENID
应用未审核超时，请提交认证
未知的请求源
被禁止的IP
被禁止的KEY
当前IP请求超过限制
请求超过次数限制
测试KEY超过请求限制
系统内部异常(调用充值类业务时，请务必联系客服或通过订单查询接口检测订
单，避免造成损失)
接口维护
103
 104
 105
 107
 108
 109
 111
 112
 113
 114
 120
错误码 说明
旧版本(resultcode)
 10021
接口停用
错误码格式说明（示例：200201）：
2
 121
 002
 01
服务级错误（1为系统级错误）
版本日期：2025-12-04 04:26
服务模块代码(即数据ID)
具体错误代