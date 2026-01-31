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
            name TEXT NOT NULL
        );

        create table if not exists chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER REFERENCES chats(id),
            content TEXT,
            role TEXT CHECK(role in ('system', 'ai', 'human')),
            files_info TEXT CHECK(json_valid(files_info)),
            statuses TEXT CHECK(json_valid(statuses))
        );

        -- files_info is gonna be array of {filename, file_path, file_size, mime_type}
        -- statuses is gonna be like {thinking, processing, context}
    """

    conn = get_conn()
    cursor = conn.cursor()

    cursor.executescript(query)

    conn.commit()
    conn.close()


# setup()


def create_chat(name: str, user_id: int):
    conn = get_conn()
    cursor = conn.cursor()

    query = """
    insert into chats (name, user_id) values (?, ?)
    """
    cursor.execute(query, (name, user_id))

    conn.commit()
    conn.close()


def delete_chat(id: int):
    conn = get_conn()
    cursor = conn.cursor()

    query = """
    delete from chats where id = ?
    """
    cursor.execute(query, (id,))

    conn.commit()
    conn.close()


def get_user_chats(user_id: int):
    conn = get_conn()
    cursor = conn.cursor()

    query = """
    select * from chats where user_id = ?
    """
    cursor.execute(query, (user_id,))
    rows = cursor.fetchall()

    conn.commit()
    conn.close()

    return rows


def get_chat_messages(chat_id: int):
    conn = get_conn()
    cursor = conn.cursor()

    query = """
    select * from chat_messages
    where chat_id = ?
    """
    cursor.execute(query, (chat_id,))
    rows = cursor.fetchall()

    conn.commit()
    conn.close()

    return rows


from typing import List, Literal
import json


def insert_chat_message(
    chat_id: int, content: str, role: Literal["system", "ai", "human"], files_info: List[dict], statuses: dict
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
