import streamlit as st
from coolname import generate_slug
from uuid import uuid4
import time
from random import randint
from coolname import generate_slug


def generate_unique_name():
    return generate_slug(randint(2, 3))


def sidebar():
    with st.sidebar:
        st.title(":material/borg: ChatDocs", text_alignment="center")

        new_chat_btn = st.button("New Chat", icon=":material/add:", width="stretch", type="primary")

        if new_chat_btn:
            # max_id = st.session_state["max_chat_id"]
            # new_id = max_id + 1
            new_id = uuid4().hex
            st.session_state["chats"][new_id] = {"name": generate_unique_name(), "history": [], "last_interaction": time.time()}
            st.session_state["current_chat_id"] = new_id
            # st.session_state["max_chat_id"] = new_id
            st.rerun()

        # st.markdown("### Chats")
        chats = st.session_state["chats"]
        chats_sorted_by_time = sorted(chats.items(), key=lambda x: x[1]["last_interaction"], reverse=True)
        for chat_id, chat in chats_sorted_by_time:
            chat_name = chat["name"]
            if len(chat_name) > 18:
                chat_name = chat_name[:18] + "..."

            if st.button(
                chat_name, icon=":material/chat:", width="stretch", disabled=st.session_state["current_chat_id"] == chat_id
            ):
                st.session_state["current_chat_id"] = chat_id
                st.session_state["disabled"] = False
                st.rerun()
