import streamlit as st
from coolname import generate_slug
from uuid import uuid4
import time
from random import randint
from coolname import generate_slug
import db


def generate_unique_name():
    return generate_slug(randint(2, 3))


def sidebar():
    with st.sidebar:
        st.title(":material/borg: ChatDocs", text_alignment="center")

        new_chat_btn = st.button("New Chat", icon=":material/add:", width="stretch", type="primary")

        if new_chat_btn:
            # uuid4().hex
            new_id = 0
            replaced = False
            for c in st.session_state["chats"]:
                if c["id"] == 0:
                    c["name"] = generate_unique_name()
                    c["last_interaction"] = time.time()
                    replaced = True
                    break

            if not replaced:  # add new
                st.session_state["chats"].insert(
                    0, {"id": new_id, "name": generate_unique_name(), "last_interaction": time.time()}
                )
            st.session_state["current_chat_id"] = new_id
            st.session_state["current_chat_history"] = []
            # st.session_state["max_chat_id"] = new_id
            st.rerun()

        # st.markdown("### Chats")
        with st.spinner():
            # getting latest chats from db
            saved_chats = db.get_chats(st.session_state["user_id"])
            new_chat = None
            for c in st.session_state["chats"]:
                if c["id"] == 0:
                    new_chat = c
            st.session_state["chats"] = [new_chat] + saved_chats if new_chat else saved_chats

            # chats = sorted(chats.items(), key=lambda x: x[1]["last_interaction"], reverse=True)

            for chat in saved_chats:
                chat_id = chat["id"]
                chat_name = chat["name"]
                if len(chat_name) > 18:
                    chat_name = chat_name[:18] + "..."

                if st.button(
                    chat_name,
                    icon=":material/chat:",
                    width="stretch",
                    disabled=st.session_state["current_chat_id"] == chat_id,
                    key=chat_id,
                ):
                    for c in st.session_state["chats"]:
                        if c["id"] == chat_id:
                            break

                    st.session_state["current_chat_id"] = chat_id
                    st.session_state["current_chat_history"] = db.get_chat_messages(chat_id)
                    st.session_state["disabled"] = False
                    st.rerun()
