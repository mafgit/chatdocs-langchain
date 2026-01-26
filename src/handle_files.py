from langchain_community.document_loaders import TextLoader, UnstructuredMarkdownLoader, Docx2txtLoader, PyPDFLoader, CSVLoader
import tempfile
from pathlib import Path
from langchain_text_splitters import MarkdownHeaderTextSplitter

mime_types = {
    "pdf": "application/pdf",
    "txt": "text/plain",
    "md": "text/markdown",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "csv": "text/csv",
}


def alter_metadata(doc, file, user_id, chat_id):
    doc.metadata["source"] = file.name  # to replace the actual temp file path with the name as was provided
    doc.metadata["user_id"] = user_id
    doc.metadata["chat_id"] = chat_id


def handle_files(files, user_id: str, chat_id: str):
    """Saves files, reads them, and gets docs from them and returns them as in an array and also returns a file locations array"""

    all_docs = []
    all_files_info = []

    for file in files:
        ext = file.name.split(".")[-1].lower()

        # creating folder to save files if doesnt exist
        dir = "files"
        Path(dir).mkdir(
            parents=True, exist_ok=True
        )  # parents=True to ensure all parent folders are also created and exist_ok means dont throw error if exists
        with tempfile.NamedTemporaryFile(delete=False, dir=dir) as tf:
            tf.write(file.getbuffer())
            file_path = tf.name
            all_files_info.append((file.name, file.size, tf.name, mime_types[ext]))

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
                alter_metadata(doc, file, user_id, chat_id)
                print(doc, '\n\n')
                all_docs.append(doc)

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
                alter_metadata(doc, file, user_id, chat_id)
                all_docs.append(doc)
                # print(doc.metadata)

    return all_docs, all_files_info
