"""Pydantic схемы для API валидации и сериализации."""
from pydantic import BaseModel, Field
from typing import Optional


class AnalysisParamsRequest(BaseModel):
    """Параметры для variance analysis (запрос от клиента)."""

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
    """Одна строка variance analysis (ответ клиенту)."""

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

    @staticmethod
    def from_variance_report(report, params_request) -> "AnalysisResponse":
        """Конвертирует core.models.VarianceReport в API response."""
        return AnalysisResponse(
            rows=[VarianceRowResponse(**row.__dict__) for row in report.rows],
            total_rows=report.total_rows,
            filtered_rows=report.filtered_rows,
            params=params_request
        )


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

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "version": "1.0.0"
            }
        }


class ChatRequest(BaseModel):
    """Запрос для чата с AI агентом."""

    message: str = Field(description="Сообщение пользователя")
    file_path: Optional[str] = Field(default="test_data.csv", description="Путь к файлу данных")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Какие счета имеют наибольшее отклонение?",
                "file_path": "test_data.csv"
            }
        }


class ChatResponse(BaseModel):
    """Ответ от AI агента."""

    response: str = Field(description="Ответ агента")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Анализируя данные, наибольшее отклонение имеет счёт Revenue..."
            }
        }
