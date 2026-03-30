import streamlit as st
import requests
import time

def get_ai_response_stream(subject, prompt):
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    # כתובת ראשית (Flash)
    url_flash = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    # כתובת גיבוי ברזל (Pro) למקרה של 404
    url_pro = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    context = f"אתה עוזר חכם במערכת Nexus OS. נושא: {subject}."
    
    payload = {
        "contents": [{"parts": [{"text": f"{context}\n\nשאלה: {prompt}"}]}],
        "generationConfig": {"temperature": 0.7}
    }
    
    try:
        # ניסיון ראשון
        response = requests.post(url_flash, headers=headers, json=payload)
        
        # אם קיבלנו 404, עוברים מיד לגיבוי בלי שהמשתמש ירגיש
        if response.status_code == 404:
            response = requests.post(url_pro, headers=headers, json=payload)
            
        if response.status_code == 200:
            text = response.json()['candidates'][0]['content']['parts'][0]['text']
            # אפקט הדפסה חלקה
            for char in text:
                yield char
                time.sleep(0.005)
        else:
            yield f"🚨 שגיאת שרת גוגל: {response.status_code} - {response.text}"
            
    except Exception as e:
        yield f"🚨 שגיאת תקשורת: {str(e)}"

def process_file_to_db(file_path, subject):
    pass
