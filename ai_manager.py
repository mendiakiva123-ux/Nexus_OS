import streamlit as st
import requests
import time

def get_ai_response_stream(subject, prompt):
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    # הפתרון הסופי: מעבר למודל gemini-pro הקלאסי והיציב
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    context = f"אתה עוזר אקדמי במערכת Nexus OS. נושא השיחה הנוכחי: {subject}."
    
    payload = {
        "contents": [{"parts": [{"text": f"{context}\n\nשאלה: {prompt}"}]}],
        "generationConfig": {"temperature": 0.7}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            try:
                text = data['candidates'][0]['content']['parts'][0]['text']
                # אפקט הדפסה אנושי (סטרימינג חלק)
                for char in text:
                    yield char
                    time.sleep(0.005) 
            except Exception as e:
                yield f"🚨 שגיאה בפענוח התשובה: {str(e)}"
        else:
            yield f"🚨 השרת של גוגל חסם את הבקשה. קוד: {response.status_code}. הודעה: {response.text}"
            
    except Exception as e:
        yield f"🚨 שגיאת רשת קריטית: {str(e)}"

def process_file_to_db(file_path, subject):
    pass
