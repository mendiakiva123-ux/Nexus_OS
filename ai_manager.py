import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
from PIL import Image

def init_genai():
    # הגדרת ה-API בצורה הפשוטה והיציבה ביותר
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)

def extract_text_from_file(uploaded_file):
    text = ""
    try:
        init_genai()
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages: text += page.extract_text() + "\n"
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs: text += para.text + "\n"
        elif uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            model = genai.GenerativeModel('gemini-1.5-flash')
            img = Image.open(uploaded_file)
            text = model.generate_content(["Extract text:", img]).text
    except Exception as e:
        return f"🚨 שגיאה בסריקה: {e}"
    return text

def get_ai_response_stream(subject, prompt, file_context=""):
    try:
        init_genai()
        
        # שימוש בשם המודל בלבד ללא הקידומת models/ - זה פותר את ה-404 ברוב המקרים
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        full_p = f"Subject: {subject}. Respond in Hebrew. Question: {prompt}"
        if file_context: 
            full_p += f"\nContext from files: {file_context[:8000]}"

        # הזרמה ישירה
        response = model.generate_content(full_p, stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            yield "🚨 שגיאת מודל (404). המערכת מנסה לאתחל גרסה חלופית..."
            # ניסיון אחרון עם שם חלופי במקרה של 404
            try:
                alt_model = genai.GenerativeModel('gemini-1.5-flash-latest')
                alt_res = alt_model.generate_content(full_p, stream=True)
                for c in alt_res: yield c.text
            except:
                yield "🚨 גוגל לא מזהה את המודל בחשבון שלך. בדוק שוב את ה-API KEY."
        else:
            yield f"🚨 תקלה: {error_msg}"
