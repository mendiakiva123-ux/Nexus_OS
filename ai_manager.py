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
    try:
        # שליפת המפתח
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        
        # הגדרה מפורשת של גרסת ה-API ליציבה (v1)
        genai.configure(api_key=api_key)
        
        # שימוש בשם המודל המלא והיציב
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')
        
        # הגדרת אישיות
        role = "Data Analyst & Statistics Expert" if analyst_mode else "Academic Mentor"
        instruct = "ענה בעברית בלבד! אל תשתמש באנגלית." if lang == "עברית" else "Respond in English only."
        
        full_prompt = f"Role: {role}. {instruct} Subject: {subject}.\n"
        if file_context:
            full_prompt += f"Context: {file_context[:8000]}\n"
        full_prompt += f"User: {prompt}"

        # יצירת התשובה בהזרמה
        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        error_str = str(e)
        if "404" in error_str:
            yield "🚨 שגיאת כתובת: גוגל עדיין לא מזהה את המודל בחשבון שלך. וודא שהמפתח תקין."
        else:
            yield f"🚨 שגיאה בחיבור: {error_str}"
