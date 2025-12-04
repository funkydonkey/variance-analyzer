# Task: Streaming Chat для AI агента

## 🎯 Цель
Научиться добавлять **streaming responses** в FastAPI с использованием Server-Sent Events (SSE) и интегрировать с OpenAI Agents SDK.

## 📋 Быстрый старт (TL;DR)

### Что уже сделано ✅
- ✅ Frontend обновлён (`frontend/chat.html`)
- ✅ EventSource API интегрирован
- ✅ Streaming UI готов к работе

### Что ТЕБЕ нужно сделать 🔨

1. **Установи библиотеку:**
   ```bash
   pip install sse-starlette
   ```

2. **Добавь в `api/routes.py`:**
   ```python
   from sse_starlette.sse import EventSourceResponse

   @router.get("/chat/stream")
   async def chat_with_agent_stream(
       message: str = Query(...),
       file_path: str = Query("test_data.csv")
   ):
       async def event_generator():
           # См. детальный код ниже в Шаге 3
           pass

       return EventSourceResponse(event_generator())
   ```

3. **Запусти и протестируй:**
   ```bash
   uvicorn api.main:app --reload --port 8000
   # Открой http://localhost:8000/frontend/chat.html
   ```

**⏱️ Время выполнения:** ~20-30 минут

---

## Что такое SSE (Server-Sent Events)?
- Технология для отправки событий от сервера к клиенту в real-time
- Проще чем WebSocket (однонаправленный поток)
- Идеально для стриминга текста от LLM

## Архитектура решения

```
Frontend (EventSource)  →  Backend (FastAPI SSE)  →  OpenAI Agent (run_stream)
      ↓                            ↓                           ↓
   Получает токены         Отправляет SSE events      Генерирует токены
```

---

## Часть 1: Backend (FastAPI SSE endpoint) - ТЫ ПИШЕШЬ

### Шаг 1: Добавь streaming endpoint в `api/routes.py`

⚠️ **ВАЖНО:** EventSource API поддерживает только GET запросы! Используй query параметры вместо request body.

```python
from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse
import json

@router.get("/chat/stream")  # ← GET, не POST!
async def chat_with_agent_stream(
    message: str = Query(..., description="Вопрос пользователя"),
    file_path: str = Query("test_data.csv", description="Путь к файлу данных")
):
    """
    Стримящий чат с AI агентом через Server-Sent Events.

    Подсказки:
    1. Используй async generator для отправки SSE events
    2. Каждый event в формате: data: {"delta": "токен", "done": false}
    3. В конце отправь: data: {"done": true}
    4. Оберни в EventSourceResponse

    OpenAI Agents SDK streaming API:
    - Runner.run_stream(agent, message, session) возвращает AsyncIterator
    - Итерируйся по нему: async for event in stream
    - event может быть разных типов (text_delta, tool_call, etc)
    """

    async def event_generator():
        # TODO: Создай VarianceAnalyst
        # TODO: Получи stream через Runner.run_stream()
        # TODO: Итерируйся по stream и yield SSE events
        # Формат: yield {"event": "message", "data": json.dumps({"delta": "текст"})}
        pass

    return EventSourceResponse(event_generator())
```

### Шаг 2: Установи зависимость
```bash
pip install sse-starlette
```

### Шаг 3: Реализуй event_generator

**Полный псевдокод с детальными подсказками:**

```python
async def event_generator():
    """
    Генератор SSE событий для стриминга ответа агента.

    Формат SSE:
    yield {
        "event": "message",  # Тип события
        "data": json.dumps({"delta": "текст", "done": False})  # JSON данные
    }
    """
    try:
        # 1. Создаём агента
        analyst = VarianceAnalyst(file_path)

        # 2. Получаем streaming iterator из Agents SDK
        from agents import Runner
        stream = Runner.run_stream(
            agent=analyst.agent,
            messages=message,  # Сообщение пользователя
            session=analyst.session
        )

        # 3. Итерируемся по событиям stream
        async for event in stream:
            # Проверяем тип события
            # OpenAI Agents SDK генерирует объекты с разными атрибутами

            # Вариант 1: Текстовый токен (именно это нам нужно!)
            if hasattr(event, 'text_delta') and event.text_delta:
                yield {
                    "event": "message",
                    "data": json.dumps({"delta": event.text_delta, "done": False})
                }

            # Вариант 2: Вызов инструмента (опционально - для debugging)
            elif hasattr(event, 'tool_name'):
                # Можно показать "🔧 Использую get_variance_data..."
                yield {
                    "event": "message",
                    "data": json.dumps({"delta": f"\n\n🔧 Использую {event.tool_name}...\n\n", "done": False})
                }

            # Вариант 3: Финальный output (завершение)
            elif hasattr(event, 'final_output'):
                yield {
                    "event": "message",
                    "data": json.dumps({"done": True})
                }

        # 4. Отправляем финальное событие (если не было final_output)
        yield {
            "event": "message",
            "data": json.dumps({"done": True})
        }

    except Exception as e:
        # Обрабатываем ошибки внутри генератора!
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)})
        }
```

**Важные детали:**

1. **Формат yield** - должен быть dict с ключами "event" и "data"
2. **JSON сериализация** - data должен быть строкой, поэтому `json.dumps()`
3. **Проверка атрибутов** - используй `hasattr()` чтобы узнать тип события
4. **Error handling** - try/except ВНУТРИ генератора, иначе SSE прервётся
5. **Финальное событие** - обязательно отправь `{"done": True}` в конце

**Возможные атрибуты event объекта:**
- `event.text_delta` - кусочек текста от LLM
- `event.tool_name` - имя вызываемого инструмента
- `event.tool_input` - аргументы инструмента
- `event.tool_output` - результат инструмента
- `event.final_output` - финальный ответ

**Документация:** Проверь актуальные названия атрибутов в [OpenAI Agents SDK Repo](https://github.com/openai/openai-agents-sdk) - они могут отличаться от моих примеров!

---

## Часть 2: Frontend (JavaScript EventSource) - Я ПИШУ

Обновлю `frontend/chat.html` чтобы:
1. Использовать `EventSource` API вместо `fetch`
2. Добавлять токены к сообщению по мере получения
3. Показывать анимацию печати

---

## Часть 3: OpenAI Agents SDK Streaming API

### Документация по streaming:

```python
from agents import Agent, Runner

# Non-streaming (текущий способ)
result = await Runner.run(agent, message, session=session)
print(result.final_output)

# Streaming
stream = Runner.run_stream(agent, message, session=session)
async for event in stream:
    print(event)  # Разные типы событий
```

### Типы событий в stream:
1. **RunStarted** - запуск
2. **TextDelta** - новый токен текста
3. **ToolCallDelta** - вызов инструмента
4. **ToolResult** - результат инструмента
5. **RunCompleted** - завершение

**Тебе нужны только `TextDelta` события** для стриминга ответа пользователю.

---

## Чеклист самопроверки

### Backend:
- [ ] Добавлен endpoint `/api/chat/stream` в `api/routes.py`
- [ ] Установлена библиотека `sse-starlette`
- [ ] Реализован `async def event_generator()`
- [ ] Используется `Runner.run_stream()` вместо `Runner.run()`
- [ ] События отправляются в формате SSE
- [ ] Обработаны ошибки внутри генератора
- [ ] Endpoint возвращает `EventSourceResponse`

### Тестирование:

**1. Запуск сервера:**
```bash
uvicorn api.main:app --reload --port 8000
```

**2. Тест через браузер (рекомендуется):**
```bash
# Открой в браузере
http://localhost:8000/frontend/chat.html

# Спроси что-то у агента:
# "Покажи топ-5 отклонений"
# "Какая общая статистика?"
```

**3. Тест через curl (для debugging):**
```bash
# GET запрос с query параметрами
curl -N "http://localhost:8000/api/chat/stream?message=Покажи%20топ-5%20отклонений&file_path=test_data.csv"

# Флаг -N отключает буферизацию для streaming
```

**4. Проверка логов:**
- Смотри в терминале вывод от FastAPI
- В браузере открой DevTools → Console для ошибок JavaScript
- В Network tab смотри SSE соединение (тип `text/event-stream`)

**Ожидаемый output в curl:**
```
data: {"delta": "Хорошо", "done": false}

data: {"delta": ", давайте", "done": false}

data: {"delta": " найдём", "done": false}

data: {"delta": " топ-5", "done": false}

...

data: {"done": true}
```

---

## Подсказки и ресурсы

### SSE формат:
```
event: message
data: {"delta": "Привет", "done": false}

event: message
data: {"delta": " мир", "done": false}

event: message
data: {"done": true}
```

### FastAPI SSE примеры:
- [SSE-Starlette Docs](https://github.com/sysid/sse-starlette)
- [FastAPI Streaming Response](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)

### OpenAI Agents SDK:
- [GitHub](https://github.com/openai/openai-agents-sdk)
- Документация по streaming в README

---

## Edge Cases

1. **Что если stream прерывается?**
   - Оберни в try/except внутри генератора
   - Отправь event с типом "error"

2. **Что если пользователь закрыл страницу?**
   - EventSource автоматически закрывается
   - FastAPI прервёт генератор

3. **Как обрабатывать вызовы tools?**
   - Tool calls тоже приходят в stream
   - Можешь показывать "🔧 Использую инструмент..."

---

## Debugging Guide 🐛

### Проблема: "EventSource failed"
**Причина:** Backend endpoint не существует или возвращает не SSE
**Решение:**
1. Проверь что endpoint `/api/chat/stream` доступен
2. Убедись что возвращается `EventSourceResponse`, а не обычный JSON
3. Проверь query параметры в URL

### Проблема: "Нет ответа от агента"
**Причина:** Ошибка внутри `event_generator`
**Решение:**
1. Добавь `print()` в генератор для debugging
2. Проверь что `VarianceAnalyst` создаётся корректно
3. Убедись что файл `test_data.csv` существует
4. Смотри логи FastAPI в терминале

### Проблема: "Текст не стримится, появляется сразу весь"
**Причина:** Используется `Runner.run()` вместо `Runner.run_stream()`
**Решение:** Замени на `Runner.run_stream()` и итерируйся по нему

### Проблема: "TypeError: object is not iterable"
**Причина:** Неправильный формат yield в генераторе
**Решение:** Убедись что yield возвращает dict: `yield {"event": "message", "data": "..."}`

### Проблема: "JSON parse error в frontend"
**Причина:** data не сериализован в JSON
**Решение:** Используй `json.dumps({"delta": "...", "done": False})`

---

## Следующие шаги после реализации

✅ **Сделано:**
- Frontend с EventSource готов
- Task Spec создан
- Debugging guide написан

🔨 **Твоя задача:**
1. Реализуй `/api/chat/stream` endpoint
2. Протестируй в браузере
3. Если застрял - задай вопрос!

🚀 **Опционально (бонусы):**
- Добавь визуализацию tool calls (иконки 🔧 в чате)
- Покажи прогресс "Анализирую данные..."
- Добавь retry логику при обрыве соединения

---

## Полезные команды

```bash
# Проверить что сервер запущен
curl http://localhost:8000/api/health

# Посмотреть все routes
curl http://localhost:8000/docs

# Тест non-streaming endpoint (для сравнения)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "file_path": "test_data.csv"}'

# Установить зависимости
pip install sse-starlette agents openai
```

---

**Вопросы? Застрял?** Спрашивай:
- "Как правильно итерироваться по stream?"
- "Какой формат у event от Agents SDK?"
- "Как отправить SSE event?"
- "Покажи пример рабочего генератора?"

**Когда закончишь** - напиши "готово" и я сделаю code review! 👨‍🏫
