import streamlit as st
from handle_docs import (
    read_files_and_extract_chunks,
    save_files,
    get_context_from_attachments,
    get_web_results,
    split_and_add_to_store,
)
from main import load_chat_model, load_vector_store, get_chain, embedding_models, chat_models
import time
from random import random
import db
from sidebar_area import create_new_chat


def render_statuses(statuses):
    for status in statuses:
        with st.status(label=status["label"], state=status["state"]):
            if status["content"]:
                st.markdown(status["content"])


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


# class Message:
#     def __init__(
#         self,
#         role: Literal["ai", "human", "system"],
#         content: str = "",
#         files_info: Optional[Sequence[dict]] = None,
#         statuses: Optional[Sequence[dict]] = None,
#     ):
#         self.content = content
#         self.role = role
#         self.files_info = files_info or []
#         self.statuses = statuses or []

#     def to_langchain(self):
#         return {"role": self.role, "content": self.content}


def main():
    chats = st.session_state["chats"]
    current_chat_id = st.session_state["current_chat_id"]
    current_chat = None
    for c in chats:
        if c["id"] == current_chat_id:
            current_chat = c
            break

    if not current_chat:
        return

    user_id = st.session_state["user_id"]

    if "current_chat_history" not in st.session_state:
        if current_chat_id == 0:
            st.session_state["current_chat_history"] = []
        else:
            st.session_state["current_chat_history"] = db.get_chat_messages(current_chat_id)

    current_chat_history = st.session_state["current_chat_history"]

    left, right = st.columns([0.9, 0.1])
    with left:
        st.subheader("✦︎  " + current_chat["name"])
    with right:
        with st.container(horizontal_alignment="right"):
            if current_chat_id != 0:
                delete_btn = st.button(":material/delete:")
                if delete_btn:
                    db.delete_chat(current_chat_id)
                    create_new_chat()

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

        with st.form("preferences", clear_on_submit=False, border=False):
            left, right = st.columns(2)
            with left:
                selected_chat_model = st.selectbox("Chat Model", chat_models, key="chat_model", accept_new_options=True)
            with right:
                selected_embedding_model = st.selectbox(
                    "Embedding Model",
                    embedding_models,
                    key="embedding_model",
                    accept_new_options=True,
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

            submitted = st.form_submit_button("Save Preferences", type="primary", icon=":material/save:", width="stretch")

            if submitted:
                db.update_user_preferences(
                    chat_model=selected_chat_model,
                    embedding_model=selected_embedding_model,
                    style=selected_style,
                    temperature=selected_temperature,
                    id=user_id,
                )

    # ---------------- GREETING OR CHAT HISTORY LOOP RENDERING ----------------

    greetings_div = st.empty()

    if len(current_chat_history) == 0:
        greetings_div.html(
            f'<div style="display:flex;flex-direction:column;justify-content:center;align-items:center;min-height:max(275px,100%);margin-top:auto;opacity:1;"><p style="font-size:1.2rem;">{st.session_state["greeting_msg"]}</p><p style="opacity:0.8;">💡 Start prompt with /search to enable web search.<p/></div>'
        )
    else:
        for item in current_chat_history:
            if item["role"] == "human":
                with st.chat_message("human"):
                    if item.get("statuses", []):
                        render_statuses(item["statuses"])
                    if item.get("files_info", []):
                        render_file_download_buttons(item["files_info"])
                    st.markdown(item["content"])
            elif item["role"] in {"ai", "assistant"}:
                with st.chat_message("ai"):
                    if item.get("statuses", []):
                        render_statuses(item["statuses"])
                    st.markdown(item["content"])

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
            greetings_div.empty()

            try:
                vector_store = load_vector_store(selected_embedding_model)

                chat_model = load_chat_model(
                    selected_chat_model,
                    temperature=selected_temperature,
                    reasoning=(
                        None
                        if selected_reasoning == "Default"
                        else False if selected_reasoning == "Off" else selected_reasoning.lower()
                    ),
                )
            except Exception as e:
                st.error(str(e))
                # st.error(
                #     f"Invalid model selected {selected_embedding_model}, please verify the exact name of the embedding model you have selected in preferences from Ollama."
                # )
                st.stop()
            finally:
                st.session_state["disabled"] = False

            # -------------- create new chat and update the session state ------------

            if len(current_chat_history) == 0:
                new_chat_id = db.create_chat(current_chat["name"], user_id)
                current_chat_id = new_chat_id
                st.session_state["current_chat_id"] = new_chat_id
                for chat in st.session_state["chats"]:
                    if chat["id"] == 0:
                        chat["id"] = new_chat_id

            with st.chat_message("human"):
                # ----------------- SAVING FILES -----------------

                files_info = []
                if files:
                    with st.status(":material/document_scanner: Handling attached documents"):
                        with st.status(":material/save: Saving files & getting their contents & info"):
                            files_info = save_files(files)

                        # ----------------- READING FILES AND EXTRACTING CHUNKS -----------------

                        chunks = read_files_and_extract_chunks(files_info, user_id, current_chat_id)
                        split_and_add_to_store(chunks, vector_store)
                # ---------------- FILE DOWNLOAD BUTTONS ----------------

                if files_info:
                    render_file_download_buttons(files_info)
                    # st.info(filename + " (" + str(file_size) + "KB)", icon=":material/file_present:")
                st.markdown(original_prompt_text)

            # --------------- AI RESPONSE ELEMENT ---------------

            with st.chat_message("ai"):

                statuses = []

                # ------------- WEB SEARCH -------------

                if original_prompt_text.startswith("/search"):
                    # original_prompt_text = original_prompt_text[7:]
                    status_label = ":material/web: Searching Web"

                    try:
                        with st.status(status_label):
                            chunks = get_web_results(original_prompt_text, chat_id=current_chat_id, user_id=user_id)
                            split_and_add_to_store(chunks, vector_store)

                        status_state = "complete"

                    except:
                        status_state = "error"
                    finally:
                        statuses.append(
                            {
                                "label": status_label,
                                "content": "",
                                "state": status_state,
                                "type": "web_search",
                            }
                        )

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
                        else ""
                    ),
                    "human_input": (
                        "I have attached some attachments" if files and not original_prompt_text else original_prompt_text
                    ),
                    "chat_history": current_chat_history,
                }

                # testing prompt
                # print("FINAL PROMPT BEING SENT\n", prompt_template.format_messages(**input))

                chunks = chain.stream(input=input)

                # ------------ inserting original message to db and history ---------------------

                db.insert_chat_message(
                    chat_id=current_chat_id, content=original_prompt_text, role="human", files_info=files_info, statuses=[]
                )
                original_message = {"content": original_prompt_text, "role": "human", "files_info": files_info}
                current_chat_history.append(original_message)

                # ------------------- updating last interaction -------------------

                for chat in st.session_state["chats"]:
                    if chat["id"] == current_chat_id:
                        new_time = int(time.time())
                        db.update_last_interaction(chat_id=current_chat_id, new_time=new_time)
                        chat["last_interaction"] = new_time
                        break

                # ----------------- STREAM GENERATOR -----------------

                def stream_generator(chunks):
                    response = ""

                    # citation_pattern = r"\[\[\SOURCE_(\d+)]\]"
                    # replacement_pattern = r"\[\1\]"

                    # thinking_status = None
                    # thinking_placeholder = None
                    # thinking_started = False

                    if selected_reasoning in {"Default", "Off"}:
                        thinking_or_processing = "processing"
                        final_thinking_status_label = ":material/memory: Processing"

                    else:
                        thinking_or_processing = "thinking"
                        final_thinking_status_label = ":material/lightbulb: Thinking"

                    final_thinking_content = ""
                    final_thinking_status_state = "running"
                    thinking_status = st.status(final_thinking_status_label)
                    thinking_placeholder = thinking_status.empty()
                    processing_start_time = time.time()
                    processing_end_time = None

                    try:
                        for chunk in chunks:
                            if st.session_state.get("stop", False) == True:
                                st.session_state["stop"] = False
                                return

                            if not isinstance(chunk, str):
                                reasoning_content = chunk.additional_kwargs.get("reasoning_content")
                                if reasoning_content:
                                    final_thinking_content += reasoning_content
                                    thinking_placeholder.markdown(final_thinking_content)

                                if chunk.content:
                                    if processing_end_time is None:
                                        processing_end_time = time.time()
                                        final_thinking_status_state = "complete"
                                        if processing_end_time:
                                            final_thinking_status_label += (
                                                f" ({round(processing_end_time - processing_start_time)}s)"
                                            )
                                        thinking_status.update(
                                            label=final_thinking_status_label,
                                            state=final_thinking_status_state,
                                        )
                                    response += chunk.content
                                    yield chunk.content
                            else:
                                final_thinking_status_state = "complete"
                                if processing_end_time:
                                    final_thinking_status_label += f" ({round(processing_end_time - processing_start_time)}s)"
                                thinking_status.update(
                                    label=final_thinking_status_label,
                                    state=final_thinking_status_state,
                                )
                                response += chunk
                                yield chunk

                        statuses.extend(
                            [
                                {
                                    "label": ":material/document_search: Finding relevant context",
                                    "content": context_string,
                                    "state": "complete",
                                    "type": "context",
                                },
                                {
                                    "label": final_thinking_status_label,
                                    "content": final_thinking_content,
                                    "state": final_thinking_status_state,
                                    "type": thinking_or_processing,
                                },
                            ]
                        )
                        current_chat_history.append({"content": response, "role": "ai", "files_info": [], "statuses": statuses})
                        db.insert_chat_message(
                            chat_id=current_chat_id, content=response, role="ai", files_info=[], statuses=statuses
                        )

                    except Exception as e:
                        # raise e
                        err = str(e)
                        if "does not support thinking" in err:
                            if thinking_status:
                                final_thinking_status_label = f":material/light_off: Thinking not supported by {selected_chat_model}. Retry after turning off thinking."
                                final_thinking_status_state = "error"
                                thinking_status.update(
                                    label=final_thinking_status_label,
                                    state=final_thinking_status_state,
                                )
                        else:
                            st.error("An error occurred:" + err)

                        st.session_state["disabled"] = False
                        st.stop()

                    finally:
                        st.session_state["disabled"] = False

                # stop_btn_container = st.empty()
                # if stop_btn_container.button(":material/stop_circle:"):
                #     st.session_state["stop"] = True
                #     stop_btn_container.empty()
                st.write_stream(stream_generator(chunks))

        st.session_state["disabled"] = False
