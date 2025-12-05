@echo off
echo ========================================
echo 清理重复的 stock_utils.py 文件
echo ========================================
echo.

echo 保留: backend\utils\stock_utils.py
echo.

echo 删除重复文件:
if exist "backend\dataflows\stock_utils.py" (
    echo   - backend\dataflows\stock_utils.py
    del "backend\dataflows\stock_utils.py"
)

if exist "backend\dataflows\stock\stock_utils.py" (
    echo   - backend\dataflows\stock\stock_utils.py
    del "backend\dataflows\stock\stock_utils.py"
)

echo.
echo 删除备份文件:
del /q "backend\dataflows\stock\*.backup" 2>nul
del /q "backend\dataflows\stock\*.backup_v2" 2>nul
del /q "backend\dataflows\*.backup" 2>nul
del /q "backend\dataflows\*.backup_v2" 2>nul

echo.
echo ✅ 清理完成！
echo.
echo 现在只保留一个 stock_utils.py:
echo   backend\utils\stock_utils.py
echo.
pause
