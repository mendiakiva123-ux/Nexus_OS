import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
import os


def get_api_key():
    if "GOOGLE_API_KEY" in st.secrets:
        return st.secrets["GOOGLE_API_KEY"]
    return os.getenv("GOOGLE_API_KEY")


def get_ai_response_stream(subject, prompt):
    # שימוש במודל המעודכן ביותר למניעת שגיאות 404
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=get_api_key(),
        temperature=0.7
    )

    context = f"אתה עוזר אקדמי במערכת Nexus OS. המשתמש שואל לגבי המקצוע: {subject}."
    full_prompt = f"{context}\n\nUser: {prompt}"

    # החזרת תשובה בסטרימינג
    return llm.stream(full_prompt)


def process_file_to_db(file_path, subject):
    # כאן תבוא הלוגיקה של העלאת קבצים בעתיד
    pass
