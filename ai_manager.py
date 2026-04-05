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
        
        # --- פתרון השורש: בחירת מודל דינמית ---
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # עדיפות ל-Flash 1.5, אם לא - לוקח את הראשון שזמין
        model_name = 'models/gemini-1.5-flash'
        if model_name not in available_models:
            model_name = next((m for m in available_models if "flash" in m), available_models[0])
        
        model = genai.GenerativeModel(model_name)
        
        # הגדרת אישיות
        role = "Senior Data Analyst Expert" if analyst_mode else "Academic Mentor"
        instruct = "ענה בעברית בלבד!" if lang == "עברית" else "Respond in English only!"
        
        full_prompt = f"System: {role}. {instruct} Subject: {subject}.\n"
        if file_context:
            full_prompt += f"Context: {file_context[:8000]}\n"
        full_prompt += f"User: {prompt}"

        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        yield f"🚨 שגיאת בינה מלאכותית: {str(e)}"
