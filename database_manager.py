import streamlit as st
from supabase import create_client, Client
import pandas as pd

# חיבור לסופאבייס דרך ה-Secrets
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def init_db():
    # בסופאבייס אנחנו יוצרים את הטבלה דרך ה-SQL Editor באתר שלהם (הסבר למטה)
    pass

def save_grade(subject, topic, grade, notes=""):
    data = {
        "subject": subject,
        "topic": topic,
        "grade": grade,
        "notes": notes
    }
    supabase.table("grades").insert(data).execute()

def get_all_grades():
    response = supabase.table("grades").select("*").execute()
    return pd.DataFrame(response.data)

def clear_db():
    # פקודה זו תמחק הכל - להשתמש בזהירות
    supabase.table("grades").delete().neq("id", 0).execute()
