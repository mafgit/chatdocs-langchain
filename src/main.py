import streamlit as st
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from handle_files import handle_files
from typing import Tuple, Literal, Optional, Sequence
from random import randint
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings


class Message:
    def __init__(
        self,
        role: Literal["ai", "human", "system"],
        content: str = "",
        files_info: Optional[Sequence[Tuple[str, float, str, str]]] = None,
    ):
        self.content = content
        self.role = role
        self.files_info = files_info or []

    def to_langchain(self):
        return {"role": self.role, "content": self.content}


@st.cache_resource
def load_llm():
    return ChatOllama(model="llama3.2")


@st.cache_resource
def load_vectorstore():
    embeddings = OllamaEmbeddings(model="llama3.2")
    return Chroma(persist_directory="vectorstore", embedding_function=embeddings)


llm = load_llm()
vectorstore = load_vectorstore()

st.set_page_config("Chat with Docs", page_icon=":material/borg:")
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
    file_type=["pdf", "txt", "md", "docx", "doc", "csv"],
    max_upload_size=800,
    max_chars=3000,
)


for item in st.session_state["history"]:
    if item.role == "human":
        with st.chat_message("human"):
            if item.files_info:
                for filename, file_size, file_location, mime_type in item.files_info:
                    with open(file_location, "rb") as f:
                        st.download_button(
                            label=filename + " (" + str(file_size) + "KB)",
                            data=f,
                            file_name=filename,
                            mime=mime_type,
                            icon=":material/file_present:",
                        )
            st.markdown(item.content)
    elif item.role in {"ai", "assistant"}:
        with st.chat_message("ai"):
            st.markdown(item.content)


def stream_generator(chunks):
    response = ""
    for chunk in chunks:
        response += chunk.text
        yield chunk

    st.session_state["disabled"] = False
    st.session_state["history"].append(Message(content=response, role="ai", files_info=[]))


sys_msg = Message(
    "system",
    content="You are a helpful assistant who gives very brief responses. If context is attached from documents, use them as well as your own knowledge to answer user's queries.",
)

if prompt_input:
    files = prompt_input.files[:10]
    original_prompt_text = prompt_input.text.strip()

    dont_continue = False
    final_prompt_text = original_prompt_text[:]

    stop = False
    if not files and not original_prompt_text:
        stop = True

    if not stop:
        if not original_prompt_text and files:
            final_prompt_text = "I am attaching some files, summarize them."

        files_info = None
        if files:
            docs, files_info = handle_files(files)
            splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=110)
            chunks = splitter.split_documents(docs)
            # chunks[0].page_content, chunks[0].metadata
            vectorstore.add_documents(chunks)

        if vectorstore._collection.count() > 0:
            results = vectorstore.similarity_search(query=final_prompt_text, k=5)
            context = "\n\n".join([doc.page_content + " [" + doc.metadata["source"] + "]" for doc in results])

            if context.strip():
                final_prompt_text = (
                    "Some relevant context from attached files/documents:\n\n" + context + "\n\nPrompt: " + final_prompt_text
                )

        print(final_prompt_text)

        with st.chat_message("human"):
            if files_info:
                for filename, file_size, file_location, mime_type in files_info:
                    with open(file_location, "rb") as f:
                        st.download_button(
                            label=filename + " (" + str(file_size) + "KB)",
                            data=f,
                            file_name=filename,
                            mime=mime_type,
                            icon=":material/file_present:",
                        )
                    # st.info(filename + " (" + str(file_size) + "KB)", icon=":material/file_present:")
            st.markdown(original_prompt_text)

        # with st.spinner(text="", width="stretch"):
        history = (
            [sys_msg.to_langchain()]
            + [item.to_langchain() for item in st.session_state["history"][-10:]]
            + [{"role": "human", "content": final_prompt_text}]
        )
        chunks = llm.stream(history)

        # appending original message to history
        original_message = Message(content=original_prompt_text, role="human", files_info=files_info)
        st.session_state["history"].append(original_message)

        with st.chat_message("ai"):
            st.write_stream(stream_generator(chunks))
