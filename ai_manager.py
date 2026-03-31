import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
from PIL import Image
import io

# --- הגדרת המפתח והמודל ---
def init_genai():
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)

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
            init_genai()
            model = genai.GenerativeModel('gemini-1.5-flash')
            img = Image.open(uploaded_file)
            response = model.generate_content(["Extract all text from this image accurately.", img])
            text = response.text
    except Exception as e:
        return f"🚨 שגיאה בסריקה: {e}"
    return text

# --- מנוע הבוט הרשמי (מהיר, חסין ויציב) ---
def get_ai_response_stream(subject, prompt, file_context=""):
    try:
        init_genai()
        
        # הגדרת הכלים (חיפוש בגוגל) והמודל
        # הערה: חיפוש בגוגל זמין כרגע רק בחלק מהאזורים, אם זה עושה שגיאה - נבטל אותו.
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            tools=[{"google_search_retrieval": {}}]
        )
        
        system_instruction = (
            f"You are Nexus AI, an elite academic assistant. Subject: {subject}. "
            "Use headers, bullet points, and bold text. Respond in Hebrew."
        )
        
        full_prompt = f"{system_instruction}\n\n"
        if file_context:
            full_prompt += f"CONTEXT FROM USER FILES:\n{file_context[:10000]}\n\n"
        full_prompt += f"USER QUESTION: {prompt}"

        # הזרמת תשובה בזמן אמת
        response = model.generate_content(full_prompt, stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        # אם יש שגיאה עם החיפוש, מנסים שוב בלי הכלים (בלי אינטרנט)
        try:
            model_basic = genai.GenerativeModel('gemini-1.5-flash')
            response = model_basic.generate_content(full_prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e2:
            yield f"🚨 שגיאת תקשורת סופית: {str(e2)}"
