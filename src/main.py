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
            "### RULES AND ASSUMPTIONS YOU MUST FOLLOW:\n"
            "- Attachments uploaded/attached by user will be found inside '### CONTEXT FROM USER UPLOADED ATTACHMENTS' section.\n"
            "- Each document excerpt is preceded by Source ID like [SOURCE_1].\n"
            "- Prioritize answering from CONTEXT FROM USER UPLOADED ATTACHMENTS. Cite the source strictly in the exact format [[SOURCE_N]] .\n"
            "- If CONTEXT FROM USER UPLOADED ATTACHMENTS says '[NO RELEVANT ATTACHMENT UPLOADED BY USER]', then assume the documents attached don't contain the answer.\n"
            "- If you don't know something, then say so.\n"
            "{style_rule}",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "### CONTEXT FROM USER UPLOADED ATTACHMENTS\n{attachments}\n\n---\n\n" "### USER QUERY: {human_input}\n"),
    ]
)


# ----------------- TESTING PROMPTS --------------

# for msg in prompt_template.format_messages(
#     style_rule="- Adopt a random style", attachments="[NO RELEVANT ATTACHMENT UPLOADED BY USER]", human_input="Hello", chat_history=[]
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
