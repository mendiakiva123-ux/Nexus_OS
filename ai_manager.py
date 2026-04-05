import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx

def extract_text_from_file(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages: text += page.extract_text() + "\n"
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs: text += para.text + "\n"
    except: pass
    return text

def get_ai_response_stream(subject, prompt, file_context="", lang="עברית", analyst_mode=False):
    # הגדרת המפתח והגדרת המודל בנתיב v1 היציב
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    genai.configure(api_key=api_key)
    
    # שימוש במודל היציב ביותר למניעת שגיאות 404
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # הגדרת הנחיות המערכת
    role = "מומחה דאטה אנליסט" if analyst_mode else "מנטור אקדמי"
    instruct = "ענה בעברית בלבד!" if lang == "עברית" else "Respond in English only!"
    
    system_message = f"Role: {role}. Instruction: {instruct}. Subject: {subject}."
    if file_context:
        system_message += f"\nContext: {file_context[:10000]}"

    try:
        # יצירת התשובה
        response = model.generate_content(f"{system_message}\n\nUser: {prompt}", stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        # טיפול בשגיאות בצורה ברורה
        error_msg = str(e)
        if "404" in error_msg:
            yield "🚨 שגיאת כתובת (404): המודל לא נמצא. וודא שאתה משתמש בגרסת הספרייה העדכנית ביותר."
        else:
            yield f"🚨 שגיאה בחיבור: {error_msg}"
