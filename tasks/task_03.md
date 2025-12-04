# Task 03: AI Agent для Variance Analysis с OpenAI Agents SDK

## Цель задания
Создать AI агента используя **OpenAI Agents SDK**, который будет анализировать финансовые данные, отвечать на вопросы пользователя и генерировать insights на основе variance analysis.

## Что ты изучишь
1. **OpenAI Agents SDK** - современный фреймворк для создания AI агентов
2. **Function Tools** - создание инструментов для агента с `@function_tool`
3. **Agent Runner** - запуск агентов и обработка результатов
4. **Sessions** - управление историей диалогов с `SQLiteSession`
5. **Prompt engineering** - написание эффективных инструкций для агента

## Отличия OpenAI Agents SDK от обычного API

| OpenAI API (Chat Completions) | OpenAI Agents SDK |
|-------------------------------|-------------------|
| `client.chat.completions.create()` | `Runner.run(agent, input)` |
| Ручная обработка function calling | Автоматическая оркестрация |
| Ручное управление историей | `SQLiteSession` для автоматической истории |
| Нет встроенной трассировки | Встроенная трассировка и визуализация |

## Архитектура

```
agents/
├── __init__.py              # Пустой файл для Python пакета
├── tools.py                 # Function tools для агента
└── variance_agent.py        # Основной AI агент с использованием SDK
```

## Установка зависимостей

```bash
uv add openai-agents
```

## Часть 1: Создание Function Tools

**Файл: `agents/tools.py`**

В OpenAI Agents SDK инструменты создаются с декоратором `@function_tool`.

### Структура ответов всех функций (единообразная)

Все три функции возвращают **структурированный dict** для консистентности:

| Функция | Основные поля ответа |
|---------|---------------------|
| `get_variance_data()` | `rows`, `total_rows`, `filtered_rows` |
| `get_top_variances()` | `rows`, `total_rows`, `returned_rows`, `sorted_by` |
| `get_summary_stats()` | `total_rows`, `periods`, `accounts`, `total_variance_abs`, `avg_variance_pct` |

Все функции где есть `rows` - содержат список словарей `list[dict]`, а не список `VarianceRow`!

**Пример взаимодействия агента с функциями:**

```
Пользователь: "Покажи топ-3 отклонения"

Агент вызывает: get_top_variances(file_path="...", n=3, by="absolute")

Агент получает:
{
  "rows": [
    {"account": "Revenue", "period": "2024-01", "absolute_variance": 200.0, ...},
    {"account": "COGS", "period": "2024-01", "absolute_variance": 100.0, ...},
    {"account": "Marketing", "period": "2024-02", "absolute_variance": -80.0, ...}
  ],
  "total_rows": 6,
  "returned_rows": 3,
  "sorted_by": "absolute"
}

Агент отвечает: "Нашел топ-3 отклонения из 6 строк..."
```

### 1. `get_variance_data()`

```python
"""Function tools для variance analysis агента."""
from agents import function_tool
from typing import Optional
from pathlib import Path

from core.loader import load_report
from core.calculator import calculate_variance_bulk
from core.filters import apply_filters
from core.models import AnalysisParams


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
    # 1. Определяем тип файла
    file_extension = Path(file_path).suffix.lower()
    file_type = "csv" if file_extension == ".csv" else "xlsx"

    # 2. Загружаем данные
    rows = load_report(Path(file_path), file_type=file_type)

    # 3. Рассчитываем variance
    rows_with_variance = calculate_variance_bulk(rows)

    # 4. Применяем фильтры
    params = AnalysisParams(
        min_absolute_threshold=min_absolute,
        min_percentage_threshold=min_percentage,
        periods=periods,
        accounts=accounts
    )
    filtered_rows = apply_filters(rows_with_variance, params)

    # 5. Конвертируем в dict для JSON-сериализации
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
        "total_rows": len(rows_with_variance),
        "filtered_rows": len(filtered_rows)
    }
```

### 2. `get_top_variances()`

```python
@function_tool
def get_top_variances(
    file_path: str,
    n: int = 5,
    by: str = "absolute"
) -> dict:
    """
    Возвращает топ-N отклонений по абсолютному или процентному значению.

    Args:
        file_path: Путь к файлу с данными
        n: Количество результатов (по умолчанию 5)
        by: Сортировка - "absolute" или "percentage"

    Returns:
        Словарь с топ отклонениями и метаданными
    """
    # Реализуй:
    # 1. Загрузи данные (load_report)
    # 2. Рассчитай variance (calculate_variance_bulk)
    # 3. Отсортируй по критерию:
    #    - если by == "absolute": сортируй по abs(row.absolute_variance)
    #    - если by == "percentage": сортируй по abs(row.percentage_variance)
    #    - используй sorted() с key=lambda и reverse=True
    # 4. Возьми первые n элементов: sorted_rows[:n]
    # 5. Верни структурированный dict с полями:
    #    - rows: список dict
    #    - total_rows: общее количество строк
    #    - returned_rows: сколько вернули (len(top_rows))
    #    - sorted_by: критерий сортировки
    pass  # ← твоя реализация
```

### 3. `get_summary_stats()`

```python
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
    # Реализуй:
    # 1. Загрузи и рассчитай variance
    # 2. Извлеки уникальные периоды и счета
    # 3. Посчитай агрегаты (сумма, среднее)
    pass  # ← твоя реализация
```

## Часть 2: Создание агента

**Файл: `agents/variance_agent.py`**

```python
"""AI агент для variance analysis с использованием OpenAI Agents SDK."""
import asyncio
from pathlib import Path
from agents import Agent, Runner, SQLiteSession
from agents.tools import (
    get_variance_data,
    get_top_variances,
    get_summary_stats
)


class VarianceAnalyst:
    """
    AI агент-аналитик для variance analysis.

    Использует OpenAI Agents SDK для анализа финансовых данных.
    """

    def __init__(self, data_file: str):
        """
        Инициализация агента.

        Args:
            data_file: Путь к CSV/XLSX файлу с данными
        """
        self.data_file = str(Path(data_file).absolute())

        # Создаём агента с инструкциями и инструментами
        self.agent = Agent(
            name="Variance Analyst",
            instructions=self._get_instructions(),
            tools=[
                get_variance_data,
                get_top_variances,
                get_summary_stats
            ],
            model="gpt-4o"  # Используем GPT-4o для лучшего качества
        )

        # Сессия для сохранения истории диалогов
        self.session = SQLiteSession("variance_analysis")

    def _get_instructions(self) -> str:
        """Системный промпт для агента."""
        return f"""
Ты - AI ассистент для финансового анализа variance (отклонений между фактом и бюджетом).

# Твоя роль
1. Анализировать финансовые данные используя доступные инструменты
2. Отвечать на вопросы о variance понятным языком
3. Предоставлять практические insights и рекомендации

# Важные правила
- ВСЕГДА используй инструменты для получения данных. Путь к файлу: {self.data_file}
- НИКОГДА не придумывай цифры - только реальные данные из инструментов
- Если видишь большие отклонения (>20%), обращай на них внимание
- Используй таблицы Markdown для представления данных
- Объясняй результаты простым языком для финансистов

# Доступные инструменты
1. `get_variance_data` - получить отфильтрованные данные variance
2. `get_top_variances` - найти топ отклонений (по модулю или %)
3. `get_summary_stats` - получить сводную статистику

# Формат ответов
- Сначала показываешь данные (таблица)
- Потом даёшь краткий анализ и выводы
- Для больших отклонений предлагаешь возможные причины

# Примеры запросов пользователя
- "Какие счета имеют наибольшее отклонение?"
- "Покажи топ-5 отклонений в январе 2024"
- "Какая общая статистика по данным?"
- "Где мы перерасходовали бюджет?"
"""

    async def chat(self, message: str) -> str:
        """
        Отправить сообщение агенту и получить ответ.

        Args:
            message: Вопрос пользователя

        Returns:
            Ответ агента
        """
        # Запускаем агента через Runner
        result = await Runner.run(
            starting_agent=self.agent,
            input=message,
            session=self.session  # История диалога сохраняется автоматически
        )

        return result.final_output

    def chat_sync(self, message: str) -> str:
        """
        Синхронная версия chat() для удобства.

        Args:
            message: Вопрос пользователя

        Returns:
            Ответ агента
        """
        return Runner.run_sync(
            starting_agent=self.agent,
            input=message,
            session=self.session
        )
```

## Часть 3: Тестирование агента

**Файл: `test_agent.py`** (в корне проекта)

```python
"""Тестирование variance analysis агента."""
import asyncio
import os
from agents.variance_agent import VarianceAnalyst


async def main():
    print("="*60)
    print("🤖 Variance Analysis Agent - Demo")
    print("="*60)

    # Проверяем наличие OPENAI_API_KEY
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Ошибка: установи OPENAI_API_KEY в .env файле")
        print("Создай .env файл:")
        print("  echo 'OPENAI_API_KEY=your-key-here' > .env")
        return

    # Создаём агента
    analyst = VarianceAnalyst(data_file="test_data.csv")

    # Тестовые вопросы
    questions = [
        "Какие счета имеют наибольшее отклонение?",
        "Покажи топ-3 отклонения по модулю",
        "Какая сводная статистика по данным?",
        "В каких периодах Revenue выше бюджета?",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n{'='*60}")
        print(f"❓ Вопрос {i}: {question}")
        print(f"{'='*60}")

        try:
            response = await analyst.chat(question)
            print(f"\n✅ Ответ:\n{response}")
        except Exception as e:
            print(f"\n❌ Ошибка: {str(e)}")

    print(f"\n{'='*60}")
    print("✨ Тестирование завершено!")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Часть 4: Интерактивный режим (опционально)

Добавь в `agents/variance_agent.py`:

```python
from agents import run_demo_loop

async def interactive_mode(data_file: str):
    """Запускает агента в интерактивном режиме."""
    analyst = VarianceAnalyst(data_file)

    print("🤖 Variance Analyst запущен в интерактивном режиме")
    print("Введи свой вопрос или 'quit' для выхода\n")

    await run_demo_loop(analyst.agent, session=analyst.session)
```

Добавь в `test_agent.py`:

```python
# В конце main():
print("\n💬 Хочешь задать свои вопросы? (y/n)")
if input().lower() == 'y':
    from agents.variance_agent import interactive_mode
    await interactive_mode("test_data.csv")
```

## Дополнительные задания (продвинутый уровень)

### 1. Multi-Agent с Handoffs

Создай систему из нескольких агентов:
- **Triage Agent** - определяет тип вопроса
- **Data Analyst Agent** - анализирует цифры
- **Explainer Agent** - объясняет результаты простым языком

```python
from agents import Agent, handoff

data_analyst = Agent(
    name="Data Analyst",
    handoff_description="Специалист по анализу цифр и расчётам",
    instructions="Ты анализируешь данные и выдаёшь точные цифры",
    tools=[get_variance_data, get_top_variances, get_summary_stats]
)

explainer = Agent(
    name="Explainer",
    handoff_description="Специалист по объяснению результатов",
    instructions="Ты объясняешь финансовые результаты простым языком"
)

triage_agent = Agent(
    name="Triage Agent",
    instructions="Направляй вопросы к нужному специалисту",
    handoffs=[data_analyst, explainer]
)
```

### 2. Structured Output

Используй Pydantic модели для структурированного вывода:

```python
from pydantic import BaseModel, Field

class VarianceInsight(BaseModel):
    account: str = Field(description="Название счёта")
    severity: str = Field(description="Уровень: low/medium/high")
    recommendation: str = Field(description="Рекомендация")

analyst_agent = Agent(
    name="Analyst",
    instructions="Анализируй variance и давай рекомендации",
    output_type=VarianceInsight,
    tools=[...]
)
```

### 3. Tracing и Визуализация

```python
from agents import gen_trace_id, trace

trace_id = gen_trace_id()
with trace(workflow_name="Variance Analysis", trace_id=trace_id):
    result = await Runner.run(agent, input="...")
    print(f"Trace URL: https://platform.openai.com/traces/trace?trace_id={trace_id}")
```

## Что проверить перед завершением

- [ ] Установлен `openai-agents`: `uv add openai-agents`
- [ ] Файл `.env` содержит `OPENAI_API_KEY`
- [ ] Все три функции в `tools.py` реализованы
- [ ] Класс `VarianceAnalyst` создан и работает
- [ ] `test_agent.py` выполняется без ошибок
- [ ] Агент НЕ придумывает данные (всегда использует функции)
- [ ] История диалога сохраняется между вызовами
- [ ] Ответы агента понятны и содержат таблицы

## Ключевые концепции OpenAI Agents SDK

### 1. Agent
```python
agent = Agent(
    name="Agent Name",
    instructions="System prompt...",
    tools=[tool1, tool2],
    model="gpt-4o"
)
```

### 2. Function Tool
```python
@function_tool
def my_tool(param: str) -> dict:
    """Docstring становится description."""
    return {"result": "..."}
```

### 3. Runner
```python
# Async
result = await Runner.run(agent, input="...")
print(result.final_output)

# Sync
result = Runner.run_sync(agent, input="...")
```

### 4. Session
```python
session = SQLiteSession("conversation_id")
result = await Runner.run(agent, input="...", session=session)
# История сохраняется автоматически!
```

## Полезные ссылки

1. **OpenAI Agents SDK Docs**: https://openai.github.io/openai-agents-python/
2. **Quickstart**: https://openai.github.io/openai-agents-python/quickstart/
3. **Tools Guide**: https://openai.github.io/openai-agents-python/tools/
4. **Sessions**: https://openai.github.io/openai-agents-python/sessions/
5. **GitHub**: https://github.com/openai/openai-agents-python

## Подсказки для реализации

### Пример реализации get_top_variances()
```python
@function_tool
def get_top_variances(file_path: str, n: int = 5, by: str = "absolute") -> dict:
    """Возвращает топ-N отклонений."""
    # 1-2. Загрузка и расчёт
    file_extension = Path(file_path).suffix.lower()
    file_type = "csv" if file_extension == ".csv" else "xlsx"
    rows = load_report(Path(file_path), file_type=file_type)
    rows_with_variance = calculate_variance_bulk(rows)

    # 3. Сортировка
    if by == "absolute":
        sorted_rows = sorted(
            rows_with_variance,
            key=lambda row: abs(row.absolute_variance or 0),
            reverse=True
        )
    elif by == "percentage":
        sorted_rows = sorted(
            rows_with_variance,
            key=lambda row: abs(row.percentage_variance or 0),
            reverse=True
        )
    else:
        raise ValueError(f"Неизвестный критерий: {by}")

    # 4. Топ N
    top_rows = sorted_rows[:n]

    # 5. Структурированный ответ
    return {
        "rows": [row.__dict__ for row in top_rows],
        "total_rows": len(rows_with_variance),
        "returned_rows": len(top_rows),
        "sorted_by": by
    }
```

### Пример реализации get_summary_stats()
```python
@function_tool
def get_summary_stats(file_path: str) -> dict:
    """Возвращает сводную статистику."""
    # 1. Загрузка и расчёт
    file_extension = Path(file_path).suffix.lower()
    file_type = "csv" if file_extension == ".csv" else "xlsx"
    rows = load_report(Path(file_path), file_type=file_type)
    rows_with_variance = calculate_variance_bulk(rows)

    # 2. Извлечение уникальных значений
    periods = sorted(set(row.period for row in rows_with_variance))
    accounts = sorted(set(row.account for row in rows_with_variance))

    # 3. Агрегация
    total_variance_abs = sum(
        abs(row.absolute_variance or 0)
        for row in rows_with_variance
    )

    # Среднее процентное отклонение (только для строк где оно есть)
    pct_variances = [
        row.percentage_variance
        for row in rows_with_variance
        if row.percentage_variance is not None
    ]
    avg_variance_pct = (
        sum(pct_variances) / len(pct_variances)
        if pct_variances else 0.0
    )

    return {
        "total_rows": len(rows_with_variance),
        "periods": periods,
        "accounts": accounts,
        "total_variance_abs": total_variance_abs,
        "avg_variance_pct": avg_variance_pct
    }
```

### Как передать file_path в функции?
```python
# В tools.py функции принимают file_path как параметр
@function_tool
def get_variance_data(file_path: str, ...) -> dict:
    ...

# В variance_agent.py агенту даём инструкции с путём к файлу
instructions = f"""
...
Путь к файлу данных: {self.data_file}
ВСЕГДА используй этот путь в параметре file_path при вызове инструментов.
"""
```

### Debugging
```python
# Включи подробное логирование
result = await Runner.run(agent, input="...", max_turns=10)

# Посмотри на все шаги агента
for item in result.new_items:
    print(item)
```

### Обработка ошибок
```python
try:
    response = await analyst.chat(question)
except Exception as e:
    print(f"Ошибка: {str(e)}")
    # Агент автоматически обрабатывает большинство ошибок
```

---

## Начни с этого

1. Установи зависимости: `uv add openai-agents`
2. Создай `.env` с `OPENAI_API_KEY`
3. Создай `agents/__init__.py` (пустой файл)
4. Реализуй `agents/tools.py` - начни с `get_variance_data()`
5. Создай `agents/variance_agent.py` с классом `VarianceAnalyst`
6. Протестируй с `test_agent.py`
7. Постепенно добавляй остальные функции

**Это ключевая часть проекта - здесь ты будешь работать с настоящим AI фреймворком! 🚀**
