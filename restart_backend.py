"""重启后端服务器的脚本"""
import subprocess
import sys
import os
import time

# 杀死现有的Python进程
print("Stopping existing Python processes...")
subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
time.sleep(2)

# 启动后端服务器
print("Starting backend server...")
os.chdir("backend")
subprocess.run([sys.executable, "server.py"])
