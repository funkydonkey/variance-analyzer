from typing import List, Optional
from core.models import VarianceRow, AnalysisParams, VarianceReport

def calculate_variance(
        actual: float, budget: float
) -> tuple[float, Optional[float]]:
    """Рассчитывает абсолютное и процентное отклонение.

    Формулы:
        absolute_variance = actual - budget
        percentage_variance = (actual - budget) / budget * 100

    Edge cases:
        - Если budget == 0: percentage_variance = None
        - Если budget < 0 и actual < 0: процент считается нормально
        - Если budget == 0 и actual != 0: percentage_variance = None (или inf?)

    Args:
        actual: Фактическое значение
        budget: Бюджетное значение

    Returns:
        Кортеж (absolute_variance, percentage_variance)
        percentage_variance может быть None если budget == 0

    Examples:
        >>> calculate_variance(100, 80)
        (20.0, 25.0)  # +20, +25%

        >>> calculate_variance(50, 100)
        (-50.0, -50.0)  # -50, -50%

        >>> calculate_variance(100, 0)
        (100.0, None)  # деление на ноль
    """
    absolute_variance = actual - budget

    if budget == 0:
        percentage_variance = None
    else:
        percentage_variance = (absolute_variance / budget) * 100

    return absolute_variance, percentage_variance

def calculate_variance_for_row(row: VarianceRow) -> VarianceRow:
    """Рассчитывает variance для одной строки отчёта.

    Модифицирует поля absolute_variance и percentage_variance.

    Args:
        row: Строка отчёта с заполненными actual и budget

    Returns:
        Та же строка с заполненными variance полями

    Example:
        >>> row = VarianceRow(account="Revenue", period="2024-01",
        ...                   actual=1000, budget=800)
        >>> calculate_variance_for_row(row)
        VarianceRow(account='Revenue', period='2024-01',
                    actual=1000, budget=800,
                    absolute_variance=200, percentage_variance=25.0)
    """

    row.absolute_variance = calculate_variance( row.actual, row.budget )[0]
    row.percentage_variance = calculate_variance( row.actual, row.budget )[1]

    return row


def calculate_variance_bulk(rows: List[VarianceRow]) -> List[VarianceRow]:
    """Рассчитывает variance для списка строк.

    Args:
        rows: Список строк отчёта

    Returns:
        Тот же список с заполненными variance полями
    """
    for row in rows:
        calculate_variance_for_row(row)
    return rows