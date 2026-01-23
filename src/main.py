import streamlit as st
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import fitz


@st.cache_resource
def load_llm():
    return ChatOllama(model="llama3.2")


llm = load_llm()

sys_msg = SystemMessage("You are a helpful assistant who gives very brief responses")

st.header("Chat with PDF")

if "history" not in st.session_state:
    st.html(
        '<div style="display:flex;justify-content:center;align-items:center;min-height:min(calc(100vw/2),250px);margin-top:auto;opacity:0.7;font-size:1.2rem;">Hey there, great to see you!</div>'
    )
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


def stream_generator(chunks):
    st.session_state["disabled"] = True
    response = ""
    for chunk in chunks:
        response += chunk.text
        yield chunk

    st.session_state["disabled"] = False

    st.session_state["history"].append(AIMessage(response))


if prompt_input:
    files = prompt_input.files[:10]
    text = prompt_input.text.strip()

    file_full_text = ""
    for file in files:
        ext = file.name.split(".")[-1]
        if ext == "pdf":
            with fitz.open(stream=file.read(), filetype="pdf") as doc:
                file_full_text += '\n\n' + file.name + ":\n"
                for page in doc:
                    file_full_text += page.get_text()

                # print(file_full_text)

    st.session_state["history"].append(HumanMessage(text))
    with st.chat_message("human"):
        st.markdown(text)

    # with st.spinner(text="", width="stretch"):

    with st.chat_message("ai"):
        chunks = llm.stream(st.session_state["history"])
        st.write_stream(stream_generator(chunks))
