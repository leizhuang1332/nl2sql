import pytest
from src.security.sensitive_filter import SensitiveDataFilter
from src.security.injection_detector import SQLInjectionDetector, InjectionIndicator


class TestSensitiveDataFilter:
    def test_sensitive_filter_init(self):
        filter = SensitiveDataFilter()
        assert filter is not None
        assert filter.mask_char == "*"
        assert filter.visible_chars == 0

    def test_sensitive_filter_init_with_params(self):
        filter = SensitiveDataFilter(
            sensitive_fields=["password", "secret"],
            mask_char="X",
            visible_chars=2
        )
        assert filter.mask_char == "X"
        assert filter.visible_chars == 2
        assert "password" in filter.sensitive_fields

    def test_is_sensitive_column_password(self):
        filter = SensitiveDataFilter()
        assert filter.is_sensitive_column("password") is True
        assert filter.is_sensitive_column("password_hash") is True

    def test_is_sensitive_column_credit_card(self):
        filter = SensitiveDataFilter()
        assert filter.is_sensitive_column("credit_card") is True
        assert filter.is_sensitive_column("card_number") is True
        assert filter.is_sensitive_column("cvv") is True

    def test_is_sensitive_column_ssn(self):
        filter = SensitiveDataFilter()
        assert filter.is_sensitive_column("ssn") is True
        assert filter.is_sensitive_column("social_security") is True

    def test_is_sensitive_column_not_sensitive(self):
        filter = SensitiveDataFilter()
        assert filter.is_sensitive_column("name") is False
        assert filter.is_sensitive_column("age") is False
        assert filter.is_sensitive_column("address") is True  # address is in default patterns

    def test_is_sensitive_column_case_insensitive(self):
        filter = SensitiveDataFilter()
        assert filter.is_sensitive_column("PASSWORD") is True
        assert filter.is_sensitive_column("Password") is True

    def test_mask_value_default(self):
        filter = SensitiveDataFilter()
        result = filter._mask_value("123456")
        assert result == "******"

    def test_mask_value_with_visible_chars(self):
        filter = SensitiveDataFilter(visible_chars=2)
        result = filter._mask_value("123456")
        assert result == "****56"

    def test_mask_value_short_value(self):
        filter = SensitiveDataFilter(visible_chars=4)
        result = filter._mask_value("123")
        assert result == "123"

    def test_mask_value_none(self):
        filter = SensitiveDataFilter()
        result = filter._mask_value(None)
        assert result == ""

    def test_mask_value_custom_char(self):
        filter = SensitiveDataFilter(mask_char="X")
        result = filter._mask_value("123456")
        assert result == "XXXXXX"

    def test_filter_result_no_sensitive_columns(self):
        filter = SensitiveDataFilter()
        result = [{"name": "John", "age": 30}]
        filtered = filter.filter_result(result, ["name", "age"])
        assert filtered[0]["name"] == "John"
        assert filtered[0]["age"] == 30

    def test_filter_result_with_sensitive_columns(self):
        filter = SensitiveDataFilter()
        result = [{"name": "John", "password": "secret123"}]
        filtered = filter.filter_result(result, ["name", "password"])
        assert filtered[0]["name"] == "John"
        assert filtered[0]["password"] == "*********"

    def test_filter_result_multiple_rows(self):
        filter = SensitiveDataFilter()
        result = [
            {"name": "John", "password": "secret1"},
            {"name": "Jane", "password": "secret2"}
        ]
        filtered = filter.filter_result(result, ["name", "password"])
        assert filtered[0]["password"] == "*******"
        assert filtered[1]["password"] == "*******"

    def test_add_sensitive_pattern(self):
        filter = SensitiveDataFilter()
        filter.add_sensitive_pattern("custom_field")
        assert filter.is_sensitive_column("custom_field") is True

    def test_remove_sensitive_pattern(self):
        filter = SensitiveDataFilter()
        filter.remove_sensitive_pattern("password")
        assert filter.is_sensitive_column("password") is False

    def test_get_sensitive_patterns(self):
        filter = SensitiveDataFilter()
        patterns = filter.get_sensitive_patterns()
        assert isinstance(patterns, set)
        assert "password" in patterns

    def test_filter_columns(self):
        filter = SensitiveDataFilter()
        columns = ["name", "password", "email", "token"]
        filtered = filter.filter_columns(columns)
        assert "password" in filtered
        assert "token" in filtered
        assert "name" not in filtered

    def test_filter_row(self):
        filter = SensitiveDataFilter()
        row = {"name": "John", "password": "secret", "age": 30}
        filtered = filter.filter_row(row)
        assert filtered["name"] == "John"
        assert filtered["password"] == "******"
        assert filtered["age"] == 30


class TestSQLInjectionDetector:
    def test_injection_detector_init(self):
        detector = SQLInjectionDetector()
        assert detector is not None

    def test_injection_detector_safe_query(self):
        detector = SQLInjectionDetector()
        is_safe, indicators = detector.detect("SELECT * FROM users")
        assert is_safe is True
        assert len(indicators) == 0

    def test_injection_detector_union_select(self):
        detector = SQLInjectionDetector()
        is_safe, indicators = detector.detect("SELECT * FROM users UNION SELECT * FROM admins")
        assert is_safe is False
        assert len(indicators) > 0

    def test_injection_detector_union_all_select(self):
        detector = SQLInjectionDetector()
        is_safe, indicators = detector.detect("SELECT name FROM users UNION ALL SELECT admin_name FROM admins")
        assert is_safe is False

    def test_injection_detector_comment_injection(self):
        detector = SQLInjectionDetector()
        is_safe, indicators = detector.detect("SELECT * FROM users -- comment")
        assert is_safe is False

    def test_injection_detector_hash_comment(self):
        detector = SQLInjectionDetector()
        is_safe, indicators = detector.detect("SELECT * FROM users # comment")
        assert is_safe is False

    def test_injection_detector_or_1_equals_1(self):
        detector = SQLInjectionDetector()
        is_safe, indicators = detector.detect("SELECT * FROM users WHERE id = 1 OR 1=1")
        assert is_safe is False

    def test_injection_detector_or_true(self):
        detector = SQLInjectionDetector()
        is_safe, indicators = detector.detect("SELECT * FROM users WHERE name = 'test' OR 'a'='a'")
        assert is_safe is False

    def test_injection_detector_sleep(self):
        detector = SQLInjectionDetector()
        is_safe, indicators = detector.detect("SELECT * FROM users WHERE id = 1 AND SLEEP(5)")
        assert is_safe is False

    def test_injection_detector_waitfor_delay(self):
        detector = SQLInjectionDetector()
        is_safe, indicators = detector.detect("SELECT * FROM users WHERE id = 1; WAITFOR DELAY '00:00:05'")
        assert is_safe is False

    def test_injection_detector_xml_injection_extractvalue(self):
        detector = SQLInjectionDetector()
        is_safe, indicators = detector.detect("SELECT EXTRACTVALUE(1, CONCAT(0x7e, version()))")
        assert is_safe is False

    def test_injection_detector_xml_injection_updatexml(self):
        detector = SQLInjectionDetector()
        is_safe, indicators = detector.detect("SELECT UPDATEXML(1, CONCAT(0x7e, version()), 1)")
        assert is_safe is False

    def test_injection_detector_boolean_blind(self):
        detector = SQLInjectionDetector()
        is_safe, indicators = detector.detect("SELECT * FROM users WHERE id = 1 AND 1=1")
        assert is_safe is False

    def test_is_safe_method(self):
        detector = SQLInjectionDetector()
        assert detector.is_safe("SELECT * FROM users") is True
        assert detector.is_safe("SELECT * FROM users UNION SELECT * FROM admins") is False

    def test_get_indicators_method(self):
        detector = SQLInjectionDetector()
        indicators = detector.get_indicators("SELECT * FROM users UNION SELECT admin FROM admins")
        assert len(indicators) > 0
        assert all(isinstance(ind, InjectionIndicator) for ind in indicators)

    def test_add_pattern(self):
        detector = SQLInjectionDetector()
        detector.add_pattern(r"custom_pattern", "HIGH", "自定义注入")
        assert detector.is_safe("SELECT * FROM users WHERE custom_pattern") is False

    def test_get_high_severity_indicators(self):
        detector = SQLInjectionDetector()
        indicators = detector.get_high_severity_indicators("SELECT * FROM users UNION SELECT * FROM admins")
        assert len(indicators) > 0
        assert all(ind.severity == "HIGH" for ind in indicators)

    def test_has_high_severity(self):
        detector = SQLInjectionDetector()
        assert detector.has_high_severity("SELECT * FROM users") is False
        assert detector.has_high_severity("SELECT * FROM users UNION SELECT * FROM admins") is True
