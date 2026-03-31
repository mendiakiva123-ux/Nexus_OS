import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
from PIL import Image
import io

# --- פונקציית עזר להגדרת המודל (נעילה על 1.5 פלאש) ---
def setup_model():
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    # אנחנו נועלים על 1.5-flash כי הוא הכי יציב עם מכסה גדולה
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model

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
            model = setup_model()
            img = Image.open(uploaded_file)
            response = model.generate_content(["Extract all text from this image accurately.", img])
            text = response.text
    except Exception as e:
        return f"🚨 שגיאה בסריקה: {e}"
    return text

# --- מנוע הבוט (מיועד לסטרימינג יציב) ---
def get_ai_response_stream(subject, prompt, file_context=""):
    try:
        model = setup_model()
        
        system_instruction = (
            f"You are Nexus AI, a professional academic assistant. Subject: {subject}. "
            "Respond in Hebrew. Use clear structure with headers and bullet points."
        )
        
        full_prompt = f"{system_instruction}\n\n"
        if file_context:
            full_prompt += f"CONTEXT FROM USER FILES:\n{file_context[:10000]}\n\n"
        full_prompt += f"USER QUESTION: {prompt}"

        # הפעלת הזרמה (Streaming)
        response = model.generate_content(full_prompt, stream=True)
        
        has_content = False
        for chunk in response:
            try:
                if chunk.text:
                    has_content = True
                    yield chunk.text
            except Exception:
                # לפעמים צ'אנק ספציפי נחסם, אנחנו פשוט ממשיכים לבא בתור
                continue
        
        if not has_content:
            yield "⚠️ גוגל החזירה תשובה ריקה. נסה לשאול שוב או לנסח אחרת."

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            yield "🚨 חרגת מהמכסה היומית (Quota). המתן דקה ונסה שוב."
        elif "API_KEY_INVALID" in error_msg:
            yield "🚨 מפתח ה-API שלך לא תקין. בדוק את ה-Secrets."
        else:
            yield f"🚨 שגיאת מערכת: {error_msg}"
