from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

import streamlit as st


@st.cache_resource
def load_chat_model(model, temperature=0.8, num_ctx=8192, reasoning=None):
    return ChatOllama(model=model, temperature=temperature, num_ctx=num_ctx, reasoning=reasoning, validate_model_on_init=True)


@st.cache_resource
def load_vector_store(embedding_model: str):
    embeddings = OllamaEmbeddings(model=embedding_model, validate_model_on_init=True)
    collection_name = embedding_model.replace(":", "-")
    return Chroma(persist_directory="vector_store", collection_name=collection_name, embedding_function=embeddings)


# vector_store.reset_collection()

models_to_embeddings = {
    "gemma2:2b": "embeddinggemma:300m",
    "gemma3:4b": "embeddinggemma:300m",
    "llama3.2": "nomic-embed-text",
}
chat_models = models_to_embeddings.keys()
embedding_models = list(set(models_to_embeddings.values()))

# reasoning_options = {
#     ""
# }

# model = "gemma2:2b"
# embedding_model = models_to_embeddings[model]
