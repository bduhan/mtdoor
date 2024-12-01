import sqlite3


def initialize_database(db: str):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS mail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    sender_short_name TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    date TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    content TEXT NOT NULL,
                    unique_id TEXT NOT NULL,
                    notify BOOLEAN DEFAULT 1
                );"""
    )
    conn.commit()
    c.execute(
        """CREATE TABLE IF NOT EXISTS xfr (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    peer TEXT NOT NULL,
                    data TEXT NOT NULL
                );"""
    )
    conn.commit()
    c.execute(
        """CREATE TABLE IF NOT EXISTS peers (
                    node_id TEXT NOT NULL PRIMARY KEY
                );"""
    )
    conn.commit()
    c.execute(
        """CREATE TABLE IF NOT EXISTS aliases (
                    node_id TEXT NOT NULL,
                    alias TEXT NOT NULL,
                    PRIMARY KEY (node_id, alias)
                );"""
    )
    conn.commit()
    conn.close()
