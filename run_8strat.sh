#!/bin/bash
# 8策略回测 - 稳定版

cd ~/.openclaw/workspace-investmindpro/InvestMindPro || exit 1
source venv_linux/bin/activate

# 清理
pkill -9 -f batch_backtest 2>/dev/null
sleep 1

# 运行（前台，带输出）
python3 -u backend/scripts/batch_backtest_all.py 2>&1 | tee RUN_8STRAT_$(date +%H%M).log

echo "完成！查看 FULL_BACKTEST_REPORT.md"
