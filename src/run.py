import streamlit as st
from sidebar_area import sidebar, generate_unique_name
from chat_area import main
import time
from random import randint
import db


def initialize_session_state():
    if not "user_id" in st.session_state:
        st.session_state["user_id"] = 0

    if not "chats" in st.session_state:
        old_chats = db.get_chats(st.session_state["user_id"])

        # assuming 0 means unsaved
        st.session_state["chats"] = [{"id": 0, "name": generate_unique_name(), "last_interaction": time.time()}] + old_chats

        st.session_state["current_chat_id"] = 0

    if not "disabled" in st.session_state:
        st.session_state["disabled"] = False

    if not "greeting_msg" in st.session_state:
        greetings = ["Hey there!", "Greetings!", "Nice to meet you!", "What shall we discuss today?", "Let's get going!"]
        greeting_msg = "👋 " + greetings[randint(0, len(greetings) - 1)]
        st.session_state["greeting_msg"] = greeting_msg

    if not "username" in st.session_state:
        user_info = db.get_user_info(st.session_state["user_id"])
        st.session_state["username"] = user_info["name"]
        st.session_state["style"] = user_info.get("style", "Normal")
        st.session_state["temperature"] = user_info.get("temperature", 0.6)
        st.session_state["chat_model"] = user_info.get("chat_model", "gemma2:2b")
        st.session_state["embedding_model"] = user_info.get("embedding_model", "embeddinggemma:300m")


if __name__ == "__main__":
    st.set_page_config("ChatDocs", page_icon=":material/borg:")
    initialize_session_state()
    sidebar()
    main()
