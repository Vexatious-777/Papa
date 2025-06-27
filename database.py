import sqlite3

def init_db(db_name="demons.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS demons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT,
        image_url TEXT,
        local_image_path TEXT,
        origin TEXT,
        race TEXT,
        alignment TEXT
        )
    """)
    conn.commit()
    return conn

def insert_demon_data(conn, demon_data):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO demons (name, url, image_url, local_image_path, origin, race, alignment)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        demon_data["name"],
        demon_data["url"],
        demon_data["image_url"],
        demon_data["local_image_path"],
        demon_data["origin"],
        demon_data["race"],
        demon_data["alignment"]
    ))
    conn.commit()
    
