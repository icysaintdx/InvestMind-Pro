# 真实API实现指南

> 创建时间: 2025-12-04 05:45  
> 参考资料: GitHub项目和JS加密代码

---

## 🎯 目标

实现以下真实API调用：
1. **中国裁判文书网** - 法律案件数据
2. **巨潮资讯网** - 公司公告数据  
3. **财联社** - 财经快讯数据

---

## 1️⃣ 中国裁判文书网

### 参考资料
- GitHub: https://github.com/nixinxin/WenShu
- GitHub: https://github.com/sixs/wenshu_spider
- 加密代码: `docs/中国裁判文书网.cpws.js.md`

### 核心技术点

#### 1. 加密参数生成
```python
import hashlib
import time
import random
import string

def generate_cipher():
    """生成cipher参数（参考JS代码）"""
    timestamp = str(int(time.time() * 1000))
    salt = ''.join(random.choices(string.ascii_letters + string.digits, k=24))
    
    # 获取日期
    now = datetime.now()
    iv = now.strftime('%Y%m%d')
    
    # 3DES加密（需要实现）
    enc = des3_encrypt(timestamp, salt, iv)
    
    # 转二进制
    cipher_str = salt + iv + enc
    cipher_binary = str_to_binary(cipher_str)
    
    return cipher_binary

def str_to_binary(text):
    """字符串转二进制"""
    result = []
    for char in text:
        binary = bin(ord(char))[2:]
        result.append(binary)
    return ' '.join(result)
```

#### 2. 请求参数
```python
def search_cases(company_name):
    """搜索案件"""
    url = "https://wenshu.court.gov.cn/website/wenshu/181107ANFZ0BXSK4/index.html"
    
    headers = {
        'User-Agent': 'Mozilla/5.0...',
        'Referer': 'https://wenshu.court.gov.cn/'
    }
    
    # 生成加密参数
    cipher = generate_cipher()
    guid = str(uuid.uuid4()).replace('-', '')
    
    params = {
        'Param': company_name,
        'Index': 1,
        'Page': 20,
        'Order': '法院层级',
        'Direction': 'asc',
        'vl5x': cipher,
        'guid': guid,
        'cfg': 'com.lawyee.judge.dc.parse.dto.SearchDataDsoDTO@queryDoc'
    }
    
    response = requests.post(url, data=params, headers=headers)
    return response.json()
```

#### 3. 3DES加密实现
```python
from Crypto.Cipher import DES3
from Crypto.Util.Padding import pad
import base64

def des3_encrypt(plaintext, key, iv):
    """3DES加密"""
    # 确保key长度为24字节
    key = key.ljust(24, '0')[:24].encode('utf-8')
    iv = iv.encode('utf-8')
    
    cipher = DES3.new(key, DES3.MODE_CBC, iv)
    padded_text = pad(plaintext.encode('utf-8'), DES3.block_size)
    encrypted = cipher.encrypt(padded_text)
    
    return base64.b64encode(encrypted).decode('utf-8')
```

---

## 2️⃣ 巨潮资讯网

### API地址
```
http://www.cninfo.com.cn/new/hisAnnouncement/query
```

### 请求参数
```python
def get_announcements(stock_code, days=30):
    """获取公告"""
    url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
    
    # 清理股票代码
    clean_code = stock_code.replace('.SH', '').replace('.SZ', '')
    
    # 判断市场
    if stock_code.startswith('6'):
        plate = 'sh'  # 上交所
    else:
        plate = 'sz'  # 深交所
    
    # 日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    headers = {
        'User-Agent': 'Mozilla/5.0...',
        'Referer': 'http://www.cninfo.com.cn/',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    data = {
        'stock': clean_code,
        'searchkey': '',
        'plate': plate,
        'category': '',  # 公告类型
        'trade': '',
        'column': plate,
        'columnTitle': '历史公告查询',
        'pageNum': 1,
        'pageSize': 30,
        'tabName': 'fulltext',
        'sortName': '',
        'sortType': '',
        'limit': '',
        'showTitle': '',
        'seDate': f"{start_date.strftime('%Y-%m-%d')}~{end_date.strftime('%Y-%m-%d')}"
    }
    
    response = requests.post(url, data=data, headers=headers)
    return response.json()
```

### 响应解析
```python
def parse_announcements(response_data):
    """解析公告数据"""
    announcements = []
    
    if 'announcements' in response_data:
        for item in response_data['announcements']:
            announcement = {
                'announcement_id': item.get('announcementId'),
                'stock_code': item.get('secCode'),
                'stock_name': item.get('secName'),
                'title': item.get('announcementTitle'),
                'type': item.get('announcementType'),
                'publish_date': item.get('announcementTime'),
                'url': f"http://www.cninfo.com.cn/{item.get('adjunctUrl')}",
                'summary': item.get('announcementContent', '')[:200]
            }
            announcements.append(announcement)
    
    return announcements
```

---

## 3️⃣ 财联社

### 参考资料
- 加密代码: `docs/财联社.js.md`

### MD5加密实现
```python
import hashlib

def generate_md5_token(timestamp):
    """生成MD5 token（参考JS代码）"""
    # 参考财联社.js.md中的加密逻辑
    secret = "your_secret_key"  # 需要从JS中提取
    raw_string = f"{timestamp}{secret}"
    
    md5_hash = hashlib.md5(raw_string.encode('utf-8')).hexdigest()
    return md5_hash
```

### API调用
```python
def get_cls_news():
    """获取财联社快讯"""
    url = "https://www.cls.cn/api/sw"
    
    timestamp = str(int(time.time() * 1000))
    token = generate_md5_token(timestamp)
    
    headers = {
        'User-Agent': 'Mozilla/5.0...',
        'Referer': 'https://www.cls.cn/',
        'token': token,
        'timestamp': timestamp
    }
    
    params = {
        'app': 'CailianpressWeb',
        'os': 'web',
        'sv': '7.7.5',
        'sign': token
    }
    
    response = requests.get(url, params=params, headers=headers)
    return response.json()
```

---

## 🔧 实现步骤

### 阶段1: 基础实现（本周）

#### 1. 安装依赖
```bash
pip install pycryptodome  # 用于3DES加密
pip install curl_cffi      # 用于模拟浏览器
```

#### 2. 实现加密函数
- 3DES加密（中国裁判文书网）
- MD5加密（财联社）

#### 3. 实现API调用
- 中国裁判文书网搜索
- 巨潮资讯网公告查询
- 财联社快讯获取

### 阶段2: 反爬虫处理（下周）

#### 1. 使用curl_cffi
```python
from curl_cffi import requests as curl_requests

session = curl_requests.Session(impersonate="chrome120")
response = session.get(url, headers=headers)
```

#### 2. 代理IP池
```python
proxies = {
    'http': 'http://proxy1:port',
    'https': 'https://proxy1:port'
}

response = requests.get(url, proxies=proxies)
```

#### 3. 请求频率控制
```python
import time

def rate_limited_request(url, min_interval=1):
    """限制请求频率"""
    time.sleep(min_interval)
    return requests.get(url)
```

### 阶段3: 集成到统一API（下下周）

#### 1. 更新unified_news_api.py
```python
# 添加法律风险数据源
from backend.dataflows.legal.wenshu_crawler import get_wenshu_crawler

# 添加公司公告数据源
from backend.dataflows.announcement.cninfo_crawler import get_cninfo_crawler
```

#### 2. 创建API端点
```python
@router.get("/api/legal-risk/{stock_code}")
async def get_legal_risk(stock_code: str):
    """获取法律风险"""
    crawler = get_wenshu_crawler()
    # 获取公司名称
    company_name = get_company_name(stock_code)
    cases = crawler.search_company_cases(company_name)
    risk = crawler.analyze_legal_risk(cases)
    return risk
```

---

## 📋 注意事项

### 1. 法律合规
- 遵守robots.txt
- 不要频繁请求
- 仅用于个人学习研究

### 2. 数据准确性
- 验证返回数据
- 处理异常情况
- 记录错误日志

### 3. 性能优化
- 使用缓存
- 异步请求
- 连接池复用

---

## 🧪 测试

### 测试脚本
```python
# test_real_api.py
def test_wenshu():
    """测试裁判文书网"""
    crawler = get_wenshu_crawler()
    cases = crawler.search_company_cases("贵州茅台酒股份有限公司")
    assert len(cases) > 0
    
def test_cninfo():
    """测试巨潮资讯网"""
    crawler = get_cninfo_crawler()
    announcements = crawler.get_company_announcements("600519")
    assert len(announcements) > 0
```

---

## 📚 参考资源

### GitHub项目
1. https://github.com/nixinxin/WenShu
2. https://github.com/sixs/wenshu_spider

### 加密代码
1. `docs/中国裁判文书网.cpws.js.md` - 3DES加密
2. `docs/财联社.js.md` - MD5加密

### API文档
1. 巨潮资讯网: http://www.cninfo.com.cn
2. 财联社: https://www.cls.cn

---

**下一步**: 开始实现3DES加密和真实API调用！
