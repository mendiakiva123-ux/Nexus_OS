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
        
        # פתרון ה-404: מציאת המודל הזמין באופן דינמי
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # מחפש מודל מסוג Flash. אם לא מוצא, לוקח את הראשון שזמין (מונע 404 לחלוטין).
        model_name = next((m for m in available_models if "flash" in m), available_models[0])
        model = genai.GenerativeModel(model_name)
        
        # בניית הזיכרון
        history = []
        for msg in chat_history_list:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})
        
        # הגדרת אישיות
        role_type = "Data Analyst Expert" if analyst_mode else "Academic Mentor"
        instruct = "ענה בעברית בלבד! ישר את הטקסט לימין (RTL)." if lang == "עברית" else "Respond in English only."
        
        system_msg = f"System: {role_type}. {instruct} Subject: {subject}.\n"
        if file_context:
            system_msg += f"Context: {file_context[:8000]}"

        # התחלת שיחה עם זיכרון והקשר
        chat = model.start_chat(history=history)
        response = chat.send_message(f"{system_msg}\n\nUser: {prompt}", stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        yield f"🚨 שגיאת בינה מלאכותית: {str(e)}"
