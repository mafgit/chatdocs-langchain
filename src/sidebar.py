import streamlit as st
from coolname import generate_slug
from uuid import uuid4

from random import randrange
from coolname import generate_slug


def generate_unique_name():
    return generate_slug(randrange(2, 3))


def sidebar():
    with st.sidebar:
        st.title(":material/borg: Chat with Docs", text_alignment="center")

        new_chat_btn = st.button("New Chat", icon=":material/add:", width="stretch", type="primary")

        if new_chat_btn:
            # max_id = st.session_state["max_chat_id"]
            # new_id = max_id + 1
            new_id = uuid4().hex
            st.session_state["chats"][new_id] = {"name": generate_unique_name(), "history": []}
            st.session_state["current_chat_id"] = new_id
            # st.session_state["max_chat_id"] = new_id
            st.rerun()

        # st.markdown("### Chats")
        chats = st.session_state["chats"]
        for id in chats:
            if st.button(
                chats[id]["name"], icon=":material/chat:", width="stretch", disabled=st.session_state["current_chat_id"] == id
            ):
                st.session_state["current_chat_id"] = id
                st.session_state["disabled"] = False
                st.rerun()
