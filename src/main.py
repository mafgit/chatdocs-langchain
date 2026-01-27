from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

import streamlit as st


# ----------------- LOAD CHAT MODEL -----------------
@st.cache_resource
def load_chat_model(model, temperature=0.8, num_ctx=8192, reasoning=None):
    return ChatOllama(model=model, temperature=temperature, num_ctx=num_ctx, reasoning=reasoning, validate_model_on_init=True)


# ----------------- LOAD VECTOR DB -----------------
@st.cache_resource
def load_vector_store(embedding_model: str):
    embeddings = OllamaEmbeddings(model=embedding_model, validate_model_on_init=True)
    collection_name = embedding_model.replace(":", "-")
    return Chroma(persist_directory="vector_store", collection_name=collection_name, embedding_function=embeddings)


# vector_store.reset_collection()

# ----------------- CHAT PROMPT TEMPLATE TO FILL IN VARIABLES LATER -----------------

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are ChatDocs, a specialized assistant helping users in document-based learning.\n"
            "- Documents or resources uploaded/attached by user will be located inside '### RESOURCES DATA' section.\n"
            "- Prioritize answering from RESOURCES DATA and citing the file name or page number or section if given. Don't use generic labels like 'CHUNK 1' or 'REFERENCE 1'.\n"
            "- If RESOURCES DATA says '[NO RELEVANT RESOURCE ATTACHED BY USER]', then assume the documents attached don't contain the answer.\n"
            "- If you don't know something, then say so.\n"
            "{style_rule}",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "### RESOURCES DATA\n{resources}\n\n---\n\n" "### USER QUERY: {human_input}\n"),
    ]
)


# ----------------- TESTING PROMPTS --------------

# for msg in prompt_template.format_messages(
#     style_rule="- Adopt a random style", resources="[NO RELEVANT RESOURCE ATTACHED BY USER]", human_input="Hello", chat_history=[]
# ):
#     print("<START>" + msg.content + "<END>") # pyright: ignore

# ----------------- GET CHAIN -----------------


@st.cache_resource
def get_chain(chat_model: ChatOllama):
    parser = StrOutputParser()
    chain = prompt_template | chat_model | parser
    return chain


# ----------------- SOME MODEL NAMES -----------------


chat_models = ["gemma2:2b", "gemma3:4b", "llama3.2"]
embedding_models = ["embeddinggemma:300m", "nomic-embed-text"]

# reasoning_options = {
#     ""
# }

# model = "gemma2:2b"
# embedding_model = models_to_embeddings[model]
