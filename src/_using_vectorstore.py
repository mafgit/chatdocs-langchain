from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

texts = [
    "LangChain is a framework for developing applications powered by language models.",
    "Ollama allows you to run large language models locally on your machine.",
    "Vector databases store embeddings and enable semantic search.",
    "ChromaDB is an open-source embedding database.",
]

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

docs = splitter.create_documents(texts)

embeddings = OllamaEmbeddings(model="llama3.2")

vector_store = Chroma.from_documents(documents=docs, embedding=embeddings, persist_directory="vector_store")

# print(vector_store._collection.count())

query = "What is LangChain?"

results = vector_store.similarity_search(query, k=2)

for result in results:
    print(result.page_content, result.metadata)
