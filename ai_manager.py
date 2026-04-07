import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
import datetime
import time
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
        
        # בחירת המודל הכי מהיר וחכם הזמין
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in available_models if "flash" in m), available_models[0])
        
        # מודל יציב ונקי - ללא כלי חיפוש (כדי למנוע את קריסת החבילה הישנה)
        model = genai.GenerativeModel(model_name=model_name)
        
        history = []
        if not is_quiz: # בחנים לא צריכים זיכרון של שיחות קודמות
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
            f"--- USER PROFILE (CRITICAL CONTEXT) ---\n"
            f"Name: Mendi.\n"
            f"Background: IDF soldier nearing the end of his service. Enrolled in a rigorous Data Analyst program (Atid College/Metro-Tech Blue Line).\n"
            f"Future Plans: Attending a pre-mechina and Mechina (Math, Physics, English) leading into a Computer Science degree.\n"
            f"Tech Stack & Experience: Python (Pandas, FastAPI), SQL (ERD, complex joins), Power BI, Advanced Excel. Completed projects analyzing Flight Delays and Earthquake/Tsunami data (Ring of Fire).\n\n"
        )

        if analyst_mode:
            system_msg += (
                f"--- DATA ANALYST MODE RULES ---\n"
                f"1. Code Quality: Provide clean, highly optimized, PEP8-compliant Python code. Use best practices for data manipulation.\n"
                f"2. SQL: When writing SQL, focus on efficiency, correct JOINs, and explain the query logic.\n"
                f"3. Power BI/DAX: Provide accurate DAX measures and explain data modeling (Star Schema) clearly.\n"
                f"4. Analogies: Feel free to use examples from flight data or seismic activity to explain complex concepts.\n"
                f"5. Professionalism: Treat him as a junior data analyst gearing up for the tech industry. Give him tips for his LinkedIn and job hunt when relevant.\n"
            )
        else:
            system_msg += (
                f"--- ACADEMIC MENTOR MODE RULES ---\n"
                f"Subject Focus: {subject}.\n"
                f"1. STEM (Math/Physics/CS): Do NOT just give the final answer. Break down formulas, explain the core logic, and use the Socratic method to help him understand the 'Why'.\n"
                f"2. English/General: Help him master academic writing, professional vocabulary, and everyday conversational English/slang if he asks.\n"
                f"3. Tone: Encouraging, academic, highly structured. Use bullet points and bold text for readability.\n"
            )
            
        if is_quiz:
            system_msg = (
                f"System Role: Strict Academic Examiner. Subject: {subject}.\n"
                f"Action Required: Generate a comprehensive, challenging 5-question multiple-choice quiz based STRICTLY on the provided file context or subject matter.\n"
                f"Format: Present the 5 questions clearly. DO NOT reveal the answers immediately. At the very bottom, add a section called 'תשובות נכונות' (Correct Answers) with brief explanations.\n"
            )
            
        if file_context:
            system_msg += f"\n--- KNOWLEDGE BASE (FILE CONTEXT) ---\n{file_context[:50000]}\n"

        # --- מנגנון ניסיונות חוזרים חכם (Auto-Retry) כנגד קריסות שרת ---
        max_retries = 3
        yielded_any = False
        
        for attempt in range(max_retries):
            try:
                chat = model.start_chat(history=history)
                response = chat.send_message(f"{system_msg}\n\nUser: {prompt}", stream=True)
                
                for chunk in response:
                    if chunk.text:
                        yielded_any = True
                        yield chunk.text
                
                break # יציאה מהלולאה אם התשובה הושלמה בהצלחה
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # אם השרת עמוס ועוד לא התחלנו להדפיס למסך, נמתין וננסה שוב בשקט
                if not yielded_any and ("503" in error_msg or "quota" in error_msg or "overloaded" in error_msg):
                    if attempt < max_retries - 1:
                        time.sleep(2) # המתנה של 2 שניות
                        continue
                
                # אם כל הניסיונות נכשלו או שהייתה קריסה באמצע משפט
                if "503" in error_msg or "quota" in error_msg or "overloaded" in error_msg:
                    yield "\n\n*(הערת מערכת: שרתי ה-AI של גוגל עמוסים כרגע. המערכת ניסתה להתגבר על כך מאחורי הקלעים אך העומס נמשך. אנא המתן מספר שניות ונסה שוב).* 🔄"
                else:
                    yield f"\n\n🚨 שגיאה טכנית: {str(e)}"
                break
                
    except Exception as e:
        yield f"🚨 תקלת חיבור כללית: {str(e)}\nבדוק את מפתח ה-API שלך."
