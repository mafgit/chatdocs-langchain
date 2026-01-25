import streamlit as st
from sidebar import sidebar, generate_unique_name
from main import main
from uuid import uuid4
import time
from random import randint

from model import load_llm, load_vector_store

def session():
    if not "chats" in st.session_state:
        new_chat_id = uuid4().hex
        st.session_state["chats"] = {
            new_chat_id: {"name": generate_unique_name(), "history": [], "last_interaction": time.time()}
        }
        st.session_state["current_chat_id"] = new_chat_id

    # if not "max_chat_id" in st.session_state:
    #     st.session_state["max_chat_id"] = 1

    if not "user_id" in st.session_state:
        st.session_state["user_id"] = "user1"

    if not "disabled" in st.session_state:
        st.session_state["disabled"] = False

    if not "greeting_msg" in st.session_state:
        greetings = ["Hey there!", "Greetings, user!", "Nice to meet you!", "Hello there!", "Good to see you!"]
        greeting_msg = "👋 " + greetings[randint(0, len(greetings) - 1)]
        st.session_state["greeting_msg"] = greeting_msg



if __name__ == "__main__":
    session()
    sidebar()
    main()
