import sqlite3

conn = sqlite3.connect("chatdocs.db")


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
            temperature NUMERIC DEFAULT 0.8
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
        );

        create table if not exists chat_message_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_message_id INTEGER REFERENCES chat_messages(id),
            filename TEXT NOT NULL,
            file_size TEXT NOT NULL,
            file_location TEXT NOT NULL,
            mime_type TEXT NOT NULL
        );

        -- create table if not exists chat_message_statuses
    """

    
