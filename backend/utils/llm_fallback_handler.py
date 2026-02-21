"""
LLM 多级降级处理器
实现智能降级策略，确保分析流程不会因个别超时而中断
"""
import asyncio
import httpx
import json
import time
import hashlib
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class RequestMetrics:
    """请求指标"""
    prompt_length: int
    prompt_tokens_est: int
    request_size_kb: float
    attempt_times: list
    error_types: list
    final_status: str
    total_time: float
    
class FallbackHandler:
    """
    多级降级处理器
    
    降级策略：
    1. 原始请求 (60s timeout)
    2. 摘要压缩 (45s timeout) - 压缩到 50%
    3. 深度压缩 (30s timeout) - 压缩到 25%
    4. 最小化请求 (20s timeout) - 只保留核心信息
    5. 默认响应 - 返回预设的保守建议
    """
    
    def __init__(self, summarizer=None):
        """
        Args:
            summarizer: 文本摘要器实例
        """
        self.summarizer = summarizer
        self.request_cache = {}  # 缓存成功的请求
        self.error_stats = {}    # 错误统计
        
    async def execute_with_fallback(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: Dict,
        data: Dict,
        agent_role: str,
        max_retries: int = 4
    ) -> Tuple[Dict, RequestMetrics]:
        """
        执行请求，带多级降级
        
        Returns:
            (response_dict, metrics)
        """
        original_prompt = data["messages"][-1]["content"]
        original_system = data["messages"][0]["content"] if len(data["messages"]) > 1 else ""
        
        metrics = RequestMetrics(
            prompt_length=len(original_prompt),
            prompt_tokens_est=len(original_prompt) // 2,
            request_size_kb=len(json.dumps(data)) / 1024,
            attempt_times=[],
            error_types=[],
            final_status="",
            total_time=0
        )
        
        start_time = time.time()
        
        # 降级级别配置
        fallback_levels = [
            {
                "name": "原始请求",
                "timeout": 60.0,
                "compression": 1.0,
                "max_tokens": data.get("max_tokens", 1024)
            },
            {
                "name": "轻度压缩",
                "timeout": 45.0,
                "compression": 0.5,
                "max_tokens": 512
            },
            {
                "name": "深度压缩",
                "timeout": 30.0,
                "compression": 0.25,
                "max_tokens": 256
            },
            {
                "name": "最小化",
                "timeout": 20.0,
                "compression": 0.1,
                "max_tokens": 128
            }
        ]
        
        # 检查缓存
        cache_key = self._get_cache_key(agent_role, original_prompt)
        if cache_key in self.request_cache:
            logger.info(f"[降级处理] 使用缓存响应: {agent_role}")
            cached = self.request_cache[cache_key]
            metrics.final_status = "cached"
            metrics.total_time = 0.001
            return cached, metrics
        
        # 逐级尝试
        for level_idx, level in enumerate(fallback_levels):
            attempt_start = time.time()
            
            try:
                # 准备请求数据
                current_data = data.copy()
                
                # 压缩提示词
                if level["compression"] < 1.0 and self.summarizer:
                    compressed_prompt = await self._compress_prompt(
                        original_prompt,
                        level["compression"],
                        agent_role
                    )
                    current_data["messages"][-1]["content"] = compressed_prompt
                    logger.info(f"[降级处理] {level['name']}: 压缩到 {len(compressed_prompt)}/{len(original_prompt)} 字符")
                
                # 调整输出长度
                current_data["max_tokens"] = level["max_tokens"]
                
                # 发送请求
                logger.info(f"[降级处理] 尝试 {level['name']} (超时: {level['timeout']}s)")
                
                response = await asyncio.wait_for(
                    client.post(url, headers=headers, json=current_data),
                    timeout=level["timeout"]
                )
                
                attempt_time = time.time() - attempt_start
                metrics.attempt_times.append(attempt_time)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 缓存成功的响应
                    self.request_cache[cache_key] = result
                    
                    # 记录成功
                    metrics.final_status = f"success_level_{level_idx}"
                    metrics.total_time = time.time() - start_time
                    
                    logger.info(f"[降级处理] ✅ {level['name']}成功 (耗时: {attempt_time:.1f}s)")
                    
                    # 如果不是原始请求，添加降级标记
                    if level_idx > 0:
                        text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        text = f"[降级级别{level_idx}: {level['name']}]\n{text}"
                        result["choices"][0]["message"]["content"] = text
                        result["fallback_level"] = level_idx
                    
                    return result, metrics
                else:
                    raise httpx.HTTPStatusError(
                        f"HTTP {response.status_code}",
                        request=response.request,
                        response=response
                    )
                    
            except asyncio.TimeoutError:
                metrics.error_types.append(f"timeout_level_{level_idx}")
                logger.warning(f"[降级处理] ⏱️ {level['name']}超时 ({level['timeout']}s)")
                # 如果还有下一级，明确日志提示将切换到下一级降级策略
                if level_idx + 1 < len(fallback_levels):
                    next_level = fallback_levels[level_idx + 1]
                    logger.info(
                        f"[降级处理] 将从{level['name']}切换到下一级降级策略: {next_level['name']} "
                        f"(压缩比例: {next_level['compression']:.0%}, 超时: {next_level['timeout']}s)"
                    )
                
            except httpx.ReadTimeout:
                metrics.error_types.append(f"read_timeout_level_{level_idx}")
                logger.warning(f"[降级处理] ⏱️ {level['name']}读取超时")
                if level_idx + 1 < len(fallback_levels):
                    next_level = fallback_levels[level_idx + 1]
                    logger.info(
                        f"[降级处理] 将从{level['name']}切换到下一级降级策略: {next_level['name']} "
                        f"(压缩比例: {next_level['compression']:.0%}, 超时: {next_level['timeout']}s)"
                    )
                
            except Exception as e:
                metrics.error_types.append(f"{type(e).__name__}_level_{level_idx}")
                logger.error(f"[降级处理] ❌ {level['name']}失败: {type(e).__name__}: {str(e)[:100]}")
                if level_idx + 1 < len(fallback_levels):
                    next_level = fallback_levels[level_idx + 1]
                    logger.info(
                        f"[降级处理] 将从{level['name']}切换到下一级降级策略: {next_level['name']} "
                        f"(压缩比例: {next_level['compression']:.0%}, 超时: {next_level['timeout']}s)"
                    )
        
        # 所有级别都失败，返回默认响应
        metrics.final_status = "all_failed_use_default"
        metrics.total_time = time.time() - start_time
        
        # 记录错误统计
        self._record_error(agent_role, metrics)
        
        # 生成详细的错误报告
        error_report = self._generate_error_report(agent_role, metrics, original_prompt)
        
        logger.error(f"[降级处理] ❌ 所有降级级别失败，返回默认响应")
        logger.error(error_report)
        
        # 返回默认响应
        return self._get_default_response(agent_role, error_report), metrics
    
    async def _compress_prompt(self, prompt: str, ratio: float, agent_role: str) -> str:
        """
        压缩提示词 - 优先使用LLM智能摘要
        
        Args:
            prompt: 原始提示词
            ratio: 压缩比例 (0.1-1.0)
            agent_role: 智能体角色
            
        Returns:
            压缩后的提示词
        """
        # 优先使用LLM智能摘要
        try:
            # 动态导入避免循环依赖
            import httpx
            import json
            import os
            
            # 读取配置
            config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agent_configs.json")
            model_name = "Qwen/Qwen2.5-7B-Instruct"
            temperature = 0.2
            api_key = os.getenv("MINIMAX_API_KEY", "icysaintdx")
            
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    model_name = config_data.get("summarizerModel", model_name)
                    temperature = config_data.get("summarizerTemperature", temperature)
            
            # 构建智能摘要请求
            system_prompt = "你是一个专业的金融文本摘要专家，擅长提取和保留关键投资信息。"
            
            if ratio <= 0.25:  # 深度压缩
                user_prompt = f"""请将下面的投资分析文本压缩到{int(ratio*100)}%，只保留最核心的信息：

{prompt}

严格要求：
1. 必须保留：所有股票代码、具体价格、涨跌百分比、关键财务数据
2. 必须保留：核心投资建议（买入/卖出/持有）和目标价位
3. 必须保留：主要风险提示和止损位
4. 删除：冗余描述、重复内容、过渡语句
5. 输出必须简洁，不要任何开场白"""
            elif ratio <= 0.5:  # 中度压缩
                user_prompt = f"""请智能提取下面投资分析的关键信息，压缩到{int(ratio*100)}%：

{prompt}

保留要点：
1. 所有数字、百分比、价格信息
2. 核心分析结论和投资建议
3. 重要风险和机会
4. 关键支撑位和阻力位
输出清晰简洁的摘要"""
            else:  # 轻度压缩
                user_prompt = f"""请精简下面的投资分析文本到{int(ratio*100)}%，保留所有关键信息：

{prompt}

去除冗余但保留要点"""
            
            # 构建请求
            data = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature,
                "max_tokens": int(len(prompt) * ratio / 2),  # 控制输出长度
                "stream": False
            }
            
            # 快速调用LLM（5秒超时）
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.post(
                    "https://kirocpa.zeabur.app/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    compressed_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    if compressed_text and len(compressed_text) < len(prompt):
                        logger.info(f"[降级处理] ✅ LLM智能摘要成功: {len(compressed_text)}/{len(prompt)} 字符")
                        return compressed_text + f"\n[智能压缩至{int(ratio*100)}%]"
                    
        except Exception as e:
            logger.warning(f"[降级处理] LLM摘要失败，降级到本地压缩: {e}")
        
        # 降级到本地智能压缩
        if not self.summarizer:
            # 最简单的截断
            target_length = int(len(prompt) * ratio)
            return prompt[:target_length] + "\n...[已截断]"
        
        try:
            # 使用本地摘要器
            compressed = await self.summarizer.compress(
                prompt,
                target_ratio=ratio,
                preserve_key_info=True,
                context=agent_role
            )
            return compressed
        except Exception as e:
            logger.error(f"本地摘要器失败: {e}")
            target_length = int(len(prompt) * ratio)
            return prompt[:target_length] + "\n...[已截断]"
    
    def _get_cache_key(self, agent_role: str, prompt: str) -> str:
        """生成缓存键"""
        content = f"{agent_role}:{prompt[:100]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _record_error(self, agent_role: str, metrics: RequestMetrics):
        """记录错误统计"""
        if agent_role not in self.error_stats:
            self.error_stats[agent_role] = {
                "total_errors": 0,
                "timeout_errors": 0,
                "last_error_time": None,
                "error_types": {}
            }
        
        stats = self.error_stats[agent_role]
        stats["total_errors"] += 1
        stats["last_error_time"] = datetime.now()
        
        for error_type in metrics.error_types:
            if "timeout" in error_type:
                stats["timeout_errors"] += 1
            stats["error_types"][error_type] = stats["error_types"].get(error_type, 0) + 1
    
    def _generate_error_report(self, agent_role: str, metrics: RequestMetrics, prompt: str) -> str:
        """生成详细的错误报告"""
        report = f"""
======== LLM 请求失败报告 ========
智能体: {agent_role}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
总耗时: {metrics.total_time:.1f}秒

请求信息:
- 原始提示词长度: {metrics.prompt_length} 字符
- 估算Token数: {metrics.prompt_tokens_est}
- 请求体大小: {metrics.request_size_kb:.1f} KB

尝试记录:
"""
        for i, (attempt_time, error) in enumerate(zip(
            metrics.attempt_times + [None] * (4 - len(metrics.attempt_times)),
            metrics.error_types + [""] * (4 - len(metrics.error_types))
        )):
            if attempt_time is not None:
                report += f"  级别{i}: {attempt_time:.1f}s - {error or '成功'}\n"
            else:
                report += f"  级别{i}: 未尝试\n"
        
        # 历史错误统计
        if agent_role in self.error_stats:
            stats = self.error_stats[agent_role]
            report += f"\n历史统计:\n"
            report += f"- 总错误次数: {stats['total_errors']}\n"
            report += f"- 超时次数: {stats['timeout_errors']}\n"
            report += f"- 错误类型分布: {stats['error_types']}\n"
        
        # 提示词片段（用于调试）
        report += f"\n提示词前100字符:\n{prompt[:100]}...\n"
        report += "=" * 40
        
        return report
    
    def _get_default_response(self, agent_role: str, error_report: str) -> Dict:
        """
        获取默认响应
        
        根据不同智能体返回合适的默认建议
        """
        default_texts = {
            "NEWS": "📰 新闻分析暂时不可用。基于历史经验，建议保持观望。",
            "FUNDAMENTAL": "📊 基本面分析暂时不可用。建议参考公开财报数据。",
            "TECHNICAL": "📈 技术分析暂时不可用。建议关注关键支撑位。",
            "BULL": "🐂 多方观点：在数据不足的情况下，建议谨慎乐观。",
            "BEAR": "🐻 空方观点：在数据不足的情况下，建议保持谨慎。",
            "RISK": "⚠️ 风险评估：系统暂时无法分析，建议采用保守策略，持有观望。",
            "MANAGER": "👔 经理建议：基于当前可用信息，建议维持现有仓位。",
            "TRADER": "💹 交易建议：暂时无法生成交易信号，建议等待。"
        }
        
        # 获取对应的默认文本
        role_key = agent_role.upper() if agent_role else "DEFAULT"
        default_text = default_texts.get(role_key, "⚠️ 分析暂时不可用，建议稍后重试。")
        
        # 添加错误信息（仅在调试模式）
        if logger.level <= logging.DEBUG:
            default_text += f"\n\n[调试信息]\n{error_report}"
        
        return {
            "success": True,
            "choices": [{
                "message": {
                    "content": default_text
                }
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "fallback": True,
            "fallback_level": 99  # 特殊标记：使用了默认响应
        }

class TextSummarizer:
    """
    文本摘要器
    用于压缩过长的提示词
    """
    
    async def compress(
        self,
        text: str,
        target_ratio: float = 0.5,
        preserve_key_info: bool = True,
        context: str = None
    ) -> str:
        """
        压缩文本
        
        Args:
            text: 原始文本
            target_ratio: 目标压缩比例
            preserve_key_info: 是否保留关键信息
            context: 上下文（如智能体角色）
        
        Returns:
            压缩后的文本
        """
        target_length = int(len(text) * target_ratio)
        
        if not preserve_key_info:
            # 简单截断
            return text[:target_length] + "\n...[已压缩]"
        
        # 智能压缩策略
        lines = text.split('\n')
        
        # 1. 识别关键部分
        key_patterns = [
            "股票", "代码", "价格", "涨跌", "成交",
            "建议", "风险", "机会", "目标", "止损",
            "财务", "营收", "利润", "增长", "下跌"
        ]
        
        key_lines = []
        other_lines = []
        
        for line in lines:
            if any(pattern in line for pattern in key_patterns):
                key_lines.append(line)
            else:
                other_lines.append(line)
        
        # 2. 优先保留关键行
        result = []
        current_length = 0
        
        # 先添加关键行
        for line in key_lines:
            if current_length + len(line) < target_length * 0.7:  # 70% 给关键信息
                result.append(line)
                current_length += len(line)
        
        # 再添加其他行
        for line in other_lines:
            if current_length + len(line) < target_length:
                result.append(line)
                current_length += len(line)
            else:
                break
        
        compressed = '\n'.join(result)
        
        # 3. 添加压缩标记
        compression_info = f"\n[已压缩: {len(compressed)}/{len(text)} 字符, 保留率: {target_ratio*100:.0f}%]"
        
        return compressed + compression_info

# 全局实例
_fallback_handler = None

def get_fallback_handler() -> FallbackHandler:
    """获取全局降级处理器实例"""
    global _fallback_handler
    if _fallback_handler is None:
        summarizer = TextSummarizer()
        _fallback_handler = FallbackHandler(summarizer)
    return _fallback_handler
