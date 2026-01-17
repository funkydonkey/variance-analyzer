"""Модуль для анализа и маппинга столбцов загруженных файлов."""

import pandas as pd
import re
from typing import Dict, Any, List, Tuple
from core.models import ColumnMapping, VarianceRow, FileMetadata
from core.calculator import calculate_variance_for_row


def analyze_columns(df: pd.DataFrame) -> Dict[str, Any]:
    """Анализирует столбцы DataFrame для определения их типов и характеристик.

    Args:
        df: Исходный DataFrame

    Returns:
        Словарь с информацией о каждом столбце:
        {
            "column_name": {
                "dtype": "string" | "number" | "date",
                "sample_values": [...],  # первые 5 значений
                "null_count": int,
                "unique_count": int
            }
        }
    """
    analysis = {}

    for col in df.columns:
        # Определяем тип данных
        dtype_str = str(df[col].dtype)
        if dtype_str.startswith('int') or dtype_str.startswith('float'):
            data_type = "number"
        elif dtype_str.startswith('datetime'):
            data_type = "date"
        else:
            data_type = "string"

        # Получаем примеры значений (первые 5)
        sample_values = df[col].head(5).tolist()

        # Статистика
        null_count = int(df[col].isnull().sum())
        unique_count = int(df[col].nunique())

        analysis[col] = {
            "dtype": data_type,
            "sample_values": sample_values,
            "null_count": null_count,
            "unique_count": unique_count
        }

    return analysis


def suggest_mapping(column_info: Dict[str, Any]) -> ColumnMapping:
    """Предлагает маппинг столбцов на основе эвристики.

    Ищет ключевые слова в названиях столбцов:
    - account: account, статья, item, category, name
    - period: period, date, month, период, дата
    - actual: actual, фактический, fact, real
    - budget: budget, бюджет, plan

    Args:
        column_info: Результат analyze_columns()

    Returns:
        ColumnMapping с предложенным маппингом

    Raises:
        ValueError: Если не удалось найти необходимые столбцы
    """
    columns = list(column_info.keys())

    # Ключевые слова для каждого типа
    account_keywords = ['account', 'статья', 'item', 'category', 'name', 'счет', 'наименование']
    period_keywords = ['period', 'date', 'month', 'период', 'дата', 'месяц', 'quarter', 'year']
    actual_keywords = ['actual', 'фактический', 'fact', 'real', 'факт']
    budget_keywords = ['budget', 'бюджет', 'plan', 'planned', 'план']

    def find_column(keywords: List[str]) -> str:
        """Ищет столбец по ключевым словам."""
        for col in columns:
            col_lower = col.lower()
            for keyword in keywords:
                if keyword in col_lower:
                    return col
        return None

    # Пробуем найти столбцы
    account = find_column(account_keywords)
    period = find_column(period_keywords)
    actual = find_column(actual_keywords)
    budget = find_column(budget_keywords)

    # Если не нашли по ключевым словам, пробуем по типам данных
    if not account:
        # Ищем string столбец с высокой уникальностью
        string_cols = [col for col, info in column_info.items()
                       if info['dtype'] == 'string']
        if string_cols:
            account = string_cols[0]

    if not period:
        # Ищем date или string столбец
        date_cols = [col for col, info in column_info.items()
                     if info['dtype'] in ['date', 'string']]
        if date_cols:
            period = date_cols[0] if date_cols[0] != account else (date_cols[1] if len(date_cols) > 1 else None)

    if not actual:
        # Ищем числовой столбец
        number_cols = [col for col, info in column_info.items()
                       if info['dtype'] == 'number']
        if number_cols:
            actual = number_cols[0]

    if not budget:
        # Ищем второй числовой столбец
        number_cols = [col for col, info in column_info.items()
                       if info['dtype'] == 'number' and col != actual]
        if number_cols:
            budget = number_cols[0]

    # Проверяем что нашли все обязательные столбцы
    if not all([account, period, actual, budget]):
        missing = []
        if not account:
            missing.append('account')
        if not period:
            missing.append('period')
        if not actual:
            missing.append('actual')
        if not budget:
            missing.append('budget')
        raise ValueError(f"Не удалось автоматически определить столбцы: {', '.join(missing)}")

    # Определяем confidence на основе найденных ключевых слов
    confidence = 0.8  # базовый уровень
    if any(kw in account.lower() for kw in account_keywords):
        confidence += 0.05
    if any(kw in period.lower() for kw in period_keywords):
        confidence += 0.05
    if any(kw in actual.lower() for kw in actual_keywords):
        confidence += 0.05
    if any(kw in budget.lower() for kw in budget_keywords):
        confidence += 0.05

    return ColumnMapping(
        account=account,
        period=period,
        actual=actual,
        budget=budget,
        confidence=min(confidence, 1.0)
    )


def apply_mapping(df: pd.DataFrame, mapping: ColumnMapping) -> List[VarianceRow]:
    """Применяет маппинг к DataFrame и преобразует в VarianceRow.

    Args:
        df: Исходный DataFrame
        mapping: Маппинг столбцов

    Returns:
        Список VarianceRow с рассчитанными variance

    Raises:
        ValueError: Если маппинг невалидный
    """
    # Валидация маппинга
    is_valid, error_msg = validate_mapping(df, mapping)
    if not is_valid:
        raise ValueError(error_msg)

    # Создаём копию DataFrame с переименованными столбцами
    df_mapped = df[[mapping.account, mapping.period, mapping.actual, mapping.budget]].copy()
    df_mapped.columns = ['account', 'period', 'actual', 'budget']

    # Удаляем строки с пустыми значениями
    df_mapped = df_mapped.dropna()

    # Преобразуем в VarianceRow
    rows = []
    for _, row in df_mapped.iterrows():
        variance_row = VarianceRow(
            account=str(row['account']),
            period=str(row['period']),
            actual=float(row['actual']),
            budget=float(row['budget'])
        )
        # Рассчитываем variance
        variance_row = calculate_variance_for_row(variance_row)
        rows.append(variance_row)

    return rows


def validate_mapping(df: pd.DataFrame, mapping: ColumnMapping) -> Tuple[bool, str]:
    """Проверяет валидность маппинга.

    Args:
        df: DataFrame для проверки
        mapping: Маппинг для валидации

    Returns:
        (is_valid, error_message) - True если валидный, иначе False с описанием ошибки
    """
    # Проверяем что все столбцы существуют
    required_columns = [mapping.account, mapping.period, mapping.actual, mapping.budget]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        return False, f"Столбцы отсутствуют в файле: {', '.join(missing_columns)}"

    # Проверяем типы данных для actual и budget (должны быть числами)
    try:
        # Пробуем преобразовать в float
        pd.to_numeric(df[mapping.actual], errors='coerce')
        pd.to_numeric(df[mapping.budget], errors='coerce')
    except Exception as e:
        return False, f"Столбцы actual/budget должны содержать числовые данные: {str(e)}"

    # Проверяем что есть хотя бы одна валидная строка
    df_test = df[[mapping.account, mapping.period, mapping.actual, mapping.budget]].dropna()
    if len(df_test) == 0:
        return False, "После удаления пустых значений не осталось данных"

    return True, ""


def create_file_metadata(filename: str, df: pd.DataFrame, file_type: str, size_bytes: int) -> FileMetadata:
    """Создаёт метаданные для загруженного файла.

    Args:
        filename: Имя файла
        df: DataFrame с данными
        file_type: 'csv' или 'xlsx'
        size_bytes: Размер файла в байтах

    Returns:
        FileMetadata объект
    """
    column_analysis = analyze_columns(df)
    column_types = {col: info['dtype'] for col, info in column_analysis.items()}

    return FileMetadata(
        filename=filename,
        rows=len(df),
        columns=list(df.columns),
        file_type=file_type,
        size_bytes=size_bytes,
        column_types=column_types
    )
