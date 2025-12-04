# Task 01: Core Variance Logic - Data Models & Calculations

## 🎯 Цель задачи

В этой задаче ты научишься:
- Проектировать доменные модели с использованием `dataclasses`
- Писать type-safe код с полной типизацией (type hints)
- Работать с pandas для загрузки и нормализации данных
- Реализовывать бизнес-логику расчётов variance
- Обрабатывать edge cases (деление на ноль, отрицательные значения)

**Результат:** Работающий core-модуль для анализа variance, который можно использовать независимо от API или UI.

---

## 📁 Файлы для работы

Тебе нужно реализовать 4 модуля в папке `core/`:

1. **`core/models.py`** - Доменные модели (датаклассы)
2. **`core/calculator.py`** - Расчёт variance (absolute & percentage)
3. **`core/loader.py`** - Загрузка и нормализация CSV/XLSX
4. **`core/filters.py`** - Фильтрация данных по порогам

---

## 📋 План выполнения

### Шаг 1: Создать доменные модели (`core/models.py`)

**Что нужно сделать:**
Создай 3 датакласса для представления данных:

#### 1.1 `VarianceRow` - одна строка отчёта
```python
from dataclasses import dataclass
from typing import Optional

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

    # TODO: Добавь метод для проверки, заполнены ли variance поля
    def has_variance_calculated(self) -> bool:
        """Проверяет, рассчитаны ли variance значения."""
        pass  # ← реализуй
```

#### 1.2 `AnalysisParams` - параметры анализа
```python
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
    periods: Optional[list[str]] = None
    accounts: Optional[list[str]] = None
```

#### 1.3 `VarianceReport` - полный отчёт
```python
@dataclass
class VarianceReport:
    """Результат variance analysis.

    Attributes:
        rows: Список строк с рассчитанными variance
        params: Параметры, с которыми был выполнен анализ
        total_rows: Общее количество строк (до фильтрации)
        filtered_rows: Количество строк после фильтрации
    """
    rows: list[VarianceRow]
    params: AnalysisParams
    total_rows: int
    filtered_rows: int

    # TODO: Добавь метод для получения топ-N отклонений
    def get_top_variances(self, n: int = 10, by: str = "absolute") -> list[VarianceRow]:
        """Возвращает топ-N строк по величине отклонения.

        Args:
            n: Количество строк
            by: Сортировка по "absolute" или "percentage"

        Returns:
            Отсортированный список VarianceRow
        """
        pass  # ← реализуй
```

**Подсказка:** Используй `from __future__ import annotations` в начале файла для поддержки `list[...]` вместо `List[...]`.

---

### Шаг 2: Реализовать расчёт variance (`core/calculator.py`)

**Что нужно сделать:**
Создай функции для расчёта variance с обработкой edge cases.

```python
from typing import Optional
from core.models import VarianceRow

def calculate_variance(
    actual: float,
    budget: float
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
    pass  # ← реализуй


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
    pass  # ← реализуй


def calculate_variance_bulk(rows: list[VarianceRow]) -> list[VarianceRow]:
    """Рассчитывает variance для списка строк.

    Args:
        rows: Список строк отчёта

    Returns:
        Тот же список с заполненными variance полями
    """
    pass  # ← реализуй
```

**Вопросы для размышления:**
- Что делать если `budget = 0`, а `actual = 100`? Вернуть `None`, `inf`, или `100.0` как "бесконечное" отклонение?
- Как обрабатывать отрицательные бюджеты (например, для доходных статей где отрицательное = возврат)?

---

### Шаг 3: Реализовать загрузку данных (`core/loader.py`)

**Что нужно сделать:**
Создай функции для загрузки CSV/XLSX и преобразования в `VarianceRow`.

```python
from pathlib import Path
import pandas as pd
from core.models import VarianceRow

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
    pass  # ← реализуй


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
    pass  # ← реализуй


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
    pass  # ← реализуй


def dataframe_to_rows(df: pd.DataFrame) -> list[VarianceRow]:
    """Преобразует DataFrame в список VarianceRow.

    Args:
        df: Нормализованный DataFrame

    Returns:
        Список объектов VarianceRow (без рассчитанных variance)
    """
    pass  # ← реализуй


def load_report(file_path: Path, file_type: str = "csv",
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
    pass  # ← реализуй
```

**Подсказки:**
- Используй `pd.read_csv()` и `pd.read_excel()`
- Для проверки колонок: `required_cols = {"account", "period", "actual", "budget"}`
- Для удаления NaN: `df.dropna(subset=["account", "period", "actual", "budget"])`
- Для преобразования в float: `df["actual"] = df["actual"].astype(float)`

---

### Шаг 4: Реализовать фильтрацию (`core/filters.py`)

**Что нужно сделать:**
Создай функции для фильтрации строк по порогам.

```python
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
    pass  # ← реализуй


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
    pass  # ← реализуй


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
    pass  # ← реализуй


def filter_by_accounts(
    rows: list[VarianceRow],
    accounts: list[str]
) -> list[VarianceRow]:
    """Фильтрует строки по списку статей.

    Args:
        rows: Список строк
        accounts: Список статей для включения

    Returns:
        Строки только из указанных статей
    """
    pass  # ← реализуй


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
    pass  # ← реализуй
```

---

## 🔗 Подсказки и ресурсы

### Python dataclasses
- [Официальная документация](https://docs.python.org/3/library/dataclasses.html)
- Пример использования:
  ```python
  from dataclasses import dataclass

  @dataclass
  class Person:
      name: str
      age: int

  p = Person(name="Alice", age=30)
  print(p.name)  # Alice
  ```

### Type hints
- [PEP 484](https://peps.python.org/pep-0484/)
- Используй `Optional[float]` для значений, которые могут быть `None`
- Используй `list[str]` вместо `List[str]` (Python 3.9+)

### Pandas
- [Read CSV](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)
- [Read Excel](https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html)
- Проверка колонок: `set(df.columns) >= required_cols`
- Итерация по строкам: `df.itertuples()` (быстрее чем `iterrows()`)

### Обработка edge cases
- Деление на ноль: используй `try/except ZeroDivisionError` или проверку `if budget == 0`
- Для сортировки: `sorted(rows, key=lambda r: abs(r.absolute_variance), reverse=True)`
- Фильтрация с None: `[r for r in rows if r.percentage_variance is not None and ...]`

---

## ✅ Чеклист самопроверки

Перед тем как сообщить "готово", проверь:

### models.py
- [ ] Все 3 датакласса созданы с правильными типами
- [ ] `VarianceRow.has_variance_calculated()` корректно проверяет заполненность
- [ ] `VarianceReport.get_top_variances()` правильно сортирует по absolute/percentage
- [ ] Используются type hints для всех полей и методов

### calculator.py
- [ ] `calculate_variance()` корректно обрабатывает случай `budget = 0`
- [ ] Формулы работают для положительных и отрицательных значений
- [ ] `calculate_variance_for_row()` модифицирует объект и возвращает его
- [ ] `calculate_variance_bulk()` работает с пустым списком

### loader.py
- [ ] `load_csv()` выбрасывает `ValueError` при отсутствии колонок
- [ ] `normalize_dataframe()` удаляет NaN и дубликаты
- [ ] `dataframe_to_rows()` создаёт VarianceRow с правильными типами
- [ ] `load_report()` работает и для CSV, и для XLSX

### filters.py
- [ ] `filter_by_absolute_threshold()` использует модуль (abs)
- [ ] `filter_by_percentage_threshold()` пропускает None значения
- [ ] `apply_filters()` применяет фильтры в правильном порядке
- [ ] Все функции работают с пустыми списками

### Общее
- [ ] Все функции имеют docstrings
- [ ] Все параметры и возвращаемые значения типизированы
- [ ] Нет import ошибок (`uv run python -c "from core import models, calculator, loader, filters"`)

---

## 🧪 Тестирование

После реализации **напиши мне "модуль готов"**, и я:
1. Создам тесты для всех твоих функций
2. Запущу их и покажу результаты
3. Дам фидбек по коду (code review)

**Не пиши тесты сам** - это моя зона! Ты пиши только бизнес-логику в `core/`.

---

## ❓ Если застрял

Спрашивай:
- "Как лучше обработать деление на ноль в calculate_variance?"
- "Покажи пример использования df.itertuples()"
- "Правильно ли я понимаю, что filter_by_periods должен использовать `in`?"
- "Можешь показать пример VarianceRow с заполненными полями?"

Я помогу подсказками, но **не напишу код за тебя** - это твоя зона роста! 💪

---

**Удачи с реализацией! Начинай с `core/models.py` - это самое простое.** 🚀
