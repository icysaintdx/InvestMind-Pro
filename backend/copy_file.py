import shutil
import os

src = os.path.join(os.path.dirname(__file__), 'static', 'index-beautiful.html')
dst = os.path.join(os.path.dirname(__file__), 'static', 'index.html')

# 删除旧文件
if os.path.exists(dst):
    os.remove(dst)
    print(f"已删除: {dst}")

# 复制新文件
shutil.copy2(src, dst)
print(f"已复制: {src} -> {dst}")

# 验证
with open(dst, 'r', encoding='utf-8') as f:
    content = f.read()
    if 'tailwindcss' in content:
        print("✅ 文件复制成功！包含 Tailwind CSS")
    else:
        print("❌ 文件复制失败！")
