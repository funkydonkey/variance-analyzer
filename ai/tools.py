from agents import function_tool
from typing import Optional
from pathlib import Path
from statistics import mean
import json

from core.loader import load_report
from core.calculator import calculate_variance_bulk
from core.filters import apply_filters
from core.models import AnalysisParams, VarianceReport, VarianceRow, ColumnMapping
from core.mapper import analyze_columns, suggest_mapping, apply_mapping


@function_tool
def get_variance_data(
    file_path: str,
    min_absolute: float = 0.0,
    min_percentage: float = 0.0,
    periods: Optional[list[str]] = None,
    accounts: Optional[list[str]] = None
) -> dict:
    """
    Загружает данные и возвращает variance analysis с фильтрацией.

    Args:
        file_path: Путь к CSV/XLSX файлу с отчётом
        min_absolute: Минимальное абсолютное отклонение для фильтрации
        min_percentage: Минимальное процентное отклонение (0-100%)
        periods: Список периодов для фильтрации (None = все периоды)
        accounts: Список счетов для фильтрации (None = все счета)

    Returns:
        Словарь с отфильтрованными данными variance analysis
    """

    file_extension = Path(file_path).suffix.lower()
    file_type = "csv" if file_extension == ".csv" else "xlsx"

    rows = load_report(Path(file_path), file_type=file_type)

    rows_with_variance = calculate_variance_bulk(rows)

    params = AnalysisParams(
        min_absolute_threshold=min_absolute,
        min_percentage_threshold=min_percentage,
        periods=periods,
        accounts=accounts
    )

    filtered_rows = apply_filters(rows_with_variance, params)

    return{
        "rows" : [
            {
                "account": row.account,
                "period": row.period,
                "actual": row.actual,
                "budget": row.budget,
                "absolute_variance": row.absolute_variance,
                "percentage_variance": row.percentage_variance
            }
            for row in filtered_rows
        ],
        "total_rows": len(rows_with_variance),
        "filtered_rows": len(filtered_rows)
    }

@function_tool
def get_top_variances(
    file_path: str,
    n: int = 5,
    by: str = "absolue"
) -> list[dict]:
    """
    Возвращает топ-N отклонений по абсолютному или процентному значению.

    Args:
        file_path: Путь к файлу с данными
        n: Количество результатов (по умолчанию 5)
        by: Сортировка - "absolute" или "percentage"

    Returns:
        Список словарей с топ отклонениями
    """

    file_extension = Path(file_path).suffix.lower()
    file_type = "csv" if file_extension == ".csv" else "xlsx"

    rows = load_report(Path(file_path), file_type=file_type)

    rows_with_variance = calculate_variance_bulk(rows)

    if by == "absolute":
        sorted_rows = sorted(rows_with_variance, key=lambda row: abs(row.absolute_variance or 0), reverse=True)
    elif by == "percentage":
        sorted_rows = sorted(rows_with_variance, key=lambda row: abs(row.percentage_variance or 0), reverse=True)
    else:
        raise ValueError("Invalid by parameter. Must be 'absolute' or 'percentage'.")
    
    top_rows = sorted_rows[:n]

    return {
        "rows": [
            {
                "account": row.account,
                "period": row.period,
                "actual": row.actual,
                "budget": row.budget,
                "absolute_variance": row.absolute_variance,
                "percentage_variance": row.percentage_variance
            }
            for row in top_rows
        ],
        "total_rows": len(rows_with_variance),
        "returned_rows": len(top_rows),
        "sorted_by": by
    }

@function_tool
def get_summary_stats(file_path: str) -> dict:
    """
    Возвращает сводную статистику по всем данным.

    Args:
        file_path: Путь к файлу с данными

    Returns:
        Словарь со статистикой:
        - total_rows: общее количество строк
        - periods: список уникальных периодов
        - accounts: список уникальных счетов
        - total_variance_abs: сумма модулей всех отклонений
        - avg_variance_pct: среднее процентное отклонение (без None)
    """
    # variance_data = get_variance_data(Path(file_path))

    file_extension = Path(file_path).suffix.lower()
    file_type = "csv" if file_extension == ".csv" else "xlsx"

    rows = load_report(Path(file_path), file_type=file_type)

    rows_with_variance = calculate_variance_bulk(rows)


    return{
        "total_rows": len(rows_with_variance),
        "periods": sorted(set(row.period for row in rows_with_variance)),
        "accounts": sorted(set(row.account for row in rows_with_variance)),
        "total_variance_abs": sum(abs(row.absolute_variance or 0) for row in rows_with_variance),
        "avg_variance_pct": mean(row.percentage_variance for row in rows_with_variance if row.percentage_variance is not None)
    }


# Глобальное хранилище для загруженного DataFrame и маппинга
_uploaded_dataframe = None
_column_mapping = None
_mapped_variance_rows = None


@function_tool
def analyze_uploaded_file_columns() -> dict:
    """
    Анализирует столбцы загруженного файла для предложения маппинга.

    Использует глобальную переменную _uploaded_dataframe.

    Returns:
        Словарь с информацией о столбцах и предложенным маппингом
    """
    global _uploaded_dataframe

    # DEBUG
    print(f"[DEBUG] analyze_uploaded_file_columns: _uploaded_dataframe is None? {_uploaded_dataframe is None}")
    if _uploaded_dataframe is not None:
        print(f"[DEBUG] _uploaded_dataframe shape: {_uploaded_dataframe.shape}")

    if _uploaded_dataframe is None:
        return {
            "error": "Файл не загружен. Пользователь должен сначала загрузить файл через интерфейс."
        }

    # Анализируем столбцы
    column_info = analyze_columns(_uploaded_dataframe)

    # Предлагаем маппинг
    try:
        suggested = suggest_mapping(column_info)

        # Сохраняем предложенный маппинг в session_state для обработки подтверждения
        import streamlit as st
        st.session_state.pending_mapping = {
            "account": suggested.account,
            "period": suggested.period,
            "actual": suggested.actual,
            "budget": suggested.budget
        }
        st.session_state.awaiting_mapping_confirmation = True

        print(f"[DEBUG] Saved pending_mapping to session_state: {st.session_state.pending_mapping}")

        return {
            "columns": list(_uploaded_dataframe.columns),
            "column_info": column_info,
            "suggested_mapping": {
                "account": suggested.account,
                "period": suggested.period,
                "actual": suggested.actual,
                "budget": suggested.budget,
                "confidence": suggested.confidence
            },
            "file_rows": len(_uploaded_dataframe),
            "awaiting_confirmation": True,
            "next_action": f"ВАЖНО: Покажи пользователю этот маппинг и спроси подтверждения. Когда пользователь подтвердит (напишет 'да'), НЕМЕДЛЕННО вызови apply_column_mapping(account_column='{suggested.account}', period_column='{suggested.period}', actual_column='{suggested.actual}', budget_column='{suggested.budget}')"
        }
    except ValueError as e:
        return {
            "error": str(e),
            "columns": list(_uploaded_dataframe.columns),
            "column_info": column_info
        }


def _apply_column_mapping_impl(
    account_column: str,
    period_column: str,
    actual_column: str,
    budget_column: str
) -> dict:
    """
    Внутренняя реализация apply_column_mapping (без декоратора).

    Применяет маппинг столбцов к загруженному файлу и сохраняет результат.

    Args:
        account_column: Название столбца для account
        period_column: Название столбца для period
        actual_column: Название столбца для actual
        budget_column: Название столбца для budget

    Returns:
        Результат применения маппинга со статистикой
    """
    global _uploaded_dataframe, _column_mapping, _mapped_variance_rows

    # DEBUG
    print(f"[DEBUG] apply_column_mapping called with: account={account_column}, period={period_column}, actual={actual_column}, budget={budget_column}")
    print(f"[DEBUG] apply_column_mapping: _uploaded_dataframe is None? {_uploaded_dataframe is None}")
    if _uploaded_dataframe is not None:
        print(f"[DEBUG] _uploaded_dataframe shape: {_uploaded_dataframe.shape}")

    if _uploaded_dataframe is None:
        return {
            "success": False,
            "error": "Файл не загружен"
        }

    # Создаём маппинг
    mapping = ColumnMapping(
        account=account_column,
        period=period_column,
        actual=actual_column,
        budget=budget_column
    )

    try:
        # Применяем маппинг и получаем VarianceRow с рассчитанными variance
        variance_rows = apply_mapping(_uploaded_dataframe, mapping)

        # Сохраняем глобально
        _column_mapping = mapping
        _mapped_variance_rows = variance_rows

        # ВАЖНО: Также сохраняем в session_state для persistence между reruns
        import streamlit as st
        st.session_state.column_mapping = mapping
        st.session_state.mapped_variance_rows = variance_rows

        # Статистика
        return {
            "success": True,
            "rows_processed": len(variance_rows),
            "total_rows": len(variance_rows),
            "periods": sorted(set(row.period for row in variance_rows)),
            "accounts": sorted(set(row.account for row in variance_rows)),
            "total_variance_abs": sum(abs(row.absolute_variance or 0) for row in variance_rows),
            "avg_variance_pct": mean(row.percentage_variance for row in variance_rows if row.percentage_variance is not None),
            "message": "Маппинг успешно применён. Данные готовы к анализу.",
            "important_instruction": "КРИТИЧЕСКИ ВАЖНО: Теперь для ВСЕХ запросов о данных используй ТОЛЬКО инструменты get_mapped_variance_data и get_mapped_top_variances. НЕ используй get_variance_data, get_top_variances, get_summary_stats - они работают с другим файлом (test_data.csv)."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@function_tool
def apply_column_mapping(
    account_column: str,
    period_column: str,
    actual_column: str,
    budget_column: str
) -> dict:
    """
    Применяет маппинг столбцов к загруженному файлу и сохраняет результат.

    Args:
        account_column: Название столбца для account
        period_column: Название столбца для period
        actual_column: Название столбца для actual
        budget_column: Название столбца для budget

    Returns:
        Результат применения маппинга со статистикой
    """
    return _apply_column_mapping_impl(account_column, period_column, actual_column, budget_column)


@function_tool
def get_mapped_variance_data(
    min_absolute: float = 0.0,
    min_percentage: float = 0.0,
    periods: Optional[list[str]] = None,
    accounts: Optional[list[str]] = None
) -> dict:
    """
    Получает отфильтрованные данные variance из замапленного файла.

    Использует глобальную переменную _mapped_variance_rows.

    Args:
        min_absolute: Минимальное абсолютное отклонение
        min_percentage: Минимальное процентное отклонение
        periods: Список периодов для фильтрации
        accounts: Список счетов для фильтрации

    Returns:
        Отфильтрованные данные variance
    """
    global _mapped_variance_rows

    if _mapped_variance_rows is None:
        return {
            "error": "Данные не замаплены. Сначала примените маппинг столбцов."
        }

    params = AnalysisParams(
        min_absolute_threshold=min_absolute,
        min_percentage_threshold=min_percentage,
        periods=periods,
        accounts=accounts
    )

    filtered_rows = apply_filters(_mapped_variance_rows, params)

    return {
        "rows": [
            {
                "account": row.account,
                "period": row.period,
                "actual": row.actual,
                "budget": row.budget,
                "absolute_variance": row.absolute_variance,
                "percentage_variance": row.percentage_variance
            }
            for row in filtered_rows
        ],
        "total_rows": len(_mapped_variance_rows),
        "filtered_rows": len(filtered_rows)
    }


@function_tool
def get_mapped_top_variances(
    n: int = 5,
    by: str = "absolute"
) -> dict:
    """
    Возвращает топ-N отклонений из замапленных данных.

    Args:
        n: Количество результатов
        by: Сортировка - "absolute" или "percentage"

    Returns:
        Топ отклонения
    """
    global _mapped_variance_rows

    if _mapped_variance_rows is None:
        return {
            "error": "Данные не замаплены. Сначала примените маппинг столбцов."
        }

    if by == "absolute":
        sorted_rows = sorted(_mapped_variance_rows, key=lambda row: abs(row.absolute_variance or 0), reverse=True)
    elif by == "percentage":
        sorted_rows = sorted(_mapped_variance_rows, key=lambda row: abs(row.percentage_variance or 0), reverse=True)
    else:
        return {
            "error": "Invalid by parameter. Must be 'absolute' or 'percentage'."
        }

    top_rows = sorted_rows[:n]

    return {
        "rows": [
            {
                "account": row.account,
                "period": row.period,
                "actual": row.actual,
                "budget": row.budget,
                "absolute_variance": row.absolute_variance,
                "percentage_variance": row.percentage_variance
            }
            for row in top_rows
        ],
        "total_rows": len(_mapped_variance_rows),
        "returned_rows": len(top_rows),
        "sorted_by": by
    }