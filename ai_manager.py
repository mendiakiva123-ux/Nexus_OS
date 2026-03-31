import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
from PIL import Image
import io

# --- פונקציה לסריקת קבצים ותמונות ---
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
            api_key = st.secrets["GOOGLE_API_KEY"]
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            img = Image.open(uploaded_file)
            response = model.generate_content(["Extract all text from this image.", img])
            text = response.text
    except Exception as e:
        return f"🚨 שגיאה בסריקה: {e}"
    return text

# --- מנוע הבוט הרשמי והסופי ---
def get_ai_response_stream(subject, prompt, file_context=""):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        # שימוש בשם המודל הכי סטנדרטי שיש
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        system_instruction = (
            f"You are Nexus AI, an elite academic assistant. Subject: {subject}. "
            "Respond in Hebrew. Use headers and bullet points for clarity."
        )
        
        full_prompt = f"{system_instruction}\n\n"
        if file_context:
            full_prompt += f"CONTEXT FROM FILES:\n{file_context[:10000]}\n\n"
        full_prompt += f"USER QUESTION: {prompt}"

        # הזרמת תשובה (Streaming)
        response = model.generate_content(full_prompt, stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            yield "🚨 חריגה ממכסת הודעות. המתן דקה ונסה שוב."
        elif "404" in error_msg:
            yield "🚨 שגיאת מודל (404). וודא שביצעת Reboot לאפליקציה ב-Streamlit Cloud."
        else:
            yield f"🚨 שגיאת תקשורת: {error_msg}"
