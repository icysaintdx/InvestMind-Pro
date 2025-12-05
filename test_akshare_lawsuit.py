#!/usr/bin/env python3
"""
测试AKShare裁判文书接口
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.utils.logging_config import get_logger

logger = get_logger("test_lawsuit")

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False
    logger.error("❌ AKShare未安装")


def test_lawsuit_interface():
    """测试裁判文书接口"""
    logger.info("=" * 60)
    logger.info("测试AKShare裁判文书接口: stock_cg_lawsuit_cninfo")
    logger.info("=" * 60)
    
    if not HAS_AKSHARE:
        logger.error("❌ 请先安装AKShare: pip install akshare")
        return False
    
    test_stocks = [
        ("600519", "贵州茅台"),
        ("000001", "平安银行"),
        ("300104", "乐视网"),  # 可能有诉讼
    ]
    
    for symbol, name in test_stocks:
        logger.info(f"\n{'='*50}")
        logger.info(f"测试股票: {name} ({symbol})")
        logger.info(f"{'='*50}")
        
        try:
            # 测试接口
            df = ak.stock_cg_lawsuit_cninfo(symbol=symbol)
            
            if df is None or df.empty:
                logger.warning(f"⚠️ {name}无裁判文书数据")
            else:
                logger.info(f"✅ 获取到{len(df)}条裁判文书数据")
                
                # 显示列名
                logger.info(f"\n数据列: {list(df.columns)}")
                
                # 显示前3条
                logger.info(f"\n前3条数据:")
                for i, row in df.head(3).iterrows():
                    logger.info(f"\n记录 {i+1}:")
                    for col in df.columns:
                        logger.info(f"  {col}: {row[col]}")
                
                return True
                
        except AttributeError as e:
            logger.error(f"❌ 接口不存在: {e}")
            logger.info("💡 AKShare可能没有此接口或接口名称已变更")
            return False
            
        except Exception as e:
            logger.error(f"❌ 调用失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    return False


def test_risk_interfaces():
    """测试期权风险接口"""
    logger.info("\n" + "=" * 60)
    logger.info("测试期权风险接口")
    logger.info("=" * 60)
    
    if not HAS_AKSHARE:
        return False
    
    # 测试1: option_risk_analysis_em
    logger.info("\n测试1: option_risk_analysis_em")
    try:
        df = ak.option_risk_analysis_em()
        if df is not None and not df.empty:
            logger.info(f"✅ 获取到{len(df)}条期权风险分析数据")
            logger.info(f"数据列: {list(df.columns)}")
        else:
            logger.warning("⚠️ 无数据")
    except Exception as e:
        logger.error(f"❌ 调用失败: {e}")
    
    # 测试2: option_risk_indicator_sse
    logger.info("\n测试2: option_risk_indicator_sse")
    try:
        df = ak.option_risk_indicator_sse()
        if df is not None and not df.empty:
            logger.info(f"✅ 获取到{len(df)}条上交所期权风险指标")
            logger.info(f"数据列: {list(df.columns)}")
        else:
            logger.warning("⚠️ 无数据")
    except Exception as e:
        logger.error(f"❌ 调用失败: {e}")


def main():
    """主函数"""
    logger.info("🚀 开始测试AKShare风险相关接口")
    logger.info("=" * 60)
    
    try:
        # 测试裁判文书接口
        lawsuit_available = test_lawsuit_interface()
        
        # 测试期权风险接口
        test_risk_interfaces()
        
        # 总结
        logger.info("\n" + "=" * 60)
        logger.info("测试总结")
        logger.info("=" * 60)
        
        if lawsuit_available:
            logger.info("✅ 裁判文书接口可用，建议优先使用")
        else:
            logger.warning("⚠️ 裁判文书接口不可用，需要开发爬虫")
            logger.info("💡 建议方案:")
            logger.info("  1. 中国执行信息公开网爬虫（参考docs/爬虫执行网.md）")
            logger.info("  2. 国家企业信用信息公示系统爬虫（参考docs/爬虫企业信用.md）")
            logger.info("  3. 中国裁判文书网爬虫（参考docs/中国裁判文书网.cpws.js.md）")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
