@echo off
python test_one_request.py > test_output.txt 2>&1
type test_output.txt
pause
