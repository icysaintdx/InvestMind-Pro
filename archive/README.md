# 回测结果归档目录

本目录用于归档InvestMindPro项目的历史回测结果文件，保持`results/`根目录整洁。

## 目录结构

```
archive/
├── 2026-backtests/     # 2026年的历史回测报告和数据
├── optimization/       # 参数优化历史记录
├── abandoned/          # 废弃/测试/空文件
└── README.md          # 本文件
```

## 归档规则

### 1. 2026-backtests/
存放2026年的历史批量回测结果：
- 2天前的批量回测报告（.md）
- 对应的数据文件（.json）
- 执行报告和日志

**当前归档文件（2026-02-27）：**
- BATCH_BACKTEST_REPORT_20260227.md
- EMA_V2_EXECUTION_REPORT_20260227.md
- EMA_V2_FULL_BACKTEST_20260227.md
- HS300_BACKTEST_REPORT_20260227.md
- INDIVIDUAL_BACKTEST_REPORT_20260227.md
- NEGATIVE_STOCK_ANALYSIS_20260227.md
- ema_v2_backtest_*_20260227_*.json
- pingan_improvement_20260227.json

### 2. optimization/
存放参数优化过程中的历史数据：
- 遗传算法优化详情
- 参数优化完整结果
- 个股优化报告和结果

**当前归档文件：**
- genetic_optimization_detail.json
- param_optimization_full_*.json
- PARAM_OPTIMIZATION_REPORT_*.md
- ema_v2_*_optimized_*_20260227.*
- extended_optimization_*.json

### 3. abandoned/
存放废弃、测试或损坏的文件：
- 空文件（0-100字节）
- 测试日志
- 失败的优化尝试

**当前归档文件：**
- param_optimization_full_20260227_131825.json (2字节空文件)
- PARAM_OPTIMIZATION_REPORT_20260227_131825.md (空报告)
- ema_v2_2_test_20260227_*.log (测试日志)
- ema_v2_2_full_backtest_20260227_230053.log

## 保留在 results/ 根目录的文件

以下类型的文件保留在 `results/` 根目录：
1. **最新报告**：最近2天内生成的回测报告
2. **汇总文件**：SUMMARY.md, BATCH_BACKTEST_REPORT.md 等
3. **活跃优化**：ema_v2_optimization_progress.json 等正在使用的文件
4. **最新结果**：2026-02-28及之后的结果文件
5. **重要报告**：AI_SENTIMENT_V2_BACKTEST.md, ENSEMBLE_STRATEGY*.md 等

## 归档流程

1. 定期检查 `results/` 目录中的文件
2. 识别2天前的批量回测结果
3. 使用 `git mv` 移动文件到相应归档目录
4. 更新本 README.md
5. 提交Git变更

## 文件命名约定

归档文件保持原名，通过目录结构分类：
- 文件名中的日期戳（YYYYMMDD）用于识别文件年龄
- 文件类型（.md报告/.json数据/.log日志）决定处理方式

---
*最后更新：2026-03-01*
*归档执行：自动归档任务*
