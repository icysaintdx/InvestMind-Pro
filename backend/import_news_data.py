#!/usr/bin/env python3
"""历史新闻数据导入 - 流式读取，低内存"""
import os, sys, time, sqlite3, zipfile, tempfile
from pathlib import Path
import openpyxl

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "InvestMindPro.db"
DATA_ROOT = PROJECT_ROOT.parent / "（03.17）中国上市公司财经新闻数据库（1994-2024年）"
BATCH = 5000

def safe_int(v):
    try: return int(v)
    except: return 0

def safe_str(v):
    return str(v).strip() if v is not None else None

def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")
    conn.execute("DROP TABLE IF EXISTS news_daily_sentiment")
    conn.execute("DROP TABLE IF EXISTS news_articles")
    conn.executescript("""
    CREATE TABLE news_daily_sentiment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_code TEXT NOT NULL, company_name TEXT, date TEXT NOT NULL,
        news_title_count INT DEFAULT 0, news_content_count INT DEFAULT 0,
        positive_all INT DEFAULT 0, neutral_all INT DEFAULT 0, negative_all INT DEFAULT 0,
        positive_original INT DEFAULT 0, neutral_original INT DEFAULT 0, negative_original INT DEFAULT 0,
        source TEXT DEFAULT 'online');
    CREATE INDEX idx_nds_code_date ON news_daily_sentiment(stock_code, date);
    CREATE INDEX idx_nds_date ON news_daily_sentiment(date);
    CREATE TABLE news_articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_code TEXT NOT NULL, company_name TEXT, industry TEXT, industry_code TEXT,
        news_id TEXT, report_time TEXT, media TEXT, media_area TEXT, source_media TEXT,
        sentiment INT DEFAULT 0, is_original INT DEFAULT 0, url TEXT,
        sentence_count INT DEFAULT 0, title_mentioned INT DEFAULT 0,
        code_sentence_count INT DEFAULT 0, code_content_count INT DEFAULT 0,
        company_count INT DEFAULT 0, all_code_sentence_count INT DEFAULT 0,
        all_code_content_count INT DEFAULT 0, source TEXT DEFAULT 'online');
    CREATE INDEX idx_na_code_time ON news_articles(stock_code, report_time);
    CREATE INDEX idx_na_time ON news_articles(report_time);
    """)
    conn.commit()
    return conn

def stream_xlsx_from_zip(zf, xlsx_name):
    """Extract xlsx to tmp, open read_only, yield rows, cleanup"""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        tmp.write(zf.read(xlsx_name))
        tmp_path = tmp.name
    try:
        wb = openpyxl.load_workbook(tmp_path, read_only=True, data_only=True)
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        header = next(rows, None)  # row 1: English headers
        next(rows, None)           # row 2: Chinese headers (skip)
        yield header, rows
        wb.close()
    finally:
        os.unlink(tmp_path)

def import_daily(conn, zip_path, src):
    if not os.path.exists(zip_path): return 0
    total = 0
    with zipfile.ZipFile(zip_path) as zf:
        xlsxs = sorted(f for f in zf.namelist() if f.endswith('.xlsx'))
        print(f"  📦 {Path(zip_path).name}: {len(xlsxs)} files")
        for xn in xlsxs:
            t0 = time.time()
            try:
                for header, rows in stream_xlsx_from_zip(zf, xn):
                    if not header: continue
                    h = {v: i for i, v in enumerate(header)}
                    batch = []
                    count = 0
                    for row in rows:
                        code = safe_str(row[h.get('Scode',0)])
                        if not code or len(code) < 4: continue
                        code = code.zfill(6)
                        dt = safe_str(row[h.get('Date',2)])
                        if not dt: continue
                        batch.append((code, safe_str(row[h.get('Coname',1)]), dt[:10],
                            safe_int(row[h.get('Newsnum_Title',3)]), safe_int(row[h.get('Newsnum_Cont',4)]),
                            safe_int(row[h.get('Posnews_All',5)]), safe_int(row[h.get('Neunews_All',6)]),
                            safe_int(row[h.get('Negnews_All',7)]), safe_int(row[h.get('Posnews_Ori',8)]),
                            safe_int(row[h.get('Neunews_Ori',9)]), safe_int(row[h.get('Negnews_Ori',10)]), src))
                        count += 1
                        if len(batch) >= BATCH:
                            conn.executemany("INSERT INTO news_daily_sentiment(stock_code,company_name,date,news_title_count,news_content_count,positive_all,neutral_all,negative_all,positive_original,neutral_original,negative_original,source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", batch)
                            conn.commit(); batch = []
                    if batch:
                        conn.executemany("INSERT INTO news_daily_sentiment(stock_code,company_name,date,news_title_count,news_content_count,positive_all,neutral_all,negative_all,positive_original,neutral_original,negative_original,source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", batch)
                        conn.commit()
                    total += count
                    print(f"    ✅ {xn.split('/')[0]}: {count:,} rows ({time.time()-t0:.1f}s)")
            except Exception as e:
                print(f"    ❌ {xn}: {e}")
    return total

def import_articles(conn, zip_path, src):
    if not os.path.exists(zip_path): return 0
    total = 0
    SQL = "INSERT INTO news_articles(stock_code,company_name,industry,industry_code,news_id,report_time,media,media_area,source_media,sentiment,is_original,url,sentence_count,title_mentioned,code_sentence_count,code_content_count,company_count,all_code_sentence_count,all_code_content_count,source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
    with zipfile.ZipFile(zip_path) as zf:
        xlsxs = sorted(f for f in zf.namelist() if f.endswith('.xlsx'))
        print(f"  📦 {Path(zip_path).name}: {len(xlsxs)} files")
        for xn in xlsxs:
            t0 = time.time()
            try:
                for header, rows in stream_xlsx_from_zip(zf, xn):
                    if not header: continue
                    h = {v: i for i, v in enumerate(header)}
                    batch = []; count = 0
                    for row in rows:
                        code = safe_str(row[h.get('Scode',0)])
                        if not code or len(code) < 4: continue
                        code = code.zfill(6)
                        orig = 1 if safe_str(row[h.get('Orirep_Dum',10)]) == '是' else 0
                        rt = safe_str(row[h.get('Reptime',5)])
                        batch.append((code, safe_str(row[h.get('Coname',1)]),
                            safe_str(row[h.get('Industry',2)]), safe_str(row[h.get('Indcode',3)]),
                            safe_str(row[h.get('Newsid',4)]), rt[:19] if rt else None,
                            safe_str(row[h.get('Repmedia',6)]), safe_str(row[h.get('Mediarea',7)]),
                            safe_str(row[h.get('Sourcemed',8)]), safe_int(row[h.get('Newsemot',9)]),
                            orig, safe_str(row[h.get('URL',11)]),
                            safe_int(row[h.get('senten_Num',12)]), safe_int(row[h.get('titlementioned',13)]),
                            safe_int(row[h.get('codesentNum',14)]), safe_int(row[h.get('codecontentNum',15)]),
                            safe_int(row[h.get('companyNum',16)]), safe_int(row[h.get('allcodesentNum',17)]),
                            safe_int(row[h.get('allcodecontentNum',18)]), src))
                        count += 1
                        if len(batch) >= BATCH:
                            conn.executemany(SQL, batch); conn.commit(); batch = []
                    if batch:
                        conn.executemany(SQL, batch); conn.commit()
                    total += count
                    print(f"    ✅ {xn.split('/')[0]}: {count:,} rows ({time.time()-t0:.1f}s)")
            except Exception as e:
                print(f"    ❌ {xn}: {e}")
    return total

def main():
    print("="*60)
    print("📰 历史新闻数据导入（流式，低内存）")
    print(f"DB: {DB_PATH}")
    print("="*60)
    conn = init_db()
    t0 = time.time()
    gt = 0
    print("\n📊 Phase 1: 量化统计")
    gt += import_daily(conn, str(DATA_ROOT/"网络财经新闻库"/"网络新闻量化统计（按自然日）.zip"), 'online')
    gt += import_daily(conn, str(DATA_ROOT/"报刊财经新闻库"/"报刊财经新闻量化统计.zip"), 'newspaper')
    print("\n📰 Phase 2: 新闻基本信息")
    gt += import_articles(conn, str(DATA_ROOT/"网络财经新闻库"/"网络财经新闻基本信息.zip"), 'online')
    gt += import_articles(conn, str(DATA_ROOT/"报刊财经新闻库"/"报刊财经新闻基本信息.zip"), 'newspaper')
    d = conn.execute("SELECT COUNT(*) FROM news_daily_sentiment").fetchone()[0]
    a = conn.execute("SELECT COUNT(*) FROM news_articles").fetchone()[0]
    conn.close()
    print(f"\n{'='*60}")
    print(f"✅ 完成！{(time.time()-t0)/60:.1f}分钟 | daily:{d:,} | articles:{a:,} | total:{gt:,}")

if __name__ == "__main__":
    import traceback
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
