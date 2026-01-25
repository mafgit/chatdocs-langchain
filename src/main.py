import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter
from handle_files import handle_files
from typing import Tuple, Literal, Optional, Sequence
from model import load_llm, load_vector_store, embedding_models, chat_models
import time


def convert_file_size(filename, file_size):
    if file_size > 1_048_576:
        file_size = file_size / 1_048_576
        unit = "MB"
    elif file_size > 1024:
        file_size = file_size / 1024
        unit = "KB"
    else:
        # file_size = file_size
        unit = "B"

    label = f"{filename} `{file_size:.1f} {unit}`"
    return file_size, unit, label


class Message:
    def __init__(
        self,
        role: Literal["ai", "human", "system"],
        content: str = "",
        files_info: Optional[Sequence[Tuple[str, float, str, str]]] = None,
    ):
        self.content = content
        self.role = role
        self.files_info = files_info or []

    def to_langchain(self):
        return {"role": self.role, "content": self.content}


def main():
    st.set_page_config("ChatDocs", page_icon=":material/borg:")

    chats = st.session_state["chats"]
    current_chat_id = st.session_state["current_chat_id"]
    current_chat = chats[current_chat_id]
    current_chat_history = current_chat["history"]

    st.header(":material/borg: " + current_chat["name"])

    # preferences
    with st.expander("Preferences", icon=":material/settings:"):
        left, middle, right = st.columns(3)
        with left:
            selected_chat_model = st.selectbox("Chat Model", tuple(chat_models), key="chat_model")
        with middle:
            selected_embedding_model = st.selectbox("Embedding Model", tuple(embedding_models), key="embedding_model")
        with right:
            st.selectbox(
                "Style",
                (
                    "Normal",
                    "Professional, Polished, Precise",
                    "Friendly, Warm, Chatty",
                    "Efficient, Concise, Plain",
                    "Candid, Direct, Encouraging",
                    "Nerdy, Exploratory, Enthusiastic",
                    "Quirky, Playful, Imaginative",
                ),
                key="style",
            )

        left, right = st.columns(2)
        with left:
            selected_temperature = st.slider(
                "Temperature (Randomness/Creativity)", 0.0, 2.0, value=0.8, step=0.1, format="plain", key="temperature"
            )
        # with right:
        #     st.selectbox()

    greetings_div = st.empty()

    if len(current_chat_history) == 0:
        greetings_div.html(
            f'<div style="display:flex;justify-content:center;align-items:center;min-height:max(250px,100%);margin-top:auto;opacity:0.8;font-size:1.2rem;">{st.session_state["greeting_msg"]}</div>'
        )
    else:
        # looping over chat history
        for item in current_chat_history:
            if item.role == "human":
                with st.chat_message("human"):
                    if item.files_info:
                        for filename, file_size, file_location, mime_type in item.files_info:
                            _, _, label = convert_file_size(filename, file_size)
                            with open(file_location, "rb") as f:
                                st.download_button(
                                    label=label,
                                    data=f,
                                    file_name=filename,
                                    mime=mime_type,
                                    icon=":material/file_present:",
                                )
                    st.markdown(item.content)
            elif item.role in {"ai", "assistant"}:
                with st.chat_message("ai"):
                    st.markdown(item.content)

    def stream_generator(chunks):
        response = ""

        for chunk in chunks:
            response += chunk.text
            yield chunk

        st.session_state["disabled"] = False
        current_chat_history.append(Message(content=response, role="ai", files_info=[]))

    sys_msg = Message(
        "system",
        content="You are a helpful assistant who focuses on providing relevant and useful information to user. If context is attached from documents, use it as well as your own knowledge to answer user's queries. If you don't know something, then say so.",
    )

    user_id = st.session_state["user_id"]

    prompt_input = st.chat_input(
        "Enter prompt or attach documents",
        disabled=st.session_state["disabled"],
        accept_file="multiple",
        accept_audio=False,
        file_type=["pdf", "txt", "md", "docx", "csv"],
        max_upload_size=800,
        max_chars=3000,
    )

    if prompt_input:
        files = prompt_input.files[:10]
        original_prompt_text = prompt_input.text.strip()

        final_prompt_text = original_prompt_text[:]

        error = False
        if not files and not original_prompt_text:
            error = True

        if not error:
            vector_store = load_vector_store(selected_embedding_model)
            st.session_state["disabled"] = True
            st.session_state["chats"][current_chat_id]["last_interaction"] = time.time()
            greetings_div.empty()
            if not original_prompt_text and files:
                final_prompt_text = "I am attaching some documents"

            with st.chat_message("human"):
                files_info = None
                if files:
                    with st.status("Handling attached documents"):
                        with st.status("Saving files & getting their contents & info"):
                            docs, files_info = handle_files(files, user_id=user_id, chat_id=current_chat_id)

                        with st.status("Splitting into chunks"):
                            splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=110)
                            chunks = splitter.split_documents(docs)
                            # chunks[0].page_content, chunks[0].metadata
                        with st.status("Adding to vector store"):
                            vector_store.add_documents(chunks)

                if vector_store._collection.count() > 0:
                    with st.status("Finding relevant context"):
                        results = vector_store.similarity_search(
                            query=final_prompt_text,
                            k=5,
                            filter={"$and": [{"user_id": user_id}, {"chat_id": current_chat_id}]},  # pyright: ignore
                        )

                        # context = "\n\n".join([doc.page_content + " [" + doc.metadata["source"] + "]" for doc in results])

                        context = ""
                        for doc in results:
                            info = doc.page_content + " [" + doc.metadata["source"] + "]"
                            st.info(info)
                            context += "\n\n" + doc.page_content + " [" + doc.metadata["source"] + "]"

                        if context:
                            context = context[:-2]  # to remove last two \n\n

                    if context.strip():
                        final_prompt_text = (
                            "Some relevant context from attached files/documents:\n\n"
                            + context
                            + "\n\nPrompt: "
                            + final_prompt_text
                        )

                # print(final_prompt_text)

                if files_info:
                    for filename, file_size, file_location, mime_type in files_info:
                        _, _, label = convert_file_size(filename, file_size)
                        with open(file_location, "rb") as f:
                            st.download_button(
                                label=label,
                                data=f,
                                file_name=filename,
                                mime=mime_type,
                                icon=":material/file_present:",
                            )
                        # st.info(filename + " (" + str(file_size) + "KB)", icon=":material/file_present:")
                st.markdown(original_prompt_text)

            # with st.spinner(text="", width="stretch"):
            history = (
                [sys_msg.to_langchain()]
                + [item.to_langchain() for item in current_chat_history[-5:]]
                + [{"role": "human", "content": final_prompt_text}]
            )

            llm = load_llm(selected_chat_model, temperature=selected_temperature)
            with st.chat_message("ai"):
                chunks = llm.stream(history)
                # appending original message to history
                original_message = Message(content=original_prompt_text, role="human", files_info=files_info)
                current_chat_history.append(original_message)
                st.write_stream(stream_generator(chunks))

        st.session_state["disabled"] = False
