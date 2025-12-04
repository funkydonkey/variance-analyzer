from agents import function_tool
from typing import Optional
from pathlib import Path
from statistics import mean

from core.loader import load_report
from core.calculator import calculate_variance_bulk
from core.filters import apply_filters
from core.models import AnalysisParams, VarianceReport, VarianceRow


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