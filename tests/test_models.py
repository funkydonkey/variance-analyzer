"""Тесты для core.models"""
import pytest
from core.models import VarianceRow, AnalysisParams, VarianceReport


class TestVarianceRow:
    """Тесты для VarianceRow"""

    def test_create_variance_row(self):
        """Тест создания VarianceRow"""
        row = VarianceRow(
            account="Revenue",
            period="2024-01",
            actual=1000.0,
            budget=800.0
        )
        assert row.account == "Revenue"
        assert row.period == "2024-01"
        assert row.actual == 1000.0
        assert row.budget == 800.0
        assert row.absolute_variance is None
        assert row.percentage_variance is None

    def test_has_variance_calculated_false_when_empty(self):
        """Тест has_variance_calculated когда variance не рассчитаны"""
        row = VarianceRow(
            account="Revenue",
            period="2024-01",
            actual=1000.0,
            budget=800.0
        )
        assert row.has_variance_calculated() is False

    def test_has_variance_calculated_true_when_filled(self):
        """Тест has_variance_calculated когда variance рассчитаны"""
        row = VarianceRow(
            account="Revenue",
            period="2024-01",
            actual=1000.0,
            budget=800.0,
            absolute_variance=200.0,
            percentage_variance=25.0
        )
        assert row.has_variance_calculated() is True

    def test_has_variance_calculated_false_when_only_absolute(self):
        """Тест has_variance_calculated когда заполнен только absolute"""
        row = VarianceRow(
            account="Revenue",
            period="2024-01",
            actual=1000.0,
            budget=800.0,
            absolute_variance=200.0,
            percentage_variance=None
        )
        assert row.has_variance_calculated() is False


class TestAnalysisParams:
    """Тесты для AnalysisParams"""

    def test_create_analysis_params_defaults(self):
        """Тест создания AnalysisParams с дефолтными значениями"""
        params = AnalysisParams()
        assert params.min_absolute_threshold == 0.0
        assert params.min_percentage_threshold == 0.0
        assert params.periods is None
        assert params.accounts is None

    def test_create_analysis_params_custom(self):
        """Тест создания AnalysisParams с кастомными значениями"""
        params = AnalysisParams(
            min_absolute_threshold=100.0,
            min_percentage_threshold=10.0,
            periods=["2024-01", "2024-02"],
            accounts=["Revenue", "COGS"]
        )
        assert params.min_absolute_threshold == 100.0
        assert params.min_percentage_threshold == 10.0
        assert params.periods == ["2024-01", "2024-02"]
        assert params.accounts == ["Revenue", "COGS"]


class TestVarianceReport:
    """Тесты для VarianceReport"""

    def test_create_variance_report(self):
        """Тест создания VarianceReport"""
        rows = [
            VarianceRow("Revenue", "2024-01", 1000, 800, 200, 25.0),
            VarianceRow("COGS", "2024-01", 400, 500, -100, -20.0)
        ]
        params = AnalysisParams()
        report = VarianceReport(
            rows=rows,
            params=params,
            total_rows=10,
            filtered_rows=2
        )
        assert len(report.rows) == 2
        assert report.total_rows == 10
        assert report.filtered_rows == 2

    def test_get_top_variances_by_absolute(self):
        """Тест get_top_variances с сортировкой по absolute"""
        rows = [
            VarianceRow("Revenue", "2024-01", 1000, 800, 200, 25.0),
            VarianceRow("COGS", "2024-01", 400, 500, -100, -20.0),
            VarianceRow("Sales", "2024-01", 500, 100, 400, 400.0),
            VarianceRow("Rent", "2024-01", 1000, 950, 50, 5.26)
        ]
        params = AnalysisParams()
        report = VarianceReport(rows, params, 4, 4)

        top3 = report.get_top_variances(n=3, by="absolute")

        assert len(top3) == 3
        assert top3[0].account == "Sales"  # |400| - самое большое
        assert top3[1].account == "Revenue"  # |200|
        assert top3[2].account == "COGS"  # |100|

    def test_get_top_variances_by_percentage(self):
        """Тест get_top_variances с сортировкой по percentage"""
        rows = [
            VarianceRow("Revenue", "2024-01", 1000, 800, 200, 25.0),
            VarianceRow("COGS", "2024-01", 400, 500, -100, -20.0),
            VarianceRow("Sales", "2024-01", 500, 100, 400, 400.0),
            VarianceRow("Rent", "2024-01", 1000, 950, 50, 5.26)
        ]
        params = AnalysisParams()
        report = VarianceReport(rows, params, 4, 4)

        top2 = report.get_top_variances(n=2, by="percentage")

        assert len(top2) == 2
        assert top2[0].account == "Sales"  # |400%| - самое большое
        assert top2[1].account == "Revenue"  # |25%|

    def test_get_top_variances_invalid_by_param(self):
        """Тест get_top_variances с неправильным параметром by"""
        rows = [VarianceRow("Revenue", "2024-01", 1000, 800, 200, 25.0)]
        params = AnalysisParams()
        report = VarianceReport(rows, params, 1, 1)

        with pytest.raises(ValueError, match="Не задан критерий сортировки"):
            report.get_top_variances(n=1, by="invalid")

    def test_get_top_variances_returns_exactly_n(self):
        """Тест что get_top_variances возвращает ровно n элементов"""
        rows = [
            VarianceRow(f"Account{i}", "2024-01", 1000, 800, 200, 25.0)
            for i in range(10)
        ]
        params = AnalysisParams()
        report = VarianceReport(rows, params, 10, 10)

        top5 = report.get_top_variances(n=5)
        assert len(top5) == 5  # Должно быть РОВНО 5, не 4!
