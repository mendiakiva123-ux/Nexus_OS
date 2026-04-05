import streamlit as st
from supabase import create_client, Client
import pandas as pd

# חיבור מאובטח
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def save_grade(subject, topic, grade, notes=""):
    data = {"subject": subject, "topic": topic, "grade": grade, "notes": notes}
    try:
        supabase.table("grades").insert(data).execute()
    except Exception as e:
        st.error(f"שגיאת סנכרון: {e}")

def get_all_grades():
    try:
        res = supabase.table("grades").select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame(columns=["id", "subject", "topic", "grade", "date", "notes"])

def clear_db():
    supabase.table("grades").delete().neq("id", 0).execute()
