from dotenv import load_dotenv
import streamlit as st
import asyncio
from ai.variance_agent import VarianceAnalyst
from core.loader import load_from_uploaded_file
from ai import tools

load_dotenv(override=True)

# Web app config
st.set_page_config(
    page_title="Variance Analyzer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="auto"
)

## State manager
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hey! I'm your variance analyzer. How can I help you?"
        },
    ]
if "data_file" not in st.session_state:
    st.session_state.data_file = "test_data.csv"

if "analyst" not in st.session_state:
    try:
        st.session_state.analyst = VarianceAnalyst(st.session_state.data_file)
    except Exception as e:
        st.error(f"❌ Ошибка инициализации агента: {str(e)}")

# Синхронизируем session_state с глобальными переменными tools
# Это нужно делать при каждом запуске, так как Streamlit перезапускает скрипт
if "uploaded_dataframe" in st.session_state and st.session_state.uploaded_dataframe is not None:
    tools._uploaded_dataframe = st.session_state.uploaded_dataframe
    print(f"[DEBUG SYNC] Restored uploaded_dataframe from session_state: shape={tools._uploaded_dataframe.shape}")
else:
    tools._uploaded_dataframe = None
    print(f"[DEBUG SYNC] No uploaded_dataframe in session_state")

if "column_mapping" in st.session_state and st.session_state.column_mapping is not None:
    tools._column_mapping = st.session_state.column_mapping
    print(f"[DEBUG SYNC] Restored column_mapping from session_state")
else:
    tools._column_mapping = None

if "mapped_variance_rows" in st.session_state and st.session_state.mapped_variance_rows is not None:
    tools._mapped_variance_rows = st.session_state.mapped_variance_rows
    print(f"[DEBUG SYNC] Restored mapped_variance_rows from session_state: {len(tools._mapped_variance_rows)} rows")
else:
    tools._mapped_variance_rows = None

## UX
st.title("Variance Analyzer", anchor="variance-analyzer")

with st.sidebar:
    st.title("⚙️ Настройки")
    st.markdown("Analyze your budget variances with AI-powered insights 📊")
    uploaded_file = st.file_uploader(
        "Load new file:",
        type=["csv", "xlsx"],
        help="CSV or XLSX file with your budget data"
        )

    if uploaded_file is not None:
        # Проверяем, был ли этот файл уже обработан
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"

        if st.session_state.get("last_uploaded_file_id") != file_id:
            try:
                # Загружаем файл в DataFrame
                df, metadata = load_from_uploaded_file(uploaded_file)

                # ВАЖНО: Сохраняем в session_state (будет синхронизировано с tools при следующем запуске)
                st.session_state.uploaded_dataframe = df
                st.session_state.column_mapping = None
                st.session_state.mapped_variance_rows = None

                # Также сохраняем в tools для текущего запуска
                tools._uploaded_dataframe = df
                tools._column_mapping = None
                tools._mapped_variance_rows = None

                # Сохраняем метаданные
                st.session_state.last_uploaded_file_id = file_id
                st.session_state.uploaded_filename = metadata.filename
                st.session_state.uploaded_rows = metadata.rows
                st.session_state.file_size = metadata.size_bytes

                st.success(f"✅ Файл загружен: {metadata.filename} ({metadata.rows} строк)")

                # Автоматически уведомляем агента о загрузке файла
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"📋 Я вижу, что вы загрузили файл **{metadata.filename}**. Давайте проанализируем его столбцы для маппинга."
                })

                # Добавляем автоматический запрос на анализ столбцов
                st.session_state.file_upload_trigger = True
                st.rerun()

            except Exception as e:
                st.error(f"❌ Ошибка загрузки файла: {str(e)}")
        else:
            # Файл уже загружен, показываем информацию
            st.success(f"✅ Файл загружен: {st.session_state.uploaded_filename} ({st.session_state.uploaded_rows} строк)")

    st.divider()
    st.info(f"📊 Loaded file: {st.session_state.data_file}")
    
    st.divider()
    if st.button("🗑️ Очистить чат"):
        st.session_state.messages = [
            {
              "role": "assistant",
              "content": "Hey! I'm your variance analyzer. How can I help you?"
          }
        ]
        st.rerun()

# Создаём табы
tab1, tab2 = st.tabs(["💬 Чат с AI", "📊 Данные"])

# ===== TAB 1: ЧАТ =====
with tab1:
    # Отображаем историю сообщений (пропускаем системные)
    for message in st.session_state.messages:
        if message["role"] != "system":  # Системные сообщения не показываем пользователю
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Автоматический триггер для анализа столбцов после загрузки файла
    if st.session_state.get("file_upload_trigger", False):
        st.session_state.file_upload_trigger = False
        auto_prompt = "Проанализируй столбцы загруженного файла и предложи маппинг"

        # Добавляем в историю только если этого сообщения ещё нет
        if not st.session_state.messages or st.session_state.messages[-1]["content"] != auto_prompt:
            st.session_state.messages.append({"role": "user", "content": auto_prompt})

            with st.chat_message("user"):
                st.markdown(auto_prompt)

            with st.chat_message("assistant"):
                with st.spinner("Анализирую столбцы..."):
                    full_response = st.write_stream(st.session_state.analyst.chat_stream(auto_prompt))
                    st.session_state.messages.append({"role": "assistant", "content": str(full_response)})

# Поле ввода ВЫНЕСЕНО ЗА ПРЕДЕЛЫ ТАБА - это критически важно для правильной работы
prompt = st.chat_input("Your question")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Обработка нового промпта внутри таба
with tab1:
    # Если последнее сообщение от пользователя и ещё нет ответа
    if (len(st.session_state.messages) > 0 and
        st.session_state.messages[-1]["role"] == "user" and
        (len(st.session_state.messages) < 2 or st.session_state.messages[-2]["role"] == "assistant")):

        user_prompt = st.session_state.messages[-1]["content"]

        # === STATE MACHINE: Проверяем, ожидаем ли подтверждение маппинга ===
        if st.session_state.get("awaiting_mapping_confirmation", False):
            # Проверяем, что пользователь подтвердил (короткий ответ)
            confirmation_keywords = ["да", "yes", "ок", "ok", "подтверждаю", "верно", "+", "apply", "принять"]
            user_prompt_lower = user_prompt.lower().strip()

            if any(keyword in user_prompt_lower for keyword in confirmation_keywords) and len(user_prompt.split()) <= 3:
                print(f"[DEBUG] Detected mapping confirmation: '{user_prompt}'")

                # Автоматически применяем маппинг
                pending_mapping = st.session_state.get("pending_mapping")

                if pending_mapping:
                    with st.chat_message("assistant"):
                        with st.spinner("Применяю маппинг..."):
                            # Вызываем apply_column_mapping НАПРЯМУЮ из Python
                            try:
                                result = tools._apply_column_mapping_impl(
                                    account_column=pending_mapping['account'],
                                    period_column=pending_mapping['period'],
                                    actual_column=pending_mapping['actual'],
                                    budget_column=pending_mapping['budget']
                                )

                                # Формируем красивый ответ
                                if result["success"]:
                                    response_text = f"""✅ **Маппинг успешно применён!**

📊 Обработано строк: {result['rows_processed']}

Теперь вы можете задавать вопросы о данных, например:
- "Покажи топ-5 отклонений"
- "Какая общая статистика?"
- "Где мы перерасходовали бюджет?"
"""
                                    # ВАЖНО: Добавляем системное уведомление для агента
                                    # Это НЕ показывается пользователю, но агент видит его в контексте
                                    system_notification = """[SYSTEM] Маппинг файла успешно применён. С этого момента для ВСЕХ запросов о данных используй ТОЛЬКО инструменты:
- get_mapped_variance_data (вместо get_variance_data)
- get_mapped_top_variances (вместо get_top_variances)

НЕ используй get_variance_data, get_top_variances, get_summary_stats - они работают только с дефолтным test_data.csv."""

                                else:
                                    response_text = f"❌ **Ошибка применения маппинга:**\n{result.get('error', 'Неизвестная ошибка')}"
                                    system_notification = None

                                st.markdown(response_text)
                                st.session_state.messages.append({"role": "assistant", "content": response_text})

                                # Синхронизируем mapped_variance_rows в session_state
                                if tools._mapped_variance_rows is not None:
                                    st.session_state.mapped_variance_rows = tools._mapped_variance_rows
                                if tools._column_mapping is not None:
                                    st.session_state.column_mapping = tools._column_mapping

                                # Очищаем флаг ожидания
                                st.session_state.awaiting_mapping_confirmation = False
                                st.session_state.pending_mapping = None

                                st.rerun()

                            except Exception as e:
                                error_text = f"❌ **Ошибка при применении маппинга:**\n{str(e)}"
                                st.error(error_text)
                                st.session_state.messages.append({"role": "assistant", "content": error_text})
                                st.session_state.awaiting_mapping_confirmation = False
                                st.rerun()
                else:
                    st.error("❌ Ошибка: не найден pending_mapping")
                    st.session_state.awaiting_mapping_confirmation = False
                    st.rerun()
            else:
                # Пользователь написал что-то другое, возможно корректировку
                print(f"[DEBUG] User provided non-confirmation message, treating as correction")

                # ВАЖНО: Не очищаем pending_mapping, а передаём его агенту в контексте
                pending_mapping = st.session_state.get("pending_mapping")

                if pending_mapping:
                    # Формируем контекстный промпт для агента
                    context_prompt = f"""Пользователь корректирует маппинг столбцов.

ТЕКУЩИЙ ПРЕДЛОЖЕННЫЙ МАППИНГ:
- account: "{pending_mapping['account']}"
- period: "{pending_mapping['period']}"
- actual: "{pending_mapping['actual']}"
- budget: "{pending_mapping['budget']}"

КОРРЕКТИРОВКА ПОЛЬЗОВАТЕЛЯ: {user_prompt}

ЗАДАЧА: Пойми, какие столбцы пользователь хочет поменять, и примени НОВЫЙ маппинг используя инструмент apply_column_mapping с ОТКОРРЕКТИРОВАННЫМИ параметрами."""

                    with st.chat_message("assistant"):
                        with st.spinner("Применяю корректировку..."):
                            full_response = st.write_stream(st.session_state.analyst.chat_stream(context_prompt))
                            st.session_state.messages.append({"role": "assistant", "content": str(full_response)})

                            # Очищаем флаги после обработки
                            st.session_state.awaiting_mapping_confirmation = False
                            st.session_state.pending_mapping = None
                            st.rerun()
                else:
                    # Нет pending_mapping - передаём сообщение агенту как обычно
                    st.session_state.awaiting_mapping_confirmation = False

                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            full_response = st.write_stream(st.session_state.analyst.chat_stream(user_prompt))
                            st.session_state.messages.append({"role": "assistant", "content": str(full_response)})
                            st.rerun()
        else:
            # Обычный режим работы

            # Если маппинг был применён (проверяем наличие mapped_variance_rows), добавляем системную инструкцию к промпту
            if st.session_state.get("mapped_variance_rows") is not None:
                enhanced_prompt = f"""[SYSTEM REMINDER] Файл с пользовательскими данными был замаплен. Для всех запросов о данных используй ТОЛЬКО:
- get_mapped_variance_data (НЕ get_variance_data!)
- get_mapped_top_variances (НЕ get_top_variances!)

Не используй get_variance_data, get_top_variances, get_summary_stats - они работают с test_data.csv.

---

ЗАПРОС ПОЛЬЗОВАТЕЛЯ: {user_prompt}"""
            else:
                enhanced_prompt = user_prompt

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    full_response = st.write_stream(st.session_state.analyst.chat_stream(enhanced_prompt))
                    st.session_state.messages.append({"role": "assistant", "content": str(full_response)})
                    st.rerun()

# ===== TAB 2: ДАННЫЕ =====
with tab2:
    if st.session_state.get("uploaded_dataframe") is not None and st.session_state.get("uploaded_filename"):
        st.header("📋 Информация о файле")

        # Секция 1: Метаданные файла
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📄 Имя файла", st.session_state.uploaded_filename)

        with col2:
            file_size_kb = st.session_state.get("file_size", 0) / 1024
            st.metric("💾 Размер", f"{file_size_kb:.1f} КБ")

        with col3:
            st.metric("📊 Строк", st.session_state.uploaded_rows)

        with col4:
            st.metric("🔢 Столбцов", len(st.session_state.uploaded_dataframe.columns))

        st.divider()

        # Секция 2: Превью данных
        st.subheader("👁️ Превью данных (первые 20 строк)")
        st.dataframe(
            st.session_state.uploaded_dataframe.head(20),
            width="stretch",
            height=400
        )

        st.divider()

        # Секция 3: Статистика по столбцам
        st.subheader("📈 Статистика по столбцам")

        col_stats = []
        for col in st.session_state.uploaded_dataframe.columns:
            dtype = str(st.session_state.uploaded_dataframe[col].dtype)
            null_count = st.session_state.uploaded_dataframe[col].isnull().sum()
            unique_count = st.session_state.uploaded_dataframe[col].nunique()

            col_stats.append({
                "Столбец": col,
                "Тип": dtype,
                "Пустых": null_count,
                "Уникальных": unique_count
            })

        import pandas as pd
        stats_df = pd.DataFrame(col_stats)
        st.dataframe(stats_df, width="stretch", hide_index=True)

        # Секция 4: Информация о маппинге (если есть)
        if st.session_state.get("column_mapping") is not None:
            st.divider()
            st.subheader("🔗 Применённый маппинг столбцов")

            mapping_data = {
                "Стандартное поле": ["account", "period", "actual", "budget"],
                "Столбец в файле": [
                    st.session_state.column_mapping.account,
                    st.session_state.column_mapping.period,
                    st.session_state.column_mapping.actual,
                    st.session_state.column_mapping.budget
                ]
            }

            mapping_df = pd.DataFrame(mapping_data)
            st.dataframe(mapping_df, width="stretch", hide_index=True)

            if st.session_state.get("mapped_variance_rows"):
                st.success(f"✅ Маппинг применён успешно! Обработано {len(st.session_state.mapped_variance_rows)} строк")
    else:
        st.info("📁 Загрузите файл в боковой панели, чтобы увидеть данные")

        st.markdown("""
        ### Как использовать:

        1. **Загрузите файл** через боковую панель (CSV или XLSX)
        2. **AI автоматически проанализирует** столбцы
        3. **Подтвердите или скорректируйте** маппинг в чате
        4. **Просмотрите данные** на этой вкладке
        5. **Задавайте вопросы** агенту во вкладке "Чат"

        ### Поддерживаемые форматы:
        - CSV (до 10 МБ)
        - XLSX (до 10 МБ)

        ### Требования к файлу:
        - Минимум 2 столбца
        - Минимум 1 строка данных
        - Должны быть столбцы для: account, period, actual, budget
        """)