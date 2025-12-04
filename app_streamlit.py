"""Streamlit интерфейс для Variance Analyzer AI."""
import streamlit as st
import asyncio
from pathlib import Path
from ai.variance_agent import VarianceAnalyst, interactive_mode
from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv()

# Настройка страницы
st.set_page_config(
    page_title="Variance Analyzer AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Стили
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .main > div {
        padding: 2rem;
        background: white;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        animation: fadeIn 0.3s ease-in;
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 20%;
    }
    .assistant-message {
        background: #f0f2f6;
        color: #333;
        margin-right: 20%;
    }
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
</style>
""", unsafe_allow_html=True)

# Заголовок
st.title("🤖 Variance Analyzer AI")
st.markdown("**Спроси меня об анализе отклонений в финансовых данных**")
st.divider()

# Проверка API ключа
if not os.getenv("OPENAI_API_KEY"):
    st.error("❌ Ошибка: установи OPENAI_API_KEY в .env файле")
    st.info("Создай .env файл: `echo 'OPENAI_API_KEY=your-key-here' > .env`")
    st.stop()

# Боковая панель с настройками
with st.sidebar:
    st.header("⚙️ Настройки")

    # Выбор файла данных
    data_file = st.text_input(
        "Файл данных",
        value="test_data.csv",
        help="Путь к CSV/XLSX файлу с данными"
    )

    st.divider()

    st.markdown("### 💡 Примеры вопросов:")
    st.markdown("""
    - Какие счета имеют наибольшее отклонение?
    - Покажи топ-5 отклонений
    - Какая сводная статистика?
    - Где мы перерасходовали бюджет?
    """)

    st.divider()

    # Кнопка очистки истории
    if st.button("🗑️ Очистить историю", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Инициализация session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": """👋 Привет! Я AI ассистент для анализа variance (отклонений между фактом и бюджетом).

**Ты можешь спросить меня:**
- Какие счета имеют наибольшее отклонение?
- Покажи топ-5 отклонений
- Какая сводная статистика по данным?
- Где мы перерасходовали бюджет?"""
        }
    ]

if "analyst" not in st.session_state:
    try:
        st.session_state.analyst = interactive_mode(data_file)
    except Exception as e:
        st.error(f"❌ Ошибка инициализации агента: {str(e)}")
        st.stop()

# Отображение истории сообщений
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Поле ввода
if prompt := st.chat_input("Напиши свой вопрос..."):
    # Добавить сообщение пользователя
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Получить ответ от агента со стримингом
    with st.chat_message("assistant"):
        try:
            # Создаём асинхронный генератор для стриминга
            async def stream_response():
                async for chunk in st.session_state.analyst.chat_stream(prompt):
                    yield chunk

            # Оборачиваем в синхронный генератор для st.write_stream
            def sync_stream():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    async_gen = stream_response()
                    while True:
                        try:
                            chunk = loop.run_until_complete(async_gen.__anext__())
                            yield chunk
                        except StopAsyncIteration:
                            break
                finally:
                    loop.close()

            # Отобразить стрим
            response = st.write_stream(sync_stream())

            # Добавить в историю
            st.session_state.messages.append(
                {"role": "assistant", "content": response}
            )
        except Exception as e:
            error_message = f"❌ Ошибка: {str(e)}"
            st.error(error_message)
            st.session_state.messages.append(
                {"role": "assistant", "content": error_message}
            )

# Футер
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 1rem;'>
        Powered by OpenAI Agents SDK | Made with ❤️ using Streamlit
    </div>
    """,
    unsafe_allow_html=True
)
