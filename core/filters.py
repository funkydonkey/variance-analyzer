from core.models import VarianceRow, AnalysisParams

def filter_by_absolute_threshold(
        rows: list[VarianceRow],
        min_threshold: float
) -> list[VarianceRow]:
    """Фильтрует строки по абсолютному отклонению.

    Оставляет строки где |absolute_variance| >= min_threshold.

    Args:
        rows: Список строк с рассчитанными variance
        min_threshold: Минимальный порог (по модулю)

    Returns:
        Отфильтрованный список

    Example:
        >>> rows = [
        ...     VarianceRow(..., absolute_variance=100),
        ...     VarianceRow(..., absolute_variance=-50),
        ...     VarianceRow(..., absolute_variance=10),
        ... ]
        >>> filter_by_absolute_threshold(rows, min_threshold=30)
        # Вернёт первые 2 строки (|100| >= 30, |-50| >= 30)
    """
    filtered_rows = []

    for row in rows:
        if abs(row.absolute_variance) >= min_threshold:
            filtered_rows.append(row)

    return filtered_rows


def filter_by_percentage_threshold(
        rows: list[VarianceRow],
        min_threshold: float
) -> list[VarianceRow]:
    """Фильтрует строки по процентному отклонению.

    Оставляет строки где |percentage_variance| >= min_threshold.
    Пропускает строки где percentage_variance = None.

    Args:
        rows: Список строк с рассчитанными variance
        min_threshold: Минимальный порог в процентах (0-100)

    Returns:
        Отфильтрованный список
    """
    filtered_rows = []

    for row in rows:
        if row.percentage_variance is not None and abs(row.percentage_variance) >= min_threshold:
            filtered_rows.append(row)

            

    return filtered_rows


def filter_by_periods(
    rows: list[VarianceRow],
    periods: list[str]
) -> list[VarianceRow]:
    """Фильтрует строки по списку периодов.

    Args:
        rows: Список строк
        periods: Список периодов для включения

    Returns:
        Строки только из указанных периодов
    """

    return [row for row in rows if row.period in periods]


def filter_by_accounts(
    rows: list[VarianceRow],
    accounts: list[str]
) -> list[VarianceRow]:
    """Фильтрует строки по списку аккаунтов.

    Args:
        rows: Список строк
        accounts: Список аккаунтов для включения

    Returns:
        Строки только из указанных аккаунтов
    """

    return [row for row in rows if row.account in accounts]


def apply_filters(
    rows: list[VarianceRow],
    params: AnalysisParams
) -> list[VarianceRow]:
    """Применяет все фильтры из AnalysisParams.

    Порядок фильтрации:
        1. По периодам (если указаны)
        2. По статьям (если указаны)
        3. По абсолютному порогу
        4. По процентному порогу

    Args:
        rows: Список строк с рассчитанными variance
        params: Параметры фильтрации

    Returns:
        Отфильтрованный список
    """

    filtered_rows = rows

    if params.periods is not None:
        filtered_rows = filter_by_periods(rows, params.periods)
    if params.accounts is not None:
        filtered_rows = filter_by_accounts(filtered_rows, params.accounts)
    filtered_rows = filter_by_absolute_threshold(filtered_rows, params.min_absolute_threshold)
    filtered_rows = filter_by_percentage_threshold(filtered_rows, params.min_percentage_threshold)

    return filtered_rows
