import streamlit as st
from supabase import create_client, Client
import pandas as pd

url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- ניהול משתמשים (חדש!) ---
def authenticate_user(code):
    try:
        res = supabase.table("users").select("*").eq("passcode", code).execute()
        return res.data[0] if res.data else None
    except: return None

def update_user_name(user_id, name):
    try:
        supabase.table("users").update({"user_name": name}).eq("user_id", user_id).execute()
    except: pass

# --- ניהול ציונים (מסונן לפי משתמש) ---
def save_grade(user_id, subject, topic, grade, credits=1.0, notes=""):
    try:
        data = {"user_id": user_id, "subject": subject, "topic": topic, "grade": grade, "credits": credits, "notes": notes}
        supabase.table("grades").insert(data).execute()
    except: pass

def get_all_grades(user_id):
    try:
        res = supabase.table("grades").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame(columns=["id", "subject", "topic", "grade", "credits", "created_at"])

def clear_db(user_id):
    try:
        supabase.table("grades").delete().eq("user_id", user_id).execute()
    except: pass

# --- ניהול זיכרון צ'אט (מסונן לפי משתמש) ---
def save_chat_message(user_id, role, content):
    try:
        supabase.table("chat_history").insert({"user_id": user_id, "role": role, "content": content}).execute()
    except: pass

def get_persistent_chat_history(user_id, limit=25):
    try:
        res = supabase.table("chat_history").select("*").eq("user_id", user_id).order("created_at", desc=False).limit(limit).execute()
        return res.data
    except: return []

def clear_chat_history(user_id):
    try:
        supabase.table("chat_history").delete().eq("user_id", user_id).execute()
    except: pass

# --- ניהול משימות (מסונן לפי משתמש) ---
def save_task(user_id, title, subject, due_date):
    try:
        data = {"user_id": user_id, "title": title, "subject": subject, "due_date": str(due_date)}
        supabase.table("tasks").insert(data).execute()
    except: pass

def get_all_tasks(user_id):
    try:
        res = supabase.table("tasks").select("*").eq("user_id", user_id).order("due_date", desc=False).execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame(columns=["id", "title", "subject", "due_date", "status"])

def delete_task(task_id):
    try:
        supabase.table("tasks").delete().eq("id", task_id).execute()
    except: pass
