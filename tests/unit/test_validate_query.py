"""
Unit tests for validate_query.py - SQL query validation and safety checks.
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

from validate_query import QueryValidator, check_batch_size


class TestQueryValidatorInit:
    """Test QueryValidator initialization."""

    def test_default_strict_false(self):
        validator = QueryValidator()
        assert validator.strict is False

    def test_explicit_strict_true(self):
        validator = QueryValidator(strict=True)
        assert validator.strict is True

    def test_initial_warnings_empty(self):
        validator = QueryValidator()
        assert validator.warnings == []

    def test_initial_errors_empty(self):
        validator = QueryValidator()
        assert validator.errors == []


class TestDetectWriteOperation:
    """Test _detect_write_operation method."""

    def test_select_is_not_write(self):
        validator = QueryValidator()
        assert validator._detect_write_operation("SELECT * FROM users") is False

    def test_insert_is_write(self):
        validator = QueryValidator()
        assert validator._detect_write_operation("INSERT INTO users VALUES (1)") is True

    def test_insert_capitalized_is_write(self):
        validator = QueryValidator()
        assert validator._detect_write_operation("INSERT INTO users VALUES (1)") is True

    def test_update_is_write(self):
        validator = QueryValidator()
        assert validator._detect_write_operation("UPDATE users SET name = 'test'") is True

    def test_delete_from_is_write(self):
        validator = QueryValidator()
        assert validator._detect_write_operation("DELETE FROM users WHERE id = 1") is True

    def test_delete_is_write(self):
        validator = QueryValidator()
        assert validator._detect_write_operation("DELETE FROM users") is True

    def test_truncate_is_write(self):
        validator = QueryValidator()
        assert validator._detect_write_operation("TRUNCATE TABLE users") is True

    def test_drop_table_is_write(self):
        validator = QueryValidator()
        assert validator._detect_write_operation("DROP TABLE users") is True

    def test_drop_database_is_write(self):
        validator = QueryValidator()
        assert validator._detect_write_operation("DROP DATABASE mydb") is True

    def test_alter_table_is_write(self):
        validator = QueryValidator()
        assert validator._detect_write_operation("ALTER TABLE users ADD COLUMN age INT") is True

    def test_create_is_write(self):
        validator = QueryValidator()
        assert validator._detect_write_operation("CREATE TABLE test (id INT)") is True

    def test_grant_is_write(self):
        validator = QueryValidator()
        assert validator._detect_write_operation("GRANT SELECT ON users TO analyst") is True

    def test_revoke_is_write(self):
        validator = QueryValidator()
        assert validator._detect_write_operation("REVOKE INSERT ON users FROM intern") is True

    def test_cte_with_insert_not_detected_greedy_regex(self):
        validator = QueryValidator()
        query = "WITH new_users AS (INSERT INTO users VALUES (1)) SELECT * FROM users"
        assert validator._detect_write_operation(query) is False

    def test_cte_with_update_not_detected_greedy_regex(self):
        validator = QueryValidator()
        query = "WITH updated AS (UPDATE users SET active = true) SELECT * FROM users"
        assert validator._detect_write_operation(query) is False

    def test_cte_with_delete_not_detected_greedy_regex(self):
        validator = QueryValidator()
        query = "WITH deleted AS (DELETE FROM users WHERE active = false) SELECT * FROM users"
        assert validator._detect_write_operation(query) is False

    def test_cte_select_not_write(self):
        validator = QueryValidator()
        assert validator._detect_write_operation("WITH data AS (SELECT 1) SELECT * FROM data") is False

    def test_case_insensitive(self):
        validator = QueryValidator()
        assert validator._detect_write_operation("select * from users") is False
        assert validator._detect_write_operation("INSERT into users values (1)") is True

    def test_whitespace_variations(self):
        validator = QueryValidator()
        assert validator._detect_write_operation("  SELECT * FROM users") is False
        assert validator._detect_write_operation("INSERT  INTO  users VALUES (1)") is True


class TestCheckDangerousPatterns:
    """Test _check_dangerous_patterns method."""

    def test_drop_after_semicolon_warning(self):
        validator = QueryValidator(strict=False)
        validator._check_dangerous_patterns("SELECT 1; DROP TABLE users")
        assert any("DROP after semicolon" in w for w in validator.warnings)

    def test_delete_after_semicolon_warning(self):
        validator = QueryValidator(strict=False)
        validator._check_dangerous_patterns("SELECT 1; DELETE FROM users")
        assert any("DELETE after semicolon" in w for w in validator.warnings)

    def test_comment_injection_warning(self):
        validator = QueryValidator(strict=False)
        validator._check_dangerous_patterns("SELECT * FROM users --")
        assert any("Comment injection" in w for w in validator.warnings)

    def test_block_comment_warning(self):
        validator = QueryValidator(strict=False)
        validator._check_dangerous_patterns("SELECT * /* comment */ FROM users")
        assert any("Block comment" in w for w in validator.warnings)

    def test_union_select_warning(self):
        validator = QueryValidator(strict=False)
        validator._check_dangerous_patterns("SELECT * FROM users UNION SELECT * FROM admins")
        assert any("UNION SELECT" in w for w in validator.warnings)

    def test_sleep_function_warning(self):
        validator = QueryValidator(strict=False)
        validator._check_dangerous_patterns("SELECT SLEEP(5)")
        assert any("SLEEP function" in w for w in validator.warnings)

    def test_benchmark_function_warning(self):
        validator = QueryValidator(strict=False)
        validator._check_dangerous_patterns("SELECT BENCHMARK(1000000, MD5('test'))")
        assert any("BENCHMARK function" in w for w in validator.warnings)

    def test_strict_mode_converts_to_error(self):
        validator = QueryValidator(strict=True)
        validator._check_dangerous_patterns("SELECT SLEEP(5)")
        assert any("SLEEP function" in e for e in validator.errors)
        assert len(validator.warnings) == 0

    def test_no_dangerous_patterns(self):
        validator = QueryValidator(strict=False)
        validator._check_dangerous_patterns("SELECT * FROM users WHERE id = 1")
        assert len(validator.warnings) == 0
        assert len(validator.errors) == 0

    def test_multiple_dangerous_patterns(self):
        validator = QueryValidator(strict=False)
        validator._check_dangerous_patterns("SELECT SLEEP(5); DROP TABLE users")
        assert len(validator.warnings) == 2


class TestCheckCommonMistakes:
    """Test _check_common_mistakes method."""

    def test_select_star_without_where(self):
        validator = QueryValidator()
        validator._check_common_mistakes("SELECT * FROM users")
        assert "Missing WHERE clause on SELECT *" in validator.warnings

    def test_equals_null_comparison(self):
        validator = QueryValidator()
        validator._check_common_mistakes("SELECT * FROM users WHERE name = NULL")
        assert "Use IS NULL instead of = NULL" in validator.warnings

    def test_no_mistake_with_where_clause(self):
        validator = QueryValidator()
        validator._check_common_mistakes("SELECT * FROM users WHERE id = 1")
        assert len(validator.warnings) == 0

    def test_no_mistake_with_is_null(self):
        validator = QueryValidator()
        validator._check_common_mistakes("SELECT * FROM users WHERE name IS NULL")
        assert len(validator.warnings) == 0

    def test_case_insensitive_mistakes(self):
        validator = QueryValidator()
        validator._check_common_mistakes("select * from users")
        assert "Missing WHERE clause on SELECT *" in validator.warnings


class TestCheckStructure:
    """Test _check_structure method."""

    def test_unmatched_parentheses_error(self):
        validator = QueryValidator()
        validator._check_structure("SELECT * FROM users WHERE (id = 1")
        assert any("Unmatched parentheses" in err for err in validator.errors)

    def test_unmatched_single_quotes_error(self):
        validator = QueryValidator()
        validator._check_structure("SELECT * FROM users WHERE name = 'test")
        assert "Syntax: Unmatched single quotes" in validator.errors

    def test_valid_parentheses_no_error(self):
        validator = QueryValidator()
        validator._check_structure("SELECT COUNT(*) FROM (SELECT id FROM users) t")
        assert len(validator.errors) == 0

    def test_valid_quotes_no_error(self):
        validator = QueryValidator()
        validator._check_structure("SELECT * FROM users WHERE name = 'test'")
        assert len(validator.errors) == 0

    def test_escaped_quotes_no_error(self):
        validator = QueryValidator()
        validator._check_structure("SELECT * FROM users WHERE name = 'O\\'Brien'")
        assert len(validator.errors) == 0


class TestClassifyQuery:
    """Test _classify_query method."""

    def test_select_classification(self):
        validator = QueryValidator()
        assert validator._classify_query("SELECT * FROM users") == "SELECT"

    def test_insert_classification(self):
        validator = QueryValidator()
        assert validator._classify_query("INSERT INTO users VALUES (1)") == "INSERT"

    def test_update_classification(self):
        validator = QueryValidator()
        assert validator._classify_query("UPDATE users SET name = 'test'") == "UPDATE"

    def test_delete_classification(self):
        validator = QueryValidator()
        assert validator._classify_query("DELETE FROM users") == "DELETE"

    def test_create_classification(self):
        validator = QueryValidator()
        assert validator._classify_query("CREATE TABLE test (id INT)") == "CREATE"

    def test_drop_classification(self):
        validator = QueryValidator()
        assert validator._classify_query("DROP TABLE users") == "DROP"

    def test_alter_classification(self):
        validator = QueryValidator()
        assert validator._classify_query("ALTER TABLE users ADD COLUMN age") == "ALTER"

    def test_cte_classification(self):
        validator = QueryValidator()
        assert validator._classify_query("WITH data AS (SELECT 1) SELECT * FROM data") == "CTE"

    def test_other_classification(self):
        validator = QueryValidator()
        assert validator._classify_query("SHOW TABLES") == "OTHER"

    def test_leading_whitespace(self):
        validator = QueryValidator()
        assert validator._classify_query("   SELECT * FROM users") == "SELECT"

    def test_case_insensitive(self):
        validator = QueryValidator()
        assert validator._classify_query("select * from users") == "SELECT"
        assert validator._classify_query("SELECT * FROM users") == "SELECT"


class TestGetSummary:
    """Test get_summary method."""

    def test_valid_query_summary(self):
        validator = QueryValidator()
        result = validator.validate("SELECT * FROM users WHERE id = 1")
        summary = validator.get_summary(result)
        assert "Query Type: SELECT" in summary
        assert "Write Operation: No" in summary
        assert "Valid: ✓" in summary
        assert "ERRORS:" not in summary

    def test_invalid_query_summary(self):
        validator = QueryValidator()
        result = validator.validate("SELECT * FROM users WHERE (id = 1")
        summary = validator.get_summary(result)
        assert "Valid: ✗" in summary
        assert "ERRORS:" in summary

    def test_write_operation_summary(self):
        validator = QueryValidator()
        result = validator.validate("INSERT INTO users VALUES (1)")
        summary = validator.get_summary(result)
        assert "Write Operation: Yes" in summary

    def test_warnings_in_summary(self):
        validator = QueryValidator()
        result = validator.validate("SELECT * FROM users")
        summary = validator.get_summary(result)
        assert "WARNINGS:" in summary

    def test_empty_warnings_no_warnings_section(self):
        validator = QueryValidator()
        result = validator.validate("SELECT id FROM users WHERE id = 1")
        summary = validator.get_summary(result)
        assert "WARNINGS:" not in summary


class TestValidate:
    """Test the main validate method."""

    def test_valid_select_query(self):
        validator = QueryValidator()
        result = validator.validate("SELECT id, name FROM users WHERE active = true")
        assert result["is_valid"] is True
        assert result["is_write"] is False
        assert result["query_type"] == "SELECT"
        assert len(result["errors"]) == 0

    def test_valid_insert_query(self):
        validator = QueryValidator()
        result = validator.validate("INSERT INTO users (name) VALUES ('test')")
        assert result["is_valid"] is True
        assert result["is_write"] is True
        assert result["query_type"] == "INSERT"

    def test_dangerous_query_not_valid(self):
        validator = QueryValidator(strict=True)
        result = validator.validate("SELECT SLEEP(10)")
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

    def test_strict_mode_affects_dangerous(self):
        validator_strict = QueryValidator(strict=True)
        result_strict = validator_strict.validate("SELECT SLEEP(10)")
        assert result_strict["is_valid"] is False

    def test_non_strict_mode_allows_dangerous(self):
        validator_non_strict = QueryValidator(strict=False)
        result_non_strict = validator_non_strict.validate("SELECT SLEEP(10)")
        assert result_non_strict["is_valid"] is True
        assert len(result_non_strict["warnings"]) > 0


class TestCheckBatchSize:
    """Test check_batch_size function."""

    def test_read_operation_not_batch(self):
        result = check_batch_size("SELECT * FROM users", 1000)
        assert result["is_batch"] is False

    def test_small_write_not_batch(self):
        result = check_batch_size("UPDATE users SET active = true", 500)
        assert result["is_batch"] is False

    def test_large_write_is_batch(self):
        result = check_batch_size("UPDATE users SET active = true", 1500)
        assert result["is_batch"] is True
        assert result["affected_rows"] == 1500
        assert result["threshold"] == 1000
        assert "warning" in result
        assert "suggestion" in result

    def test_delete_all_is_batch(self):
        result = check_batch_size("DELETE FROM users", 2000)
        assert result["is_batch"] is True
        assert result["affected_rows"] == 2000

    def test_custom_threshold(self):
        result = check_batch_size("DELETE FROM users", 500, threshold=400)
        assert result["is_batch"] is True
        assert result["threshold"] == 400

    def test_exact_threshold_not_batch(self):
        result = check_batch_size("DELETE FROM users", 1000)
        assert result["is_batch"] is False

    def test_zero_rows_not_batch(self):
        result = check_batch_size("DELETE FROM users", 0)
        assert result["is_batch"] is False


class TestQueryValidatorEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_query(self):
        validator = QueryValidator()
        result = validator.validate("")
        assert result["is_write"] is False
        assert result["query_type"] == "OTHER"

    def test_whitespace_only_query(self):
        validator = QueryValidator()
        result = validator.validate("   ")
        assert result["is_write"] is False
        assert result["query_type"] == "OTHER"

    def test_multiple_semicolons(self):
        validator = QueryValidator()
        result = validator.validate("SELECT 1; SELECT 2; DROP TABLE users")
        assert any("DROP after semicolon" in w for w in result["warnings"])

    def test_nested_comments(self):
        validator = QueryValidator()
        result = validator.validate("SELECT /* outer /* inner */ */ * FROM users")
        assert any("Block comment" in w for w in result["warnings"])

    def test_case_variations_in_dangerous(self):
        validator = QueryValidator()
        validator._check_dangerous_patterns("select sleep(5)")
        assert len(validator.warnings) == 1

    def test_whitespace_variations_in_mistakes(self):
        validator = QueryValidator()
        validator._check_common_mistakes("SELECT  *  FROM  users")
        assert "Missing WHERE clause on SELECT *" in validator.warnings


class TestValidateQueryCLIAdditional:
    """Additional tests for CLI coverage."""

    def test_get_summary_with_both_errors_and_warnings(self):
        validator = QueryValidator(strict=True)
        result = validator.validate("SELECT SLEEP(5)")
        assert len(result["errors"]) > 0
        assert len(result["warnings"]) == 0
        summary = validator.get_summary(result)
        assert "ERRORS:" in summary

    def test_get_summary_with_only_errors(self):
        validator = QueryValidator(strict=True)
        result = validator.validate("SELECT SLEEP(5)")
        assert len(result["errors"]) > 0
        summary = validator.get_summary(result)
        assert "ERRORS:" in summary
        assert "WARNINGS:" not in summary

    def test_get_summary_with_only_warnings(self):
        validator = QueryValidator(strict=False)
        result = validator.validate("SELECT * FROM users")
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) > 0
        summary = validator.get_summary(result)
        assert "ERRORS:" not in summary
        assert "WARNINGS:" in summary

    def test_validate_with_cte_query(self):
        validator = QueryValidator()
        result = validator.validate("WITH data AS (SELECT 1) SELECT * FROM data")
        assert result["query_type"] == "CTE"
        assert result["is_write"] is False

    def test_validate_with_multiple_warnings(self):
        validator = QueryValidator(strict=False)
        result = validator.validate("SELECT SLEEP(5); DROP TABLE users")
        assert len(result["warnings"]) >= 2

    def test_validate_classifies_unknown_query(self):
        validator = QueryValidator()
        result = validator.validate("EXPLAIN SELECT 1")
        assert result["query_type"] == "OTHER"

    def test_validate_handles_unicode_in_query(self):
        validator = QueryValidator()
        result = validator.validate("SELECT * FROM users WHERE name = 'José'")
        assert result["is_valid"] is True

    def test_batch_check_with_zero_rows(self):
        result = check_batch_size("DELETE FROM users", 0)
        assert result["is_batch"] is False
        assert result["affected_rows"] == 0

    def test_batch_check_read_operation(self):
        result = check_batch_size("SELECT * FROM users", 5000)
        assert result["is_batch"] is False


class TestValidateQueryMain:
    """Tests for the main() function in validate_query.py"""

    def test_main_with_valid_query(self, capsys):
        import sys
        from validate_query import main as validate_main
        original_argv = sys.argv
        sys.argv = ['validate_query.py', '--query', 'SELECT * FROM users WHERE id = 1']
        try:
            result = validate_main()
            assert result == 0
        finally:
            sys.argv = original_argv

    def test_main_with_strict_mode(self, capsys):
        import sys
        from validate_query import main as validate_main
        original_argv = sys.argv
        sys.argv = ['validate_query.py', '--query', 'SELECT SLEEP(5)', '--strict']
        try:
            result = validate_main()
            assert result == 1
        finally:
            sys.argv = original_argv

    def test_main_with_batch_check(self, capsys):
        import sys
        from validate_query import main as validate_main
        original_argv = sys.argv
        sys.argv = ['validate_query.py', '--query', 'DELETE FROM users', '--check-batch', '--estimated-rows', '2000']
        try:
            result = validate_main()
            assert result == 0
        finally:
            sys.argv = original_argv