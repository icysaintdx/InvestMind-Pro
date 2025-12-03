#!/usr/bin/env python3
"""检查目录结构"""

from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).parent.parent

# 检查关键目录
dirs_to_check = [
    project_root / "agents",
    project_root / "backend" / "agents",
    project_root / "api",
    project_root / "backend" / "api"
]

print("Checking directory structure:")
print("=" * 60)

for dir_path in dirs_to_check:
    if dir_path.exists():
        items = list(dir_path.iterdir())
        print(f"✅ {dir_path.relative_to(project_root)}")
        print(f"   Contains {len(items)} items")
        # 显示前5个文件/目录
        for item in items[:5]:
            if item.is_dir():
                print(f"   📁 {item.name}/")
            else:
                print(f"   📄 {item.name}")
        if len(items) > 5:
            print(f"   ... and {len(items) - 5} more")
    else:
        print(f"❌ {dir_path.relative_to(project_root)} - NOT FOUND")
    print()

print("=" * 60)
