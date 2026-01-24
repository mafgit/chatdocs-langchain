import streamlit as st
from sidebar import sidebar, generate_unique_name
from main import main
from uuid import uuid4


def session():
    if not "chats" in st.session_state:
        new_chat_id = uuid4().hex
        st.session_state["chats"] = {new_chat_id: {"name": generate_unique_name(), "history": []}}
        st.session_state["current_chat_id"] = new_chat_id

    # if not "max_chat_id" in st.session_state:
    #     st.session_state["max_chat_id"] = 1

    if not "user_id" in st.session_state:
        st.session_state["user_id"] = "user1"

    if not "disabled" in st.session_state:
        st.session_state["disabled"] = False


from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings


@st.cache_resource
def load_llm(model):
    return ChatOllama(model=model)


@st.cache_resource
def load_vectorstore(model):
    embeddings = OllamaEmbeddings(model=model)
    return Chroma(persist_directory="vectorstore", collection_name="chat_histories", embedding_function=embeddings)


if __name__ == "__main__":
    models_to_embeddings = {"gemma2:2b": "embeddinggemma:300m", "llama3.2": "llama3.2"}
    model = "gemma2:2b"

    llm = load_llm(model)
    vectorstore = load_vectorstore(models_to_embeddings[model])

    # vectorstore.reset_collection()
    session()
    sidebar()
    main(llm, vectorstore)
