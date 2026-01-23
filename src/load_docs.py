import fitz
from docx import Document


def get_full_text_from_files(files):
    full_text = ""

    for file in files:
        full_text += "\n\n" + file.name + ":\n"
        ext = file.name.split(".")[-1]
        if ext == "pdf":
            with fitz.open(stream=file.read(), filetype="pdf") as doc:
                for page in doc:
                    full_text += page.get_text()
        elif ext in {"txt", "md"}:
            full_text += file.getvalue().decode("utf-8")
        elif ext in {"docx", "doc"}:
            doc = Document(file)
            for para in doc.paragraphs:
                full_text += para.text + '\n'

    return full_text
