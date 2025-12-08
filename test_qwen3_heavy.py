"""Qwen3-8B 在 SiliconFlow 上的并发压测脚本

- 使用环境变量 SILICONFLOW_API_KEY（不要在代码中写死密钥）
- 模拟第二阶段类似场景：约 5000 字符 prompt + 并发 5
- 可调整 max_tokens 和并发数，观察真实耗时和 ReadTimeout 情况

运行方式：
    python test_qwen3_heavy.py

建议在和后端同一台机器上运行，便于对比耗时。
"""

import os
import asyncio
import time
from typing import List

import httpx

API_URL = "https://api.siliconflow.cn/v1/chat/completions"
MODEL = "Qwen/Qwen3-8B"

# 构造一个接近第二阶段风格的基础中文提示词
BASE_PROMPT = """
你是一个专业的证券研究员，请根据以下多维度信息，对某只股票的投资价值进行深度分析。请严格按照【市场环境】【公司基本面】【行业格局】【风险提示】【投资建议】五个部分依次作答，每个部分控制在 3-5 段，语言简洁清晰。

以下是前序分析 agent 的要点汇总（模拟）：
- 中国市场整体情绪中性偏多，北向资金小幅流入，成交额放大。
- 新闻舆情以利好为主，市场关注政策支持与行业景气度回升。
- 社交媒体讨论热度较高，短期波动风险上升，但中长期预期乐观。

请在回答时避免重复上述原文，用你自己的话做系统性归纳。
""".strip()


def build_prompt(target_length: int) -> str:
    """根据目标长度构造长提示词"""
    prompt = ""
    # 重复 BASE_PROMPT，直到长度达到或超过目标，然后截断到精确长度
    while len(prompt) < target_length:
        prompt += BASE_PROMPT + "\n\n"
    return prompt[:target_length]


async def call_qwen3(
    client: httpx.AsyncClient,
    api_key: str,
    idx: int,
    max_tokens: int,
    prompt: str,
) -> float:
    """单个请求，返回耗时（秒）。发生异常时返回 -1。"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个严谨的投资研究员。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": max_tokens,
        "stream": False,
    }

    print(f"[Task {idx}] 开始请求，prompt长度={len(prompt)} 字符, max_tokens={max_tokens}")
    start = time.time()
    try:
        resp = await client.post(API_URL, headers=headers, json=data)
        cost = time.time() - start
        if resp.status_code != 200:
            print(f"[Task {idx}] ❌ HTTP {resp.status_code}, 耗时 {cost:.2f}s, body={resp.text[:200]}")
            return -1
        j = resp.json()
        text = j.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = j.get("usage", {})
        print(
            f"[Task {idx}] ✅ 成功，耗时 {cost:.2f}s, total_tokens={usage.get('total_tokens', 'NA')}, "
            f"reply_len={len(text)}"
        )
        return cost
    except httpx.ReadTimeout:
        cost = time.time() - start
        print(f"[Task {idx}] ❌ ReadTimeout, 等待约 {cost:.2f}s")
        return -1
    except asyncio.TimeoutError:
        cost = time.time() - start
        print(f"[Task {idx}] ❌ asyncio.TimeoutError, 等待约 {cost:.2f}s")
        return -1
    except Exception as e:
        cost = time.time() - start
        print(f"[Task {idx}] ❌ 其它异常 {type(e).__name__}: {str(e)[:200]}, 耗时 {cost:.2f}s")
        return -1


async def run_batch(concurrency: int, max_tokens: int, prompt_length: int) -> bool:
    api_key = os.getenv("SILICONFLOW_API_KEY", "")
    if not api_key:
        raise RuntimeError("未设置环境变量 SILICONFLOW_API_KEY")

    timeout = httpx.Timeout(
        timeout=220.0,  # 给压测更宽裕的时间，避免脚本自身过早超时
        connect=20.0,
        read=200.0,
        write=20.0,
        pool=20.0,
    )

    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)

    prompt = build_prompt(prompt_length)

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        print("=" * 60)
        print(f"Qwen3-8B 压测开始: 并发={concurrency}, max_tokens={max_tokens}")
        print(f"提示词长度: {len(prompt)} 字符 (目标 {prompt_length})")
        print("=" * 60)

        tasks = [
            call_qwen3(client, api_key, i + 1, max_tokens, prompt) for i in range(concurrency)
        ]
        start_all = time.time()
        results: List[float] = await asyncio.gather(*tasks)
        total_cost = time.time() - start_all

        success_times = [c for c in results if c > 0]
        fail_count = sum(1 for c in results if c <= 0)

        print("-" * 60)
        print(f"总耗时: {total_cost:.2f}s (从并发开始到全部结束)")
        print(f"成功数量: {len(success_times)} / {concurrency}")
        if success_times:
            print(
                f"成功耗时统计: 最快={min(success_times):.2f}s, "
                f"最慢={max(success_times):.2f}s, 平均={sum(success_times)/len(success_times):.2f}s"
            )
        print(f"失败数量(ReadTimeout/异常): {fail_count}")

        all_success = len(success_times) == concurrency
        print(f"本轮结果: {'✅ 全部成功' if all_success else '❌ 存在失败'}")
        print("=" * 60)

        return all_success


async def search_prompt_length(
    concurrency: int,
    max_tokens: int,
    start_length: int,
    min_length: int = 1000,
) -> None:
    """按照指定策略搜索合适的 prompt 长度。

    策略：
    1. 从 start_length 开始，如果失败，每次减 2000，直到第一次全部成功或小于 min_length。
    2. 找到第一次成功长度后，每次加 1000，直到再次出现失败。
    """

    length = start_length
    print(f"起始测试 prompt 长度: {length} 字符，最小长度: {min_length} 字符")

    # 阶段 1：自上而下寻找第一个全部成功的长度
    while True:
        print(f"\n>>> 阶段1：测试长度 {length} 字符")
        success = await run_batch(concurrency, max_tokens, prompt_length=length)
        if success:
            print(f"阶段1结束：首次全部成功的长度为 {length} 字符")
            break

        length -= 2000
        if length < min_length:
            print(f"已降到 {length} (<{min_length}) 仍全部失败，停止测试")
            return

    # 阶段 2：在成功长度基础上逐步增加，寻找失败边界
    while True:
        next_length = length + 1000
        print(f"\n>>> 阶段2：测试增加后长度 {next_length} 字符")
        success = await run_batch(concurrency, max_tokens, prompt_length=next_length)
        if not success:
            print(f"在长度 {next_length} 字符时出现失败，上一次成功长度为 {length} 字符")
            print(
                f"建议安全 prompt 长度 ≈ {length} 字符（并发 {concurrency}, max_tokens={max_tokens}）"
            )
            break
        length = next_length


def main() -> None:
    concurrency = 3
    max_tokens = 512  # 可以根据需要调整
    start_length = 10000
    min_length = 1000

    print(f"使用模型: {MODEL}")
    print(f"并发数: {concurrency}, max_tokens: {max_tokens}")
    asyncio.run(
        search_prompt_length(
            concurrency=concurrency,
            max_tokens=max_tokens,
            start_length=start_length,
            min_length=min_length,
        )
    )


if __name__ == "__main__":
    main()
