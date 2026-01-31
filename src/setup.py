import pathlib
import db
import shutil

pathlib.Path("chatdocs.db").unlink(missing_ok=True)
db.setup()

try:
    shutil.rmtree("vector_store")
except:
    pass

try:
    shutil.rmtree("uploaded_files")
except:
    pass
