import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
from PIL import Image
import io

def init_genai():
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
            text = model.generate_content(["Extract all text accurately.", img]).text
    except Exception as e:
        return f"🚨 שגיאה בסריקה: {e}"
    return text

def get_ai_response_stream(subject, prompt, file_context=""):
    try:
        init_genai()
        # נעילה על 1.5 פלאש למניעת שגיאות מכסה (429)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        system_msg = f"You are Nexus AI, an elite academic assistant. Subject: {subject}. Respond in Hebrew. Use professional formatting."
        full_p = f"{system_msg}\n\n"
        if file_context: full_p += f"Context from files:\n{file_context[:8000]}\n\n"
        full_p += f"User Question: {prompt}"

        response = model.generate_content(full_p, stream=True)
        for chunk in response:
            if chunk.text: yield chunk.text
    except Exception as e:
        if "429" in str(e):
            yield "🚨 חריגה ממכסת הודעות. גוגל מגבילה את המפתח שלך כרגע. נסה שוב בעוד דקה."
        else:
            yield f"🚨 שגיאה: {str(e)}"
