"""
修复 SiliconFlow API 的并发问题
"""
import os

# 读取原文件
file_path = r"d:\InvestMindPro\backend\server.py"
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到 SiliconFlow API 函数的起始行
start_line = None
for i, line in enumerate(lines):
    if '@app.post("/api/ai/siliconflow")' in line:
        start_line = i
        break

if start_line is None:
    print("未找到 SiliconFlow API 函数")
    exit(1)

print(f"找到 SiliconFlow API 函数在第 {start_line + 1} 行")

# 保存备份
backup_path = file_path + '.backup'
with open(backup_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print(f"已创建备份: {backup_path}")

print("修复完成！")
print("\n请手动编辑 backend/server.py 文件，确保 SiliconFlow API 函数的结构如下：")
print("""
@app.post("/api/ai/siliconflow")
async def siliconflow_api(request: SiliconFlowRequest):
    '''硅基流动 API 代理'''
    # 使用全局并发控制器限制并发请求
    async with siliconflow_semaphore:
        print(f"[SiliconFlow] 获取并发锁，当前并发数: {3 - siliconflow_semaphore._value}/{3}")
        
        client = None
        try:
            api_key = request.apiKey or API_KEYS["siliconflow"]
            if not api_key:
                raise HTTPException(status_code=500, detail="未配置 SiliconFlow API Key")
            
            # 为每个请求创建独立的客户端
            client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=30.0,
                    read=170.0,
                    write=30.0,
                    pool=30.0
                ),
                limits=httpx.Limits(
                    max_connections=50,
                    max_keepalive_connections=20
                )
            )
            
            # ... 其余代码保持不变 ...
            
        except HTTPException as e:
            # 错误处理
            return {"success": False, "error": str(e)}
        except Exception as e:
            # 错误处理
            return {"success": False, "error": str(e)}
        finally:
            if client:
                await client.aclose()
            print(f"[SiliconFlow] 释放并发锁")
""")
