import streamlit as st
import google.generativeai as genai

def get_ai_response_stream(subject, prompt):
    # משיכת המפתח מהסודות
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # שימוש במודל העדכני ביותר
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    context = f"אתה עוזר אקדמי אישי במערכת Nexus OS. הנושא הנוכחי: {subject}."
    full_prompt = f"{context}\n\nUser Question: {prompt}"
    
    # יצירת תשובה בסטרימינג (Streaming)
    response = model.generate_content(full_prompt, stream=True)
    return response

def process_file_to_db(file_path, subject):
    # לוגיקה עתידית לניתוח קבצים
    pass
