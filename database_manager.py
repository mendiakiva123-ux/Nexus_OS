import streamlit as st
from supabase import create_client, Client
import pandas as pd

# חיבור מאובטח לסופאבייס
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- ניהול ציונים ---
def save_grade(subject, topic, grade, notes=""):
    try:
        data = {"subject": subject, "topic": topic, "grade": grade, "notes": notes}
        supabase.table("grades").insert(data).execute()
    except Exception as e:
        st.error(f"שגיאת סנכרון נתונים: {e}")

def get_all_grades():
    try:
        res = supabase.table("grades").select("*").order("created_at", desc=True).execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame(columns=["id", "subject", "topic", "grade", "created_at"])

def clear_db():
    supabase.table("grades").delete().neq("id", 0).execute()

# --- ניהול זיכרון צ'אט (חדש) ---
def save_chat_message(role, content):
    try:
        supabase.table("chat_history").insert({"role": role, "content": content}).execute()
    except Exception as e:
        print(f"Error saving chat: {e}")

def get_persistent_chat_history(limit=25):
    try:
        res = supabase.table("chat_history").select("*").order("created_at", desc=False).limit(limit).execute()
        return res.data
    except:
        return []

def clear_chat_history():
    supabase.table("chat_history").delete().neq("id", 0).execute()
