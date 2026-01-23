from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3.2")
# response = llm.invoke("What is your name, O model!")
# print(response.content)

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_template("Respond to user queries concisely and helpfully and very briefly: {msg}")
parser = StrOutputParser()

chain = prompt | llm | parser
response = chain.stream({"msg": "Hello there how are you, my name is Abdullah."})

for chunk in response:
    print(chunk, end="", flush=True)

print("\n------\n")
response = chain.stream({"msg": "Do you remember my name?"})

for chunk in response:
    print(chunk, end="", flush=True)
