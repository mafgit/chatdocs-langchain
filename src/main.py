import streamlit as st
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from load_docs import get_full_text_from_files
from typing import Tuple, Literal, Optional, Sequence
from random import randint


class Message:
    def __init__(
        self,
        role: Literal["ai", "human", "system"],
        content: str = "",
        files_metadata: Optional[Sequence[Tuple[str, float]]] = None,
    ):
        self.content = content
        self.role = role
        self.files_metadata = files_metadata or []

    def to_langchain(self):
        return {"role": self.role, "content": self.content}


@st.cache_resource
def load_llm():
    return ChatOllama(model="llama3.2")


llm = load_llm()

sys_msg = Message("system", content="You are a helpful assistant who gives very brief responses")

st.set_page_config("Chat with PDF", page_icon=":material/borg:")
st.markdown("#### :material/borg: Chat with Docs")

if "history" not in st.session_state:
    greetings = ["Hey there!", "Greetings, user!", "Nice to meet you!", "Hello there!", "Good to see you!"]
    greeting_msg = greetings[randint(0, len(greetings) - 1)]
    st.html(
        f'<div style="display:flex;justify-content:center;align-items:center;min-height:min(calc(100vw/2),250px);margin-top:auto;opacity:0.8;font-size:1.2rem;">👋 {greeting_msg}</div>'
    )
    st.session_state["history"] = []


if "disabled" not in st.session_state:
    st.session_state["disabled"] = False

prompt_input = st.chat_input(
    "Enter prompt or attach documents",
    disabled=st.session_state["disabled"],
    accept_file="multiple",
    accept_audio=False,
    file_type=["pdf", "txt", "md", "docx", "doc"],
    max_upload_size=800,
    max_chars=3000,
)


for item in st.session_state["history"]:
    if item.role == "human":
        msg = st.chat_message("human")
        if msg.files_metadata:
            for filename, filesize in item.files_metadata:
                msg.info(filename + " (" + str(filesize) + " KB)", icon=":material/file_present:")
        msg.markdown(item.content)
    elif item.role in {"ai", "assistant"}:
        msg = st.chat_message("ai")
        msg.markdown(item.content)


def stream_generator(chunks):
    response = ""
    for chunk in chunks:
        response += chunk.text
        yield chunk

    st.session_state["disabled"] = False
    st.session_state["history"].append(Message(content=response, role="ai", files_metadata=[]))


if prompt_input:
    files = prompt_input.files[:10]
    prompt_text = prompt_input.text.strip()

    if files:
        full_files_text = get_full_text_from_files(files)
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=110)
        chunks = splitter.split_text(full_files_text)
        # print(len(chunks), chunks[0])

        # print(full_files_text)

    if not prompt_text and files:
        prompt_text = "I am attaching some files, summarize them."

    if prompt_text:
        st.session_state["disabled"] = True

        # add user prompt to history and UI
        files_metadata = [(f.name, f.size) for f in files]
        st.session_state["history"].append(Message(content=prompt_text, role="human", files_metadata=files_metadata))
        with st.chat_message("human"):
            for filename, filesize in files_metadata:
                st.info(filename + " (" + str(filesize) + "KB)", icon=":material/file_present:")
            st.markdown(prompt_text)

        # add AI response to history and UI
        # with st.spinner(text="", width="stretch"):
        chunks = llm.stream([sys_msg.to_langchain()] + [item.to_langchain() for item in st.session_state["history"][-10:]])
        with st.chat_message("ai"):
            st.write_stream(stream_generator(chunks))
