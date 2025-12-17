#!/usr/bin/env python3
"""
项目目录重组工具
将agents移动到backend下，删除无用的api目录
"""

import os
import shutil
import sys
from pathlib import Path

def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    
    print("=" * 60)
    print("InvestMindPro 项目目录重组工具")
    print("=" * 60)
    print()
    
    # 1. 移动agents到backend
    agents_src = project_root / "agents"
    agents_dst = project_root / "backend" / "agents"
    
    if agents_src.exists() and not agents_dst.exists():
        print(f"📦 移动 agents/ -> backend/agents/")
        shutil.move(str(agents_src), str(agents_dst))
        print("  ✅ agents目录已移动到backend下")
    elif agents_dst.exists():
        print("  ⚠️ backend/agents已存在，跳过移动")
    else:
        print("  ❌ agents目录不存在")
        
    # 2. 删除旧的api目录
    old_api = project_root / "api"
    if old_api.exists():
        print(f"\n🗑️ 删除旧的api目录")
        try:
            shutil.rmtree(old_api)
            print("  ✅ 旧api目录已删除")
        except Exception as e:
            print(f"  ❌ 删除失败: {e}")
    else:
        print("\n  ℹ️ 旧api目录不存在")
        
    # 3. 更新导入路径
    print("\n🔧 更新导入路径...")
    
    # 需要更新的路径映射
    replacements = [
        # agents移动到backend下的路径更新
        (r'from agents\.', 'from backend.agents.'),
        (r'import agents\.', 'import backend.agents.'),
        
        # 确保backend路径正确
        (r'from backend\.backend\.', 'from backend.'),
        (r'import backend\.backend\.', 'import backend.'),
    ]
    
    # 需要扫描的目录
    dirs_to_scan = [
        project_root / "backend",
        project_root / "scripts"
    ]
    
    fixed_count = 0
    for scan_dir in dirs_to_scan:
        if not scan_dir.exists():
            continue
            
        for py_file in scan_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                original_content = content
                
                # 应用替换规则
                import re
                for pattern, replacement in replacements:
                    content = re.sub(pattern, replacement, content)
                    
                # 如果有改动，写回文件
                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixed_count += 1
                    print(f"  ✅ 更新: {py_file.relative_to(project_root)}")
                    
            except Exception as e:
                print(f"  ❌ 处理失败 {py_file}: {e}")
                
    print(f"\n  📊 共更新 {fixed_count} 个文件的导入路径")
    
    # 4. 创建新的__init__.py
    backend_agents = project_root / "backend" / "agents"
    if backend_agents.exists():
        init_file = backend_agents / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""智能体模块"""\n')
            print("\n  ✅ 创建 backend/agents/__init__.py")
            
    # 5. 更新.gitignore
    gitignore_path = project_root / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
            
        # 移除旧的api目录忽略（如果有）
        if "/api/" in gitignore_content:
            gitignore_content = gitignore_content.replace("/api/", "")
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(gitignore_content)
            print("\n  ✅ 更新.gitignore")
            
    print("\n" + "=" * 60)
    print("✨ 目录重组完成！")
    print("\n新的目录结构：")
    print("  backend/")
    print("    ├── agents/       # 智能体模块")
    print("    ├── api/          # API接口")
    print("    ├── dataflows/    # 数据流")
    print("    ├── utils/        # 工具类")
    print("    └── server.py     # 主服务器")
    print("\n建议：")
    print("  1. 运行 'python scripts/fix_imports.py' 再次检查导入")
    print("  2. 测试后端服务是否正常: 'python backend/server.py'")
    print("  3. 提交更改到Git")
    
if __name__ == "__main__":
    main()
