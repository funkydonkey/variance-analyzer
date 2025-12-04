"""API endpoints для variance analysis."""
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Form, Query
from sse_starlette import EventSourceResponse
from agents import Runner
from pathlib import Path
import tempfile
from typing import Optional
import json

from api.schemas import (
    AnalysisParamsRequest,
    AnalysisResponse,
    ErrorResponse,
    HealthResponse,
    ChatRequest,
    ChatResponse
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
    """Health check endpoint."""
    return HealthResponse(status="ok", version="1.0.0")


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
    """Загружает файл отчёта и возвращает базовую информацию."""

    # Проверка расширения файла
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_extension}. Use .csv or .xlsx"
        )

    try:
        # Сохранение во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)

        # Загрузка данных
        file_type = "csv" if file_extension == ".csv" else "xlsx"
        rows = load_report(tmp_path, file_type=file_type)

        # Удаление временного файла
        tmp_path.unlink()

        # Извлечение уникальных периодов и аккаунтов
        periods = sorted(set(row.period for row in rows))
        accounts = sorted(set(row.account for row in rows))

        return {
            "filename": file.filename,
            "rows_count": len(rows),
            "periods": periods,
            "accounts": accounts
        }

    except ValueError as e:
        if tmp_path.exists():
            tmp_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        if tmp_path.exists():
            tmp_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


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
    min_absolute_threshold: float = Form(0.0),
    min_percentage_threshold: float = Form(0.0),
    periods: Optional[str] = Form(None),
    accounts: Optional[str] = Form(None)
) -> AnalysisResponse:
    """Выполняет полный variance analysis."""

    # Проверка расширения файла
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_extension}"
        )

    tmp_path = None
    try:
        # 1. Загрузить файл во временную директорию
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)

        # 2. Загрузить данные
        file_type = "csv" if file_extension == ".csv" else "xlsx"
        rows = load_report(tmp_path, file_type=file_type)

        # 3. Рассчитать variance
        rows_with_variance = calculate_variance_bulk(rows)

        # 4. Парсинг параметров
        periods_list = json.loads(periods) if periods and periods != "null" else None
        accounts_list = json.loads(accounts) if accounts and accounts != "null" else None

        params_request = AnalysisParamsRequest(
            min_absolute_threshold=min_absolute_threshold,
            min_percentage_threshold=min_percentage_threshold,
            periods=periods_list,
            accounts=accounts_list
        )

        # 5. Конвертация в core.models.AnalysisParams
        core_params = AnalysisParams(
            min_absolute_threshold=params_request.min_absolute_threshold,
            min_percentage_threshold=params_request.min_percentage_threshold,
            periods=params_request.periods,
            accounts=params_request.accounts
        )

        # 6. Применить фильтры
        filtered_rows = apply_filters(rows_with_variance, core_params)

        # 7. Создать VarianceReport
        report = VarianceReport(
            rows=filtered_rows,
            params=core_params,
            total_rows=len(rows_with_variance),
            filtered_rows=len(filtered_rows)
        )

        # 8. Конвертировать в API response
        response = AnalysisResponse.from_variance_report(report, params_request)

        return response

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
    finally:
        # Удаление временного файла
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Чат с AI агентом",
    description="Отправить сообщение AI агенту для анализа данных",
    responses={
        500: {"model": ErrorResponse, "description": "Ошибка AI агента"}
    }
)
async def chat_with_agent(request: ChatRequest) -> ChatResponse:
    """Чат с AI агентом для variance analysis."""
    try:
        from ai.variance_agent import VarianceAnalyst, interactive_mode

        # Создаём агента с указанным файлом
        analyst = VarianceAnalyst(request.file_path)
        # await interactive_mode(request.file_path)

        # Получаем ответ от агента
        response = await analyst.chat(request.message)

        return ChatResponse(response=response)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI agent error: {str(e)}"
        )



@router.get("/chat/stream")
async def chat_with_agent_stream(
    message: str = Query(..., description="Вопрос пользователя"),
    file_path: str = Query("test_data.csv", description="Путь к файлу данных")
):
    """
    Стримящий чат с AI агентом через Server-Sent Events.

    Returns:
        EventSourceResponse: Streaming SSE response с токенами от AI агента
    """

    async def event_generator():
        """Генератор SSE событий для стриминга ответа агента."""
        try:
            from ai.variance_agent import VarianceAnalyst

            # Создать агента
            analyst = VarianceAnalyst(file_path)

            # Получить streaming результат
            result = Runner.run_streamed(analyst.agent, message)
            stream = result.stream_events()

            # Итерироваться по событиям и отправлять текстовые токены
            async for event in stream:
                # Проверяем event.data.delta для текстовых токенов
                if hasattr(event, 'data') and hasattr(event.data, 'delta') and event.data.delta:
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "delta": event.data.delta,
                            "done": False
                        })
                    }

            # Финальное событие
            yield {
                "event": "message",
                "data": json.dumps({"done": True})
            }

        except Exception as e:
            # Обработка ошибок внутри генератора
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(event_generator())