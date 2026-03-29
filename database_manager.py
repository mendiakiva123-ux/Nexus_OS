import sqlite3
import pandas as pd

DB_NAME = "nexus_vault.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS grades 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT, topic TEXT, 
                       grade REAL, date TEXT, notes TEXT)''')
    conn.commit()
    conn.close()

def save_grade(subject, topic, grade, notes=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    date_now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("INSERT INTO grades (subject, topic, grade, date, notes) VALUES (?, ?, ?, ?, ?)",
                   (subject, topic, grade, date_now, notes))
    conn.commit()
    conn.close()

def get_all_grades():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM grades", conn)
    conn.close()
    return df

def clear_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM grades")
    conn.commit()
    conn.close()
