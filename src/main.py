import streamlit as st
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


@st.cache_resource
def load_llm():
    return ChatOllama(model="llama3.2")


llm = load_llm()

sys_msg = SystemMessage("You are a helpful assistant who gives very brief responses")

st.header("Chat")

if "history" not in st.session_state:
    st.session_state["history"] = []


if "disabled" not in st.session_state:
    st.session_state["disabled"] = False

prompt_input = st.chat_input(
    "Enter prompt or attach documents",
    disabled=st.session_state["disabled"],
    accept_file="multiple",
    accept_audio=False,
    file_type=["pdf"],
    max_upload_size=800,
    max_chars=3000,
)

for item in st.session_state["history"]:
    if isinstance(item, HumanMessage):
        msg = st.chat_message("human")
    else:
        msg = st.chat_message("ai")

    msg.markdown(item.content)

if prompt_input:
    files = prompt_input.files[:10]
    text = prompt_input.text.strip()

    st.session_state["history"].append(HumanMessage(text))
    with st.chat_message("human"):
        st.markdown(text)

    # with st.spinner(text="", width="stretch"):
    chunks = llm.stream(st.session_state["history"])

    with st.chat_message("ai"):

        def stream_generator():
            st.session_state["disabled"] = True
            response = ""
            for chunk in chunks:
                response += chunk.text
                yield chunk

            st.session_state["disabled"] = False

            st.session_state["history"].append(AIMessage(response))

        st.write_stream(stream_generator())
