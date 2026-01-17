"""Streamlit интерфейс для Variance Analyzer AI."""
import streamlit as st
import asyncio
import pandas as pd
from pathlib import Path
from ai.variance_agent import VarianceAnalyst
from core.loader import load_from_uploaded_file
from ai import tools
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
    .file-info {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Проверка API ключа
if not os.getenv("OPENAI_API_KEY"):
    st.error("❌ Ошибка: установи OPENAI_API_KEY в .env файле")
    st.info("Создай .env файл: `echo 'OPENAI_API_KEY=your-key-here' > .env`")
    st.stop()

# Инициализация session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": """👋 Привет! Я AI ассистент для анализа variance (отклонений между фактом и бюджетом).

**Ты можешь:**
- Загрузить свой файл (CSV/XLSX) через боковую панель
- Спросить меня об анализе данных
- Посмотреть данные на табе "📊 Данные"

**Примеры вопросов:**
- Какие счета имеют наибольшее отклонение?
- Покажи топ-5 отклонений
- Какая сводная статистика?"""
        }
    ]

if "uploaded_dataframe" not in st.session_state:
    st.session_state.uploaded_dataframe = None
if "file_metadata" not in st.session_state:
    st.session_state.file_metadata = None
if "column_mapping" not in st.session_state:
    st.session_state.column_mapping = None
if "mapped_data" not in st.session_state:
    st.session_state.mapped_data = None
if "file_uploaded_trigger" not in st.session_state:
    st.session_state.file_uploaded_trigger = False

if "analyst" not in st.session_state:
    try:
        st.session_state.analyst = VarianceAnalyst("test_data.csv")
    except Exception as e:
        st.error(f"❌ Ошибка инициализации агента: {str(e)}")
        st.stop()

# Боковая панель с загрузкой файлов
with st.sidebar:
    st.header("📁 Загрузка данных")

    uploaded_file = st.file_uploader(
        "Загрузите ваш файл",
        type=["csv", "xlsx"],
        help="CSV или XLSX файл с финансовыми данными (макс 10 МБ)",
        key="file_uploader"
    )

    if uploaded_file:
        try:
            # Проверяем изменился ли файл
            if (st.session_state.file_metadata is None or
                st.session_state.file_metadata.filename != uploaded_file.name):

                with st.spinner("Загружаю файл..."):
                    # Загружаем файл
                    df, metadata = load_from_uploaded_file(uploaded_file)

                    # Сохраняем в session_state
                    st.session_state.uploaded_dataframe = df
                    st.session_state.file_metadata = metadata

                    # Сохраняем в глобальное хранилище для tools
                    tools._uploaded_dataframe = df

                    # Триггер для автоматического запроса маппинга
                    st.session_state.file_uploaded_trigger = True

                    st.success(f"✅ Файл загружен: {metadata.filename}")
                    st.rerun()

        except Exception as e:
            st.error(f"❌ Ошибка загрузки: {str(e)}")
            st.session_state.uploaded_dataframe = None
            st.session_state.file_metadata = None

    # Показываем информацию о текущем файле
    if st.session_state.file_metadata:
        metadata = st.session_state.file_metadata
        st.markdown("### 📋 Информация о файле")
        st.markdown(f"""
        - **Имя:** {metadata.filename}
        - **Размер:** {metadata.size_kb:.2f} КБ
        - **Строк:** {metadata.rows}
        - **Столбцов:** {len(metadata.columns)}
        - **Тип:** {metadata.file_type.upper()}
        """)

    st.divider()

    # Кнопка сброса
    if st.button("🔄 Сбросить всё", use_container_width=True):
        st.session_state.uploaded_dataframe = None
        st.session_state.file_metadata = None
        st.session_state.column_mapping = None
        st.session_state.mapped_data = None
        st.session_state.file_uploaded_trigger = False
        st.session_state.messages = []
        tools._uploaded_dataframe = None
        tools._column_mapping = None
        tools._mapped_variance_rows = None
        st.success("✅ Всё сброшено")
        st.rerun()

# Главная область - табы
st.title("🤖 Variance Analyzer AI")

tab1, tab2 = st.tabs(["💬 Чат с AI", "📊 Данные"])

with tab1:
    st.markdown("**Спроси меня об анализе отклонений в финансовых данных**")
    st.divider()

    # Отображение истории сообщений
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Автоматический запрос маппинга после загрузки файла
    if st.session_state.file_uploaded_trigger:
        st.session_state.file_uploaded_trigger = False

        # Добавляем системное сообщение
        auto_message = "Файл загружен. Проанализируй столбцы и предложи маппинг."
        st.session_state.messages.append({"role": "user", "content": "🔄 Файл загружен, анализирую..."})

        with st.chat_message("assistant"):
            with st.spinner("Анализирую столбцы файла..."):
                try:
                    # Создаём асинхронный генератор для стриминга
                    async def stream_response():
                        async for chunk in st.session_state.analyst.chat_stream(auto_message):
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

        st.rerun()

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

with tab2:
    if st.session_state.uploaded_dataframe is not None:
        df = st.session_state.uploaded_dataframe
        metadata = st.session_state.file_metadata

        # Секция 1: Информация о файле
        st.markdown("### 📋 Информация о файле")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Строки", metadata.rows)
        with col2:
            st.metric("Столбцы", len(metadata.columns))
        with col3:
            st.metric("Размер", f"{metadata.size_kb:.2f} КБ")
        with col4:
            st.metric("Тип", metadata.file_type.upper())

        st.divider()

        # Секция 2: Превью данных
        st.markdown("### 📊 Превью данных")
        st.dataframe(df.head(20), use_container_width=True)

        st.divider()

        # Секция 3: Статистика по столбцам
        st.markdown("### 📈 Статистика по столбцам")

        col_stats = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            null_count = int(df[col].isnull().sum())
            unique_count = int(df[col].nunique())

            col_stats.append({
                "Столбец": col,
                "Тип": dtype,
                "Уникальных": unique_count,
                "Пустых": null_count
            })

        stats_df = pd.DataFrame(col_stats)
        st.dataframe(stats_df, use_container_width=True)

        st.divider()

        # Секция 4: Скачивание
        st.markdown("### 💾 Скачать данные")

        # CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Скачать как CSV",
            data=csv,
            file_name=f"variance_data_{metadata.filename}.csv",
            mime="text/csv",
        )

    else:
        st.info("📁 Загрузите файл через боковую панель чтобы увидеть данные")
        st.markdown("""
        ### Как начать:
        1. Нажмите на **"Browse files"** в боковой панели
        2. Выберите CSV или XLSX файл (макс 10 МБ)
        3. Файл должен содержать минимум 2 столбца и 1 строку данных
        4. После загрузки AI автоматически предложит маппинг столбцов
        5. Подтвердите или скорректируйте маппинг в чате
        6. Начните анализировать данные!
        """)

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
