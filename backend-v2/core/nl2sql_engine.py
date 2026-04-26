"""
core/nl2sql_engine.py — NL2SQL Engine cho PACS++
UC15: Hỏi đáp tự nhiên → SQL → kết quả

Pipeline:
  Query → Router (STRUCTURED/SEMANTIC) → NL2SQL hoặc RAG → Answer

Schema context:
  patients(id, patient_id, full_name, birth_date, gender, phone, address)
  studies(id, patient_id, study_uid, modality, study_date, description, status, orthanc_id)
  diagnostic_reports(id, study_id, doctor_id, findings, conclusion, recommendation, report_date)
"""

import re
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, date

from database.connection import get_connection, release_connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# Schema cache — đọc từ DB thật, cache lại
_schema_cache = {"schema": None, "samples": None, "timestamp": None}


def _read_db_schema() -> str:
    """Đọc schema thật từ database (tables, columns, types, foreign keys).
    Cache 5 phút để không query liên tục."""
    import time
    now = time.time()

    # Cache 5 phút
    if _schema_cache["schema"] and _schema_cache["timestamp"] and (now - _schema_cache["timestamp"]) < 300:
        return _schema_cache["schema"], _schema_cache["samples"]

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # 1. Đọc tất cả tables + columns từ information_schema
        cursor.execute("""
            SELECT table_name, column_name, data_type, is_nullable,
                   column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN ('patients', 'studies', 'diagnostic_reports', 'users')
            ORDER BY table_name, ordinal_position
        """)
        columns = cursor.fetchall()

        # 2. Đọc foreign keys
        cursor.execute("""
            SELECT tc.table_name, kcu.column_name,
                   ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
              ON tc.constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
        """)
        fks = cursor.fetchall()

        # 3. Build schema text
        schema_lines = ["DATABASE SCHEMA (PostgreSQL):"]
        current_table = None
        for col in columns:
            if col["table_name"] != current_table:
                current_table = col["table_name"]
                schema_lines.append(f"\nTABLE {current_table}:")
            nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col["column_default"] else ""
            schema_lines.append(f"  - {col['column_name']} {col['data_type']} {nullable}{default}")

        if fks:
            schema_lines.append("\nFOREIGN KEYS:")
            for fk in fks:
                schema_lines.append(f"  - {fk['table_name']}.{fk['column_name']} → {fk['foreign_table']}.{fk['foreign_column']}")

        schema_text = "\n".join(schema_lines)

        # 4. Đọc sample data (giúp LLM hiểu values thực tế)
        samples = {}
        try:
            cursor.execute("SELECT DISTINCT modality FROM studies WHERE modality IS NOT NULL LIMIT 10")
            samples["modalities"] = [r["modality"] for r in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT status FROM studies WHERE status IS NOT NULL LIMIT 10")
            samples["statuses"] = [r["status"] for r in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT role FROM users WHERE role IS NOT NULL LIMIT 10")
            samples["roles"] = [r["role"] for r in cursor.fetchall()]

            cursor.execute("SELECT COUNT(*) as total FROM patients")
            samples["total_patients"] = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as total FROM studies")
            samples["total_studies"] = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as total FROM diagnostic_reports")
            samples["total_reports"] = cursor.fetchone()["total"]
        except Exception:
            pass

        sample_text = f"""
SAMPLE DATA (giá trị thực tế trong DB):
  - Modality values: {', '.join(samples.get('modalities', []))}
  - Status values: {', '.join(samples.get('statuses', []))}
  - User roles: {', '.join(samples.get('roles', []))}
  - Total patients: {samples.get('total_patients', '?')}
  - Total studies: {samples.get('total_studies', '?')}
  - Total reports: {samples.get('total_reports', '?')}"""

        # Cache
        _schema_cache["schema"] = schema_text
        _schema_cache["samples"] = sample_text
        _schema_cache["timestamp"] = now

        logger.info(f"[NL2SQL] DB schema loaded: {len(columns)} columns, {len(fks)} FKs")
        return schema_text, sample_text

    except Exception as e:
        logger.error(f"[NL2SQL] Failed to read DB schema: {e}")
        # Fallback tĩnh
        fallback = """DATABASE SCHEMA:
TABLE patients: id, patient_id VARCHAR, full_name VARCHAR, birth_date DATE, gender CHAR(1)
TABLE studies: id, patient_id INT FK→patients.id, modality VARCHAR, study_date DATE, description TEXT, status VARCHAR, orthanc_id VARCHAR
TABLE diagnostic_reports: id, study_id INT FK→studies.id, doctor_id INT FK→users.id, findings TEXT, conclusion TEXT, recommendation TEXT, report_date TIMESTAMP
TABLE users: id, username VARCHAR, full_name VARCHAR, role VARCHAR"""
        return fallback, ""
    finally:
        cursor.close()
        release_connection(conn)


# ============================================================
# 3. LLM-based NL2SQL — Ollama / Gemini (đọc schema DB thật)
# ============================================================

def llm_nl2sql(question: str) -> Optional[Dict]:
    """Dùng LLM để sinh SQL từ câu hỏi tự nhiên.
    LLM đọc schema thật từ DB trước khi sinh query."""

    # Đọc schema thật từ database
    schema_text, sample_text = _read_db_schema()

    prompt = f"""Bạn là chuyên gia SQL cho hệ thống PACS (Picture Archiving and Communication System) y tế.
Hãy chuyển đổi câu hỏi của người dùng thành câu SQL PostgreSQL chính xác.

{schema_text}
{sample_text}

COMMON JOINS:
  studies JOIN patients ON studies.patient_id = patients.id
  diagnostic_reports JOIN studies ON diagnostic_reports.study_id = studies.id
  diagnostic_reports JOIN users ON diagnostic_reports.doctor_id = users.id

QUY TẮC BẮT BUỘC:
1. Chỉ dùng SELECT (KHÔNG INSERT/UPDATE/DELETE/DROP)
2. LIMIT 20 nếu trả về danh sách
3. Dùng ILIKE cho tìm kiếm text tiếng Việt
4. JOIN bảng khi cần thông tin liên quan
5. Trả về CHỈ SQL thuần — không giải thích, không markdown

Câu hỏi: {question}

SQL:"""

    # Try Ollama first (local)
    try:
        import requests
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "gemma3:4b", "prompt": prompt, "stream": False},
            timeout=30
        )
        if resp.status_code == 200:
            sql = resp.json().get("response", "").strip()
            sql = _extract_sql(sql)
            if sql and _validate_sql(sql):
                logger.info(f"[NL2SQL] Ollama generated SQL: {sql[:80]}")
                return {'sql': sql, 'source': 'ollama'}
    except Exception as e:
        logger.warning(f"[NL2SQL] Ollama failed: {e}")

    # Fallback: Gemini (cloud)
    try:
        import google.generativeai as genai
        import os
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            resp = model.generate_content(prompt)
            sql = _extract_sql(resp.text)
            if sql and _validate_sql(sql):
                logger.info(f"[NL2SQL] Gemini generated SQL: {sql[:80]}")
                return {'sql': sql, 'source': 'gemini'}
    except Exception as e:
        logger.warning(f"[NL2SQL] Gemini failed: {e}")

    return None


def _extract_sql(text: str) -> str:
    """Trích xuất SQL từ output LLM (có thể có markdown ```sql ... ```)"""
    # Remove markdown code blocks
    match = re.search(r'```(?:sql)?\s*\n?(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Remove leading/trailing whitespace and semicolons
    text = text.strip().rstrip(';')
    # Take first statement only
    if ';' in text:
        text = text.split(';')[0]
    return text.strip()


def _validate_sql(sql: str) -> bool:
    """Validate SQL: chỉ cho phép SELECT"""
    sql_upper = sql.upper().strip()
    if not sql_upper.startswith('SELECT'):
        return False
    # Block dangerous keywords
    dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'TRUNCATE', 'CREATE', 'EXEC']
    for kw in dangerous:
        if kw in sql_upper:
            return False
    return True


# ============================================================
# 4. Execute SQL + Format Answer
# ============================================================

def execute_sql(sql: str, params: tuple = None) -> Dict:
    """Execute validated SQL with parameterized query and return results"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        rows = cursor.fetchall()
        # Convert to serializable format
        results = []
        for row in rows:
            d = {}
            for k, v in dict(row).items():
                if isinstance(v, (date, datetime)):
                    d[k] = v.isoformat()
                else:
                    d[k] = v
            results.append(d)
        return {'data': results, 'count': len(results)}
    except Exception as e:
        logger.error(f"[NL2SQL] SQL execution error: {e}")
        return {'error': str(e), 'data': [], 'count': 0}
    finally:
        cursor.close()
        release_connection(conn)


def generate_answer(question: str, intent: str, sql_result: Dict = None, rag_results: list = None) -> str:
    """Tạo câu trả lời text từ kết quả"""
    if intent == "STRUCTURED" and sql_result:
        if sql_result.get('error'):
            return f"Không thể truy vấn: {sql_result['error']}"

        data = sql_result.get('data', [])
        if not data:
            return "Không tìm thấy dữ liệu phù hợp."

        # Single count result
        if len(data) == 1 and 'total' in data[0]:
            return f"Kết quả: **{data[0]['total']}** ca."

        # List result
        return f"Tìm thấy **{len(data)}** kết quả."

    elif intent == "SEMANTIC" and rag_results:
        if not rag_results:
            return "Không tìm thấy báo cáo liên quan."
        return f"Tìm thấy **{len(rag_results)}** báo cáo liên quan."

    return "Không hiểu câu hỏi. Vui lòng thử lại."


# ============================================================
# 5. Main ask() function
# ============================================================

def ask(question: str) -> Dict[str, Any]:
    """
    Main entry point cho UC15.
    Input: câu hỏi tự nhiên
    Output: { intent, sql, source, data, answer, rag_results }
    """
    if not question or not question.strip():
        return {'intent': None, 'answer': 'Vui lòng nhập câu hỏi.'}

    question = question.strip()
    logger.info(f"[NL2SQL] Question: {question}")

    # Step 1: Classify bằng query_router (pattern 6805)
    from core.query_router import classify
    intent, confidence, debug_info = classify(question)
    logger.info(f"[NL2SQL] Intent: {intent} (conf={confidence:.2f})")

    result = {
        'intent': intent,
        'confidence': round(confidence, 4),
        'question': question,
        'sql': None,
        'source': None,
        'data': [],
        'answer': '',
        'rag_results': [],
        'router_debug': debug_info,
    }

    if intent == "PATIENT_LOOKUP":
        # Tìm kiếm theo tên bệnh nhân (chỉ match full_name + patient_id)
        from core.rag_engine import patient_search
        # Trích xuất tên (bỏ prefix "tìm", "bệnh nhân"...)
        name_query = re.sub(
            r'^(?:tìm|tim|benh nhan|bệnh nhân|tên|ten|hồ sơ|ho so)\s+',
            '', question.strip(), flags=re.IGNORECASE
        ).strip()
        patient_results = patient_search(name_query, limit=20)
        result['rag_results'] = patient_results
        result['source'] = 'patient_lookup'
        if patient_results:
            result['answer'] = f"Tìm thấy **{len(patient_results)}** kết quả cho bệnh nhân \"{name_query}\"."
        else:
            result['answer'] = f"Không tìm thấy bệnh nhân có tên \"{name_query}\"."

    elif intent == "STRUCTURED":
        # LLM đọc schema DB thật → sinh SQL
        nl2sql_result = llm_nl2sql(question)

        if nl2sql_result:
            result['sql'] = nl2sql_result['sql']
            result['source'] = nl2sql_result.get('source', 'unknown')

            # Execute SQL
            sql_result = execute_sql(nl2sql_result['sql'], nl2sql_result.get('params'))
            result['data'] = sql_result.get('data', [])
            result['answer'] = generate_answer(question, intent, sql_result=sql_result)
        else:
            result['answer'] = 'Không thể tạo truy vấn từ câu hỏi này. Hãy thử hỏi cách khác.'

    elif intent == "SEMANTIC":
        # RAG search
        from core.rag_engine import hybrid_search
        rag_results = hybrid_search(question, top_k=5)
        result['rag_results'] = rag_results
        result['answer'] = generate_answer(question, intent, rag_results=rag_results)

    elif intent == "HYBRID":
        # Cả SQL + RAG
        nl2sql_result = llm_nl2sql(question)

        sql_result = None
        if nl2sql_result:
            result['sql'] = nl2sql_result['sql']
            result['source'] = nl2sql_result.get('source', 'unknown')
            sql_result = execute_sql(nl2sql_result['sql'], nl2sql_result.get('params'))
            result['data'] = sql_result.get('data', [])

        from core.rag_engine import hybrid_search
        rag_results = hybrid_search(question, top_k=5)
        result['rag_results'] = rag_results
        result['answer'] = generate_answer(question, intent, sql_result=sql_result, rag_results=rag_results)

    return result

