from dataclasses import dataclass
from typing import List, Optional

@dataclass
class VarianceRow:
     """Одна строка variance analysis.

    Attributes:
        account: Название статьи (например, "Revenue", "Cost of Sales")
        period: Период (например, "2024-01", "Q1 2024")
        actual: Фактическое значение
        budget: Бюджетное значение
        absolute_variance: actual - budget (рассчитывается)
        percentage_variance: (actual - budget) / budget * 100 (рассчитывается)
    """
     account: str
     period: str
     actual: float
     budget: float
     absolute_variance: Optional[float] = None
     percentage_variance: Optional[float] = None

     def has_variance_calculated(self) -> bool:
        """Проверяет, рассчитаны ли variance значения."""
        if self.absolute_variance is not None and self.percentage_variance is not None:
           return True          
        else:
            return False
        
@dataclass
class AnalysisParams:
    """Параметры для variance analysis.

    Attributes:
        min_absolute_threshold: Минимальное абсолютное отклонение для фильтра
        min_percentage_threshold: Минимальное процентное отклонение (0-100)
        periods: Список периодов для анализа (None = все)
        accounts: Список статей для анализа (None = все)
    """
    min_absolute_threshold: float = 0.0
    min_percentage_threshold: float = 0.0
    periods: Optional[List[str]] = None
    accounts: Optional[List[str]] = None

@dataclass
class VarianceReport:
     """Результат variance analysis.

    Attributes:
        rows: Список строк с рассчитанными variance
        params: Параметры, с которыми был выполнен анализ
        total_rows: Общее количество строк (до фильтрации)
        filtered_rows: Количество строк после фильтрации
    """
     rows: List[VarianceRow]
     params: AnalysisParams
     total_rows: int
     filtered_rows: int

     def get_top_variances(self, n: int  = 10, by: str = "absolute") -> List[VarianceRow]:
        """Возвращает топ N строк с наибольшими отклонениями.

        Args:
            n: Количество строк для возврата
            by: Критерий сортировки ("absolute" или "percentage")

        Returns:
            Список из n строк с наибольшими отклонениями
        """
        if by == "absolute":
            sorted_rows = sorted(self.rows, key=lambda row: abs(row.absolute_variance or 0), reverse=True)
        elif by == "percentage":
            sorted_rows = sorted(self.rows, key=lambda row: abs(row.percentage_variance or 0), reverse=True)
        else:
            raise ValueError("Не задан критерий сортировки 'absolute' или 'percentage'.")

        return sorted_rows[:n]