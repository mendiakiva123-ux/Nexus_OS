import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
from PIL import Image

# פונקציה לסריקת קבצים ותמונות
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
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash')
            img = Image.open(uploaded_file)
            response = model.generate_content(["Extract all text from this image.", img])
            text = response.text
    except Exception as e:
        return f"🚨 שגיאה בסריקה: {e}"
    return text

# מנוע הבוט הרשמי
def get_ai_response_stream(subject, prompt, file_context=""):
    try:
        # הגדרה ישירה מה-Secrets
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        # שימוש בשם המודל הרשמי והיציב
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        system_msg = f"You are Nexus AI, a helpful academic assistant. Subject: {subject}. Respond in Hebrew."
        full_prompt = f"{system_msg}\n\n"
        if file_context:
            full_prompt += f"Context from files: {file_context[:5000]}\n\n"
        full_prompt += f"Question: {prompt}"

        # הזרמה
        response = model.generate_content(full_prompt, stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        yield f"🚨 שגיאת API ישירה: {str(e)}"
