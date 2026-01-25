from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

import streamlit as st


@st.cache_resource
def load_llm(model, temperature=0.8, num_ctx=8192, reasoning=None):
    return ChatOllama(model=model, temperature=temperature, num_ctx=num_ctx, reasoning=reasoning)


@st.cache_resource
def load_vector_store(model):
    embeddings = OllamaEmbeddings(model=model)
    return Chroma(persist_directory="vector_store", collection_name=model, embedding_function=embeddings)


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
