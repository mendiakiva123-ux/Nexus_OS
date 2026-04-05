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
    # הגדרת המפתח מה-Secrets
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    genai.configure(api_key=api_key)
    
    # בחירת המודל הכי חזק ומהיר
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # בניית ההנחיות לבוט
    role = "Data Analyst Expert" if analyst_mode else "Academic Mentor"
    instruction = "ענה בעברית בלבד!" if lang == "עברית" else "Respond in English only!"
    
    full_prompt = f"System: {role}. {instruction} Subject: {subject}.\n"
    if file_context:
        full_prompt += f"Study Material: {file_context[:10000]}\n"
    full_prompt += f"User Question: {prompt}"

    try:
        # הזרמת התשובה (Streaming)
        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"🚨 שגיאה בחיבור לגוגל: {str(e)}"
