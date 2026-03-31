import streamlit as st
import requests
import json
import time
import PyPDF2
import docx

# פונקציה חדשה: קריאת קבצים (PDF/Word) והפיכתם לטקסט חי
def extract_text_from_file(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
    except Exception as e:
        return f"Error extracting text: {e}"
    return text

# הבוט עודכן לקבל "file_context" (הטקסט מהקבצים שלך)
def get_ai_response_stream(subject, prompt, file_context=""):
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        list_res = requests.get(list_url)
        if list_res.status_code != 200:
            yield f"🚨 שגיאת התחברות לגוגל: {list_res.text}"
            return
            
        models_list = list_res.json().get("models", [])
        valid_model = None
        for m in models_list:
            if "generateContent" in m.get("supportedGenerationMethods", []):
                valid_model = m["name"]
                if "flash" in valid_model:
                    break
        if not valid_model:
            yield "🚨 לא נמצא מודל נתמך."
            return
    except Exception as e:
        yield f"🚨 שגיאה מול גוגל: {e}"
        return

    stream_url = f"https://generativelanguage.googleapis.com/v1beta/{valid_model}:streamGenerateContent?alt=sse&key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    # בניית ההנחיה החכמה (Prompt Engineering)
    system_prompt = f"You are a brilliant academic assistant in Nexus OS. Current subject: {subject}."
    
    # אם העלית קובץ - הבוט יקבל פקודה קפדנית להשתמש בו!
    if file_context:
        system_prompt += f"\n\nHere is the user's study material for this subject. Prioritize this information in your answers:\n<study_material>\n{file_context[:10000]}\n</study_material>"
    
    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser Question: {prompt}"}]}],
        "tools": [{"googleSearch": {}}] # חיבור מלא לאינטרנט בזמן אמת!
    }
    
    try:
        res = requests.post(stream_url, headers=headers, json=payload, stream=True)
        res.encoding = 'utf-8' # תיקון הג'יבריש!
        
        if res.status_code != 200:
            yield f"🚨 שגיאה בשרת גוגל: {res.status_code} - {res.text}"
            return
            
        for line in res.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    data_str = decoded_line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk_json = json.loads(data_str)
                        if 'candidates' in chunk_json and len(chunk_json['candidates']) > 0:
                            content = chunk_json['candidates'][0].get('content', {})
                            parts = content.get('parts', [])
                            if parts:
                                text_chunk = parts[0].get('text', '')
                                yield text_chunk
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield f"🚨 שגיאת רשת הזרמה: {e}"
