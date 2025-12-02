#!/usr/bin/env python3
"""
InvestMind Pro 开发环境一键启动脚本
自动启动Vue前端和FastAPI后端
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path
import platform

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
VUE_DIR = PROJECT_ROOT / "alpha-council-vue"
BACKEND_DIR = PROJECT_ROOT / "backend"

# 进程列表（用于清理）
processes = []

def cleanup(signum=None, frame=None):
    """清理所有启动的进程"""
    print("\n🛑 正在停止所有服务...")
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
    print("✅ 所有服务已停止")
    sys.exit(0)

# 注册信号处理
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def check_node():
    """检查Node.js是否安装"""
    try:
        result = subprocess.run(['node', '-v'], capture_output=True, text=True)
        print(f"✅ Node.js 版本: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ 未检测到Node.js，请先安装: https://nodejs.org")
        return False

def check_npm():
    """检查npm是否安装"""
    try:
        # Windows系统可能需要使用npm.cmd
        npm_cmd = 'npm.cmd' if platform.system() == 'Windows' else 'npm'
        result = subprocess.run([npm_cmd, '-v'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"✅ npm 版本: {result.stdout.strip()}")
            return True
        else:
            # 尝试直接使用npm
            result = subprocess.run(['npm', '-v'], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                print(f"✅ npm 版本: {result.stdout.strip()}")
                return True
            print("❌ npm命令执行失败")
            return False
    except Exception as e:
        print(f"❌ 检测npm时出错: {e}")
        # 尝试直接执行看是否存在
        try:
            subprocess.run(['npm', '--version'], capture_output=True, check=True, shell=True)
            print("✅ npm 已安装（通过备用方法检测）")
            return True
        except:
            print("❌ 未检测到npm")
            return False

def create_vue_project():
    """创建Vue项目"""
    print("\n🔧 首次运行，创建Vue项目...")
    print("=" * 60)
    
    # 检查是否已安装Vue CLI
    npm_cmd = 'npm.cmd' if platform.system() == 'Windows' else 'npm'
    vue_cmd = 'vue.cmd' if platform.system() == 'Windows' else 'vue'
    
    try:
        subprocess.run([vue_cmd, '--version'], capture_output=True, check=True, shell=True)
    except:
        print("📦 安装Vue CLI...")
        subprocess.run([npm_cmd, 'install', '-g', '@vue/cli'], check=True, shell=True)
    
    # 创建项目（使用预设配置）
    print("🚀 创建alpha-council-vue项目...")
    
    # 创建项目配置文件
    preset_file = PROJECT_ROOT / "vue-preset.json"
    preset_content = """{
  "useConfigFiles": true,
  "plugins": {
    "@vue/cli-plugin-router": {
      "historyMode": true
    },
    "@vue/cli-plugin-vuex": {}
  },
  "vueVersion": "3",
  "cssPreprocessor": "sass"
}"""
    
    with open(preset_file, 'w') as f:
        f.write(preset_content)
    
    # 使用预设创建项目
    vue_cmd = 'vue.cmd' if platform.system() == 'Windows' else 'vue'
    subprocess.run(
        [vue_cmd, 'create', 'alpha-council-vue', '--preset', str(preset_file), '--skipGetStarted'],
        cwd=PROJECT_ROOT,
        check=True,
        shell=True
    )
    
    # 删除预设文件
    preset_file.unlink()
    
    print("✅ Vue项目创建成功！")

def install_vue_dependencies():
    """安装Vue项目依赖"""
    print("\n📦 安装Vue项目依赖...")
    
    npm_cmd = 'npm.cmd' if platform.system() == 'Windows' else 'npm'
    
    # 基础依赖
    dependencies = [
        "axios",           # HTTP客户端
        "pinia",          # 状态管理
        "@vueuse/core",   # Vue组合式工具库
        "echarts",        # 图表库
        "vue-echarts",    # ECharts Vue组件
    ]
    
    # 开发依赖
    dev_dependencies = [
        "@types/node",
        "sass",
        "sass-loader"
    ]
    
    print("安装生产依赖...")
    subprocess.run(
        [npm_cmd, 'install'] + dependencies,
        cwd=VUE_DIR,
        check=True,
        shell=True
    )
    
    print("安装开发依赖...")
    subprocess.run(
        [npm_cmd, 'install', '-D'] + dev_dependencies,
        cwd=VUE_DIR,
        check=True,
        shell=True
    )
    
    print("✅ 依赖安装完成！")

def create_vue_config():
    """创建Vue配置文件"""
    config_file = VUE_DIR / "vue.config.js"
    
    config_content = """module.exports = {
  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
        logLevel: 'debug'
      }
    }
  },
  
  publicPath: process.env.NODE_ENV === 'production' ? '/' : '/',
  outputDir: 'dist',
  assetsDir: 'assets',
  productionSourceMap: false
}
"""
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print("✅ Vue配置文件创建成功")

def start_vue_dev_server():
    """启动Vue开发服务器"""
    print("\n🚀 启动Vue开发服务器...")
    
    npm_cmd = 'npm.cmd' if platform.system() == 'Windows' else 'npm'
    
    # Windows和Unix系统命令不同
    if platform.system() == 'Windows':
        process = subprocess.Popen(
            [npm_cmd, 'run', 'serve'],
            cwd=VUE_DIR,
            shell=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        process = subprocess.Popen(
            ['npm', 'run', 'serve'],
            cwd=VUE_DIR,
            shell=False,
            preexec_fn=os.setsid
        )
    
    processes.append(process)
    print("✅ Vue开发服务器启动中... (http://localhost:8080)")
    return process

def modify_backend_server():
    """修改后端服务器以支持Vue"""
    server_file = BACKEND_DIR / "server.py"
    
    # 读取现有内容
    with open(server_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经修改过
    if "VUE_DIR" in content:
        print("✅ 后端服务器已配置Vue支持")
        return
    
    # 在导入部分后添加Vue支持代码
    vue_support_code = '''
# Vue开发支持
import subprocess
from pathlib import Path

# Vue项目目录
VUE_DIR = Path(__file__).parent.parent / "alpha-council-vue"
DEV_MODE = os.getenv("ENV", "development") == "development"

# 开发模式下的Vue支持
if DEV_MODE:
    @app.on_event("startup")
    async def startup_event():
        """启动时检查Vue项目"""
        if VUE_DIR.exists():
            print("✅ Vue项目已就绪: http://localhost:8080")
        else:
            print("⚠️ Vue项目未找到，请运行 scripts/dev.py 初始化")
'''
    
    # 在app = FastAPI()之后插入
    import_end = content.find("app = FastAPI()")
    if import_end != -1:
        insert_pos = content.find("\n", import_end) + 1
        new_content = content[:insert_pos] + vue_support_code + content[insert_pos:]
        
        # 写回文件
        with open(server_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ 后端服务器已添加Vue支持")

def start_backend_server():
    """启动FastAPI后端服务器"""
    print("\n🚀 启动FastAPI后端服务器...")
    
    # 设置环境变量
    env = os.environ.copy()
    env['ENV'] = 'development'
    
    # Windows和Unix系统命令不同
    if platform.system() == 'Windows':
        process = subprocess.Popen(
            [sys.executable, str(BACKEND_DIR / "server.py")],
            env=env,
            shell=False,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        process = subprocess.Popen(
            [sys.executable, str(BACKEND_DIR / "server.py")],
            env=env,
            shell=False,
            preexec_fn=os.setsid
        )
    
    processes.append(process)
    print("✅ FastAPI后端启动中... (http://localhost:8000)")
    return process

def main():
    """主函数"""
    print("=" * 60)
    print("🎯 InvestMind Pro 开发环境一键启动")
    print("=" * 60)
    
    # 1. 检查Node环境
    if not check_node() or not check_npm():
        sys.exit(1)
    
    # 2. 检查或创建Vue项目
    if not VUE_DIR.exists():
        create_vue_project()
        install_vue_dependencies()
        create_vue_config()
    else:
        print("✅ Vue项目已存在")
        
        # 检查node_modules
        if not (VUE_DIR / "node_modules").exists():
            print("📦 检测到缺少依赖，正在安装...")
            npm_cmd = 'npm.cmd' if platform.system() == 'Windows' else 'npm'
            subprocess.run([npm_cmd, 'install'], cwd=VUE_DIR, check=True, shell=True)
        
        # 检查配置文件
        if not (VUE_DIR / "vue.config.js").exists():
            create_vue_config()
    
    # 3. 修改后端支持Vue
    modify_backend_server()
    
    # 4. 启动服务
    print("\n" + "=" * 60)
    print("🚀 启动服务...")
    print("=" * 60)
    
    # 启动Vue开发服务器
    vue_process = start_vue_dev_server()
    
    # 等待Vue启动
    time.sleep(3)
    
    # 启动FastAPI后端
    backend_process = start_backend_server()
    
    # 等待服务完全启动
    time.sleep(3)
    
    # 显示访问信息
    print("\n" + "=" * 60)
    print("✨ InvestMind Pro 开发环境已就绪！")
    print("=" * 60)
    print("📍 访问地址:")
    print("   前端界面: http://localhost:8080")
    print("   后端API: http://localhost:8000")
    print("   API文档: http://localhost:8000/docs")
    print("\n💡 提示:")
    print("   - 前端修改会自动热重载")
    print("   - 后端修改需要重启服务")
    print("   - 按 Ctrl+C 停止所有服务")
    print("=" * 60)
    
    try:
        # 等待进程结束
        while True:
            # 检查进程是否还在运行
            for process in processes:
                if process.poll() is not None:
                    print(f"⚠️ 有服务异常退出，正在重启...")
                    cleanup()
                    sys.exit(1)
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
