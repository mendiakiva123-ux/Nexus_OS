import streamlit as st
import requests
import time

def get_ai_response_stream(subject, prompt):
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    # שימוש בכתובת היציבה (v1) שעובדת מושלם עם המפתח החדש
    url_flash = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    url_pro = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.0-pro:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    context = f"You are an elite academic assistant in Nexus OS. Current subject context: {subject}."
    
    payload = {
        "contents": [{"parts": [{"text": f"{context}\n\nUser Question: {prompt}"}]}]
    }
    
    try:
        # קריאה למודל המהיר
        res = requests.post(url_flash, headers=headers, json=payload)
        
        # מנגנון גיבוי מיידי למקרה של עומס בשרתי גוגל
        if res.status_code != 200:
            res = requests.post(url_pro, headers=headers, json=payload)
            
        if res.status_code == 200:
            text = res.json()['candidates'][0]['content']['parts'][0]['text']
            # אפקט כתיבה אנושי וזורם למסך
            for char in text:
                yield char
                time.sleep(0.005)
        else:
            yield f"🚨 שגיאה בשרת גוגל. קוד תקלה: {res.status_code}"
            
    except Exception as e:
        yield f"🚨 שגיאת רשת מול גוגל: {e}"

def process_file_to_db(file_path, subject):
    pass
