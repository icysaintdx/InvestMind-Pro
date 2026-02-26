"""
动态API提供商管理服务
SQLite存储 + 模型检测 + 连通性测试
"""

import json
import sqlite3
import time
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

import httpx

from backend.utils.logging_config import get_logger

logger = get_logger("services.api_provider")

# 数据库路径：与主数据库同目录
_DB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.exists("/app/data"):
    _DB_PATH = "/app/data/InvestMindPro.db"
else:
    _project_root = os.path.dirname(_DB_DIR)
    _DB_PATH = os.path.join(_project_root, "InvestMindPro.db")


def _get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def _init_table():
    """初始化 api_providers 表"""
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                base_url TEXT NOT NULL,
                api_key TEXT NOT NULL,
                sdk_type TEXT NOT NULL DEFAULT 'openai',
                models TEXT DEFAULT '[]',
                enabled INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)
        conn.commit()
        logger.info("api_providers 表初始化完成")
    except Exception as e:
        logger.error(f"初始化 api_providers 表失败: {e}")
    finally:
        conn.close()


# 模块加载时自动建表
_init_table()


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """将数据库行转为字典，解析 models JSON"""
    d = dict(row)
    d["enabled"] = bool(d.get("enabled", 1))
    try:
        d["models"] = json.loads(d.get("models", "[]"))
    except (json.JSONDecodeError, TypeError):
        d["models"] = []
    return d


# ==================== CRUD ====================


def list_providers(enabled_only: bool = False) -> List[Dict[str, Any]]:
    """列出所有提供商"""
    conn = _get_connection()
    try:
        if enabled_only:
            rows = conn.execute(
                "SELECT * FROM api_providers WHERE enabled = 1 ORDER BY priority DESC, id ASC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM api_providers ORDER BY priority DESC, id ASC"
            ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_provider(provider_id: int) -> Optional[Dict[str, Any]]:
    """获取单个提供商"""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM api_providers WHERE id = ?", (provider_id,)
        ).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def add_provider(data: Dict[str, Any]) -> Dict[str, Any]:
    """添加提供商"""
    conn = _get_connection()
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        models_json = json.dumps(data.get("models", []), ensure_ascii=False)
        cursor = conn.execute(
            """INSERT INTO api_providers (name, base_url, api_key, sdk_type, models, enabled, priority, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["name"],
                data["base_url"],
                data["api_key"],
                data.get("sdk_type", "openai"),
                models_json,
                1 if data.get("enabled", True) else 0,
                data.get("priority", 0),
                now,
                now,
            ),
        )
        conn.commit()
        return get_provider(cursor.lastrowid)
    finally:
        conn.close()


def update_provider(provider_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """更新提供商"""
    existing = get_provider(provider_id)
    if not existing:
        return None

    conn = _get_connection()
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fields = []
        values = []

        for key in ("name", "base_url", "api_key", "sdk_type", "priority"):
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])

        if "models" in data:
            fields.append("models = ?")
            values.append(json.dumps(data["models"], ensure_ascii=False))

        if "enabled" in data:
            fields.append("enabled = ?")
            values.append(1 if data["enabled"] else 0)

        fields.append("updated_at = ?")
        values.append(now)
        values.append(provider_id)

        conn.execute(
            f"UPDATE api_providers SET {', '.join(fields)} WHERE id = ?",
            values,
        )
        conn.commit()
        return get_provider(provider_id)
    finally:
        conn.close()


def delete_provider(provider_id: int) -> bool:
    """删除提供商"""
    conn = _get_connection()
    try:
        cursor = conn.execute("DELETE FROM api_providers WHERE id = ?", (provider_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ==================== 模型检测 & 连通性测试 ====================


async def detect_models(provider_id: int) -> Dict[str, Any]:
    """
    调用提供商的 /v1/models (或 /models) 端点获取可用模型列表
    仅适用于 OpenAI 兼容 API
    """
    provider = get_provider(provider_id)
    if not provider:
        return {"success": False, "error": "提供商不存在"}

    base_url = provider["base_url"].rstrip("/")
    api_key = provider["api_key"]

    # 构造 models 端点 URL
    if base_url.endswith("/v1"):
        models_url = f"{base_url}/models"
    else:
        models_url = f"{base_url}/v1/models"

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            response = await client.get(
                models_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )

        if response.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text[:200]}",
            }

        result = response.json()
        model_list = []

        # OpenAI 格式: {"data": [{"id": "model-name", ...}, ...]}
        if "data" in result:
            model_list = [m.get("id", "") for m in result["data"] if m.get("id")]
        elif isinstance(result, list):
            model_list = [m.get("id", "") if isinstance(m, dict) else str(m) for m in result]

        model_list.sort()

        # 更新数据库
        update_provider(provider_id, {"models": model_list})

        return {"success": True, "models": model_list, "count": len(model_list)}

    except httpx.TimeoutException:
        return {"success": False, "error": "请求超时（15秒）"}
    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


async def test_connection(provider_id: int) -> Dict[str, Any]:
    """
    测试提供商连通性：发送一个简单的 chat completion 请求
    """
    provider = get_provider(provider_id)
    if not provider:
        return {"success": False, "error": "提供商不存在"}

    base_url = provider["base_url"].rstrip("/")
    api_key = provider["api_key"]
    sdk_type = provider["sdk_type"]
    models = provider.get("models", [])

    # 选择一个模型用于测试
    test_model = models[0] if models else None

    start_time = time.time()

    try:
        if sdk_type == "openai":
            return await _test_openai_compatible(base_url, api_key, test_model, start_time)
        elif sdk_type == "anthropic":
            return await _test_anthropic(base_url, api_key, test_model, start_time)
        elif sdk_type == "google":
            return await _test_google(base_url, api_key, test_model, start_time)
        else:
            return {"success": False, "error": f"不支持的SDK类型: {sdk_type}"}
    except httpx.TimeoutException:
        return {"success": False, "error": "请求超时", "latency_ms": int((time.time() - start_time) * 1000)}
    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}", "latency_ms": int((time.time() - start_time) * 1000)}


async def _test_openai_compatible(base_url: str, api_key: str, model: Optional[str], start_time: float) -> Dict[str, Any]:
    """测试 OpenAI 兼容 API"""
    if not base_url.endswith("/v1"):
        chat_url = f"{base_url}/v1/chat/completions"
    else:
        chat_url = f"{base_url}/chat/completions"

    if not model:
        model = "gpt-3.5-turbo"  # 占位，大部分兼容API会自动选择

    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
        response = await client.post(
            chat_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5,
                "stream": False,
            },
        )

    latency_ms = int((time.time() - start_time) * 1000)

    if response.status_code == 200:
        return {
            "success": True,
            "latency_ms": latency_ms,
            "model_used": model,
            "message": "连接成功",
        }
    else:
        return {
            "success": False,
            "latency_ms": latency_ms,
            "error": f"HTTP {response.status_code}: {response.text[:200]}",
        }


async def _test_anthropic(base_url: str, api_key: str, model: Optional[str], start_time: float) -> Dict[str, Any]:
    """测试 Anthropic API"""
    chat_url = f"{base_url}/v1/messages" if not base_url.endswith("/v1") else f"{base_url}/messages"

    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
        response = await client.post(
            chat_url,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": model or "claude-3-haiku-20240307",
                "max_tokens": 5,
                "messages": [{"role": "user", "content": "Hi"}],
            },
        )

    latency_ms = int((time.time() - start_time) * 1000)

    if response.status_code == 200:
        return {"success": True, "latency_ms": latency_ms, "model_used": model, "message": "连接成功"}
    else:
        return {"success": False, "latency_ms": latency_ms, "error": f"HTTP {response.status_code}: {response.text[:200]}"}


async def _test_google(base_url: str, api_key: str, model: Optional[str], start_time: float) -> Dict[str, Any]:
    """测试 Google Gemini API（OpenAI兼容模式）"""
    chat_url = f"{base_url}/v1beta/openai/chat/completions"

    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
        response = await client.post(
            chat_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model or "gemini-2.0-flash",
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5,
            },
        )

    latency_ms = int((time.time() - start_time) * 1000)

    if response.status_code == 200:
        return {"success": True, "latency_ms": latency_ms, "model_used": model, "message": "连接成功"}
    else:
        return {"success": False, "latency_ms": latency_ms, "error": f"HTTP {response.status_code}: {response.text[:200]}"}
