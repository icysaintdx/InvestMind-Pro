#!/usr/bin/env python3
"""移动agents目录到backend下"""

import shutil
from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).parent.parent

# 源目录和目标目录
src = project_root / "agents"
dst = project_root / "backend" / "agents"

print(f"Moving {src} to {dst}")

if src.exists():
    if dst.exists():
        print(f"Destination {dst} already exists, removing it first...")
        shutil.rmtree(dst)
    
    print("Moving directory...")
    shutil.move(str(src), str(dst))
    print("✅ Successfully moved agents to backend/agents")
else:
    print("❌ Source directory does not exist")
    
# 检查结果
if dst.exists():
    items = len(list(dst.iterdir()))
    print(f"✅ backend/agents now contains {items} items")
else:
    print("❌ Move failed")
