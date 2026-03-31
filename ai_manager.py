import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
from PIL import Image

# פונקציית סריקה
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

# מנוע הבוט - גרסת הברזל
def get_ai_response_stream(subject, prompt, file_context=""):
    try:
        # הגדרה מחדש בכל קריאה כדי לוודא שהמפתח תמיד שם
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        full_prompt = f"Subject: {subject}. Respond in Hebrew. Use structure. "
        if file_context:
            full_prompt += f"Context: {file_context[:5000]} "
        full_prompt += f"Question: {prompt}"

        # הזרמה ישירה
        response = model.generate_content(full_prompt, stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        yield f"🚨 שגיאה ישירה מגוגל: {str(e)}"
