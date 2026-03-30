import streamlit as st
import requests
import time

def get_ai_response_stream(subject, prompt):
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    # כתובת v1 היציבה (לא v1beta!)
    url_flash = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    url_pro = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.0-pro:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    context = f"You are a helpful academic assistant in Nexus OS. Current subject: {subject}."
    
    payload = {
        "contents": [{"parts": [{"text": f"{context}\n\nUser: {prompt}"}]}]
    }
    
    try:
        # ניסיון ראשון מול המודל המהיר ביותר בגרסה היציבה
        response = requests.post(url_flash, headers=headers, json=payload)
        
        # אם יש שגיאה (כמו 404), מעבר מיידי למודל הגיבוי
        if response.status_code != 200:
            response = requests.post(url_pro, headers=headers, json=payload)
            
        if response.status_code == 200:
            text = response.json()['candidates'][0]['content']['parts'][0]['text']
            # אפקט הדפסה חלקה
            for char in text:
                yield char
                time.sleep(0.005)
        else:
            yield f"🚨 שגיאת שרת סופית מגוגל: {response.text}"
            
    except Exception as e:
        yield f"🚨 שגיאת תקשורת: {str(e)}"

def process_file_to_db(file_path, subject):
    pass
