import streamlit as st
from supabase import create_client, Client
import pandas as pd

url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- ניהול ציונים (עודכן לממוצע אוניברסיטאי) ---
def save_grade(subject, topic, grade, credits=1.0, notes=""):
    try:
        data = {"subject": subject, "topic": topic, "grade": grade, "credits": credits, "notes": notes}
        supabase.table("grades").insert(data).execute()
    except Exception as e:
        st.error(f"שגיאת סנכרון נתונים: {e}")

def get_all_grades():
    try:
        res = supabase.table("grades").select("*").order("created_at", desc=True).execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame(columns=["id", "subject", "topic", "grade", "credits", "created_at"])

def clear_db():
    try:
        # שיטה בטוחה למחיקה - מוחק הכל איפה שה-ID גדול מ-0
        supabase.table("grades").delete().gt("id", 0).execute()
    except Exception as e:
        print(f"Error clearing db: {e}")

# --- ניהול זיכרון צ'אט ---
def save_chat_message(role, content):
    try:
        supabase.table("chat_history").insert({"role": role, "content": content}).execute()
    except: pass

def get_persistent_chat_history(limit=25):
    try:
        res = supabase.table("chat_history").select("*").order("created_at", desc=False).limit(limit).execute()
        return res.data
    except: return []

def clear_chat_history():
    try:
        # שיטה בטוחה למחיקה - מוחק הכל איפה שה-ID גדול מ-0
        supabase.table("chat_history").delete().gt("id", 0).execute()
    except Exception as e:
        print(f"Error clearing chat: {e}")
