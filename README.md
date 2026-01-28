# 🌀 ChatDocs

Chat with LLMs, attach documents, create multiple chats!

![](./ss1.webp)

![](./ss2.webp)

![](./ss3.webp)

## In this project, I worked with:

- LangChain
- Ollama
- RAG
- Text splitters (Recursive Character)
- Document Loaders (PDF, DOCX, TXT, MD, CSV)
- Vector stores (Chroma)
- Streamlit
- Python

## Main Procedure:

- File contents are broken into small chunks (like paragraphs) (with overlaps to maintain some context).
- They are turned into an embedding vector (one chunk has one embedding vector) using embedding model. This embedding represents the meaning of the chunk.
- The chunk and its vector are stored in a vector store.
- A top-K similarity search is conducted in the vector store with respect to the user query/prompt.
- Context (i.e. the top K similar results concatenated) is provided, to the LLM, within the prompt.
- A history of the conversation is maintained which is fed to the LLM each time a user prompts.

## How to run?

1. Clone repo
1. `python -m venv .venv` to create a virtual environment
1. `pip install -r requirements.txt`
1. Install Ollama from [https://ollama.com/](https://ollama.com/)
1. `streamlit run src/run.py`

## TODOS:

- add citations
- add youtube transcripts
- add website content reading
- add xlsx
- add better docx reader
- delete chat
- stop response in middle
- catch errors regarding not logged in or network error or other ollama errors
- ~~add thinking models functionality~~
- changing preferences in the middle of response stops it (reruns the flow)
- add sqlite3
- make relevant content getting better
- learn about retrievalQA
- ~~some statuses should be inside ai chat message, not human~~
- ~~make readme better with new images~~
- ~~make system message / CONTEXT, PROMPT, etc better~~
- add user auth
- ~~last prompt time based ordering of sidebar chats~~, sidebar items not updating order until rerun
- ~~add option of using whichever model~~
- ~~add option of choosing style~~
- ~~convert to ChatPromptTemplate~~
- ~~fix .md file not being read correctly~~
- ~~check session storage keys of preferences and change chat if embedding model changed~~
