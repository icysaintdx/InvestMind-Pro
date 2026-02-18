# TDX服务问题分析与解决方案

**文档日期**: 2026-01-12 13:54  
**责任人**: AI Assistant  
**版本**: v1.0

---

## 一、背景/问题描述

系统日志频繁出现以下错误：
```
2026-01-12 15:42:51 - api.kline - ERROR - TDX获取K线失败: TDX服务不可用
2026-01-12 15:42:51 - api.kline - WARNING - ⚠️ 数据源 tdx 失败: TDX服务不可用，尝试下一个
```

用户反馈：
1. TDX经常显示"服务不可用"
2. 之前说TDX获取不到上海交易所的股票列表，需要通过AKShare获取传递给它

---

## 二、TDX系统架构分析

### 2.1 项目中存在的TDX相关组件

| 文件 | 类型 | 说明 |
|------|------|------|
| `tdx_provider.py` | HTTP Provider | 通过HTTP API调用外部TDX服务（需要Docker/Go服务） |
| `tdx_native_provider.py` | Native Provider | 使用pytdx库直接连接通达信服务器（纯Python） |
| `tdx_provider_full.py` | HTTP Provider | tdx_provider的完整版本 |
| `tdx_cache_service.py` | 缓存服务 | 后台定时缓存TDX数据 |

### 2.2 两种TDX Provider的区别

#### TDX HTTP Provider (`tdx_provider.py`)
- **工作原理**: 通过HTTP请求调用外部TDX API服务
- **依赖**: 需要运行独立的TDX API服务（Go语言实现，通常通过Docker部署）
- **API地址**: 默认 `http://127.0.0.1:8080`
- **可用性检测**: 调用 `/api/health` 端点

```python
def is_available(self) -> bool:
    try:
        response = requests.get(f"{self.base_url}/api/health", timeout=1)
        return response.status_code == 200
    except:
        return False
```

#### TDX Native Provider (`tdx_native_provider.py`)
- **工作原理**: 使用 `pytdx` 库直接连接通达信行情服务器
- **依赖**: 仅需安装 `pytdx` Python包
- **服务器**: 连接公共通达信服务器（如 218.75.126.9:7709）
- **可用性检测**: 尝试连接服务器并获取数据

```python
def is_available(self) -> bool:
    try:
        from pytdx.hq import TdxHq_API
        result = self._ensure_connection()
        return result
    except:
        return False
```

### 2.3 数据源优先级

系统采用多数据源降级策略，优先级如下：
```
TDX Native → TDX HTTP → Tushare → AKShare → Sina → Juhe
```

---

## 三、问题根因分析

### 3.1 "TDX服务不可用"的直接原因

错误来源于 `kline_api.py` 第428-429行：
```python
if not provider.is_available():
    raise ValueError("TDX服务不可用")
```

这表示 **TDX HTTP Provider** 的健康检查失败。

### 3.2 根本原因分析

#### 原因1: TDX HTTP服务未启动
- TDX HTTP Provider 依赖外部Go服务（端口8080）
- 如果该服务未启动，`/api/health` 请求会失败
- **这是最常见的原因**

#### 原因2: TDX Native Provider连接失败
- pytdx连接通达信公共服务器
- 服务器可能因网络问题、服务器负载等原因连接失败
- 连接超时设置为8秒

#### 原因3: 上海交易所股票列表问题（历史问题）

**这个问题已经被修复**。查看 `tdx_native_provider.py` 的 `get_all_stock_codes()` 方法：

```python
def get_all_stock_codes(self) -> List[Dict]:
    all_stocks = []
    
    # 深圳市场
    for start in range(0, 10000, 1000):
        stocks = self.get_stock_list(0, start)  # market=0 深圳
        ...
    
    # 上海市场
    for start in range(0, 10000, 1000):
        stocks = self.get_stock_list(1, start)  # market=1 上海
        ...
    
    return all_stocks
```

代码已正确实现双市场（上海+深圳）股票列表获取。

### 3.3 为什么之前说需要AKShare传递股票列表？

查看 `tdx_cache_service.py` 的 `_update_stock_list()` 方法：

```python
def _update_stock_list(self):
    # 使用AKShare获取A股列表
    try:
        df = ak.stock_info_a_code_name()
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                code = str(row.get('code', ''))
                name = row.get('name', '')
                if code.startswith(('00', '30', '60', '68')):
                    ...
    except Exception as e:
        logger.error(f"[TDX缓存] AKShare获取股票列表失败: {e}")
    
    # 如果AKShare失败，尝试TDX（只能获取深圳）  <-- 这个注释是错误的！
    if not all_stocks or len(all_stocks) < 100:
        provider = self._get_tdx_provider()
        if provider and provider.is_available():
            tdx_stocks = provider.get_all_stock_codes()
            ...
```

**关键发现**：
1. 缓存服务优先使用AKShare获取股票列表（因为更稳定）
2. 代码注释说"TDX只能获取深圳"是**错误的**
3. `tdx_native_provider.py` 的 `get_all_stock_codes()` 已正确实现双市场获取

---

## 四、解决方案

### 4.1 方案一：确保TDX Native Provider正常工作（推荐）

TDX Native Provider 是纯Python实现，无需外部服务，应该优先使用。

**检查步骤**：
1. 确认 `pytdx` 已安装：`pip install pytdx`
2. 测试连接：

```python
from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider

provider = get_tdx_native_provider()
print(f"可用性: {provider.is_available()}")
print(f"连接状态: {provider.get_connection_status()}")

# 测试获取行情
quote = provider.get_realtime_quote("000001")
print(f"平安银行行情: {quote}")
```

### 4.2 方案二：启动TDX HTTP服务

如果需要使用TDX HTTP Provider，需要启动外部服务：

```bash
# 使用Docker启动TDX API服务
docker run -d -p 8080:8080 tdx-api:latest

# 或者直接运行Go程序
./tdx-api -port 8080
```

### 4.3 方案三：调整数据源优先级

当前 `kline_api.py` 的数据源优先级：
```python
data_sources = [
    ("tdx", lambda: get_kline_from_tdx(symbol, period, limit)),
    ("tushare", lambda: get_kline_from_tushare(symbol, period, limit)),
    ("akshare", lambda: get_kline_from_akshare(symbol, period, adjust)),
    ("sina", lambda: get_kline_from_sina(symbol, period)),
]
```

如果TDX经常不可用，可以考虑：
1. 将AKShare提升到第一优先级
2. 或者增加TDX可用性缓存时间，减少频繁检测

### 4.4 方案四：优化TDX Native Provider连接稳定性

当前配置：
```python
CONNECT_TIMEOUT = 8  # 连接超时
IDLE_TIMEOUT = 120   # 空闲超时
AVAILABILITY_CACHE_SUCCESS = 180  # 成功缓存3分钟
AVAILABILITY_CACHE_FAIL = 5  # 失败缓存5秒
```

建议优化：
1. 增加服务器列表，提高连接成功率
2. 实现服务器健康度排序，优先使用响应快的服务器
3. 增加连接池，避免频繁建立连接

---

## 五、代码示例

### 5.1 测试TDX可用性

```python
# 测试脚本：test_tdx.py
import sys
sys.path.insert(0, 'D:/InvestMindPro')

from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
from backend.dataflows.providers.tdx_provider import get_tdx_provider

def test_tdx():
    print("=" * 50)
    print("测试 TDX Native Provider")
    print("=" * 50)
    
    native = get_tdx_native_provider()
    print(f"Native可用: {native.is_available()}")
    print(f"连接状态: {native.get_connection_status()}")
    
    if native.is_available():
        # 测试获取行情
        quote = native.get_realtime_quote("000001")
        print(f"平安银行: {quote}")
        
        # 测试获取K线
        kline = native.get_kline("000001", 9, 5)
        print(f"K线数据: {len(kline)}条")
        
        # 测试获取股票列表
        stocks = native.get_all_stock_codes()
        sh_count = len([s for s in stocks if s['code'].startswith(('60', '68'))])
        sz_count = len([s for s in stocks if s['code'].startswith(('00', '30'))])
        print(f"股票列表: 上海{sh_count}只, 深圳{sz_count}只")
    
    print("\n" + "=" * 50)
    print("测试 TDX HTTP Provider")
    print("=" * 50)
    
    http = get_tdx_provider()
    print(f"HTTP可用: {http.is_available()}")

if __name__ == "__main__":
    test_tdx()
```

### 5.2 重置TDX连接

```python
from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider

provider = get_tdx_native_provider()
provider.reset_connection()  # 强制重新连接
print(f"重连后可用性: {provider.is_available()}")
```

---

## 六、相关文件

| 文件路径 | 说明 |
|----------|------|
| `backend/dataflows/providers/tdx_native_provider.py` | TDX Native Provider实现 |
| `backend/dataflows/providers/tdx_provider.py` | TDX HTTP Provider实现 |
| `backend/dataflows/providers/tdx_provider_full.py` | TDX HTTP Provider完整版 |
| `backend/services/tdx_cache_service.py` | TDX数据缓存服务 |
| `backend/api/kline_api.py` | K线API（调用TDX） |
| `docs/Tdx接口文档.md` | TDX HTTP API文档 |
| `docs/tdx缓存脚本的问题.md` | 历史问题记录 |

---

## 七、版本信息

- **项目版本**: InvestMind Pro v2.5.0
- **文档版本**: v1.0
- **最后更新**: 2026-01-12

---

## 八、总结

### 问题本质
"TDX服务不可用"错误主要是因为 **TDX HTTP服务未启动**，而不是TDX Native Provider的问题。

### 关于上海交易所股票列表
- 这是一个**已解决的历史问题**
- `tdx_native_provider.py` 已正确实现双市场（上海+深圳）股票获取
- 缓存服务中的注释"TDX只能获取深圳"是**错误的**，应该更新

### 推荐方案
1. **优先使用 TDX Native Provider**（纯Python，无需外部服务）
2. 确保 `pytdx` 库已正确安装
3. 如果Native Provider也不可用，系统会自动降级到AKShare等其他数据源
4. 考虑更新缓存服务中的错误注释

### 后续优化建议
1. 增加TDX服务器健康度监控
2. 实现智能服务器选择（基于延迟和成功率）
3. 优化连接池管理，减少连接建立开销
4. 考虑增加本地数据缓存，减少对实时连接的依赖
