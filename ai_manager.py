import streamlit as st
import requests
import time

def get_ai_response_stream(subject, prompt):
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    # שלב 1: מפסיקים לנחש! שואלים את גוגל אילו מודלים זמינים למפתח שלך
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    try:
        list_res = requests.get(list_url)
        if list_res.status_code != 200:
            yield f"🚨 שגיאת התחברות ראשונית לגוגל: {list_res.text}"
            return
            
        models_list = list_res.json().get("models", [])
        valid_model = None
        
        # שלב 2: שולפים את השם המדויק של המודל הראשון שתומך ביצירת טקסט
        for m in models_list:
            if "generateContent" in m.get("supportedGenerationMethods", []):
                valid_model = m["name"] # השם המדויק שגוגל מכיר בחשבון שלך
                if "flash" in valid_model:
                    break # נעדיף את מודל הפלאש המהיר אם הוא ברשימה שלך
                    
        if not valid_model:
            yield "🚨 מפתח ה-API שלך חסום לחלוטין לשימוש במודלים של טקסט ב-Gemini."
            return
            
    except Exception as e:
        yield f"🚨 שגיאה בשליפת רשימת המודלים: {e}"
        return

    # שלב 3: שליחת השאלה לכתובת של המודל המדויק שגוגל אישר הרגע
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
            # הדפסה זורמת ואנושית למסך
            for char in text:
                yield char
                time.sleep(0.005)
        else:
            yield f"🚨 שגיאה ביצירת תשובה: {res.status_code} - {res.text}"
            
    except Exception as e:
        yield f"🚨 שגיאת רשת (generate): {e}"

def process_file_to_db(file_path, subject):
    pass
