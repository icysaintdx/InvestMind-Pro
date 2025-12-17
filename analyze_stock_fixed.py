"""
修复后的 analyze_stock 函数
请复制此函数替换 server.py 中的 analyze_stock 函数（从第704行开始）
"""

@app.post("/api/analyze")
async def analyze_stock(request: AnalyzeRequest):
    """统一的智能体分析接口"""
    # 使用信号量限制并发，避免同时调用过多LLM API
    async with LLM_SEMAPHORE:
        print(f"[分析] {request.agent_id} 获取LLM资源，开始分析...")
        try:
            agent_id = request.agent_id
            stock_code = request.stock_code
            stock_data = request.stock_data
            previous_outputs = request.previous_outputs
            custom_instruction = request.custom_instruction
            
            # 从缓存获取配置
            agent_config = get_agent_config(agent_id)
            
            # 如果没有找到配置，使用默认值（使用SiliconFlow避免余额问题）
            if not agent_config:
                agent_config = {
                    "modelName": "Qwen/Qwen2.5-7B-Instruct",  # 默认使用SiliconFlow的通义千问
                    "modelProvider": "SILICONFLOW",
                    "temperature": 0.3
                }
            
            model_name = agent_config.get("modelName", "deepseek-chat")
            temperature = agent_config.get("temperature", 0.3)
            
            # 根据模型名称判断使用哪个API
            # 优先判断：如果包含斜杠，说明是平台模型（如 Qwen/Qwen3-8B），使用硅基流动
            api_endpoint = None
            if "/" in model_name:
                # 包含斜杠的都是平台模型，通过硅基流动访问
                api_endpoint = "/api/ai/siliconflow"
                provider = "SILICONFLOW"
            elif model_name.startswith("gemini"):
                # Gemini官方模型
                api_endpoint = "/api/ai/gemini"
                provider = "GEMINI"
            elif model_name in ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]:
                # DeepSeek官方模型（明确列举）
                api_endpoint = "/api/ai/deepseek"
                provider = "DEEPSEEK"
            elif model_name in ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-max-longcontext", "qwen-turbo-latest"] or "通义千问" in model_name:
                # Qwen官方模型（明确列举）
                api_endpoint = "/api/ai/qwen"
                provider = "QWEN"
            else:
                # 默认使用硅基流动（支持最多模型）
                api_endpoint = "/api/ai/siliconflow"
                provider = "SILICONFLOW"
            
            # 构建系统提示词
            role_name = get_agent_role(agent_id)
            system_prompt = f"你是一个专业的{role_name}，隶属于InvestMindPro顶级投研团队。你的目标是提供深度、犀利且独到的投资见解。"
            system_prompt += "\n\n【风格要求】\n1. 直接切入主题，严禁废话。\n2. 严禁在开头复述股票代码、名称、当前价格等基础信息（除非数据出现重大异常）。\n3. 像华尔街资深分析师一样说话，使用专业术语但逻辑清晰。\n4. 必须引用前序同事的分析结论作为支撑或反驳的依据。"

            # 构建用户提示词
            user_prompt = ""
            
            # 如果有自定义指令，优先放入
            if custom_instruction:
                user_prompt += f"【当前任务指令】\n{custom_instruction}\n\n"
            
            # 基础数据仅作为参考附录，不强制要求分析
            user_prompt += f"【参考数据 - {stock_code}】\n"
            user_prompt += f"价格: {stock_data.get('nowPri', stock_data.get('price', 'N/A'))} | 涨跌: {stock_data.get('increase', stock_data.get('change', 'N/A'))}%\n"
            user_prompt += f"成交: {stock_data.get('traAmount', stock_data.get('volume', 'N/A'))}\n"
            
            # 重点：前序分析结果
            if previous_outputs and len(previous_outputs) > 0:
                user_prompt += "\n【团队成员已完成的分析】(请基于此进行深化，不要重复)\n"
                for agent_name, output in previous_outputs.items():
                    if output:
                        # 截取前500字符摘要，避免Token溢出
                        summary = output[:500] + "..." if len(output) > 500 else output
                        user_prompt += f">>> {get_agent_role(agent_name)} 的结论:\n{summary}\n\n"
            else:
                user_prompt += "\n你是第一批进入分析的专家，请基于原始市场数据构建初始观点。\n"

            # 调用相应的AI API
            if provider == "GEMINI":
                req = GeminiRequest(
                    prompt=user_prompt,
                    systemPrompt=system_prompt,
                    model=model_name,
                    temperature=temperature
                )
                result = await gemini_api(req)
            elif provider == "DEEPSEEK":
                req = DeepSeekRequest(
                    prompt=user_prompt,
                    systemPrompt=system_prompt,
                    model=model_name,
                    temperature=temperature
                )
                result = await deepseek_api(req)
            elif provider == "QWEN":
                req = QwenRequest(
                    prompt=user_prompt,
                    systemPrompt=system_prompt,
                    model=model_name,
                    temperature=temperature
                )
                result = await qwen_api(req)
            else:
                req = SiliconFlowRequest(
                    prompt=user_prompt,
                    systemPrompt=system_prompt,
                    model=model_name,
                    temperature=temperature
                )
                result = await siliconflow_api(req)
            
            if result.get("success"):
                print(f"[分析] {request.agent_id} 分析完成，释放LLM资源")
                return {"success": True, "result": result.get("text", "")}
            else:
                print(f"[分析] {request.agent_id} 分析失败: {result.get('error')}")
                return {"success": False, "error": result.get("error", "分析失败")}
                
        except Exception as e:
            import traceback
            print(f"[Analyze] {request.agent_id} 错误: {str(e)}")
            print(traceback.format_exc())
            return {"success": False, "error": str(e)}
