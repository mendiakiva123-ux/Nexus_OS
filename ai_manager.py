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
        # שליפת המפתח מה-Secrets
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        genai.configure(api_key=api_key)
        
        # שימוש במודל בגרסה הכי יציבה (בלי v1beta ידני)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # בניית הנחיות המערכת
        role = "Data Analyst Expert" if analyst_mode else "Academic Mentor"
        instruct = "ענה בעברית בלבד! אל תשתמש באנגלית." if lang == "עברית" else "Respond in English only."
        
        full_prompt = f"Role: {role}. Instruction: {instruct}. Subject: {subject}.\n"
        if file_context:
            full_prompt += f"Context from files: {file_context[:8000]}\n"
        full_prompt += f"Question: {prompt}"

        # הזרמת תשובה חסינה
        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg:
            yield "🚨 המפתח של גוגל לא תקין. בדוק את ה-Secrets."
        else:
            yield f"🚨 שגיאת מערכת: {error_msg}"
