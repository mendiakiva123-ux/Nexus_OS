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

def get_ai_response_stream(subject, prompt, chat_history_list, file_context="", lang="עברית", analyst_mode=False):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # בניית הזיכרון עבור ה-AI (המרה למבנה של גוגל)
        history = []
        for msg in chat_history_list:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})
        
        # הגדרת תפקיד ושפה
        role_type = "מומחה דאטה אנליסט וסטטיסטיקה" if analyst_mode else "מנטור אקדמי בכיר"
        instruct = "ענה בעברית בלבד, ישר הכל לימין (RTL)." if lang == "עברית" else "Respond in English only."
        
        system_msg = f"System: {role_type}. {instruct} נושא: {subject}."
        if file_context:
            system_msg += f"\nהקשר מהקבצים שנסרקו: {file_context[:8000]}"

        # התחלת צ'אט עם הקשר מלא
        chat = model.start_chat(history=history)
        response = chat.send_message(f"{system_msg}\n\nשאלה: {prompt}", stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"🚨 שגיאת תקשורת: {str(e)}"
