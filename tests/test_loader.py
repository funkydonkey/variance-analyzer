"""Тесты для core.loader"""
import pytest
import pandas as pd
from pathlib import Path
from core.loader import (
    load_csv,
    load_excel,
    normalize_dataframe,
    dataframe_to_rows,
    load_report
)
from core.models import VarianceRow


@pytest.fixture
def sample_csv_file(tmp_path):
    """Создаёт временный CSV файл для тестов"""
    csv_content = """account,period,actual,budget
Revenue,2024-01,1000,800
COGS,2024-01,400,500
Rent,2024-01,1000,1000"""

    csv_file = tmp_path / "test_report.csv"
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def sample_csv_with_nan(tmp_path):
    """Создаёт CSV файл с NaN значениями"""
    csv_content = """account,period,actual,budget
Revenue,2024-01,1000,800
COGS,2024-01,,500
Rent,2024-01,1000,"""

    csv_file = tmp_path / "test_report_nan.csv"
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def sample_csv_with_duplicates(tmp_path):
    """Создаёт CSV файл с дубликатами"""
    csv_content = """account,period,actual,budget
Revenue,2024-01,1000,800
Revenue,2024-01,1200,800
COGS,2024-01,400,500"""

    csv_file = tmp_path / "test_report_dupes.csv"
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def invalid_csv_file(tmp_path):
    """Создаёт CSV файл с неправильными колонками"""
    csv_content = """name,date,value
Revenue,2024-01,1000"""

    csv_file = tmp_path / "invalid.csv"
    csv_file.write_text(csv_content)
    return csv_file


class TestLoadCsv:
    """Тесты для load_csv"""

    def test_load_csv_success(self, sample_csv_file):
        """Тест успешной загрузки CSV"""
        df = load_csv(sample_csv_file)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert list(df.columns) == ["account", "period", "actual", "budget"]

    def test_load_csv_file_not_found(self, tmp_path):
        """Тест FileNotFoundError когда файл не существует"""
        non_existent = tmp_path / "non_existent.csv"

        with pytest.raises(FileNotFoundError, match="File not fount"):
            load_csv(non_existent)

    def test_load_csv_missing_columns(self, invalid_csv_file):
        """Тест ValueError когда отсутствуют обязательные колонки"""
        with pytest.raises(ValueError, match="Missing mandatory columns"):
            load_csv(invalid_csv_file)


class TestLoadExcel:
    """Тесты для load_excel"""

    @pytest.fixture
    def sample_excel_file(self, tmp_path):
        """Создаёт временный Excel файл"""
        df = pd.DataFrame({
            "account": ["Revenue", "COGS"],
            "period": ["2024-01", "2024-01"],
            "actual": [1000, 400],
            "budget": [800, 500]
        })
        excel_file = tmp_path / "test_report.xlsx"
        df.to_excel(excel_file, index=False, sheet_name="Sheet1")
        return excel_file

    def test_load_excel_success(self, sample_excel_file):
        """Тест успешной загрузки Excel"""
        df = load_excel(sample_excel_file, sheet_name="Sheet1")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert set(df.columns) == {"account", "period", "actual", "budget"}

    def test_load_excel_file_not_found(self, tmp_path):
        """Тест FileNotFoundError когда файл не существует"""
        non_existent = tmp_path / "non_existent.xlsx"

        with pytest.raises(FileNotFoundError, match="File not fount"):
            load_excel(non_existent)


class TestNormalizeDataframe:
    """Тесты для normalize_dataframe"""

    def test_normalize_dataframe_success(self):
        """Тест успешной нормализации"""
        df = pd.DataFrame({
            "account": ["Revenue", "COGS", "Rent"],
            "period": ["2024-01", "2024-01", "2024-01"],
            "actual": [1000, 400, 1000],
            "budget": [800, 500, 1000]
        })

        normalized = normalize_dataframe(df)

        assert len(normalized) == 3
        assert normalized["actual"].dtype == float
        assert normalized["budget"].dtype == float

    def test_normalize_dataframe_removes_nan(self, sample_csv_with_nan):
        """Тест удаления строк с NaN"""
        df = pd.read_csv(sample_csv_with_nan)
        normalized = normalize_dataframe(df)

        # Должна остаться только 1 строка (Revenue)
        assert len(normalized) == 1
        assert normalized.iloc[0]["account"] == "Revenue"

    def test_normalize_dataframe_removes_duplicates(self, sample_csv_with_duplicates):
        """Тест удаления дубликатов"""
        df = pd.read_csv(sample_csv_with_duplicates)
        normalized = normalize_dataframe(df)

        # Должно остаться 2 строки (Revenue дубликат удалён)
        assert len(normalized) == 2

    def test_normalize_dataframe_missing_columns(self):
        """Тест ValueError при отсутствии колонок"""
        df = pd.DataFrame({
            "name": ["Revenue"],
            "date": ["2024-01"],
            "value": [1000]
        })

        with pytest.raises(ValueError, match="Missing mandatory columns"):
            normalize_dataframe(df)


class TestDataframeToRows:
    """Тесты для dataframe_to_rows"""

    def test_dataframe_to_rows_success(self):
        """Тест успешного преобразования DataFrame в VarianceRow"""
        df = pd.DataFrame({
            "account": ["Revenue", "COGS"],
            "period": ["2024-01", "2024-01"],
            "actual": [1000.0, 400.0],
            "budget": [800.0, 500.0]
        })

        rows = dataframe_to_rows(df)

        assert len(rows) == 2
        assert all(isinstance(row, VarianceRow) for row in rows)

        assert rows[0].account == "Revenue"
        assert rows[0].actual == 1000.0
        assert rows[0].absolute_variance is None

        assert rows[1].account == "COGS"
        assert rows[1].budget == 500.0

    def test_dataframe_to_rows_empty(self):
        """Тест с пустым DataFrame"""
        df = pd.DataFrame(columns=["account", "period", "actual", "budget"])

        rows = dataframe_to_rows(df)

        assert rows == []


class TestLoadReport:
    """Тесты для load_report (интеграционные)"""

    def test_load_report_csv(self, sample_csv_file):
        """Тест загрузки отчёта из CSV"""
        rows = load_report(sample_csv_file, file_type="csv")

        assert len(rows) == 3
        assert all(isinstance(row, VarianceRow) for row in rows)
        assert rows[0].account == "Revenue"
        assert rows[0].actual == 1000.0

    def test_load_report_xlsx(self, tmp_path):
        """Тест загрузки отчёта из XLSX"""
        df = pd.DataFrame({
            "account": ["Revenue", "COGS"],
            "period": ["2024-01", "2024-01"],
            "actual": [1000, 400],
            "budget": [800, 500]
        })
        excel_file = tmp_path / "test_report.xlsx"
        df.to_excel(excel_file, index=False, sheet_name="Sheet1")

        rows = load_report(excel_file, file_type="xlsx", sheet_name="Sheet1")

        assert len(rows) == 2
        assert all(isinstance(row, VarianceRow) for row in rows)

    def test_load_report_unsupported_type(self, sample_csv_file):
        """Тест ValueError для неподдерживаемого типа файла"""
        with pytest.raises(ValueError, match="Unsupported file type"):
            load_report(sample_csv_file, file_type="json")

    def test_load_report_removes_nan_and_duplicates(self, sample_csv_with_nan):
        """Тест что load_report удаляет NaN и дубликаты"""
        rows = load_report(sample_csv_with_nan, file_type="csv")

        assert len(rows) == 1
        assert rows[0].account == "Revenue"
