import streamlit as st
import requests
import json

def get_ai_response_stream(subject, prompt):
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    # שלב 1: מציאת המודל (הקוד היציב שלנו)
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

    # שלב 2: הזרמת נתונים אמיתית (True Streaming)
    # הוספנו פה streamGenerateContent?alt=sse - זה אומר שהמידע יזרום אליך בחתיכות מיידיות!
    stream_url = f"https://generativelanguage.googleapis.com/v1beta/{valid_model}:streamGenerateContent?alt=sse&key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    context = f"You are a brilliant academic assistant in Nexus OS. Current subject: {subject}."
    
    payload = {
        "contents": [{"parts": [{"text": f"{context}\n\nUser Question: {prompt}"}]}],
        # הנה הקסם שמחבר אותו לאינטרנט! כלי החיפוש של גוגל בזמן אמת:
        "tools": [{"googleSearch": {}}] 
    }
    
    try:
        # stream=True אומר לפייתון לא לחכות לסוף התשובה אלא לשאוב אותה תוך כדי תנועה
        res = requests.post(stream_url, headers=headers, json=payload, stream=True)
        
        if res.status_code != 200:
            yield f"🚨 שגיאה בשרת גוגל: {res.status_code} - {res.text}"
            return
            
        # פיענוח ההזרמה בזמן אמת והצגה על המסך
        for line in res.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break # סוף התשובה
                try:
                    chunk_json = json.loads(data_str)
                    if 'candidates' in chunk_json and len(chunk_json['candidates']) > 0:
                        content = chunk_json['candidates'][0].get('content', {})
                        parts = content.get('parts', [])
                        if parts:
                            text_chunk = parts[0].get('text', '')
                            yield text_chunk # זורק את המילה ישר למסך שלך בלי השהיות!
                except json.JSONDecodeError:
                    continue
                    
    except Exception as e:
        yield f"🚨 שגיאת רשת הזרמה: {e}"

def process_file_to_db(file_path, subject):
    pass
