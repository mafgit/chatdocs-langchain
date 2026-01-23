from langchain_community.document_loaders import TextLoader, UnstructuredMarkdownLoader, Docx2txtLoader, PyPDFLoader, CSVLoader
import tempfile

mime_types = {
    "pdf": "application/pdf",
    "txt": "text/plain",
    "md": "text/markdown",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "csv": "text/csv",
}


def handle_files(files):
    """Saves files, reads them, and gets docs from them and returns them as in an array and also returns a file locations array"""

    all_docs = []
    all_files_info = []

    for file in files:
        ext = file.name.split(".")[-1].lower()

        with tempfile.NamedTemporaryFile(delete=False, dir="files") as tf:
            tf.write(file.getbuffer())
            file_path = tf.name
            all_files_info.append((file.name, file.size, tf.name, mime_types[ext]))

        if ext == "pdf":
            loader = PyPDFLoader(file_path)
        elif ext == "txt":
            loader = TextLoader(file_path)
        elif ext == "md":
            loader = UnstructuredMarkdownLoader(file_path)
        elif ext == "docx":
            loader = Docx2txtLoader(file_path)
        elif ext == "csv":
            loader = CSVLoader(file_path)
        else:
            loader = None

        if loader:
            docs = loader.load()
            for doc in docs:
                # doc.metadata["download_location"] = doc.metadata["source"]
                doc.metadata["source"] = file.name

            all_docs.extend(docs)

    return all_docs, all_files_info
