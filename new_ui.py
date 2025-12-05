from dotenv import load_dotenv
import streamlit as st
import asyncio
from ai.variance_agent import VarianceAnalyst

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

## UX
st.title("Variance Analyzer", anchor="variance-analyzer")

with st.sidebar:
    st.title("⚙️ Настройки")
    st.markdown("Analyze your budget variances with AI-powered insights 📊")
    st.file_uploader("Load new file:")
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

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Your question"):

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Typing..."):
            response = asyncio.run(st.session_state.analyst.chat(prompt))
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.markdown(response)