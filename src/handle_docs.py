from langchain_community.document_loaders import TextLoader, UnstructuredMarkdownLoader, Docx2txtLoader, PyPDFLoader, CSVLoader
import tempfile
from pathlib import Path
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_chroma import Chroma
import streamlit as st


mime_types = {
    "pdf": "application/pdf",
    "txt": "text/plain",
    "md": "text/markdown",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "csv": "text/csv",
}


def alter_metadata(doc, filename, user_id, chat_id):
    doc.metadata["source"] = filename  # to replace the actual temp file path with the name as was provided
    doc.metadata["user_id"] = user_id
    doc.metadata["chat_id"] = chat_id


def save_files(files):
    # making sure files/ exists
    dir = "uploaded_files"
    Path(dir).mkdir(parents=True, exist_ok=True)
    # parents=True to ensure all parent folders are also created and exist_ok means dont throw error if exists

    files_info = []
    for file in files:
        ext = file.name.split(".")[-1].lower()

        with tempfile.NamedTemporaryFile(delete=False, dir=dir) as tf:
            tf.write(file.getbuffer())

        files_info.append(
            {
                "filename": file.name,
                "file_size": file.size,
                "mime_type": mime_types.get(ext, "UNKNOWN"),
                "file_path": tf.name,
                "ext": ext,
            }
        )

    return files_info


def read_files_and_extract_chunks(files_info, user_id, chat_id):
    all_chunks = []

    for file_info in files_info:
        ext = file_info["ext"]
        file_path = file_info["file_path"]
        filename = file_info["filename"]

        if ext == "pdf":
            loader = PyPDFLoader(file_path)
        elif ext == "txt":
            loader = TextLoader(file_path)
        elif ext == "md":
            loader = None  # handling here especially
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=[("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")]
            )

            docs = splitter.split_text(content)
            for doc in docs:
                alter_metadata(doc, filename, user_id, chat_id)
                print(doc, "\n\n")
                all_chunks.append(doc)

        elif ext == "docx":
            loader = Docx2txtLoader(file_path)
        elif ext == "csv":
            loader = CSVLoader(file_path)
        else:
            loader = None

        if loader:
            docs_generator = loader.lazy_load()
            for doc in docs_generator:
                # print("ANALYYYYYYYZE", doc, '\n\n\n')
                # doc.metadata["download_location"] = doc.metadata["source"]
                alter_metadata(doc, filename, user_id, chat_id)
                all_chunks.append(doc)
                # print(doc.metadata)

    return all_chunks


def get_context_from_attachments(vector_store: Chroma, original_prompt_text: str, user_id, chat_id):
    if vector_store._collection.count() == 0:
        return ""

    context_string = ""
    with st.status(":material/document_search: Finding relevant context"):
        results = vector_store.similarity_search(
            query=original_prompt_text,
            k=5,
            filter={"$and": [{"user_id": user_id}, {"chat_id": chat_id}]},  # pyright: ignore
        )

        # context = "\n\n".join([doc.page_content + " [" + doc.metadata["source"] + "]" for doc in results])
        context_chunk_arr = []
        for i, doc in enumerate(results, start=1):
            fields = [
                "source",
                "page",
                "page_number",
                "header",
                "title",
                "description",
                "section",
                "category",
                "author",
                "language",
                "Header 1",
                "Header 2",
                "Header 3",
            ]

            metadata_strs = []
            for key in fields:
                if key in doc.metadata:
                    metadata_strs.append(
                        f"- **{key.upper()}**: {doc.metadata[key] if key != 'source' else '`' + doc.metadata[key] + '`'}"
                    )

            chunk_context_string = f"#### [SOURCE_{i}]\n" f"{'\n'.join(metadata_strs)}\n" f"- **CONTENT**:\n{doc.page_content}"
            st.info(chunk_context_string)
            context_chunk_arr.append(chunk_context_string)

        context_string = "\n---\n\n".join(context_chunk_arr)
        # print("<CCCOOONTEXT>" + context_string + "</CCCOOONTEXT>")

        return context_string
