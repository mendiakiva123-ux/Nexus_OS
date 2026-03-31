import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
from PIL import Image

def init_genai():
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
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
            response = model.generate_content(["Extract text:", img])
            text = response.text
    except Exception as e:
        return f"🚨 Error: {e}"
    return text

def get_ai_response_stream(subject, prompt, file_context=""):
    try:
        init_genai()
        # שימוש במודל הרשמי - חסין ל-404
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        system_msg = f"You are Nexus AI, an academic assistant. Subject: {subject}. Respond in Hebrew."
        full_p = f"{system_msg}\n\nContext: {file_context[:8000]}\n\nQuestion: {prompt}"

        # הזרמה ישירה מהספרייה הרשמית
        response = model.generate_content(full_p, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"🚨 שגיאת מערכת: {str(e)}. וודא שהמפתח ב-Secrets תקין."
