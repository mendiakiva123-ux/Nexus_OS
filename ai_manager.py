import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
from PIL import Image

def init_genai():
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    genai.configure(api_key=api_key)

def get_working_model():
    """מוצא את השם המדויק שה-API של המשתמש דורש כרגע"""
    init_genai()
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini-1.5-flash' in m.name:
                    return m.name
        return 'gemini-1.5-flash' # Fallback
    except:
        return 'gemini-1.5-flash'

def extract_text_from_file(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages: text += page.extract_text() + "\n"
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs: text += para.text + "\n"
        elif uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            init_genai()
            model = genai.GenerativeModel(get_working_model())
            img = Image.open(uploaded_file)
            response = model.generate_content(["Extract all text accurately.", img])
            text = response.text
    except Exception as e:
        return f"🚨 Error: {e}"
    return text

def get_ai_response_stream(subject, prompt, file_context=""):
    try:
        init_genai()
        # מזהה את שם המודל המדויק שגוגל רוצה לקבל
        model_name = get_working_model()
        model = genai.GenerativeModel(model_name)
        
        system_instruction = f"You are Nexus AI, a top-tier academic assistant. Subject: {subject}. Respond in Hebrew."
        full_prompt = f"{system_instruction}\n\nContext: {file_context[:8000]}\n\nQuestion: {prompt}"

        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"🚨 שגיאת מערכת: {str(e)}. נסה לרפרש או לבדוק את המפתח ב-Secrets."
