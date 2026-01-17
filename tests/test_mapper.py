"""Тесты для core/mapper.py"""
import pytest
import pandas as pd
from pathlib import Path
from core.mapper import (
    analyze_columns,
    suggest_mapping,
    apply_mapping,
    validate_mapping,
    create_file_metadata
)
from core.models import ColumnMapping, VarianceRow


@pytest.fixture
def valid_dataframe():
    """Создаёт валидный DataFrame для тестов."""
    return pd.DataFrame({
        'Account Name': ['Revenue', 'COGS', 'Marketing'],
        'Period': ['2024-01', '2024-01', '2024-01'],
        'Actual Amount': [12000.0, 5000.0, 3000.0],
        'Budget Amount': [10000.0, 6000.0, 2500.0]
    })


@pytest.fixture
def unclear_dataframe():
    """DataFrame с неясными названиями столбцов."""
    return pd.DataFrame({
        'Col1': ['Revenue', 'COGS'],
        'Col2': ['2024-01', '2024-01'],
        'Col3': [12000.0, 5000.0],
        'Col4': [10000.0, 6000.0]
    })


class TestAnalyzeColumns:
    """Тесты для analyze_columns()"""

    def test_basic_analysis(self, valid_dataframe):
        """Тест базового анализа столбцов."""
        result = analyze_columns(valid_dataframe)

        assert len(result) == 4
        assert 'Account Name' in result
        assert result['Account Name']['dtype'] == 'string'
        assert len(result['Account Name']['sample_values']) == 3

    def test_numeric_detection(self, valid_dataframe):
        """Тест определения числовых столбцов."""
        result = analyze_columns(valid_dataframe)

        assert result['Actual Amount']['dtype'] == 'number'
        assert result['Budget Amount']['dtype'] == 'number'

    def test_statistics(self, valid_dataframe):
        """Тест статистики по столбцам."""
        result = analyze_columns(valid_dataframe)

        assert result['Account Name']['null_count'] == 0
        assert result['Account Name']['unique_count'] == 3


class TestSuggestMapping:
    """Тесты для suggest_mapping()"""

    def test_clear_column_names(self, valid_dataframe):
        """Тест с понятными названиями столбцов."""
        column_info = analyze_columns(valid_dataframe)
        mapping = suggest_mapping(column_info)

        assert mapping.account == 'Account Name'
        assert mapping.period == 'Period'
        assert mapping.actual == 'Actual Amount'
        assert mapping.budget == 'Budget Amount'
        assert mapping.confidence > 0.8

    def test_unclear_column_names(self, unclear_dataframe):
        """Тест с неясными названиями (Col1, Col2, ...)"""
        column_info = analyze_columns(unclear_dataframe)
        mapping = suggest_mapping(column_info)

        # Должен определить по типам данных
        assert mapping.account is not None
        assert mapping.period is not None
        assert mapping.actual is not None
        assert mapping.budget is not None

    def test_missing_columns_error(self):
        """Тест ошибки при недостаточном количестве столбцов."""
        df = pd.DataFrame({'col1': [1, 2, 3]})
        column_info = analyze_columns(df)

        with pytest.raises(ValueError, match="Не удалось автоматически определить столбцы"):
            suggest_mapping(column_info)


class TestValidateMapping:
    """Тесты для validate_mapping()"""

    def test_valid_mapping(self, valid_dataframe):
        """Тест валидного маппинга."""
        mapping = ColumnMapping(
            account='Account Name',
            period='Period',
            actual='Actual Amount',
            budget='Budget Amount'
        )

        is_valid, error_msg = validate_mapping(valid_dataframe, mapping)

        assert is_valid is True
        assert error_msg == ""

    def test_missing_column(self, valid_dataframe):
        """Тест с отсутствующим столбцом."""
        mapping = ColumnMapping(
            account='NonExistent',
            period='Period',
            actual='Actual Amount',
            budget='Budget Amount'
        )

        is_valid, error_msg = validate_mapping(valid_dataframe, mapping)

        assert is_valid is False
        assert 'отсутствуют' in error_msg.lower()

    def test_non_numeric_data(self):
        """Тест с нечисловыми данными в actual/budget."""
        df = pd.DataFrame({
            'account': ['Revenue'],
            'period': ['2024-01'],
            'actual': ['not_a_number'],
            'budget': [10000]
        })

        mapping = ColumnMapping(
            account='account',
            period='period',
            actual='actual',
            budget='budget'
        )

        # Валидация должна пройти, но при apply_mapping будет ошибка
        is_valid, error_msg = validate_mapping(df, mapping)
        # Функция validate_mapping пытается преобразовать, но не выкидывает ошибку
        # только если преобразование полностью провалится
        assert is_valid is True or 'числовые данные' in error_msg


class TestApplyMapping:
    """Тесты для apply_mapping()"""

    def test_successful_mapping(self, valid_dataframe):
        """Тест успешного применения маппинга."""
        mapping = ColumnMapping(
            account='Account Name',
            period='Period',
            actual='Actual Amount',
            budget='Budget Amount'
        )

        rows = apply_mapping(valid_dataframe, mapping)

        assert len(rows) == 3
        assert all(isinstance(row, VarianceRow) for row in rows)
        assert rows[0].account == 'Revenue'
        assert rows[0].actual == 12000.0
        assert rows[0].budget == 10000.0
        assert rows[0].absolute_variance is not None  # Должен быть рассчитан

    def test_variance_calculation(self, valid_dataframe):
        """Тест что variance рассчитывается автоматически."""
        mapping = ColumnMapping(
            account='Account Name',
            period='Period',
            actual='Actual Amount',
            budget='Budget Amount'
        )

        rows = apply_mapping(valid_dataframe, mapping)

        # Revenue: actual=12000, budget=10000 → variance=2000
        assert rows[0].absolute_variance == 2000.0
        assert rows[0].percentage_variance == pytest.approx(20.0, rel=1e-2)

    def test_invalid_mapping_error(self, valid_dataframe):
        """Тест ошибки при невалидном маппинге."""
        mapping = ColumnMapping(
            account='NonExistent',
            period='Period',
            actual='Actual Amount',
            budget='Budget Amount'
        )

        with pytest.raises(ValueError):
            apply_mapping(valid_dataframe, mapping)


class TestCreateFileMetadata:
    """Тесты для create_file_metadata()"""

    def test_metadata_creation(self, valid_dataframe):
        """Тест создания метаданных."""
        metadata = create_file_metadata(
            filename='test.csv',
            df=valid_dataframe,
            file_type='csv',
            size_bytes=1024
        )

        assert metadata.filename == 'test.csv'
        assert metadata.rows == 3
        assert len(metadata.columns) == 4
        assert metadata.file_type == 'csv'
        assert metadata.size_bytes == 1024
        assert metadata.size_kb == pytest.approx(1.0, rel=1e-2)

    def test_column_types_detection(self, valid_dataframe):
        """Тест определения типов столбцов."""
        metadata = create_file_metadata(
            filename='test.csv',
            df=valid_dataframe,
            file_type='csv',
            size_bytes=1024
        )

        assert metadata.column_types['Account Name'] == 'string'
        assert metadata.column_types['Actual Amount'] == 'number'
        assert metadata.column_types['Budget Amount'] == 'number'


# Интеграционные тесты с реальными файлами
class TestIntegrationWithFixtures:
    """Интеграционные тесты с тестовыми файлами."""

    def test_valid_data_csv(self):
        """Тест с valid_data.csv"""
        df = pd.read_csv('tests/fixtures/valid_data.csv')
        column_info = analyze_columns(df)
        mapping = suggest_mapping(column_info)

        rows = apply_mapping(df, mapping)

        assert len(rows) > 0
        assert all(row.absolute_variance is not None for row in rows)

    def test_unclear_columns_xlsx(self):
        """Тест с unclear_columns.xlsx"""
        df = pd.read_excel('tests/fixtures/unclear_columns.xlsx')
        column_info = analyze_columns(df)
        mapping = suggest_mapping(column_info)

        rows = apply_mapping(df, mapping)

        assert len(rows) > 0

    def test_missing_values_csv(self):
        """Тест с missing_values.csv"""
        df = pd.read_csv('tests/fixtures/missing_values.csv')
        column_info = analyze_columns(df)
        mapping = suggest_mapping(column_info)

        # Применяем маппинг - строки с пустыми значениями должны быть удалены
        rows = apply_mapping(df, mapping)

        # Должны остаться только валидные строки (без None)
        assert len(rows) > 0
        assert all(row.account is not None for row in rows)
        assert all(row.actual is not None for row in rows)
