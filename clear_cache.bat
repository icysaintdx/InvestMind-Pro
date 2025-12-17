@echo off
echo ========================================
echo 清除 Python 缓存
echo ========================================
echo.

echo 正在删除 __pycache__ 目录...
for /d /r "d:\InvestMindPro\backend" %%d in (__pycache__) do (
    if exist "%%d" (
        echo 删除: %%d
        rd /s /q "%%d"
    )
)

echo.
echo 正在删除 .pyc 文件...
del /s /q "d:\InvestMindPro\backend\*.pyc" 2>nul

echo.
echo ✅ 缓存清除完成！
echo.
echo 现在可以重新运行测试:
echo python backend\test_data_sources_fixed.py
echo.
pause
