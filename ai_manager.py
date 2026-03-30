import streamlit as st
import requests
import time

def get_ai_response_stream(subject, prompt):
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    # שלב 1: המנגנון שעבד לך - שואל את גוגל איזה מודל זמין למפתח החדש שלך
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    try:
        list_res = requests.get(list_url)
        if list_res.status_code != 200:
            yield f"🚨 שגיאת התחברות ראשונית לגוגל: {list_res.text}"
            return
            
        models_list = list_res.json().get("models", [])
        valid_model = None
        
        for m in models_list:
            if "generateContent" in m.get("supportedGenerationMethods", []):
                valid_model = m["name"]
                if "flash" in valid_model:
                    break
                    
        if not valid_model:
            yield "🚨 לא נמצא מודל נתמך במפתח ה-API."
            return
            
    except Exception as e:
        yield f"🚨 שגיאה בשליפת רשימת המודלים: {e}"
        return

    # שלב 2: שליחת השאלה למודל שאושר
    generate_url = f"https://generativelanguage.googleapis.com/v1beta/{valid_model}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    context = f"You are a brilliant academic assistant in Nexus OS. Current subject: {subject}."
    
    payload = {
        "contents": [{"parts": [{"text": f"{context}\n\nUser Question: {prompt}"}]}]
    }
    
    try:
        res = requests.post(generate_url, headers=headers, json=payload)
        
        if res.status_code == 200:
            text = res.json()['candidates'][0]['content']['parts'][0]['text']
            for char in text:
                yield char
                time.sleep(0.005)
        else:
            yield f"🚨 שגיאה בשרת גוגל. קוד תקלה: {res.status_code} - {res.text}"
            
    except Exception as e:
        yield f"🚨 שגיאת רשת: {e}"

def process_file_to_db(file_path, subject):
    pass
