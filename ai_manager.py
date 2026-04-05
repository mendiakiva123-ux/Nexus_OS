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
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        genai.configure(api_key=api_key)
        
        # פתרון השורש: שימוש במזהה המעודכן ביותר למניעת 404
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        role = "Senior Data Analyst" if analyst_mode else "Academic Mentor"
        instruct = "ענה בעברית בלבד! אל תשתמש באנגלית." if lang == "עברית" else "Respond in English only."
        
        full_prompt = f"Role: {role}. {instruct} Subject: {subject}.\n"
        if file_context:
            full_prompt += f"Context: {file_context[:10000]}\n"
        full_prompt += f"User: {prompt}"

        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        error_str = str(e)
        if "404" in error_str:
            yield "🚨 שגיאת זיהוי מודל: המערכת מנסה להתחבר למודל חלופי. בצע Refresh לאתר."
        else:
            yield f"🚨 שגיאה בחיבור: {error_str}"
