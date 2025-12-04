# Task 02: FastAPI Backend - API для Variance Analysis

## 🎯 Цель задачи

В этой задаче ты научишься:
- Создавать REST API с использованием **FastAPI**
- Работать с **Pydantic** для валидации данных
- Обрабатывать **загрузку файлов** (file upload)
- Интегрировать **core-модули** с API
- Правильно **обрабатывать ошибки** в API
- Возвращать **структурированные JSON** ответы

**Результат:** Работающий FastAPI backend с 3 эндпоинтами для анализа variance.

---

## 📁 Файлы для работы

Тебе нужно реализовать 3 модуля в папке `api/`:

1. **`api/schemas.py`** - Pydantic схемы для валидации запросов/ответов
2. **`api/routes.py`** - API endpoints (роуты)
3. **`api/main.py`** - FastAPI приложение

---

## 📋 План выполнения

### Шаг 1: Создать Pydantic схемы (`api/schemas.py`)

**Что нужно сделать:**
Создай схемы для валидации входящих запросов и исходящих ответов.

```python
from pydantic import BaseModel, Field
from typing import Optional


class AnalysisParamsRequest(BaseModel):
    """Параметры для variance analysis (запрос от клиента).

    Эта схема используется для валидации JSON, который клиент
    отправляет в POST /analyze.
    """
    min_absolute_threshold: float = Field(
        default=0.0,
        ge=0,
        description="Минимальное абсолютное отклонение для фильтрации"
    )
    min_percentage_threshold: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Минимальное процентное отклонение (0-100%)"
    )
    periods: Optional[list[str]] = Field(
        default=None,
        description="Список периодов для фильтрации (None = все)"
    )
    accounts: Optional[list[str]] = Field(
        default=None,
        description="Список статей для фильтрации (None = все)"
    )

    # TODO: Добавь пример для документации Swagger
    class Config:
        json_schema_extra = {
            "example": {
                "min_absolute_threshold": 100.0,
                "min_percentage_threshold": 10.0,
                "periods": ["2024-01", "2024-02"],
                "accounts": ["Revenue", "COGS"]
            }
        }


class VarianceRowResponse(BaseModel):
    """Одна строка variance analysis (ответ клиенту).

    Преобразуется из core.models.VarianceRow в JSON.
    """
    account: str
    period: str
    actual: float
    budget: float
    absolute_variance: Optional[float]
    percentage_variance: Optional[float]

    class Config:
        json_schema_extra = {
            "example": {
                "account": "Revenue",
                "period": "2024-01",
                "actual": 1000.0,
                "budget": 800.0,
                "absolute_variance": 200.0,
                "percentage_variance": 25.0
            }
        }


class AnalysisResponse(BaseModel):
    """Полный результат variance analysis (ответ клиенту)."""

    rows: list[VarianceRowResponse] = Field(
        description="Список строк с variance"
    )
    total_rows: int = Field(
        description="Количество строк до фильтрации"
    )
    filtered_rows: int = Field(
        description="Количество строк после фильтрации"
    )
    params: AnalysisParamsRequest = Field(
        description="Параметры, с которыми выполнен анализ"
    )

    # TODO: Добавь метод для конвертации VarianceReport → AnalysisResponse
    @staticmethod
    def from_variance_report(report) -> "AnalysisResponse":
        """Конвертирует core.models.VarianceReport в API response.

        Args:
            report: Объект VarianceReport из core модуля

        Returns:
            AnalysisResponse для отправки клиенту

        Подсказка:
            Используй [VarianceRowResponse(**row.__dict__) for row in report.rows]
            для конвертации списка VarianceRow в VarianceRowResponse
        """
        pass  # ← реализуй


class ErrorResponse(BaseModel):
    """Стандартный формат ошибок API."""
    error: str = Field(description="Тип ошибки")
    message: str = Field(description="Подробное описание ошибки")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Missing required columns: account, period"
            }
        }


class HealthResponse(BaseModel):
    """Ответ health check эндпоинта."""
    status: str = Field(default="ok", description="Статус API")
    version: str = Field(default="1.0.0", description="Версия API")
```

**Важно:**
- `Field()` позволяет добавить валидацию и описание
- `Config.json_schema_extra` добавляет примеры в Swagger документацию
- `from_variance_report()` - помощник для конвертации между слоями

---

### Шаг 2: Создать API endpoints (`api/routes.py`)

**Что нужно сделать:**
Создай 3 эндпоинта:

```python
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pathlib import Path
import tempfile
from typing import Optional

from api.schemas import (
    AnalysisParamsRequest,
    AnalysisResponse,
    ErrorResponse,
    HealthResponse
)
from core.loader import load_report
from core.calculator import calculate_variance_bulk
from core.filters import apply_filters
from core.models import AnalysisParams, VarianceReport


router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Проверка работоспособности API"
)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Статус API и версию
    """
    pass  # ← реализуй


@router.post(
    "/upload",
    response_model=dict,
    summary="Загрузить файл отчёта",
    description="Загружает CSV или XLSX файл и возвращает количество строк",
    responses={
        400: {"model": ErrorResponse, "description": "Неправильный формат файла"}
    }
)
async def upload_file(
    file: UploadFile = File(..., description="CSV или XLSX файл с отчётом")
) -> dict:
    """Загружает файл отчёта и возвращает базовую информацию.

    Шаги реализации:
        1. Проверить расширение файла (.csv или .xlsx)
        2. Сохранить загруженный файл во временную директорию
        3. Использовать core.loader.load_report() для загрузки
        4. Вернуть количество строк и список периодов/аккаунтов

    Args:
        file: Загруженный файл

    Returns:
        {
            "filename": "report.csv",
            "rows_count": 100,
            "periods": ["2024-01", "2024-02"],
            "accounts": ["Revenue", "COGS", "Rent"]
        }

    Raises:
        HTTPException 400: Если файл не CSV/XLSX или некорректный формат

    Подсказки:
        - file.filename содержит имя файла
        - file.file - это file-like объект для чтения
        - tempfile.NamedTemporaryFile() для временного файла
        - Path(file.filename).suffix для получения расширения
        - set(row.period for row in rows) для уникальных периодов
    """
    pass  # ← реализуй


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Выполнить variance analysis",
    description="Загружает файл, выполняет variance analysis и возвращает результаты",
    responses={
        400: {"model": ErrorResponse, "description": "Ошибка валидации данных"},
        500: {"model": ErrorResponse, "description": "Внутренняя ошибка сервера"}
    }
)
async def analyze_variance(
    file: UploadFile = File(..., description="CSV или XLSX файл"),
    params: Optional[AnalysisParamsRequest] = None
) -> AnalysisResponse:
    """Выполняет полный variance analysis.

    Шаги реализации:
        1. Загрузить файл (как в upload_file)
        2. Использовать core.loader.load_report() для парсинга
        3. Рассчитать variance с помощью core.calculator.calculate_variance_bulk()
        4. Конвертировать AnalysisParamsRequest → core.models.AnalysisParams
        5. Применить фильтры с помощью core.filters.apply_filters()
        6. Создать VarianceReport
        7. Конвертировать в AnalysisResponse через from_variance_report()

    Args:
        file: Загруженный файл
        params: Параметры анализа (опционально, используются дефолтные если None)

    Returns:
        AnalysisResponse с результатами анализа

    Raises:
        HTTPException 400: Ошибка валидации файла
        HTTPException 500: Непредвиденная ошибка

    Подсказка по обработке ошибок:
        try:
            # твой код
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal error: {str(e)}"
            )
    """
    pass  # ← реализуй
```

**Важные моменты:**

1. **Загрузка файлов:**
```python
# Сохранение загруженного файла во временную директорию:
with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
    content = await file.read()
    tmp.write(content)
    tmp_path = Path(tmp.name)

# Теперь tmp_path можно передать в load_report()
```

2. **Обработка ошибок:**
```python
# Всегда оборачивай в try/except и возвращай понятные ошибки
raise HTTPException(
    status_code=400,
    detail="Missing required columns: account, period"
)
```

3. **Конвертация между слоями:**
```python
# Pydantic → core.models
core_params = AnalysisParams(
    min_absolute_threshold=params.min_absolute_threshold,
    # ...
)

# core.models → Pydantic (через from_variance_report)
```

---

### Шаг 3: Создать FastAPI приложение (`api/main.py`)

**Что нужно сделать:**
Собери всё воедино - создай FastAPI app и подключи роуты.

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

# TODO: Создай FastAPI приложение
app = FastAPI(
    title="Variance Analyzer API",
    description="REST API для анализа variance между фактическими и бюджетными показателями",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# TODO: Настрой CORS (для работы фронтенда)
# Подсказка: позволь любым origins для разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO: Подключи router
app.include_router(router, prefix="/api", tags=["variance"])

# TODO: Добавь корневой endpoint
@app.get("/")
async def root():
    """Корневой endpoint - перенаправляет на документацию."""
    return {
        "message": "Variance Analyzer API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/health"
    }


# Для запуска через uvicorn:
# uvicorn api.main:app --reload --port 8000
```

**Подсказки:**
- `prefix="/api"` → все роуты будут начинаться с `/api/`
- `tags=["variance"]` → группировка в Swagger UI
- CORS нужен чтобы фронтенд мог делать запросы к API

---

## 🔗 Подсказки и ресурсы

### FastAPI
- [Официальная документация](https://fastapi.tiangolo.com/)
- [File Upload](https://fastapi.tiangolo.com/tutorial/request-files/)
- [Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)

### Pydantic
- [Документация](https://docs.pydantic.dev/)
- [Field validation](https://docs.pydantic.dev/latest/concepts/fields/)

### Загрузка файлов
```python
from fastapi import UploadFile, File

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    # Прочитать содержимое
    content = await file.read()

    # Получить имя файла
    filename = file.filename

    # Получить content type
    content_type = file.content_type
```

### Временные файлы
```python
import tempfile
from pathlib import Path

# Создать временный файл с нужным расширением
with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
    tmp.write(content)
    tmp_path = Path(tmp.name)

# Использовать tmp_path
# Не забыть удалить после: tmp_path.unlink()
```

### Конвертация между слоями
```python
# core.models.VarianceRow → api.schemas.VarianceRowResponse
response_rows = [VarianceRowResponse(**row.__dict__) for row in core_rows]

# api.schemas.AnalysisParamsRequest → core.models.AnalysisParams
core_params = AnalysisParams(
    min_absolute_threshold=request.min_absolute_threshold,
    min_percentage_threshold=request.min_percentage_threshold,
    periods=request.periods,
    accounts=request.accounts
)
```

---

## ✅ Чеклист самопроверки

Перед тем как сообщить "готово", проверь:

### schemas.py
- [ ] Все Pydantic схемы созданы с правильными типами
- [ ] Field() используется для валидации и описания
- [ ] json_schema_extra содержит примеры
- [ ] `from_variance_report()` корректно конвертирует данные

### routes.py
- [ ] `/health` возвращает статус и версию
- [ ] `/upload` принимает файл и возвращает базовую информацию
- [ ] `/analyze` выполняет полный пайплайн: load → calculate → filter → response
- [ ] Все ошибки обрабатываются через HTTPException
- [ ] Временные файлы удаляются после использования

### main.py
- [ ] FastAPI app создан с корректным title и description
- [ ] CORS настроен
- [ ] Router подключён с prefix="/api"
- [ ] Корневой endpoint "/" возвращает информацию об API

### Общее
- [ ] API запускается: `uvicorn api.main:app --reload`
- [ ] Swagger документация доступна: http://localhost:8000/docs
- [ ] Health check работает: `curl http://localhost:8000/api/health`
- [ ] Нет import ошибок

---

## 🧪 Тестирование API

После реализации протестируй API вручную:

### 1. Запустить сервер
```bash
uvicorn api.main:app --reload --port 8000
```

### 2. Открыть Swagger UI
Перейди в браузере: http://localhost:8000/docs

### 3. Протестировать через curl

**Health check:**
```bash
curl http://localhost:8000/api/health
```

**Upload файла:**
```bash
# Сначала создай тестовый CSV:
echo "account,period,actual,budget
Revenue,2024-01,1000,800
COGS,2024-01,400,500" > test_report.csv

# Загрузи:
curl -X POST http://localhost:8000/api/upload \
  -F "file=@test_report.csv"
```

**Analyze:**
```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@test_report.csv" \
  -F 'params={"min_absolute_threshold": 0, "min_percentage_threshold": 0}'
```

---

## 🎓 Что ты изучишь в этой задаче:

1. ✅ **FastAPI** - современный Python веб-фреймворк
2. ✅ **Pydantic** - валидация данных и сериализация
3. ✅ **REST API** - создание endpoints и обработка HTTP запросов
4. ✅ **File Upload** - загрузка и обработка файлов
5. ✅ **Error Handling** - правильная обработка ошибок в API
6. ✅ **API Documentation** - автоматическая генерация Swagger/ReDoc
7. ✅ **Интеграция слоёв** - связывание API с бизнес-логикой (core)

---

## ❓ Если застрял

Спрашивай:
- "Как правильно читать UploadFile в FastAPI?"
- "Как конвертировать dataclass в Pydantic модель?"
- "Покажи пример HTTPException с разными статусами"
- "Как работает tempfile.NamedTemporaryFile?"

Я помогу подсказками, но **не напишу код за тебя** - это твоя зона роста! 💪

---

## 🚀 После завершения Task 02

Когда закончишь - пиши **"API готов"**, и я:
1. Напишу тесты для API (integration tests)
2. Создам полноценный фронтенд (HTML/CSS/JS)
3. Интегрирую всё вместе

**Начинай с `api/schemas.py` - это самое простое!**

Удачи! 🎯
