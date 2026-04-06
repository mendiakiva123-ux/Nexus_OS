import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
import datetime
from zoneinfo import ZoneInfo

def extract_text_from_file(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages: text += page.extract_text() + "\n"
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs: text += para.text + "\n"
        else:
            text = uploaded_file.getvalue().decode("utf-8") # תמיכה בקבצי טקסט רגילים/CSV
    except: pass
    return text

def get_ai_response_stream(subject, prompt, chat_history_list, file_context="", lang="עברית", analyst_mode=False, is_quiz=False):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        genai.configure(api_key=api_key)
        
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in available_models if "flash" in m), available_models[0])
        model = genai.GenerativeModel(model_name)
        
        history = []
        if not is_quiz: # בחנים לא צריכים זיכרון של שיחות קודמות
            for msg in chat_history_list:
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})
            
        israel_time = datetime.datetime.now(ZoneInfo("Asia/Jerusalem"))
        current_time_str = israel_time.strftime("%A, %d/%m/%Y, %H:%M")
        
        role_type = "Data Analyst Expert" if analyst_mode else "Academic Mentor"
        instruct = "ענה בעברית בלבד! ישר את הטקסט לימין (RTL). התייחס למשתמש בלשון זכר." if lang == "עברית" else "Respond in English only."
        
        system_msg = (
            f"System Role: {role_type}. {instruct}\n"
            f"זמן נוכחי (קריטי): {current_time_str}\n"
            f"פרופיל אקדמי של המשתמש: מנדי הוא חייל לקראת שחרור וסטודנט מצטיין בקורס דאטה אנליסט במכללת עתיד בבאר שבע. "
            f"הוא עובד עם Python, SQL, ו-Power BI, ומתוכנן להמשיך למכינה ותואר במדעי המחשב. "
            f"דרוש ממך להיות חד, מקצועי, ולתת דוגמאות טכניות מדויקות שמתאימות לרמה ולכלים שהוא לומד.\n"
            f"Subject Context: {subject}.\n"
        )
        
        if is_quiz:
            system_msg += "פעולה נדרשת: צור מבחן פתע מקיף ואמריקאי המבוסס אך ורק על חומר הלימוד המסופק. עליך לספק 5 שאלות, ולבסוף את התשובות הנכונות מוסתרות.\n"
            
        if file_context:
            system_msg += f"Context from files: {file_context[:8000]}\n"

        chat = model.start_chat(history=history)
        response = chat.send_message(f"{system_msg}\n\nUser: {prompt}", stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        yield f"🚨 שגיאת בינה מלאכותית: {str(e)}"
