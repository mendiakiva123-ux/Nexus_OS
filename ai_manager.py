import streamlit as st
import google.generativeai as genai

def get_ai_response_stream(subject, prompt):
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    context = f"אתה עוזר אקדמי במערכת Nexus OS. הנושא הנוכחי לשיחה הוא: {subject}."
    full_prompt = f"{context}\n\nשאלה: {prompt}"
    
    try:
        # ניסיון ראשון: המודל המהיר והחדש
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content(full_prompt, stream=True)
    except Exception as e:
        if "404" in str(e) or "v1beta" in str(e):
            # רשת ביטחון: מעבר מיידי למודל הקלאסי שתמיד קיים ולא זורק 404
            fallback_model = genai.GenerativeModel('gemini-pro')
            return fallback_model.generate_content(full_prompt, stream=True)
        else:
            raise e # שגיאה אחרת (למשל מפתח לא נכון)

def process_file_to_db(file_path, subject):
    pass
