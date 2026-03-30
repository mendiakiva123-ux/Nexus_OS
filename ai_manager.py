import streamlit as st
import requests
import time

def get_ai_response_stream(subject, prompt):
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    # הכתובת הישירה והמדויקת של גוגל - לא משתנה לעולם
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    context = f"אתה מורה פרטי ואנליסט נתונים בכיר במערכת Nexus OS. הנושא כרגע: {subject}."
    full_prompt = f"{context}\n\nשאלה: {prompt}"
    
    # בניית חבילת הנתונים הישירה
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {"temperature": 0.7}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            # שליפת הטקסט מתוך ה-JSON של גוגל
            text = data['candidates'][0]['content']['parts'][0]['text']
            
            # הדפסה אנושית (זורמת) אל המסך
            words = text.split(" ")
            for word in words:
                yield word + " "
                time.sleep(0.02) # השהייה קטנטנה לאפקט של כתיבה חיה
        else:
            yield f"🚨 שגיאת שרת: קוד {response.status_code}. פרטים: {response.text}"
            
    except Exception as e:
        yield f"🚨 שגיאת תקשורת קריטית: {str(e)}"

def process_file_to_db(file_path, subject):
    pass
