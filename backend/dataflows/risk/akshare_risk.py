#!/usr/bin/env python3
"""
AKShare风险数据封装
提供失信被执行人、被执行人、裁判文书等风险数据查询
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from backend.utils.logging_config import get_logger

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False

logger = get_logger("akshare_risk")


class AKShareRiskData:
    """AKShare风险数据封装"""
    
    def __init__(self):
        """初始化"""
        if not HAS_AKSHARE:
            logger.error("❌ AKShare未安装，请运行: pip install akshare")
            raise ImportError("AKShare未安装")
        
        logger.info("✅ AKShare风险数据模块初始化完成")
    
    def get_dishonest_persons(self, company_name: str) -> List[Dict[str, Any]]:
        """
        获取失信被执行人信息（老赖名单）
        
        注意：AKShare当前版本可能没有此接口，需要直接爬取执行信息公开网
        
        Args:
            company_name: 公司名称
            
        Returns:
            失信被执行人列表
        """
        try:
            logger.info(f"查询{company_name}的失信被执行人信息...")
            logger.warning("⚠️ AKShare当前版本没有失信被执行人接口，返回空数据")
            logger.info("💡 建议：使用中国执行信息公开网爬虫")
            return []
            
        except Exception as e:
            logger.error(f"❌ 查询失信被执行人失败: {e}")
            return []
    
    def get_executed_persons(self, company_name: str) -> List[Dict[str, Any]]:
        """
        获取被执行人信息
        
        注意：AKShare当前版本可能没有此接口
        
        Args:
            company_name: 公司名称
            
        Returns:
            被执行人列表
        """
        try:
            logger.info(f"查询{company_name}的被执行人信息...")
            logger.warning("⚠️ AKShare当前版本没有被执行人接口，返回空数据")
            logger.info("💡 建议：使用中国执行信息公开网爬虫")
            return []
            
        except Exception as e:
            logger.error(f"❌ 查询被执行人失败: {e}")
            return []
    
    def get_lawsuits(self, stock_code: str) -> List[Dict[str, Any]]:
        """
        获取裁判文书信息
        
        注意：AKShare当前版本没有裁判文书接口
        
        Args:
            stock_code: 股票代码（如：600519）
            
        Returns:
            裁判文书列表
        """
        try:
            clean_code = stock_code.replace('.SH', '').replace('.SZ', '')
            logger.info(f"查询{clean_code}的裁判文书信息...")
            logger.warning("⚠️ AKShare当前版本没有裁判文书接口，返回空数据")
            logger.info("💡 建议：使用中国裁判文书网爬虫")
            return []
            
        except Exception as e:
            logger.error(f"❌ 查询裁判文书失败: {e}")
            return []
    
    def analyze_risk(
        self, 
        company_name: str, 
        stock_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        综合风险分析
        
        Args:
            company_name: 公司名称
            stock_code: 股票代码（可选）
            
        Returns:
            风险分析结果
        """
        try:
            logger.info(f"开始综合风险分析: {company_name}")
            
            # 获取各类风险数据
            dishonest = self.get_dishonest_persons(company_name)
            executed = self.get_executed_persons(company_name)
            lawsuits = []
            if stock_code:
                lawsuits = self.get_lawsuits(stock_code)
            
            # 计算风险评分
            risk_score = self._calculate_risk_score(
                dishonest_count=len(dishonest),
                executed_count=len(executed),
                lawsuit_count=len(lawsuits)
            )
            
            # 确定风险等级
            risk_level = self._get_risk_level(risk_score)
            
            # 生成风险摘要
            summary = self._generate_risk_summary(
                company_name=company_name,
                dishonest_count=len(dishonest),
                executed_count=len(executed),
                lawsuit_count=len(lawsuits),
                risk_level=risk_level
            )
            
            result = {
                'company_name': company_name,
                'stock_code': stock_code,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'details': {
                    'dishonest_count': len(dishonest),
                    'executed_count': len(executed),
                    'lawsuit_count': len(lawsuits),
                    'dishonest_records': dishonest[:5],  # 最多返回5条
                    'executed_records': executed[:5],
                    'lawsuit_records': lawsuits[:5]
                },
                'summary': summary,
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"✅ 风险分析完成: {risk_level}风险，评分{risk_score}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 综合风险分析失败: {e}")
            return {
                'company_name': company_name,
                'stock_code': stock_code,
                'risk_score': 0,
                'risk_level': 'unknown',
                'details': {},
                'summary': f'风险分析失败: {str(e)}',
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _calculate_risk_score(
        self, 
        dishonest_count: int,
        executed_count: int,
        lawsuit_count: int
    ) -> int:
        """
        计算风险评分（0-100）
        
        Args:
            dishonest_count: 失信被执行人数量
            executed_count: 被执行人数量
            lawsuit_count: 裁判文书数量
            
        Returns:
            风险评分
        """
        # 权重配置
        dishonest_weight = 30  # 失信被执行人权重最高
        executed_weight = 20   # 被执行人权重次之
        lawsuit_weight = 15    # 裁判文书权重较低
        
        # 计算评分
        score = (
            min(dishonest_count * dishonest_weight, 30) +
            min(executed_count * executed_weight, 20) +
            min(lawsuit_count * lawsuit_weight / 10, 15)  # 裁判文书通常较多，除以10
        )
        
        return min(int(score), 100)
    
    def _get_risk_level(self, risk_score: int) -> str:
        """
        根据评分确定风险等级
        
        Args:
            risk_score: 风险评分
            
        Returns:
            风险等级: low/medium/high/critical
        """
        if risk_score >= 60:
            return 'critical'  # 极高风险
        elif risk_score >= 40:
            return 'high'      # 高风险
        elif risk_score >= 20:
            return 'medium'    # 中等风险
        else:
            return 'low'       # 低风险
    
    def _generate_risk_summary(
        self,
        company_name: str,
        dishonest_count: int,
        executed_count: int,
        lawsuit_count: int,
        risk_level: str
    ) -> str:
        """
        生成风险摘要
        
        Args:
            company_name: 公司名称
            dishonest_count: 失信被执行人数量
            executed_count: 被执行人数量
            lawsuit_count: 裁判文书数量
            risk_level: 风险等级
            
        Returns:
            风险摘要文本
        """
        risk_level_text = {
            'low': '低风险',
            'medium': '中等风险',
            'high': '高风险',
            'critical': '极高风险'
        }.get(risk_level, '未知风险')
        
        summary_parts = [f"{company_name}风险等级：{risk_level_text}"]
        
        if dishonest_count > 0:
            summary_parts.append(f"存在{dishonest_count}条失信被执行人记录")
        
        if executed_count > 0:
            summary_parts.append(f"存在{executed_count}条被执行人记录")
        
        if lawsuit_count > 0:
            summary_parts.append(f"存在{lawsuit_count}条裁判文书记录")
        
        if dishonest_count == 0 and executed_count == 0 and lawsuit_count == 0:
            summary_parts.append("未发现重大风险事项")
        
        return "，".join(summary_parts)


# 全局实例
_akshare_risk = None

def get_akshare_risk():
    """获取AKShare风险数据实例（单例）"""
    global _akshare_risk
    if _akshare_risk is None:
        _akshare_risk = AKShareRiskData()
    return _akshare_risk
