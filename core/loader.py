from pathlib import Path
import pandas as pd
from core.models import VarianceRow
from typing import Optional, List

def load_csv(file_path: Path) -> pd.DataFrame:
     """Загружает CSV файл в DataFrame.

    Ожидаемый формат CSV:
        account,period,actual,budget
        Revenue,2024-01,1000,800
        COGS,2024-01,400,500

    Args:
        file_path: Путь к CSV файлу

    Returns:
        pandas DataFrame с колонками: account, period, actual, budget

    Raises:
        FileNotFoundError: Если файл не найден
        ValueError: Если отсутствуют обязательные колонки
    """
     
     if not file_path.exists():
          raise FileNotFoundError(f"File not fount: {file_path}")
     
     df = pd.read_csv(file_path)

     mandatory_columns = {"account", "period", "actual", "budget"}

     if not mandatory_columns.issubset(df.columns):
          raise ValueError(f"Missing mandatory columns: {mandatory_columns}")

     return df


def load_excel(file_path: Path, sheet_name: str = "Sheet1") -> pd.DataFrame:
    """Загружает XLSX файл в DataFrame.

    Args:
        file_path: Путь к XLSX файлу
        sheet_name: Название листа (по умолчанию "Sheet1")

    Returns:
        pandas DataFrame с колонками: account, period, actual, budget

    Raises:
        FileNotFoundError: Если файл не найден
        ValueError: Если отсутствуют обязательные колонки или лист не найден
    """

    if not file_path.exists():
          raise FileNotFoundError(f"File not fount: {file_path}")
     
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    mandatory_columns = {"account", "period", "actual", "budget"}

    if not mandatory_columns.issubset(df.columns):
          raise ValueError(f"Missing mandatory columns: {mandatory_columns}")

    return df


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Нормализует DataFrame к единому формату.

    Операции:
        1. Проверить наличие колонок: account, period, actual, budget
        2. Удалить строки с пустыми значениями (NaN)
        3. Привести actual и budget к float
        4. Убрать дубликаты по (account, period)

    Args:
        df: Исходный DataFrame

    Returns:
        Нормализованный DataFrame

    Raises:
        ValueError: Если отсутствуют обязательные колонки
    """
    mandatory_columns = {"account", "period", "actual", "budget"}

    if set(df.columns) != mandatory_columns:
          raise ValueError(f"Missing mandatory columns: {mandatory_columns}")

    # if not mandatory_columns.issubset(df.columns):
    #       raise ValueError(f"Missing mandatory columns: {mandatory_columns}")

    df = df.dropna(subset=mandatory_columns)
    df = df.drop_duplicates(subset=["account", "period"])

    df["actual"] = df["actual"].astype(float)
    df["budget"] = df["budget"].astype(float)

    return df


def dataframe_to_rows(df: pd.DataFrame) -> list[VarianceRow]:
    """Преобразует DataFrame в список VarianceRow.

    Args:
        df: Нормализованный DataFrame

    Returns:
        Список объектов VarianceRow (без рассчитанных variance)
    """
    rows = []

    for row in df.itertuples(index=False):
        variance_row = VarianceRow(
            account=row.account,
            period=row.period,
            actual=row.actual,
            budget=row.budget
        )
        rows.append(variance_row)

    return rows


def load_report(
          file_path: Path, 
          file_type: str = "csv", 
          sheet_name: str = "Sheet1") -> list[VarianceRow]:
    """Универсальная функция для загрузки отчёта.

    Комбинирует все шаги:
        1. Загрузка файла (CSV или XLSX)
        2. Нормализация
        3. Преобразование в VarianceRow

    Args:
        file_path: Путь к файлу
        file_type: "csv" или "xlsx"
        sheet_name: Название листа (для XLSX)

    Returns:
        Список VarianceRow

    Example:
        >>> rows = load_report(Path("data/report.csv"), file_type="csv")
        >>> len(rows)
        100
    """

    if file_type == "csv":
         df = load_csv(file_path)
    elif file_type.startswith("xls"):
         df = load_excel(
              file_path=file_path,
              sheet_name=sheet_name
         )
    else:
         raise ValueError(f"Unsupported file type: {file_type}")

    df = normalize_dataframe(df)

    rows = dataframe_to_rows(df)

    return rows