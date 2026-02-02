from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

import streamlit as st


# ----------------- LOAD CHAT MODEL -----------------
@st.cache_resource(show_spinner=False)
def load_chat_model(model, temperature=0.6, num_ctx=8192, reasoning=None):
    return ChatOllama(model=model, temperature=temperature, num_ctx=num_ctx, reasoning=reasoning, validate_model_on_init=True)


# ----------------- LOAD VECTOR DB -----------------
@st.cache_resource(show_spinner=False)
def load_vector_store(embedding_model: str):
    embeddings = OllamaEmbeddings(model=embedding_model, validate_model_on_init=True)
    collection_name = embedding_model.replace(":", "-")
    return Chroma(persist_directory="vector_store", collection_name=collection_name, embedding_function=embeddings)


# vector_store.reset_collection()

# ----------------- CHAT PROMPT TEMPLATE TO FILL IN VARIABLES LATER -----------------

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# from langchain_core.output_parsers import StrOutputParser

prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are ChatDocs, a specialized assistant helping users in document-based learning.\n"
            "- When document excerpts are provided, cite sources like [1], [2] format\n"
            "- Prioritize document content over general knowledge\n"
            "- If unsure about a detail, say so\n"
            "- If prompt starts with /search, assume that relevant web search results are given in context"
            "- Don't explain your internal process or how you accessed documents\n"
            "{style_rule}",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{attachments}\n\n---\n\n" "{human_input}"),
    ]
)


# ----------------- TESTING PROMPTS --------------

# for msg in prompt_template.format_messages(
#     style_rule="- Adopt a random style", attachments="[NO RELEVANT ATTACHMENT UPLOADED BY USER]", human_input="Hello", chat_history=[]
# ):
#     print("<START>" + msg.content + "<END>") # pyright: ignore

# ----------------- GET CHAIN -----------------


@st.cache_resource(show_spinner=False)
def get_chain(chat_model: ChatOllama):
    # parser = StrOutputParser()
    chain = prompt_template | chat_model
    return chain


# ----------------- SOME MODEL NAMES -----------------


chat_models = [
    "gemma2:2b",
    "gpt-oss:20b-cloud",
    "kimi-k2-thinking:cloud",
    "gemma3:4b",
    "llama3.2",
    "phi4-reasoning:14b",
]
embedding_models = ["embeddinggemma:300m", "nomic-embed-text", "qwen3-embedding", "all-minilm"]

# reasoning_options = {
#     ""
# }

# model = "gemma2:2b"
# embedding_model = models_to_embeddings[model]
