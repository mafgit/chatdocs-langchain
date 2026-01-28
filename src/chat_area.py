import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter
from handle_docs import read_files_and_extract_chunks, save_files, get_context_from_attachments
from typing import Tuple, Literal, Optional, Sequence
from main import load_chat_model, load_vector_store, get_chain, embedding_models, chat_models, prompt_template
import time
from random import random
import re


def render_file_download_buttons(files_info):
    for file_info in files_info:
        filename, file_size, file_path, mime_type = (
            file_info["filename"],
            file_info["file_size"],
            file_info["file_path"],
            file_info["mime_type"],
        )
        _, _, label = convert_file_size(filename, file_size)
        with open(file_path, "rb") as f:
            st.download_button(
                label=label,
                data=f,
                file_name=filename,
                mime=mime_type,
                icon=":material/file_present:",
                key=filename + str(random() * 99999),
            )


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

    left, right = st.columns([0.9, 0.1])
    with left:
        st.subheader(":material/borg: " + current_chat["name"])
    with right:
        with st.container(horizontal_alignment="right"):
            st.button(":material/delete:")

    # ---------------- PREFERENCES ----------------

    with st.expander("Preferences", icon=":material/settings:"):
        st.warning(
            "Ensure models are downloaded locally: `ollama pull <model_name>` (unless the model_name is ending with `cloud` which requires login in Ollama software instead.)\n\nYou can manually type a different model from Ollama library below as well.",
            icon=":material/info:",
        )
        st.warning(
            "Changing embedding model would require you to either re-upload documents or start a new chat for it to work properly",
            icon=":material/warning:",
        )
        left, right = st.columns(2)
        with left:
            selected_chat_model = st.selectbox("Chat Model", chat_models, key="chat_model", accept_new_options=True)
        with right:
            selected_embedding_model = st.selectbox(
                "Embedding Model", embedding_models, key="embedding_model", accept_new_options=True
            )

        left, right = st.columns(2)
        with left:
            selected_reasoning = st.selectbox(
                "Reasoning (Only supported in some models)", ("Default", "Off", "Low", "Medium", "High"), key="reasoning"
            )
        with right:
            selected_style = st.selectbox(
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

        selected_temperature = st.slider(
            "Temperature (Creativity) (Default = 0.6)", 0.0, 2.0, value=0.6, step=0.1, format="plain", key="temperature"
        )

    # ---------------- GREETING OR CHAT HISTORY LOOP RENDERING ----------------

    greetings_div = st.empty()

    if len(current_chat_history) == 0:
        greetings_div.html(
            f'<div style="display:flex;justify-content:center;align-items:center;min-height:max(250px,100%);margin-top:auto;opacity:0.8;font-size:1.2rem;">{st.session_state["greeting_msg"]}</div>'
        )
    else:
        for item in current_chat_history:
            if item.role == "human":
                with st.chat_message("human"):
                    if item.files_info:
                        render_file_download_buttons(item.files_info)
                    st.markdown(item.content)
            elif item.role in {"ai", "assistant"}:
                with st.chat_message("ai"):
                    st.markdown(item.content)

    user_id = st.session_state["user_id"]

    # ----------------- PROMPT INPUT ELEMENT -----------------

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

        error = False
        if not files and not original_prompt_text:
            error = True

        if not error:
            try:
                vector_store = load_vector_store(selected_embedding_model)
            except:
                st.error(
                    "Invalid model selected, please verify the exact name of the embedding model you have selected in preferences from Ollama."
                )
                st.stop()
            finally:
                st.session_state["disabled"] = False

            st.session_state["chats"][current_chat_id]["last_interaction"] = time.time()
            greetings_div.empty()

            with st.chat_message("human"):

                # ----------------- SAVING FILES -----------------

                files_info = None
                if files:
                    with st.status(":material/document_scanner: Handling attached documents"):
                        with st.status(":material/save: Saving files & getting their contents & info"):
                            files_info = save_files(files)

                        # ----------------- READING FILES AND EXTRACTING CHUNKS -----------------

                        chunks = read_files_and_extract_chunks(files_info, user_id, current_chat_id)
                        if chunks:
                            with st.status(":material/split_scene_left: Splitting into chunks"):
                                splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=110)
                                chunks = splitter.split_documents(chunks)
                                # chunks[0].page_content, chunks[0].metadata

                            if chunks:
                                with st.status(":material/splitscreen_add: Adding chunks to vector store"):
                                    vector_store.add_documents(chunks)

                # ---------------- FILE DOWNLOAD BUTTONS ----------------

                if files_info:
                    render_file_download_buttons(files_info)
                    # st.info(filename + " (" + str(file_size) + "KB)", icon=":material/file_present:")
                st.markdown(original_prompt_text)

                try:
                    chat_model = load_chat_model(
                        selected_chat_model,
                        temperature=selected_temperature,
                        reasoning=(
                            None
                            if selected_reasoning == "Default"
                            else False if selected_reasoning == "Off" else selected_reasoning.lower()
                        ),
                    )
                except:
                    st.error(
                        "Invalid model selected, please verify the exact name of the chat model you have selected in preferences from Ollama."
                    )
                    st.stop()
                finally:
                    st.session_state["disabled"] = False

            # --------------- AI RESPONSE ELEMENT ---------------

            with st.chat_message("ai"):

                # --------------- VECTOR DB RETRIEVAL AND CONTEXT BUILDING ---------------

                context_string = get_context_from_attachments(
                    vector_store, original_prompt_text, chat_id=current_chat_id, user_id=user_id
                )

                # -------------- GETTING CHAIN AND STREAMING --------------

                chain = get_chain(chat_model=chat_model)

                input = {
                    "style_rule": f"- Adopt a {selected_style} tone" if selected_style != "Normal" else "",
                    "attachments": (
                        f"Following contents were found from documents attached. Use them to answer user query. Also reference them.\n\n---\n{context_string.strip()}"
                        if context_string.strip()
                        else "[NO RELEVANT ATTACHMENT UPLOADED BY USER]"
                    ),
                    "human_input": (
                        "I have attached some attachments" if files and not original_prompt_text else original_prompt_text
                    ),
                    "chat_history": [msg.to_langchain() for msg in current_chat_history],
                }

                # testing prompt
                print("FINAL PROMPT BEING SENT\n", prompt_template.format_messages(**input))

                chunks = chain.stream(input=input)

                # appending original message to history
                original_message = Message(content=original_prompt_text, role="human", files_info=files_info)
                current_chat_history.append(original_message)

                # ----------------- STREAM GENERATOR -----------------

                def stream_generator(chunks):
                    response = ""

                    # citation_pattern = r"\[\[\SOURCE_(\d+)]\]"
                    # replacement_pattern = r"\[\1\]"

                    # thinking_status = None
                    # thinking_placeholder = None
                    # thinking_started = False

                    if selected_reasoning in {"Default", "Off"}:
                        status = ":material/memory: Processing"
                    else:
                        status = ":material/lightbulb: Thinking"

                    full_thinking = ""
                    thinking_status = st.status(status)
                    thinking_placeholder = thinking_status.empty()

                    try:
                        for chunk in chunks:
                            if st.session_state.get("stop", False) == True:
                                st.session_state["stop"] = False
                                current_chat_history.append(Message(content=response, role="ai", files_info=[]))
                                st.session_state["disabled"] = False
                                return

                            if not isinstance(chunk, str):

                                reasoning_content = chunk.additional_kwargs.get("reasoning_content")
                                if reasoning_content:
                                    full_thinking += reasoning_content
                                    thinking_placeholder.markdown(full_thinking)  # pyright: ignore

                                if chunk.content:
                                    thinking_status.update(  # pyright: ignore
                                        label=status,
                                        state="complete",
                                    )
                                    response += chunk.content
                                    yield chunk.content
                            else:
                                response += chunk
                                yield chunk

                    except Exception as e:
                        # raise e
                        err = str(e)
                        if "does not support thinking" in err:
                            if thinking_status:
                                thinking_status.update(
                                    label=f":material/light_off: Thinking not supported by {selected_chat_model}", state="error"
                                )
                        else:
                            st.error("An error occurred:" + err)

                        st.session_state["disabled"] = False
                        st.stop()

                    current_chat_history.append(Message(content=response, role="ai", files_info=[]))
                    st.session_state["disabled"] = False
                
                stop_btn_container = st.empty()
                if stop_btn_container.button(":material/stop_circle:"):
                    st.session_state["stop"] = True
                    stop_btn_container.empty()
                st.write_stream(stream_generator(chunks))

        st.session_state["disabled"] = False
