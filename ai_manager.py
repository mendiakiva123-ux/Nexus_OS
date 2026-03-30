import streamlit as st
import google.generativeai as genai

def get_ai_response_stream(subject, prompt):
    # משיכת המפתח מה-Secrets (הגדרנו ב-Streamlit)
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # שימוש במודל היציב ביותר - גרסה 1.5 פלאש
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    context = f"אתה עוזר אקדמי במערכת Nexus OS. המשתמש שואל לגבי: {subject}."
    full_prompt = f"{context}\n\nהודעת משתמש: {prompt}"
    
    # יצירת תשובה בסטרימינג למהירות מקסימלית
    response = model.generate_content(full_prompt, stream=True)
    return response

def process_file_to_db(file_path, subject):
    pass
