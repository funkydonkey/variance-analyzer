"""Тесты для core.calculator"""
import pytest
from core.models import VarianceRow
from core.calculator import (
    calculate_variance,
    calculate_variance_for_row,
    calculate_variance_bulk
)


class TestCalculateVariance:
    """Тесты для calculate_variance"""

    def test_positive_variance(self):
        """Тест положительного отклонения"""
        abs_var, pct_var = calculate_variance(actual=100, budget=80)
        assert abs_var == 20.0
        assert pct_var == 25.0

    def test_negative_variance(self):
        """Тест отрицательного отклонения"""
        abs_var, pct_var = calculate_variance(actual=50, budget=100)
        assert abs_var == -50.0
        assert pct_var == -50.0

    def test_zero_variance(self):
        """Тест нулевого отклонения"""
        abs_var, pct_var = calculate_variance(actual=100, budget=100)
        assert abs_var == 0.0
        assert pct_var == 0.0

    def test_budget_zero(self):
        """Тест деления на ноль (budget=0)"""
        abs_var, pct_var = calculate_variance(actual=100, budget=0)
        assert abs_var == 100.0
        assert pct_var is None

    def test_budget_zero_and_actual_zero(self):
        """Тест когда и budget, и actual равны 0"""
        abs_var, pct_var = calculate_variance(actual=0, budget=0)
        assert abs_var == 0.0
        assert pct_var is None

    def test_negative_budget_and_actual(self):
        """Тест с отрицательными budget и actual"""
        abs_var, pct_var = calculate_variance(actual=-100, budget=-80)
        assert abs_var == -20.0
        assert pct_var == 25.0  # (-100 - (-80)) / (-80) * 100 = -20 / -80 * 100 = 25%

    def test_actual_zero_budget_nonzero(self):
        """Тест когда actual=0, но budget != 0"""
        abs_var, pct_var = calculate_variance(actual=0, budget=100)
        assert abs_var == -100.0
        assert pct_var == -100.0  # Это валидно! -100%


class TestCalculateVarianceForRow:
    """Тесты для calculate_variance_for_row"""

    def test_calculate_variance_for_row(self):
        """Тест расчёта variance для одной строки"""
        row = VarianceRow(
            account="Revenue",
            period="2024-01",
            actual=1000,
            budget=800
        )

        result = calculate_variance_for_row(row)

        assert result is row  # Должна вернуться та же строка
        assert row.absolute_variance == 200.0
        assert row.percentage_variance == 25.0

    def test_calculate_variance_for_row_with_zero_budget(self):
        """Тест расчёта variance при budget=0"""
        row = VarianceRow(
            account="Revenue",
            period="2024-01",
            actual=100,
            budget=0
        )

        result = calculate_variance_for_row(row)

        assert row.absolute_variance == 100.0
        assert row.percentage_variance is None

    def test_calculate_variance_for_row_negative_values(self):
        """Тест расчёта variance с отрицательными значениями"""
        row = VarianceRow(
            account="COGS",
            period="2024-01",
            actual=-500,
            budget=-400
        )

        result = calculate_variance_for_row(row)

        assert row.absolute_variance == -100.0
        assert row.percentage_variance == 25.0


class TestCalculateVarianceBulk:
    """Тесты для calculate_variance_bulk"""

    def test_calculate_variance_bulk(self):
        """Тест bulk-расчёта variance"""
        rows = [
            VarianceRow("Revenue", "2024-01", 1000, 800),
            VarianceRow("COGS", "2024-01", 400, 500),
            VarianceRow("Rent", "2024-01", 1000, 1000)
        ]

        result = calculate_variance_bulk(rows)

        assert result is rows  # Должен вернуться тот же список
        assert len(result) == 3

        assert rows[0].absolute_variance == 200.0
        assert rows[0].percentage_variance == 25.0

        assert rows[1].absolute_variance == -100.0
        assert rows[1].percentage_variance == -20.0

        assert rows[2].absolute_variance == 0.0
        assert rows[2].percentage_variance == 0.0

    def test_calculate_variance_bulk_empty_list(self):
        """Тест bulk-расчёта для пустого списка"""
        rows = []
        result = calculate_variance_bulk(rows)
        assert result == []

    def test_calculate_variance_bulk_with_zero_budgets(self):
        """Тест bulk-расчёта с нулевыми бюджетами"""
        rows = [
            VarianceRow("Revenue", "2024-01", 100, 0),
            VarianceRow("COGS", "2024-01", 200, 100)
        ]

        result = calculate_variance_bulk(rows)

        assert rows[0].absolute_variance == 100.0
        assert rows[0].percentage_variance is None

        assert rows[1].absolute_variance == 100.0
        assert rows[1].percentage_variance == 100.0
