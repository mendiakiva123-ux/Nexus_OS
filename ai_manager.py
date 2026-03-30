import streamlit as st
import google.generativeai as genai

def get_ai_response_stream(subject, prompt):
    # משיכת המפתח מהסודות
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # הסוד לפתרון ה-404: מעבר למודל 'gemini-pro' שתמיד זמין וחסין תקלות
    model = genai.GenerativeModel('gemini-pro')
    
    context = f"אתה עוזר אקדמי במערכת Nexus OS. נושא השיחה הנוכחי: {subject}."
    full_prompt = f"{context}\n\nשאלה: {prompt}"
    
    # החזרת התשובה בסטרימינג ישירות מהמודל היציב
    response = model.generate_content(full_prompt, stream=True)
    return response

def process_file_to_db(file_path, subject):
    pass
