#!/usr/bin/env python3
"""
中国裁判文书网爬虫
获取上市公司相关的法律诉讼信息
"""

import requests
import uuid
import time
import random
import string
import base64
from typing import List, Dict, Any
from datetime import datetime, timedelta
from backend.utils.logging_config import get_logger

try:
    from Crypto.Cipher import DES3
    from Crypto.Util.Padding import pad
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    logger.warning("⚠️ pycryptodome未安装，将使用模拟数据")

logger = get_logger("wenshu_crawler")


class WenshuCrawler:
    """中国裁判文书网爬虫"""
    
    def __init__(self):
        """初始化"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 中国裁判文书网API（注意：实际API可能需要认证）
        self.base_url = "https://wenshu.court.gov.cn"
        
        logger.info("中国裁判文书网爬虫初始化完成")
    
    def search_company_cases(self, company_name: str, days: int = 365) -> List[Dict[str, Any]]:
        """
        搜索公司相关案件
        
        Args:
            company_name: 公司名称
            days: 回溯天数
            
        Returns:
            案件列表
        """
        try:
            logger.info(f"搜索{company_name}的法律案件...")
            
            # 注意：这是示例代码，实际API需要根据官方文档调整
            # 中国裁判文书网需要复杂的认证和反爬虫处理
            
            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 构建搜索参数
            params = {
                'keyword': company_name,
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d')
            }
            
            # 这里返回模拟数据，实际需要实现真实的API调用
            cases = self._mock_cases(company_name)
            
            logger.info(f"✅ 找到{len(cases)}个相关案件")
            return cases
            
        except Exception as e:
            logger.error(f"❌ 搜索案件失败: {e}")
            return []
    
    def _generate_cipher(self) -> str:
        """
        生成cipher加密参数
        参考JS代码中的cipher()函数
        
        Returns:
            加密后的cipher字符串
        """
        if not HAS_CRYPTO:
            logger.warning("⚠️ 加密库未安装，返回模拟值")
            return "mock_cipher_value"
        
        try:
            # 1. 生成时间戳
            timestamp = str(int(time.time() * 1000))
            
            # 2. 生成随机盐（24位）
            salt = ''.join(random.choices(string.ascii_letters + string.digits, k=24))
            
            # 3. 生成IV（当前日期）
            now = datetime.now()
            iv = now.strftime('%Y%m%d')
            
            # 4. 3DES加密
            enc = self._des3_encrypt(timestamp, salt, iv)
            
            # 5. 组合字符串
            cipher_str = salt + iv + enc
            
            # 6. 转二进制
            cipher_binary = self._str_to_binary(cipher_str)
            
            return cipher_binary
            
        except Exception as e:
            logger.error(f"❌ 生成cipher失败: {e}")
            return "mock_cipher_value"
    
    def _des3_encrypt(self, plaintext: str, key: str, iv: str) -> str:
        """
        3DES加密
        
        Args:
            plaintext: 明文
            key: 密钥（24位）
            iv: 初始化向量
            
        Returns:
            Base64编码的密文
        """
        try:
            # 确保key长度为24字节
            key_bytes = key.ljust(24, '0')[:24].encode('utf-8')
            iv_bytes = iv.encode('utf-8')
            
            # 创建DES3加密器
            cipher = DES3.new(key_bytes, DES3.MODE_CBC, iv_bytes)
            
            # 填充并加密
            padded_text = pad(plaintext.encode('utf-8'), DES3.block_size)
            encrypted = cipher.encrypt(padded_text)
            
            # Base64编码
            return base64.b64encode(encrypted).decode('utf-8')
            
        except Exception as e:
            logger.error(f"❌ 3DES加密失败: {e}")
            raise
    
    def _str_to_binary(self, text: str) -> str:
        """
        字符串转二进制
        
        Args:
            text: 输入字符串
            
        Returns:
            二进制字符串（空格分隔）
        """
        result = []
        for char in text:
            binary = bin(ord(char))[2:]
            result.append(binary)
        return ' '.join(result)
    
    def _generate_guid(self) -> str:
        """
        生成GUID
        
        Returns:
            32位GUID字符串
        """
        return str(uuid.uuid4()).replace('-', '')
    
    def _mock_cases(self, company_name: str) -> List[Dict[str, Any]]:
        """
        模拟案件数据（用于测试）
        实际使用时需要替换为真实的API调用
        """
        return [
            {
                'case_id': 'MOCK001',
                'case_name': f'{company_name}与XX公司合同纠纷',
                'case_type': '民事案件',
                'court': '北京市第一中级人民法院',
                'case_date': '2024-11-15',
                'parties': [company_name, 'XX公司'],
                'case_reason': '合同纠纷',
                'trial_procedure': '二审',
                'document_type': '判决书',
                'risk_level': 'medium',
                'summary': f'{company_name}因合同履行问题被诉...'
            }
        ]
    
    def analyze_legal_risk(self, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析法律风险
        
        Args:
            cases: 案件列表
            
        Returns:
            风险分析结果
        """
        if not cases:
            return {
                'total_cases': 0,
                'risk_level': 'low',
                'risk_score': 0,
                'summary': '未发现重大法律风险'
            }
        
        # 统计案件类型
        case_types = {}
        for case in cases:
            case_type = case.get('case_type', '未知')
            case_types[case_type] = case_types.get(case_type, 0) + 1
        
        # 计算风险评分
        risk_score = min(len(cases) * 10, 100)
        
        # 确定风险等级
        if risk_score >= 70:
            risk_level = 'high'
        elif risk_score >= 40:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'total_cases': len(cases),
            'case_types': case_types,
            'risk_level': risk_level,
            'risk_score': risk_score,
            'recent_cases': cases[:5],  # 最近5个案件
            'summary': f'共发现{len(cases)}个相关案件，风险等级：{risk_level}'
        }


# 全局实例
_wenshu_crawler = None

def get_wenshu_crawler():
    """获取裁判文书网爬虫实例（单例）"""
    global _wenshu_crawler
    if _wenshu_crawler is None:
        _wenshu_crawler = WenshuCrawler()
    return _wenshu_crawler
