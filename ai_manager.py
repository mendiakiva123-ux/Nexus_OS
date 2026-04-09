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
            text = uploaded_file.getvalue().decode("utf-8") 
    except Exception as e:
        print(f"Error reading file: {e}")
    return text

def get_ai_response_stream(subject, prompt, chat_history_list, file_context="", lang="עברית", analyst_mode=False, is_quiz=False):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        genai.configure(api_key=api_key)
        
        # --- התיקון הסופי והמוחלט ---
        # במקום לתת לקוד לבחור אוטומטית את המודל הכי חדש (שקורס עם הספרייה),
        # אנחנו מקבעים אותו ספציפית למודל 1.5-flash. המודל הזה תומך במילה google_search_retrieval ועובד מושלם.
        model_name = "models/gemini-1.5-flash"
        
        # 🌐 חיבור חכם לאינטרנט בלייב
        model = genai.GenerativeModel(
            model_name=model_name,
            tools='google_search_retrieval'
        )
        
        history = []
        if not is_quiz:
            for msg in chat_history_list:
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})
            
        israel_time = datetime.datetime.now(ZoneInfo("Asia/Jerusalem"))
        current_time_str = israel_time.strftime("%A, %d/%m/%Y, %H:%M")
        
        # --- בניית מוח ה-AI (המערכת) ---
        role_type = "Senior Data Analyst & Tech Lead" if analyst_mode else "Expert Academic Mentor & Tutor"
        instruct = "ענה בעברית טבעית, זורמת ומקצועית. יישר את הקוד לשמאל ואת הטקסט לימין. התייחס למשתמש בלשון זכר." if lang == "עברית" else "Respond in highly professional English."
        
        system_msg = (
            f"System Role: {role_type}. {instruct}\n"
            f"IMPORTANT: The current year is 2026. The current time is {current_time_str}.\n"
            f"You are connected to Google Search. If the user asks about current events, news, recent tech updates, or real-time data, USE THE SEARCH TOOL to fetch accurate, up-to-date information.\n\n"
            f"--- USER PROFILE ---\n"
            f"Name: Mendi.\n"
            f"Background: IDF soldier nearing the end of his service. Enrolled in a rigorous Data Analyst program.\n"
            f"Future Plans: Attending a pre-mechina and Mechina leading into a Computer Science degree.\n"
            f"Tech Stack: Python (Pandas, FastAPI), SQL (ERD, joins), Power BI, Advanced Excel.\n\n"
        )

        if analyst_mode:
            system_msg += (
                f"--- DATA ANALYST MODE RULES ---\n"
                f"1. Code Quality: Provide clean, PEP8-compliant Python code.\n"
                f"2. SQL: Focus on efficiency, correct JOINs, and explain the query logic.\n"
                f"3. Power BI/DAX: Provide accurate DAX measures and explain data modeling clearly.\n"
            )
        else:
            system_msg += (
                f"--- ACADEMIC MENTOR MODE RULES ---\n"
                f"Subject Focus: {subject}.\n"
                f"1. STEM: Break down formulas, explain the core logic, and use the Socratic method.\n"
                f"2. Tone: Encouraging, academic, structured.\n"
            )
            
        if is_quiz:
            system_msg = (
                f"System Role: Strict Academic Examiner. Subject: {subject}.\n"
                f"Action: Generate a 5-question multiple-choice quiz based on the context. Do not reveal answers immediately. Add 'Correct Answers' at the bottom.\n"
            )
            
        if file_context:
            system_msg += f"\n--- KNOWLEDGE BASE (FILE CONTEXT) ---\n{file_context[:50000]}\n"

        chat = model.start_chat(history=history)
        response = chat.send_message(f"{system_msg}\n\nUser: {prompt}", stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        yield f"🚨 תקלת בינה מלאכותית: {str(e)}\nאם השגיאה קשורה ל-Tools, ייתכן שגרסת ה-API שלך דורשת עדכון (pip install -U google-generativeai)."
