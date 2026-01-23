from langchain_community.document_loaders import PyPDFLoader, TextLoader


# print(TextLoader("assets/a.txt").load())

loader = PyPDFLoader("assets/what_is_a_constitution_0.pdf")
pages = loader.load()

# for pg in pages:
#     print(pg.metadata, ": ", pg.page_content)


from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
chunks = splitter.split_documents(pages)

# print(chunks[0].page_content)
# print('\n\nAAAAAAAAAAAAAAAAAAAAA\n\n')
# print(chunks[1].page_content)

