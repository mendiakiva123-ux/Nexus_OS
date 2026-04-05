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
        
        # בחירת מודל דינמית למניעת שגיאות כתובת
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # הגדרת אישיות ה-AI
        role = "Data Analyst Expert & Statistics Professional" if analyst_mode else "Academic Mentor"
        instruct = "ענה בעברית בלבד! ישר את הטקסט לימין." if lang == "עברית" else "Respond in English only."
        
        full_prompt = f"System: {role}. {instruct} Subject: {subject}.\n"
        if file_context:
            full_prompt += f"Context from student files: {file_context[:8000]}\n"
        full_prompt += f"Question: {prompt}"

        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"🚨 שגיאת מערכת: {str(e)}"

def get_ai_response_stream(subject, prompt, chat_history_list, file_context="", lang="עברית", analyst_mode=False):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # בניית הזיכרון עבור גוגל
        history = []
        for msg in chat_history_list:
            history.append({"role": "user" if msg["role"] == "user" else "model", 
                            "parts": [msg["content"]]})
        
        # הנחיות מערכת (System Instructions)
        role_type = "Data Analyst Expert" if analyst_mode else "Academic Mentor"
        sys_instr = f"ענה בעברית מיושרת לימין. תפקיד: {role_type}. נושא: {subject}."
        if file_context: sys_instr += f"\nמידע מהקבצים: {file_context[:5000]}"

        # התחלת צ'אט עם זיכרון
        chat = model.start_chat(history=history)
        response = chat.send_message(f"{sys_instr}\n\nשאלה: {prompt}", stream=True)
        
        for chunk in response:
            if chunk.text: yield chunk.text
    except Exception as e:
        yield f"🚨 שגיאה: {str(e)}"
