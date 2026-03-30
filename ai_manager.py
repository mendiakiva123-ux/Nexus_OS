import streamlit as st
import google.generativeai as genai

def get_ai_response_stream(subject, prompt):
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # מנגנון חסין: רשימת מודלים מהחדש ביותר ליציב ביותר
    models_to_try = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-latest',
        'gemini-pro',
        'models/gemini-1.5-flash'
    ]
    
    context = f"אתה עוזר אקדמי אישי במערכת Nexus OS. המשתמש שואל לגבי המקצוע: {subject}."
    full_prompt = f"{context}\n\nשאלה: {prompt}"
    
    last_error = None
    
    # הבוט מנסה מודל אחרי מודל מאחורי הקלעים עד שזה מצליח
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(full_prompt, stream=True)
            return response # ברגע שהצליח, מחזיר את התשובה ויוצא
        except Exception as e:
            last_error = e
            continue # אם נכשל (כמו 404), מדלג מיד למודל הבא
            
    # אם הכל קרס (לא אמור לקרות)
    raise Exception(f"All models failed. Last error: {last_error}")

def process_file_to_db(file_path, subject):
    pass
