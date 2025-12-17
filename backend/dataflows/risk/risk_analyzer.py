"""
综合风险分析模块
整合停复牌风险、ST风险、舆情风险等多维度风险评估
"""

from typing import Dict, Optional
from datetime import datetime

from backend.utils.logging_config import get_logger
from .suspend_monitor import get_suspend_monitor
from .st_monitor import get_st_monitor
from .realtime_monitor import get_realtime_monitor

logger = get_logger("dataflows.risk_analysis")


class RiskAnalyzer:
    """综合风险分析器"""
    
    def __init__(self):
        self.suspend_monitor = get_suspend_monitor()
        self.st_monitor = get_st_monitor()
        self.realtime_monitor = get_realtime_monitor()
    
    def analyze_stock_risk(
        self, 
        ts_code: str,
        include_realtime: bool = True,
        sentiment_score: Optional[float] = None
    ) -> Dict:
        """
        综合分析股票风险
        
        Args:
            ts_code: 股票代码，如600519.SH
            include_realtime: 是否包含实时数据分析
            sentiment_score: 舆情情绪得分（0-100，50为中性）
            
        Returns:
            {
                'ts_code': str,
                'risk_level': str,  # 'high'/'medium'/'low'
                'risk_score': int,  # 0-100，分数越高风险越大
                'risk_factors': {
                    'suspend_risk': {...},
                    'st_risk': {...},
                    'sentiment_risk': {...},
                    'realtime_risk': {...}
                },
                'warnings': [],
                'timestamp': str
            }
        """
        logger.info(f"🔍 开始分析{ts_code}的风险...")
        
        risk_factors = {}
        warnings = []
        total_score = 0
        
        # 1. 停复牌风险分析
        try:
            suspend_status = self.suspend_monitor.check_stock_suspend_status(ts_code)
            suspend_level = self.suspend_monitor.get_suspend_risk_level(suspend_status)
            
            suspend_score = self._get_risk_score(suspend_level)
            if suspend_status.get('is_suspended'):
                suspend_score += 30  # 当前停牌额外加分
                warnings.append(f"⚠️ 股票当前处于停牌状态")
            
            risk_factors['suspend_risk'] = {
                'level': suspend_level,
                'score': suspend_score,
                'is_suspended': suspend_status.get('is_suspended', False),
                'suspend_count': suspend_status.get('suspend_count', 0),
                'latest_status': suspend_status.get('latest_status', 'unknown')
            }
            
            total_score += suspend_score
            
            if suspend_status.get('suspend_count', 0) > 0:
                warnings.append(f"近期停牌{suspend_status['suspend_count']}次")
                
        except Exception as e:
            logger.error(f"停复牌风险分析失败: {e}")
            risk_factors['suspend_risk'] = {'level': 'unknown', 'score': 0, 'error': str(e)}
        
        # 2. ST风险分析
        try:
            st_status = self.st_monitor.check_if_st(ts_code)
            st_level = self.st_monitor.get_st_risk_level(st_status)
            st_score = self._get_risk_score(st_level)
            
            if st_status.get('is_st'):
                st_type = st_status.get('st_type', 'ST')
                if st_type.startswith('*ST'):
                    st_score += 40  # *ST额外高风险
                    warnings.append(f"🚨 *ST股票，连续亏损风险")
                else:
                    st_score += 25
                    warnings.append(f"⚠️ ST股票，存在风险警示")
            
            risk_factors['st_risk'] = {
                'level': st_level,
                'score': st_score,
                'is_st': st_status.get('is_st', False),
                'st_type': st_status.get('st_type'),
                'st_type_name': st_status.get('st_type_name')
            }
            
            total_score += st_score
            
        except Exception as e:
            logger.error(f"ST风险分析失败: {e}")
            risk_factors['st_risk'] = {'level': 'unknown', 'score': 0, 'error': str(e)}
        
        # 3. 舆情风险分析
        if sentiment_score is not None:
            sentiment_risk = self._analyze_sentiment_risk(sentiment_score)
            risk_factors['sentiment_risk'] = sentiment_risk
            total_score += sentiment_risk['score']
            
            if sentiment_risk['level'] in ['high', 'medium']:
                warnings.append(f"舆情{sentiment_risk['description']}")
        else:
            risk_factors['sentiment_risk'] = {'level': 'unknown', 'score': 0}
        
        # 4. 实时交易风险分析（可选）
        if include_realtime:
            try:
                realtime_data = self.realtime_monitor.get_realtime_quote(ts_code)
                if realtime_data is not None and isinstance(realtime_data, dict):
                    realtime_analysis = self._analyze_realtime_risk(realtime_data)
                    risk_factors['realtime_risk'] = realtime_analysis
                    total_score += realtime_analysis['score']
                    
                    if realtime_analysis.get('warnings'):
                        warnings.extend(realtime_analysis['warnings'])
                else:
                    risk_factors['realtime_risk'] = {'level': 'unknown', 'score': 0}
            except Exception as e:
                logger.error(f"实时风险分析失败: {e}")
                risk_factors['realtime_risk'] = {'level': 'unknown', 'score': 0, 'error': str(e)}
        
        # 计算综合风险等级
        overall_risk_level = self._calculate_overall_risk(total_score)
        
        result = {
            'ts_code': ts_code,
            'risk_level': overall_risk_level,
            'risk_score': min(total_score, 100),  # 最高100分
            'risk_factors': risk_factors,
            'warnings': warnings,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ {ts_code} 风险分析完成: {overall_risk_level} (得分:{result['risk_score']})")
        
        return result
    
    def _get_risk_score(self, risk_level: str) -> int:
        """将风险等级转换为分数"""
        score_map = {
            'high': 30,
            'medium': 15,
            'low': 5,
            'unknown': 0
        }
        return score_map.get(risk_level, 0)
    
    def _analyze_sentiment_risk(self, sentiment_score: float) -> Dict:
        """
        分析舆情风险
        
        Args:
            sentiment_score: 情绪得分 0-100，50为中性
        """
        if sentiment_score >= 70:
            level = 'low'
            score = 0
            desc = '偏正面'
        elif sentiment_score >= 50:
            level = 'low'
            score = 5
            desc = '中性偏正'
        elif sentiment_score >= 30:
            level = 'medium'
            score = 15
            desc = '偏负面'
        else:
            level = 'high'
            score = 30
            desc = '严重负面'
        
        return {
            'level': level,
            'score': score,
            'sentiment_score': sentiment_score,
            'description': desc
        }
    
    def _analyze_realtime_risk(self, realtime_data: Dict) -> Dict:
        """
        分析实时交易风险
        
        基于：
        - 涨跌幅异常
        - 买卖盘失衡
        - 成交量异常
        """
        warnings = []
        score = 0
        
        change_pct = realtime_data.get('change_pct', 0)
        buy_sell_pressure = realtime_data.get('buy_sell_pressure', 1.0)
        
        # 涨跌幅风险
        if abs(change_pct) > 9:
            score += 15
            warnings.append(f"涨跌幅异常: {change_pct:+.2f}%")
        elif abs(change_pct) > 5:
            score += 8
        
        # 买卖盘失衡风险
        if buy_sell_pressure < 0.5:
            score += 10
            warnings.append(f"卖盘压力大，买卖比: {buy_sell_pressure:.2f}")
        elif buy_sell_pressure > 2.0:
            score += 5
            warnings.append(f"买盘压力大，买卖比: {buy_sell_pressure:.2f}")
        
        # 确定风险等级
        if score >= 20:
            level = 'high'
        elif score >= 10:
            level = 'medium'
        else:
            level = 'low'
        
        return {
            'level': level,
            'score': score,
            'change_pct': change_pct,
            'buy_sell_pressure': buy_sell_pressure,
            'warnings': warnings
        }
    
    def _calculate_overall_risk(self, total_score: int) -> str:
        """计算综合风险等级"""
        if total_score >= 60:
            return 'high'
        elif total_score >= 30:
            return 'medium'
        else:
            return 'low'
    
    def batch_analyze_risk(self, ts_codes: list) -> Dict[str, Dict]:
        """
        批量分析股票风险
        
        Args:
            ts_codes: 股票代码列表
            
        Returns:
            {ts_code: risk_analysis_result}
        """
        results = {}
        
        for ts_code in ts_codes:
            try:
                result = self.analyze_stock_risk(
                    ts_code, 
                    include_realtime=False  # 批量分析不包含实时数据
                )
                results[ts_code] = result
            except Exception as e:
                logger.error(f"分析{ts_code}失败: {e}")
                results[ts_code] = {
                    'ts_code': ts_code,
                    'risk_level': 'unknown',
                    'risk_score': 0,
                    'error': str(e)
                }
        
        logger.info(f"✅ 批量风险分析完成: {len(results)}/{len(ts_codes)}只股票")
        
        return results


# 全局分析器实例
_risk_analyzer = None


def get_risk_analyzer() -> RiskAnalyzer:
    """获取全局风险分析器实例"""
    global _risk_analyzer
    if _risk_analyzer is None:
        _risk_analyzer = RiskAnalyzer()
    return _risk_analyzer


# ==================== 便捷函数 ====================

def analyze_stock_risk(ts_code: str, sentiment_score: Optional[float] = None) -> Dict:
    """分析股票风险"""
    analyzer = get_risk_analyzer()
    return analyzer.analyze_stock_risk(ts_code, sentiment_score=sentiment_score)


def get_risk_level(ts_code: str) -> str:
    """获取股票风险等级"""
    analyzer = get_risk_analyzer()
    result = analyzer.analyze_stock_risk(ts_code, include_realtime=False)
    return result.get('risk_level', 'unknown')
