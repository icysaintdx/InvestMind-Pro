#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巨潮资讯数据提供者 — 通过 cninfo WebAPI 获取上市公司历史数据

核心功能：
  - 公司公告（年报/季报/重大事项）
  - 财务数据（利润表/资产负债表/现金流量表/财务指标）
  - 股东信息（十大股东/股东人数变化）
  - 数据缓存到本地数据库（避免重复请求）
  - 请求频率控制（防止被封）

用法:
    python backend/cninfo_data_provider.py --stock 600519 --type announcement
    python backend/cninfo_data_provider.py --stock 000858 --type financial --subtype balance_sheet
    python backend/cninfo_data_provider.py --stock 601318 --type shareholder
    python backend/cninfo_data_provider.py --stock 600519 --type company_info
    python backend/cninfo_data_provider.py --stock 600519 --type all

Author: InvestMindPro
Date: 2026-02-20
"""

import sys
import os
import json
import time
import hashlib
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from backend.database.database import get_db_context, init_database
from backend.database.models import CninfoDataCache
from backend.utils.logging_config import get_logger

logger = get_logger("cninfo_data_provider")

BASE_URL = "http://webapi.cninfo.com.cn"
TOKEN_URL = f"{BASE_URL}/api-cloud-platform/oauth2/token"

MIN_REQUEST_INTERVAL = 0.35
CACHE_TTL_HOURS = {
    "announcement": 6,
    "company_info": 168,       # 7 days
    "stock_info": 168,
    "balance_sheet": 72,       # 3 days
    "income_statement": 72,
    "cash_flow": 72,
    "financial_indicator": 72,
    "top_shareholder": 72,
    "shareholder_count": 72,
    "management": 168,
    "employee": 168,
}

# 免费API端点（已验证可用）
FREE_ENDPOINTS = {
    "company_info":    "/api/stock/p_stock2100",
    "stock_info":      "/api/stock/p_stock2101",
    "management":      "/api/stock/p_stock2102",
    "employee":        "/api/stock/p_stock2107",
    "listing_status":  "/api/stock/p_stock2117",
    "announcement":    "/api/info/p_info3015",
    "ann_category":    "/api/info/p_info3005",
    "sectors":         "/api/stock/p_stock0004",
}

# 可能需要VIP的端点（仍然尝试请求）
VIP_ENDPOINTS = {
    "balance_sheet":       "/api/stock/p_stock2101",
    "income_statement":    "/api/stock/p_stock2102",
    "cash_flow":           "/api/stock/p_stock2103",
    "financial_indicator": "/api/stock/p_stock2104",
    "top_shareholder":     "/api/stock/p_stock3001",
    "shareholder_count":   "/api/stock/p_stock3003",
}


def _make_cache_hash(stock_code: str, data_type: str, params: dict) -> str:
    raw = f"{stock_code}|{data_type}|{json.dumps(params, sort_keys=True)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class CninfoDataProvider:

    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        self.client_id = client_id or os.getenv("CNINFO_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("CNINFO_CLIENT_SECRET", "")
        self._token: str | None = None
        self._token_expires: float = 0
        self._last_request_time: float = 0

        self._session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        self._session.mount("http://", HTTPAdapter(max_retries=retry))
        self._session.mount("https://", HTTPAdapter(max_retries=retry))
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        })

        init_database()

    # -------------------- Token --------------------

    def _ensure_token(self):
        if not self.client_id or not self.client_secret:
            logger.debug("未配置 CNINFO_CLIENT_ID/CNINFO_CLIENT_SECRET，使用无认证模式（仅免费API）")
            return
        if self._token and time.time() < self._token_expires:
            return
        try:
            resp = self._session.post(TOKEN_URL, data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self._token = data.get("access_token")
                expires_in = int(data.get("expires_in", 3600))
                self._token_expires = time.time() + expires_in - 60
                logger.info(f"获取 cninfo token 成功，有效期 {expires_in}s")
            else:
                logger.warning(f"获取 token 失败: HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"获取 token 异常: {e}")

    # -------------------- Rate Limit --------------------

    def _throttle(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    # -------------------- Request --------------------

    def _request(self, endpoint: str, params: dict | None = None) -> dict:
        self._ensure_token()
        self._throttle()

        url = f"{BASE_URL}{endpoint}"
        req_params = dict(params or {})
        req_params["format"] = "json"
        if self._token:
            req_params["access_token"] = self._token

        try:
            resp = self._session.get(url, params=req_params, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"HTTP {resp.status_code}: {endpoint}")
                return {"error": f"HTTP {resp.status_code}", "records": []}

            data = resp.json()
            result_code = data.get("resultcode", data.get("code", 200))
            if result_code in (415, 416):
                logger.warning(f"{endpoint}: 需要VIP权限 (code={result_code})")
                return {"error": f"VIP required (code={result_code})", "vip_required": True, "records": []}
            if result_code not in (200, "200"):
                msg = data.get("resultmsg", data.get("description", "unknown"))
                logger.warning(f"{endpoint}: API错误 code={result_code} msg={msg}")
                return {"error": msg, "records": []}

            return data

        except requests.Timeout:
            logger.error(f"请求超时: {endpoint}")
            return {"error": "timeout", "records": []}
        except Exception as e:
            logger.error(f"请求异常: {endpoint} — {e}")
            return {"error": str(e), "records": []}

    # -------------------- Cache --------------------

    def _get_cache(self, cache_hash: str, data_type: str) -> dict | None:
        ttl = CACHE_TTL_HOURS.get(data_type, 24)
        cutoff = datetime.utcnow() - timedelta(hours=ttl)
        with get_db_context() as db:
            row = db.query(CninfoDataCache).filter(
                CninfoDataCache.cache_hash == cache_hash,
                CninfoDataCache.fetch_time >= cutoff,
            ).first()
            if row:
                logger.debug(f"缓存命中: {data_type} hash={cache_hash[:12]}...")
                return row.data
        return None

    def _set_cache(self, stock_code: str, data_type: str, report_date: str | None,
                   data: dict | list, cache_hash: str):
        record_count = len(data) if isinstance(data, list) else 1
        with get_db_context() as db:
            existing = db.query(CninfoDataCache).filter_by(cache_hash=cache_hash).first()
            if existing:
                existing.data = data
                existing.fetch_time = datetime.utcnow()
                existing.record_count = record_count
            else:
                db.add(CninfoDataCache(
                    stock_code=stock_code,
                    data_type=data_type,
                    report_date=report_date,
                    data=data,
                    record_count=record_count,
                    cache_hash=cache_hash,
                ))

    def _fetch_with_cache(self, stock_code: str, data_type: str, endpoint: str,
                          params: dict, report_date: str | None = None) -> list[dict]:
        cache_hash = _make_cache_hash(stock_code, data_type, params)
        cached = self._get_cache(cache_hash, data_type)
        if cached is not None:
            return cached if isinstance(cached, list) else [cached]

        resp = self._request(endpoint, params)
        records = resp.get("records", [])
        if records:
            self._set_cache(stock_code, data_type, report_date, records, cache_hash)
        elif resp.get("vip_required"):
            logger.info(f"{data_type}: VIP权限不足，跳过缓存")
        return records

    # ==================== 公司基本信息 ====================

    def get_company_info(self, stock_code: str) -> list[dict]:
        logger.info(f"获取公司基本信息: {stock_code}")
        return self._fetch_with_cache(
            stock_code, "company_info",
            FREE_ENDPOINTS["company_info"],
            {"scode": stock_code},
        )

    # ==================== 公告信息 ====================

    def get_announcements(self, stock_code: str, sdate: str | None = None,
                          edate: str | None = None, page: int = 1,
                          pagesize: int = 30) -> list[dict]:
        if not sdate:
            sdate = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not edate:
            edate = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"获取公告: {stock_code} ({sdate} ~ {edate})")
        params = {"scode": stock_code, "sdate": sdate, "edate": edate,
                  "page": page, "pagesize": pagesize}
        return self._fetch_with_cache(
            stock_code, "announcement",
            FREE_ENDPOINTS["announcement"],
            params,
        )

    # ==================== 财务数据 ====================

    def get_balance_sheet(self, stock_code: str, sdate: str | None = None,
                          edate: str | None = None) -> list[dict]:
        if not edate:
            edate = datetime.now().strftime("%Y-%m-%d")
        if not sdate:
            sdate = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

        logger.info(f"获取资产负债表: {stock_code} ({sdate} ~ {edate})")
        params = {"scode": stock_code, "sdate": sdate, "edate": edate}
        return self._fetch_with_cache(
            stock_code, "balance_sheet",
            VIP_ENDPOINTS["balance_sheet"],
            params, report_date=edate,
        )

    def get_income_statement(self, stock_code: str, sdate: str | None = None,
                             edate: str | None = None) -> list[dict]:
        if not edate:
            edate = datetime.now().strftime("%Y-%m-%d")
        if not sdate:
            sdate = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

        logger.info(f"获取利润表: {stock_code} ({sdate} ~ {edate})")
        params = {"scode": stock_code, "sdate": sdate, "edate": edate}
        return self._fetch_with_cache(
            stock_code, "income_statement",
            VIP_ENDPOINTS["income_statement"],
            params, report_date=edate,
        )

    def get_cash_flow(self, stock_code: str, sdate: str | None = None,
                      edate: str | None = None) -> list[dict]:
        if not edate:
            edate = datetime.now().strftime("%Y-%m-%d")
        if not sdate:
            sdate = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

        logger.info(f"获取现金流量表: {stock_code} ({sdate} ~ {edate})")
        params = {"scode": stock_code, "sdate": sdate, "edate": edate}
        return self._fetch_with_cache(
            stock_code, "cash_flow",
            VIP_ENDPOINTS["cash_flow"],
            params, report_date=edate,
        )

    def get_financial_indicators(self, stock_code: str, sdate: str | None = None,
                                 edate: str | None = None) -> list[dict]:
        if not edate:
            edate = datetime.now().strftime("%Y-%m-%d")
        if not sdate:
            sdate = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

        logger.info(f"获取财务指标: {stock_code} ({sdate} ~ {edate})")
        params = {"scode": stock_code, "sdate": sdate, "edate": edate}
        return self._fetch_with_cache(
            stock_code, "financial_indicator",
            VIP_ENDPOINTS["financial_indicator"],
            params, report_date=edate,
        )

    # ==================== 股东信息 ====================

    def get_top_shareholders(self, stock_code: str, rdate: str | None = None) -> list[dict]:
        logger.info(f"获取十大股东: {stock_code} (报告期={rdate or '最新'})")
        params: dict = {"scode": stock_code}
        if rdate:
            params["rdate"] = rdate
        return self._fetch_with_cache(
            stock_code, "top_shareholder",
            VIP_ENDPOINTS["top_shareholder"],
            params, report_date=rdate,
        )

    def get_shareholder_count(self, stock_code: str) -> list[dict]:
        logger.info(f"获取股东户数: {stock_code}")
        params = {"scode": stock_code}
        return self._fetch_with_cache(
            stock_code, "shareholder_count",
            VIP_ENDPOINTS["shareholder_count"],
            params,
        )

    # ==================== 辅助免费接口 ====================

    def get_management(self, stock_code: str) -> list[dict]:
        logger.info(f"获取管理人员: {stock_code}")
        return self._fetch_with_cache(
            stock_code, "management",
            FREE_ENDPOINTS["management"],
            {"scode": stock_code, "state": "1"},
        )

    def get_employee_info(self, stock_code: str) -> list[dict]:
        logger.info(f"获取员工情况: {stock_code}")
        return self._fetch_with_cache(
            stock_code, "employee",
            FREE_ENDPOINTS["employee"],
            {"scode": stock_code, "state": "1"},
        )

    # ==================== 聚合查询 ====================

    def get_all(self, stock_code: str) -> dict:
        logger.info(f"{'='*60}")
        logger.info(f"巨潮资讯全量数据获取: {stock_code}")
        logger.info(f"{'='*60}")

        result = {
            "stock_code": stock_code,
            "timestamp": datetime.now().isoformat(),
            "company_info": [],
            "announcements": [],
            "management": [],
            "employee": [],
            "balance_sheet": [],
            "income_statement": [],
            "cash_flow": [],
            "financial_indicator": [],
            "top_shareholder": [],
            "shareholder_count": [],
        }

        fetchers = [
            ("company_info", lambda: self.get_company_info(stock_code)),
            ("announcements", lambda: self.get_announcements(stock_code)),
            ("management", lambda: self.get_management(stock_code)),
            ("employee", lambda: self.get_employee_info(stock_code)),
            ("balance_sheet", lambda: self.get_balance_sheet(stock_code)),
            ("income_statement", lambda: self.get_income_statement(stock_code)),
            ("cash_flow", lambda: self.get_cash_flow(stock_code)),
            ("financial_indicator", lambda: self.get_financial_indicators(stock_code)),
            ("top_shareholder", lambda: self.get_top_shareholders(stock_code)),
            ("shareholder_count", lambda: self.get_shareholder_count(stock_code)),
        ]

        for key, fetcher in fetchers:
            try:
                result[key] = fetcher()
            except Exception as e:
                logger.error(f"{key} 获取失败: {e}")
                result[key] = []

        return result


# ==================== 输出格式化 ====================


def _print_records(title: str, records: list[dict], max_rows: int = 10):
    print(f"\n{'─'*60}")
    print(f"  {title}  ({len(records)} 条记录)")
    print(f"{'─'*60}")
    if not records:
        print("  (无数据)")
        return
    for i, rec in enumerate(records[:max_rows]):
        # 取关键字段展示
        display_parts = []
        for key in ("SECCODE", "SECNAME", "ORGNAME", "F002V", "F001D", "ENDDATE",
                     "RDATE", "SHNAME", "HOLDPCT", "TOTALASSETS", "NETPROFIT",
                     "BASICEPS", "ROE", "STAFFNUM"):
            if key in rec and rec[key]:
                display_parts.append(f"{key}={rec[key]}")
        line = " | ".join(display_parts[:5]) if display_parts else json.dumps(rec, ensure_ascii=False)[:120]
        print(f"  [{i+1}] {line}")
    if len(records) > max_rows:
        print(f"  ... 还有 {len(records) - max_rows} 条")


def _print_all_result(result: dict):
    print()
    print("=" * 60)
    print(f"  巨潮资讯数据报告 — {result['stock_code']}")
    print(f"  时间: {result['timestamp']}")
    print("=" * 60)

    label_map = {
        "company_info": "公司基本信息",
        "announcements": "公告信息",
        "management": "管理人员",
        "employee": "员工情况",
        "balance_sheet": "资产负债表",
        "income_statement": "利润表",
        "cash_flow": "现金流量表",
        "financial_indicator": "财务指标",
        "top_shareholder": "十大股东",
        "shareholder_count": "股东户数",
    }

    total = 0
    for key, label in label_map.items():
        records = result.get(key, [])
        total += len(records)
        _print_records(label, records)

    print(f"\n{'='*60}")
    print(f"  合计: {total} 条记录")
    print(f"{'='*60}\n")


# ==================== CLI ====================


def main():
    parser = argparse.ArgumentParser(description="InvestMindPro 巨潮资讯数据提供者")
    parser.add_argument("--stock", type=str, required=True, help="股票代码 (如 600519)")
    parser.add_argument("--type", type=str, default="all",
                        choices=["all", "company_info", "announcement", "financial",
                                 "shareholder", "management", "employee"],
                        help="数据类型 (默认 all)")
    parser.add_argument("--subtype", type=str, default=None,
                        choices=["balance_sheet", "income_statement", "cash_flow",
                                 "financial_indicator"],
                        help="财务数据子类型")
    parser.add_argument("--sdate", type=str, default=None, help="开始日期 (YYYY-MM-DD)")
    parser.add_argument("--edate", type=str, default=None, help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--rdate", type=str, default=None, help="报告期 (YYYY-MM-DD)")
    args = parser.parse_args()

    provider = CninfoDataProvider()
    stock = args.stock

    if args.type == "all":
        result = provider.get_all(stock)
        _print_all_result(result)

    elif args.type == "company_info":
        records = provider.get_company_info(stock)
        _print_records("公司基本信息", records)

    elif args.type == "announcement":
        records = provider.get_announcements(stock, sdate=args.sdate, edate=args.edate)
        _print_records("公告信息", records)

    elif args.type == "financial":
        if args.subtype == "balance_sheet":
            records = provider.get_balance_sheet(stock, sdate=args.sdate, edate=args.edate)
            _print_records("资产负债表", records)
        elif args.subtype == "income_statement":
            records = provider.get_income_statement(stock, sdate=args.sdate, edate=args.edate)
            _print_records("利润表", records)
        elif args.subtype == "cash_flow":
            records = provider.get_cash_flow(stock, sdate=args.sdate, edate=args.edate)
            _print_records("现金流量表", records)
        elif args.subtype == "financial_indicator":
            records = provider.get_financial_indicators(stock, sdate=args.sdate, edate=args.edate)
            _print_records("财务指标", records)
        else:
            for sub, label, fn in [
                ("balance_sheet", "资产负债表", provider.get_balance_sheet),
                ("income_statement", "利润表", provider.get_income_statement),
                ("cash_flow", "现金流量表", provider.get_cash_flow),
                ("financial_indicator", "财务指标", provider.get_financial_indicators),
            ]:
                records = fn(stock, sdate=args.sdate, edate=args.edate)
                _print_records(label, records)

    elif args.type == "shareholder":
        records = provider.get_top_shareholders(stock, rdate=args.rdate)
        _print_records("十大股东", records)
        records = provider.get_shareholder_count(stock)
        _print_records("股东户数", records)

    elif args.type == "management":
        records = provider.get_management(stock)
        _print_records("管理人员", records)

    elif args.type == "employee":
        records = provider.get_employee_info(stock)
        _print_records("员工情况", records)


if __name__ == "__main__":
    main()
