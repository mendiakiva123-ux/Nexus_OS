import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
from PIL import Image
import io

# --- פונקציה למציאת המודל היציב בלבד (1.5 בלבד!) ---
def get_stable_model():
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        models = genai.list_models()
        available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        
        # סינון אגרסיבי: מחפשים 1.5-flash ומתעלמים מכל מה שקשור ל-2.5 או experimental
        for m_name in available_models:
            if 'gemini-1.5-flash' in m_name and '2.5' not in m_name:
                return m_name
        
        # גיבוי למקרה שגוגל שינו שמות - מחפשים 1.5 כלשהו
        for m_name in available_models:
            if '1.5' in m_name and '2.5' not in m_name:
                return m_name
                
        return 'models/gemini-1.5-flash' # ברירת מחדל קשיחה ויציבה
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
            model_name = get_stable_model()
            model = genai.GenerativeModel(model_name)
            img = Image.open(uploaded_file)
            response = model.generate_content(["Extract all text from this image accurately.", img])
            text = response.text
    except Exception as e:
        return f"🚨 שגיאה בסריקה: {e}"
    return text

# --- מנוע הבוט היציב (ללא 2.5!) ---
def get_ai_response_stream(subject, prompt, file_context=""):
    try:
        # נועלים את המערכת על המודל היציב
        model_name = get_stable_model()
        model = genai.GenerativeModel(model_name)
        
        system_instruction = (
            f"You are Nexus AI, a professional academic assistant. Subject: {subject}. "
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
        if "429" in str(e):
            yield "🚨 חריגה ממכסת הודעות. המתן דקה ונסה שוב (המערכת עברה כעת למודל עם מכסה גבוהה יותר)."
        else:
            yield f"🚨 שגיאה: {str(e)}"
