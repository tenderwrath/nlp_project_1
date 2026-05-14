import requests
import streamlit as st

RASA_URL = "http://localhost:5005/webhooks/rest/webhook"

st.set_page_config(page_title="HR Bot", page_icon="🤖")

st.markdown("""
<style>
.chat-container {
    max-width: 850px;
    margin: auto;
}

.user-row {
    display: flex;
    justify-content: flex-end;
    margin: 10px 0;
}

.bot-row {
    display: flex;
    justify-content: flex-start;
    margin: 10px 0;
}

.user-msg {
    background-color: #2b6cb0;
    color: white;
    padding: 12px 16px;
    border-radius: 16px 16px 4px 16px;
    max-width: 65%;
    font-size: 16px;
}

.bot-msg {
    background-color: #2d3748;
    color: white;
    padding: 12px 16px;
    border-radius: 16px 16px 16px 4px;
    max-width: 65%;
    font-size: 16px;
}

.title {
    text-align: center;
    margin-bottom: 30px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 class='title'>HR-бот для скрининга кандидатов</h2>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

for author, message in st.session_state.messages:
    if author == "user":
        st.markdown(
            f"""
            <div class="user-row">
                <div class="user-msg">{message}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="bot-row">
                <div class="bot-msg">{message}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("</div>", unsafe_allow_html=True)

user_message = st.chat_input("Введите сообщение")

if user_message:
    st.session_state.messages.append(("user", user_message))

    try:
        response = requests.post(
            RASA_URL,
            json={"sender": "user", "message": user_message},
            timeout=10,
        )

        bot_messages = response.json()

        if not bot_messages:
            st.session_state.messages.append(
                ("bot", "Некорректный ответ.")
            )

        for msg in bot_messages:
            text = msg.get("text")
            if text:
                st.session_state.messages.append(("bot", text))

    except requests.exceptions.RequestException:
        st.session_state.messages.append(
            ("bot", "Не удалось подключиться к Rasa. Проверь запуск сервера.")
        )

    st.rerun()