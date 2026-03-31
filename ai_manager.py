import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
from PIL import Image

def init_genai():
    # הגדרה ישירה לגרסה v1 היציבה
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)

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
            model = genai.GenerativeModel('gemini-1.5-flash')
            img = Image.open(uploaded_file)
            text = model.generate_content(["Extract text accurately.", img]).text
    except Exception as e:
        return f"🚨 שגיאה בסריקה: {e}"
    return text

def get_ai_response_stream(subject, prompt, file_context=""):
    try:
        init_genai()
        # שימוש בשם נקי ללא קידומות - הספריה תטפל בגרסה הנכונה
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        system_msg = f"You are Nexus AI, an elite academic assistant. Subject: {subject}. Respond in Hebrew."
        full_p = f"{system_msg}\n\n"
        if file_context: full_p += f"Context: {file_context[:8000]}\n\n"
        full_p += f"Question: {prompt}"

        response = model.generate_content(full_p, stream=True)
        for chunk in response:
            if chunk.text: yield chunk.text
    except Exception as e:
        yield f"🚨 תקלה טכנית: {str(e)}"
