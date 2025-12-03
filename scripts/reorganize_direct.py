#!/usr/bin/env python3
"""
直接执行项目重组
使用Python内置函数而非命令行
"""

import os
import shutil
from pathlib import Path

def main():
    # 获取项目根目录
    project_root = Path("d:/AlphaCouncil")
    
    print("=" * 60)
    print("AlphaCouncil 项目重组")
    print("=" * 60)
    
    # 1. 检查agents目录是否存在
    agents_src = project_root / "agents"
    agents_dst = project_root / "backend" / "agents"
    
    if agents_src.exists():
        print(f"\n✅ 找到agents目录: {agents_src}")
        print(f"   包含 {len(list(agents_src.iterdir()))} 个项目")
        
        # 2. 如果目标目录已存在，先删除
        if agents_dst.exists():
            print(f"\n⚠️ 目标目录已存在，删除: {agents_dst}")
            shutil.rmtree(agents_dst)
            
        # 3. 复制agents到backend下
        print(f"\n📦 复制 agents/ -> backend/agents/")
        shutil.copytree(agents_src, agents_dst)
        
        # 验证复制结果
        if agents_dst.exists():
            dst_items = list(agents_dst.iterdir())
            print(f"   ✅ 成功复制 {len(dst_items)} 个项目到backend/agents")
            
            # 显示部分内容
            print("\n   包含的模块:")
            for item in dst_items[:10]:
                if item.is_dir():
                    print(f"     📁 {item.name}/")
                else:
                    print(f"     📄 {item.name}")
            if len(dst_items) > 10:
                print(f"     ... 还有 {len(dst_items) - 10} 个项目")
                
            # 4. 删除原agents目录
            print(f"\n🗑️ 删除原agents目录")
            shutil.rmtree(agents_src)
            print("   ✅ 原agents目录已删除")
        else:
            print("   ❌ 复制失败")
            return
    else:
        print(f"\n❌ agents目录不存在: {agents_src}")
        
    # 5. 删除旧的api目录
    old_api = project_root / "api"
    if old_api.exists():
        print(f"\n🗑️ 删除旧的api目录: {old_api}")
        shutil.rmtree(old_api)
        print("   ✅ 旧api目录已删除")
    else:
        print(f"\n   ℹ️ 旧api目录不存在")
        
    # 6. 更新所有Python文件的导入路径
    print("\n🔧 更新导入路径...")
    
    # 需要更新的路径映射
    replacements = [
        ('from backend.agents.', 'from backend.agents.'),
        ('import backend.agents.', 'import backend.agents.'),
        ('from backend.', 'from backend.'),
        ('import backend.', 'import backend.'),
    ]
    
    # 扫描并更新文件
    updated_files = []
    for py_file in project_root.rglob("*.py"):
        # 跳过TradingAgents-CN-main目录
        if "TradingAgents-CN-main" in str(py_file):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original = content
            
            # 应用替换
            for old, new in replacements:
                content = content.replace(old, new)
                
            # 如果有更改，写回文件
            if content != original:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                updated_files.append(py_file.relative_to(project_root))
                
        except Exception as e:
            print(f"   ❌ 处理失败: {py_file.name} - {e}")
            
    if updated_files:
        print(f"\n   ✅ 更新了 {len(updated_files)} 个文件的导入路径:")
        for f in updated_files[:5]:
            print(f"      • {f}")
        if len(updated_files) > 5:
            print(f"      ... 还有 {len(updated_files) - 5} 个文件")
    else:
        print("   ℹ️ 没有需要更新的导入路径")
        
    # 7. 显示最终结构
    print("\n" + "=" * 60)
    print("✨ 重组完成！最终目录结构：")
    print()
    
    # 检查关键目录
    dirs = [
        project_root / "backend",
        project_root / "backend" / "agents",
        project_root / "backend" / "api",
        project_root / "backend" / "dataflows",
        project_root / "backend" / "utils",
    ]
    
    for d in dirs:
        if d.exists():
            items = len(list(d.iterdir()))
            level = str(d.relative_to(project_root)).count(os.sep)
            indent = "  " * level
            name = d.name
            print(f"{indent}📁 {name}/ ({items} items)")
        else:
            print(f"   ❌ {d.relative_to(project_root)} 不存在")
            
    print("\n建议后续操作:")
    print("  1. 运行 'python scripts/fix_imports.py' 再次检查导入")
    print("  2. 测试服务器: 'python backend/server.py'")
    print("  3. 提交到Git: 'git add -A && git commit -m \"重组项目结构\"'")
    
if __name__ == "__main__":
    main()
