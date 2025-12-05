# Task Streamlit 02: Добавляем Streaming для AI ответов

## 🎯 Цель
Сделать так, чтобы ответы AI агента появлялись **токен за токеном** (как в ChatGPT), а не целиком сразу.

## ⏱️ Время выполнения
~20-30 минут

## 🧠 Что ты узнаешь
- Как использовать `st.write_stream()` в Streamlit
- Работа с async generators в Python
- Интеграция OpenAI Agents SDK streaming с Streamlit
- Улучшение UX в AI чатах

---

## 📚 Часть 1: Как работает streaming в Streamlit

### Обычный способ (текущий):
```python
response = asyncio.run(agent.chat(prompt))  # Ждём весь ответ
st.markdown(response)  # Показываем целиком
```

**Проблема:** Пользователь ждёт 5-10 секунд и видит ничего, потом БАМ - весь текст сразу.

### Streaming способ (новый):
```python
async def response_generator():
    # Генерируем токены по мере получения
    yield "Первый"
    yield " токен"
    yield " за"
    yield " токеном"

st.write_stream(response_generator())  # Токены появляются постепенно!
```

**Преимущества:**
- ✅ Пользователь видит прогресс сразу
- ✅ Ощущение "живого" разговора
- ✅ Меньше воспринимаемое время ожидания

### Документация Streamlit:
- **st.write_stream()**: https://docs.streamlit.io/develop/api-reference/write-magic/st.write_stream

---

## 🏗️ Часть 2: Архитектура решения

### Что нужно изменить:

```
new_ui.py
├── Старый код (строки 85-90):
│   response = asyncio.run(analyst.chat(prompt))  ← Ждём весь ответ
│   st.markdown(response)                         ← Показываем сразу
│
└── Новый код:
    response_generator = agent_stream(prompt)     ← Async generator
    st.write_stream(response_generator)           ← Streaming output
```

### Два подхода к реализации:

**Подход А: Модифицировать VarianceAnalyst (более правильный)**
- Добавить метод `chat_stream()` в `ai/variance_agent.py`
- Использовать `Runner.run_stream()` вместо `Runner.run()`

**Подход Б: Wrapper в new_ui.py (быстрый)**
- Создать async generator прямо в Streamlit файле
- Вызывать streaming напрямую

**Рекомендация:** Начни с **Подхода А** - это правильная архитектура.

---

## ✍️ Часть 3: Реализация (ТЫ ПИШЕШЬ)

### Шаг 1: Добавь streaming метод в VarianceAnalyst

**Файл:** `ai/variance_agent.py`

**Задача:** Добавь новый метод `chat_stream()` в класс `VarianceAnalyst`.

```python
class VarianceAnalyst:
    # ... существующий код ...

    async def chat_stream(self, message: str):
        """
        Стримящая версия chat() - возвращает токены по мере генерации.

        Args:
            message: Вопрос пользователя

        Yields:
            str: Токены ответа агента

        Подсказки:
        1. Используй Runner.run_stream() вместо Runner.run()
        2. Итерируйся по stream: async for event in stream
        3. Проверяй тип события и yield только текстовые токены
        4. События могут быть разных типов - нужны только текстовые

        Документация OpenAI Agents SDK:
        - Runner.run_stream() возвращает AsyncIterator[Event]
        - События имеют разные атрибуты: text_delta, tool_name, final_output
        """
        from agents import Runner

        # TODO: Получи stream от Runner.run_stream()
        stream = Runner.run_stream(
            starting_agent=self.agent,
            input=message,
            session=self.session
        )

        # TODO: Итерируйся по событиям и yield текстовые токены
        # Пример структуры:
        # async for event in stream:
        #     if hasattr(event, 'text_delta') and event.text_delta:
        #         yield event.text_delta
        #     # Другие типы событий можно игнорировать

        pass  # ← твоя реализация
```

**Вопросы для размышления:**
- Что делать с событиями tool_call? (Подсказка: можешь показать "🔧 Анализирую...")
- Нужно ли показывать final_output отдельно?
- Как обработать ошибки в streaming?

---

### Шаг 2: Обнови new_ui.py для использования streaming

**Файл:** `new_ui.py`

**Задача:** Замени обычный вызов агента на streaming версию.

**Найди этот блок (строки ~85-90):**
```python
with st.chat_message("assistant"):
    with st.spinner("Typing..."):
        # sleep(1)
        response = asyncio.run(st.session_state.analyst.chat(prompt))
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.markdown(response)
```

**Замени на:**
```python
with st.chat_message("assistant"):
    with st.spinner("Typing..."):
        # TODO: Создай async generator wrapper
        async def stream_response():
            """Wrapper для streaming ответа агента."""
            # TODO: Вызови st.session_state.analyst.chat_stream(prompt)
            # TODO: Итерируйся и yield токены
            pass  # ← твоя реализация

        # TODO: Используй st.write_stream()
        # Подсказка: st.write_stream() принимает generator (НЕ async!)
        # Поэтому нужен синхронный wrapper

        pass  # ← твоя реализация
```

**Проблема:** `st.write_stream()` принимает **синхронный** generator, а `chat_stream()` - **async**!

**Решение:** Два варианта:

**Вариант 1: Использовать asyncio.run() внутри sync generator**
```python
def sync_stream_wrapper():
    """Синхронный wrapper для async generator."""
    async def get_response():
        async for token in st.session_state.analyst.chat_stream(prompt):
            yield token

    # asyncio.run() не работает с generators напрямую
    # Нужно собрать всё в список или использовать другой подход
    pass  # См. подсказки ниже
```

**Вариант 2: Запустить async loop и итерироваться (проще)**
```python
import asyncio

# Создаём event loop если его нет
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Синхронный generator
def stream_wrapper():
    async def async_generator():
        async for token in st.session_state.analyst.chat_stream(prompt):
            yield token

    # Конвертируем async → sync
    async_gen = async_generator()
    try:
        while True:
            token = loop.run_until_complete(async_gen.__anext__())
            yield token
    except StopAsyncIteration:
        pass

# Используем
full_response = st.write_stream(stream_wrapper())
```

**Вариант 3: Самый простой - собрать токены в список (для начала)**
```python
with st.chat_message("assistant"):
    with st.spinner("Typing..."):
        # Собираем все токены
        tokens = []
        async def collect_tokens():
            async for token in st.session_state.analyst.chat_stream(prompt):
                tokens.append(token)

        asyncio.run(collect_tokens())

        # Теперь показываем через streaming из списка
        def token_generator():
            for token in tokens:
                yield token

        full_response = st.write_stream(token_generator())
        st.session_state.messages.append({"role": "assistant", "content": full_response})
```

**Рекомендация:** Начни с **Варианта 3** (простейший, работает точно), потом можешь оптимизировать.

---

### Шаг 3: Сохрани полный ответ в историю

**Проблема:** `st.write_stream()` возвращает полный собранный текст!

```python
full_response = st.write_stream(generator)  # Возвращает весь текст
```

**Задача:** Сохрани `full_response` в `st.session_state.messages` для истории.

```python
# После streaming
st.session_state.messages.append({
    "role": "assistant",
    "content": full_response  # ← Полный ответ после завершения streaming
})
```

---

## 🔗 Подсказки и примеры

### Пример реализации chat_stream() в VarianceAnalyst:

```python
async def chat_stream(self, message: str):
    """Стримящий чат с агентом."""
    from agents import Runner

    stream = Runner.run_stream(
        starting_agent=self.agent,
        input=message,
        session=self.session
    )

    # Итерируемся по событиям
    async for event in stream:
        # Проверяем наличие текстового токена
        if hasattr(event, 'text_delta') and event.text_delta:
            yield event.text_delta

        # Опционально: показываем вызовы инструментов
        elif hasattr(event, 'tool_name') and event.tool_name:
            yield f"\n\n🔧 Использую {event.tool_name}...\n\n"
```

### Пример использования в Streamlit:

```python
# Простейший вариант
with st.chat_message("assistant"):
    # Собираем токены
    tokens = []
    async def collect():
        async for token in st.session_state.analyst.chat_stream(prompt):
            tokens.append(token)

    asyncio.run(collect())

    # Показываем через streaming
    full_response = st.write_stream(iter(tokens))

    # Сохраняем
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response
    })
```

---

## 🐛 Troubleshooting

### "AttributeError: 'Event' object has no attribute 'text_delta'"
**Причина:** Названия атрибутов в OpenAI Agents SDK могут отличаться.

**Решение:**
1. Добавь debug print внутри `chat_stream()`:
   ```python
   async for event in stream:
       print(f"Event type: {type(event)}")
       print(f"Event attributes: {dir(event)}")
       print(f"Event: {event}")
   ```
2. Запусти приложение и посмотри в терминале что приходит
3. Скорректируй названия атрибутов

### "RuntimeError: asyncio.run() cannot be called from a running event loop"
**Причина:** Streamlit уже использует event loop.

**Решение:** Используй Вариант 3 из Шага 2 (собирать токены в список).

### "Streaming не работает, текст появляется сразу весь"
**Причина:** Возможно `st.write_stream()` получает весь список сразу.

**Решение:** Добавь небольшую задержку между токенами:
```python
import time

def token_generator():
    for token in tokens:
        yield token
        time.sleep(0.01)  # 10ms задержка для визуального эффекта
```

### "st.write_stream() не показывает markdown форматирование"
**Это нормально!** `st.write_stream()` показывает plain text во время streaming.
Markdown рендерится только когда весь текст получен.

---

## ✅ Чеклист самопроверки

### ai/variance_agent.py
- [ ] Добавлен метод `async def chat_stream(self, message: str)`
- [ ] Используется `Runner.run_stream()` вместо `Runner.run()`
- [ ] Корректно итерируемся по stream: `async for event in stream`
- [ ] Yield только текстовые токены (проверка через `hasattr(event, 'text_delta')`)
- [ ] Опционально: показываем вызовы инструментов

### new_ui.py
- [ ] Создан wrapper generator для streaming
- [ ] Используется `st.write_stream()` вместо `st.markdown()`
- [ ] Полный ответ сохраняется в `st.session_state.messages`
- [ ] Spinner всё ещё показывается во время загрузки
- [ ] Код работает без ошибок

### Тестирование
- [ ] `streamlit run new_ui.py` запускается без ошибок
- [ ] Отправляешь сообщение агенту
- [ ] Ответ появляется **токен за токеном**, а не сразу весь
- [ ] После завершения streaming ответ сохраняется в истории
- [ ] История чата корректно отображается после перезагрузки страницы

---

## 🚀 Запуск и тестирование

### 1. Проверь что агент работает
```bash
cd /Users/mo/claude_code/variance-analyzer
source .venv/bin/activate  # Активируй окружение
python -c "from ai.variance_agent import VarianceAnalyst; print('OK')"
```

### 2. Запусти Streamlit
```bash
streamlit run new_ui.py
```

### 3. Протестируй streaming
- Открой http://localhost:8501
- Задай вопрос: "Покажи топ-5 отклонений"
- Наблюдай как ответ **появляется постепенно** 🎉

### 4. Проверь edge cases
- Задай сложный вопрос с вызовом нескольких инструментов
- Проверь что история сохраняется корректно
- Нажми "Очистить чат" и проверь что всё работает

---

## 📊 Ожидаемый результат

**До (текущее поведение):**
```
Пользователь: "Покажи топ-5"
[5 секунд тишины + spinner]
БАМ! → Весь ответ появляется сразу целиком
```

**После (с streaming):**
```
Пользователь: "Покажи топ-5"
[spinner]
"Хорошо" → "," → " давайте" → " найдём" → " топ" → "-5" → ...
[Текст появляется плавно, токен за токеном]
```

---

## 🎓 Что ты изучишь

1. ✅ `st.write_stream()` - streaming output в Streamlit
2. ✅ Async generators в Python
3. ✅ `Runner.run_stream()` - streaming в OpenAI Agents SDK
4. ✅ Синхронизация async/sync кода
5. ✅ Улучшение UX в AI чатах

---

## ❓ Если застрял - спрашивай!

**Полезные вопросы:**
- "Как правильно конвертировать async generator в sync?"
- "Покажи пример работы Runner.run_stream()"
- "Какие атрибуты у event объектов в Agents SDK?"
- "Как добавить задержку между токенами для визуального эффекта?"

---

## 🎁 Бонусные улучшения (опционально)

### 1. Показывать индикатор использования инструментов
```python
async def chat_stream(self, message: str):
    stream = Runner.run_stream(...)
    async for event in stream:
        if hasattr(event, 'text_delta') and event.text_delta:
            yield event.text_delta
        elif hasattr(event, 'tool_name'):
            yield f"\n\n🔧 **Использую {event.tool_name}**\n\n"
```

### 2. Добавить typing hints для генератора
```python
from typing import AsyncGenerator

async def chat_stream(self, message: str) -> AsyncGenerator[str, None]:
    """..."""
    yield "token"
```

### 3. Задержка между токенами для эффекта печати
```python
import time

def token_generator():
    for token in tokens:
        yield token
        time.sleep(0.015)  # 15ms = ~67 слов/мин (как человек печатает)
```

---

**Время начать!** ⏰

Начни с **Шага 1** (добавь `chat_stream()` в `VarianceAnalyst`), потом переходи к **Шагу 2** (обнови `new_ui.py`). Удачи! 🚀
