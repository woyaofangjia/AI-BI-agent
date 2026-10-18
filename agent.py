import os
import re
import json
import sqlite3
from flask import Flask, request, jsonify, send_file
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response

DB_PATH = "sales.db"

SCHEMA = """
表名: sales
字段说明:
- date: 日期，格式 YYYY-MM-DD，例如 '2026-03-15'
- channel: 销售渠道，可选值: 'DTC', 'Amazon', 'TikTok', 'Store'
- category: 商品品类，可选值: 'Blind Box', 'Plush', 'Action Figure', 'Accessories'
- traffic: 流量/访客数
- orders: 订单数
- sales: 销售额（元）
- cost: 成本（元）

重要映射:
- "渠道"或"平台"对应 channel 字段
- "品类""类别""商品类型"对应 category 字段

数据日期范围: 2026-01-01 至 2026-06-29。数据中的最大日期是 2026-06-29，因此"上个月"指 2026-05-01 至 2026-05-31，"最近一个月"指 2026-05-30 至 2026-06-29。请基于这个锚点理解所有时间表达。
"""

client = None
if os.getenv("ZHIPU_API_KEY"):
    client = OpenAI(
        api_key=os.getenv("ZHIPU_API_KEY"),
        base_url=os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
    )

def llm_generate_sql(question: str) -> str:
    """调用大模型将中文问题转为 SQLite SQL"""
    if not client:
        return None
    prompt = f"""你是一个 SQLite 数据分析助手。请根据用户问题生成一条合法的 SQLite SELECT 查询语句。

数据库表结构:
表名: sales
字段:
- date: 日期，格式 YYYY-MM-DD
- channel: 销售渠道，可选值: 'DTC', 'Amazon', 'TikTok', 'Store'
- category: 商品品类，可选值: 'Blind Box', 'Plush', 'Action Figure', 'Accessories'
- traffic: 流量/访客数
- orders: 订单数
- sales: 销售额（元）
- cost: 成本（元）

数据日期范围: 2026-01-01 至 2026-06-29。数据中的最大日期是 2026-06-29。

要求:
1. 只返回 SQL，不要任何解释、markdown 标记或代码块符号。
2. 只能使用 SELECT，禁止 INSERT/UPDATE/DELETE/DROP 等。
3. 日期过滤使用 date 字段，格式为 'YYYY-MM-DD'。
4. "上个月"指 2026-05-01 至 2026-05-31。
5. 如果问题模糊，给出最合理的聚合查询。
6. 优先使用聚合函数（SUM, COUNT, AVG）和 GROUP BY，避免返回大量明细行。
7. GROUP BY 分组时，SELECT 中必须包含分组字段名。

示例:
- "各品类销售额对比" → SELECT category, SUM(sales) as total_sales FROM sales GROUP BY category ORDER BY total_sales DESC
- "各渠道销售额对比" → SELECT channel, SUM(sales) as total_sales FROM sales GROUP BY channel ORDER BY total_sales DESC
- "TikTok上个月卖了多少钱" → SELECT SUM(sales) as total_sales FROM sales WHERE channel='TikTok' AND date BETWEEN '2026-05-01' AND '2026-05-31'
- "Blind Box 总销售额" → SELECT SUM(sales) as total_sales FROM sales WHERE category='Blind Box'

用户问题: {question}
SQL:"""
    try:
        resp = client.chat.completions.create(
            model=os.getenv("ZHIPU_MODEL", "glm-4-flash"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        sql = resp.choices[0].message.content.strip()
        sql = re.sub(r"^```(?:sql)?\s*|\s*```$", "", sql, flags=re.IGNORECASE)
        return sql
    except Exception as e:
        print(f"[LLM 调用失败] {e}")
        return None

def correct_sql(sql: str, question: str) -> str:
    """校正 LLM 生成的 SQL 中明显的字段混淆"""
    q = question.lower()
    has_category = "品类" in q or "类别" in q or "商品类型" in q
    has_channel = "渠道" in q or "平台" in q

    if has_category and "GROUP BY channel" in sql and "GROUP BY category" not in sql:
        sql = sql.replace("GROUP BY channel", "GROUP BY category")
        sql = sql.replace("SELECT channel,", "SELECT category,")
    elif has_channel and "GROUP BY category" in sql and "GROUP BY channel" not in sql:
        sql = sql.replace("GROUP BY category", "GROUP BY channel")
        sql = sql.replace("SELECT category,", "SELECT channel,")

    return sql

def fallback_sql(question: str) -> str:
    """本地规则兜底，处理常见查询模式"""
    q = question.lower()
    if "tiktok" in q and ("上个月" in q or "9月" in q or "九月" in q):
        return "SELECT SUM(sales) as total_sales FROM sales WHERE channel='TikTok' AND date BETWEEN '2026-05-01' AND '2026-05-31'"
    if "各渠道" in q or "渠道对比" in q or "渠道销售" in q:
        return "SELECT channel, SUM(sales) as total_sales, SUM(orders) as total_orders FROM sales GROUP BY channel ORDER BY total_sales DESC"
    if "品类" in q and ("对比" in q or "排名" in q or "销售额" in q):
        return "SELECT category, SUM(sales) as total_sales FROM sales GROUP BY category ORDER BY total_sales DESC"
    if "品类" in q and ("趋势" in q or "走势" in q):
        return "SELECT date, category, SUM(sales) as daily_sales FROM sales GROUP BY date, category ORDER BY date"
    if "趋势" in q or "走势" in q:
        return "SELECT date, SUM(sales) as daily_sales FROM sales GROUP BY date ORDER BY date"
    if "blind box" in q:
        return "SELECT SUM(sales) as total_sales FROM sales WHERE category='Blind Box'"
    if "plush" in q:
        return "SELECT SUM(sales) as total_sales FROM sales WHERE category='Plush'"
    if "action figure" in q:
        return "SELECT SUM(sales) as total_sales FROM sales WHERE category='Action Figure'"
    if "accessories" in q:
        return "SELECT SUM(sales) as total_sales FROM sales WHERE category='Accessories'"
    return "SELECT channel, category, SUM(sales) as total_sales, SUM(orders) as total_orders FROM sales GROUP BY channel, category ORDER BY total_sales DESC LIMIT 20"

def run_query(sql: str):
    if not re.match(r"^\s*SELECT\s", sql, re.IGNORECASE):
        raise ValueError("仅允许 SELECT 查询")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql)
    rows = [dict(r) for r in cur.fetchall()]
    cols = [d[0] for d in cur.description] if cur.description else []
    conn.close()
    return {"columns": cols, "rows": rows}

@app.route("/ask", methods=["POST"])
def ask():
    question = request.json.get("question", "").strip()
    if not question:
        return jsonify({"error": "问题不能为空"}), 400

    sql = llm_generate_sql(question)
    if sql:
        sql = correct_sql(sql, question)
    else:
        sql = fallback_sql(question)

    try:
        result = run_query(sql)
        return jsonify({
            "question": question,
            "sql": sql,
            "columns": result["columns"],
            "rows": result["rows"]
        })
    except Exception as e:
        return jsonify({"question": question, "sql": sql, "error": str(e)}), 500

@app.route("/")
def index():
    return send_file("index.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
