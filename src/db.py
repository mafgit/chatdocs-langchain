import sqlite3


def get_conn():
    conn = sqlite3.connect("chatdocs.db")
    return conn


def setup():
    query = """
        PRAGMA foreign_keys = ON;

        create table if not exists users (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            chat_model TEXT DEFAULT "gemma2:2b",
            style TEXT DEFAULT "Normal",
            embedding_model TEXT DEFAULT "embeddinggemma:300m",
            temperature NUMERIC DEFAULT 0.6

            -- deciding to keep the following default each time:
            -- reasoning TEXT CHECK(reasoning in ('Default', 'Off', 'Low', 'Medium', 'High')),
            -- web_search BOOLEAN DEFAULT FALSE
        );
        
        create table if not exists chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            name TEXT NOT NULL,
            last_interaction INTEGER DEFAULT (unixepoch())
        );

        create table if not exists chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER REFERENCES chats(id),
            content TEXT,
            role TEXT CHECK(role in ('system', 'ai', 'human')),
            files_info TEXT CHECK(json_valid(files_info)),
            statuses TEXT CHECK(json_valid(statuses)),
            sent_at INTEGER DEFAULT (unixepoch())
        );

        -- files_info is gonna be array of {filename, file_path, file_size, mime_type}
        -- statuses is gonna be like {thinking, processing, context}

        insert into users (
            id,
            name,
            password
        ) values (0, "Abdullah", "password");
    """

    conn = get_conn()
    cursor = conn.cursor()

    cursor.executescript(query)

    conn.commit()
    conn.close()


def create_chat(name: str, user_id: int) -> int:
    conn = get_conn()
    cursor = conn.cursor()

    query = """
    insert into chats (name, user_id) values (?, ?) returning id
    """
    cursor.execute(query, (name, user_id))
    new_id = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return new_id


def delete_chat(id: int):
    conn = get_conn()
    cursor = conn.cursor()

    query = """
    delete from chats where id = ?
    """
    cursor.execute(query, (id,))

    conn.commit()
    conn.close()


def get_chats(user_id: int):
    conn = get_conn()
    cursor = conn.cursor()

    query = """
    select id, user_id, name, last_interaction from chats
    where user_id = ?
    order by last_interaction DESC
    """
    cursor.execute(query, (user_id,))
    rows = cursor.fetchall()

    conn.commit()
    conn.close()

    return_data = []
    for id, user_id, name, last_interaction in rows:
        return_data.append({"id": id, "user_id": user_id, "name": name, "last_interaction": last_interaction})

    return return_data


def get_chat_messages(chat_id: int):
    conn = get_conn()
    cursor = conn.cursor()

    query = """
    select id, chat_id, content, role, files_info, statuses, sent_at from chat_messages
    where chat_id = ?
    order by sent_at ASC
    """
    cursor.execute(query, (chat_id,))
    rows = cursor.fetchall()

    conn.commit()
    conn.close()

    return_data = []
    for id, chat_id, content, role, files_info, statuses, sent_at in rows:
        return_data.append(
            {
                "id": id,
                "chat_id": chat_id,
                "content": content,
                "role": role,
                "files_info": json.loads(files_info),
                "statuses": json.loads(statuses),
                "sent_at": sent_at,
            }
        )

    return return_data


from typing import List, Literal
import json


def insert_chat_message(
    chat_id: int, content: str, role: Literal["system", "ai", "human"], files_info: List[dict], statuses: List[dict]
):
    conn = get_conn()
    cursor = conn.cursor()

    files_info_json = json.dumps(files_info)
    statuses_json = json.dumps(statuses)

    query = """
    insert into chat_messages (chat_id, content, role, files_info, statuses) values (?, ?, ?, ?, ?)
    """
    cursor.execute(query, (chat_id, content, role, files_info_json, statuses_json))

    conn.commit()
    conn.close()


def update_last_interaction(chat_id: int, new_time: int):
    conn = get_conn()
    cursor = conn.cursor()

    query = """
    update chats set last_interaction = ? where id = ?
    """
    cursor.execute(query, (new_time, chat_id))

    conn.commit()
    conn.close()


def update_user_preferences(id, chat_model, embedding_model, temperature, style):
    conn = get_conn()
    cursor = conn.cursor()

    query = f"""
    update users set chat_model = ?, embedding_model = ?, temperature = ?, style = ? where id = ?
    """
    cursor.execute(query, (chat_model, embedding_model, temperature, style, id))

    conn.commit()
    conn.close()



def get_user_info(user_id: int):
    conn = get_conn()
    cursor = conn.cursor()

    query = """
    select name, temperature, embedding_model, chat_model, style from users
    where id = ?
    """
    cursor.execute(query, (user_id,))
    name, temperature, embedding_model, chat_model, style = cursor.fetchone()

    conn.commit()
    conn.close()

    return {
        "name": name,
        "temperature": temperature,
        "embedding_model": embedding_model,
        "chat_model": chat_model,
        "style": style,
    }
