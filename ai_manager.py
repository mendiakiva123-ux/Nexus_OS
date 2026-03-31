import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
from PIL import Image

def get_best_available_model():
    """מוצא את המודל הכי יציב שזמין למפתח שלך כרגע"""
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        models = genai.list_models()
        available = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        
        # סדר עדיפויות חכם למנוע 404
        priorities = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-pro']
        for p in priorities:
            for a in available:
                if p in a: return a
        return available[0] if available else "gemini-1.5-flash"
    except:
        return "gemini-1.5-flash"

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
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            model = genai.GenerativeModel(get_best_available_model())
            img = Image.open(uploaded_file)
            text = model.generate_content(["Extract text:", img]).text
    except Exception as e:
        return f"🚨 שגיאה בסריקה: {e}"
    return text

def get_ai_response_stream(subject, prompt, file_context=""):
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model_name = get_best_available_model()
        model = genai.GenerativeModel(model_name)
        
        full_p = f"Subject: {subject}. Respond in Hebrew. Use structure. "
        if file_context: full_p += f"Context: {file_context[:8000]} "
        full_p += f"Question: {prompt}"

        response = model.generate_content(full_p, stream=True)
        for chunk in response:
            if chunk.text: yield chunk.text
    except Exception as e:
        yield f"🚨 תקלה טכנית: {str(e)}"
