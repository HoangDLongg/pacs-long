"""
tests/test_nl2sql_security.py — Test bảo mật NL2SQL
Kiểm tra SQL validator chặn đúng các truy vấn nguy hiểm
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.nl2sql_engine import _validate_sql, _extract_sql


class TestValidateSQL:
    """Test _validate_sql() — chặn SQL injection & data leak"""

    # ==================== PASS — SQL hợp lệ ====================
    def test_simple_select(self):
        assert _validate_sql("SELECT COUNT(*) FROM studies") is True

    def test_select_with_join(self):
        sql = "SELECT p.full_name, s.modality FROM studies s JOIN patients p ON s.patient_id = p.id"
        assert _validate_sql(sql) is True

    def test_select_with_where(self):
        sql = "SELECT * FROM studies WHERE status = 'PENDING' LIMIT 20"
        assert _validate_sql(sql) is True

    def test_select_with_ilike(self):
        sql = "SELECT * FROM patients WHERE full_name ILIKE '%Nguyen%'"
        assert _validate_sql(sql) is True

    def test_select_aggregate(self):
        sql = "SELECT modality, COUNT(*) as total FROM studies GROUP BY modality"
        assert _validate_sql(sql) is True

    def test_select_diagnostic_reports(self):
        sql = "SELECT findings, conclusion FROM diagnostic_reports LIMIT 10"
        assert _validate_sql(sql) is True

    # ==================== BLOCK — DML/DDL ====================
    def test_block_drop(self):
        assert _validate_sql("DROP TABLE users") is False

    def test_block_delete(self):
        assert _validate_sql("DELETE FROM patients WHERE id = 1") is False

    def test_block_insert(self):
        assert _validate_sql("INSERT INTO users (username) VALUES ('hacker')") is False

    def test_block_update(self):
        assert _validate_sql("UPDATE users SET role = 'admin' WHERE id = 5") is False

    def test_block_alter(self):
        assert _validate_sql("ALTER TABLE users ADD COLUMN hack TEXT") is False

    def test_block_truncate(self):
        assert _validate_sql("TRUNCATE patients") is False

    def test_block_grant(self):
        assert _validate_sql("GRANT ALL ON users TO public") is False

    # ==================== BLOCK — Sensitive tables ====================
    def test_block_users_table(self):
        """CRITICAL: Không cho truy cập bảng users (có password_hash)"""
        assert _validate_sql("SELECT * FROM users") is False

    def test_block_users_join(self):
        sql = "SELECT u.password_hash FROM diagnostic_reports r JOIN users u ON r.doctor_id = u.id"
        assert _validate_sql(sql) is False

    def test_block_refresh_tokens(self):
        """CRITICAL: Không cho truy cập bảng refresh_tokens"""
        assert _validate_sql("SELECT * FROM refresh_tokens") is False

    def test_block_users_in_subquery(self):
        sql = "SELECT * FROM studies WHERE patient_id IN (SELECT linked_patient_id FROM users)"
        assert _validate_sql(sql) is False

    # ==================== BLOCK — Sensitive columns ====================
    def test_block_password_hash_column(self):
        sql = "SELECT password_hash FROM some_view"
        assert _validate_sql(sql) is False

    def test_block_token_hash_column(self):
        sql = "SELECT token_hash FROM some_table"
        assert _validate_sql(sql) is False

    def test_block_embedding_column(self):
        sql = "SELECT embedding FROM diagnostic_reports"
        assert _validate_sql(sql) is False

    # ==================== BLOCK — System catalog ====================
    def test_block_information_schema(self):
        sql = "SELECT * FROM information_schema.columns"
        assert _validate_sql(sql) is False

    def test_block_pg_catalog(self):
        sql = "SELECT * FROM pg_catalog.pg_tables"
        assert _validate_sql(sql) is False

    def test_block_pg_stat(self):
        sql = "SELECT * FROM pg_stat_activity"
        assert _validate_sql(sql) is False

    # ==================== BLOCK — Not SELECT ====================
    def test_block_non_select(self):
        assert _validate_sql("EXPLAIN SELECT * FROM studies") is False

    def test_block_empty(self):
        assert _validate_sql("") is False


class TestExtractSQL:
    """Test _extract_sql() — trích SQL từ LLM output"""

    def test_plain_sql(self):
        assert _extract_sql("SELECT * FROM studies") == "SELECT * FROM studies"

    def test_markdown_code_block(self):
        text = "```sql\nSELECT COUNT(*) FROM studies\n```"
        assert _extract_sql(text) == "SELECT COUNT(*) FROM studies"

    def test_with_explanation(self):
        text = "Here is the SQL:\n```sql\nSELECT * FROM patients LIMIT 10\n```\nThis query..."
        assert _extract_sql(text) == "SELECT * FROM patients LIMIT 10"

    def test_strip_semicolons(self):
        assert _extract_sql("SELECT * FROM studies;") == "SELECT * FROM studies"

    def test_multiple_statements_takes_first(self):
        text = "SELECT 1; DROP TABLE users"
        result = _extract_sql(text)
        assert "DROP" not in result

    def test_markdown_no_lang(self):
        text = "```\nSELECT * FROM studies\n```"
        assert _extract_sql(text) == "SELECT * FROM studies"
