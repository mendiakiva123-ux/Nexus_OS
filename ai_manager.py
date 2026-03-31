import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
from PIL import Image
import io

# --- פונקציה למציאת המודל הטוב ביותר הזמין ---
def get_best_model():
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        # שואלים את גוגל אילו מודלים זמינים למפתח הזה
        models = genai.list_models()
        available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        
        # סדר עדיפויות: מחפשים 1.5 פלאש, אם אין אז 1.0 פלאש, אם אין אז כל מה שיש לו פלאש בשם
        for m_name in available_models:
            if 'gemini-1.5-flash' in m_name:
                return m_name
        for m_name in available_models:
            if 'gemini-1.0-flash' in m_name:
                return m_name
        for m_name in available_models:
            if 'flash' in m_name:
                return m_name
                
        return 'models/gemini-1.5-flash' # ברירת מחדל אחרונה
    except Exception:
        return 'models/gemini-1.5-flash'

# --- פונקציית סריקה (PDF, Word, תמונות) ---
def extract_text_from_file(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            model_name = get_best_model()
            model = genai.GenerativeModel(model_name)
            img = Image.open(uploaded_file)
            response = model.generate_content(["Extract all text from this image accurately.", img])
            text = response.text
    except Exception as e:
        return f"🚨 שגיאה בסריקה: {e}"
    return text

# --- מנוע הבוט הסופי והחסין ---
def get_ai_response_stream(subject, prompt, file_context=""):
    try:
        model_name = get_best_model()
        
        # יצירת המודל - בינתיים ללא Tools כדי להבטיח חיבור 100%
        model = genai.GenerativeModel(model_name)
        
        system_instruction = (
            f"You are Nexus AI, an elite academic assistant. Subject: {subject}. "
            "Use clear structure, headers, and bullet points. Always respond in Hebrew."
        )
        
        full_prompt = f"{system_instruction}\n\n"
        if file_context:
            full_prompt += f"CONTEXT FROM USER FILES:\n{file_context[:10000]}\n\n"
        full_prompt += f"USER QUESTION: {prompt}"

        # הזרמת תשובה
        response = model.generate_content(full_prompt, stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        yield f"🚨 שגיאת מערכת סופית: {str(e)}"
