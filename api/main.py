"""FastAPI приложение для Variance Analyzer."""
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from api.routes import router

# Загрузка переменных окружения из .env
load_dotenv()

# Создание FastAPI приложения
app = FastAPI(
    title="Variance Analyzer API",
    description="REST API для анализа variance между фактическими и бюджетными показателями",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# Настройка CORS (для работы фронтенда)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение router
app.include_router(router, prefix="/api", tags=["variance"])

# Подключение статических файлов (frontend)
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_path)), name="frontend")


@app.get("/")
async def root():
    """Корневой endpoint - перенаправляет на документацию."""
    return {
        "message": "Variance Analyzer API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/health"
    }


# Для запуска:
# uvicorn api.main:app --reload --port 8000
