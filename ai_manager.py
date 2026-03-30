import streamlit as st
import requests
import time

def get_ai_response_stream(subject, prompt):
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    # הכתובת הישירה והקבועה של גוגל
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    context = f"אתה עוזר אקדמי במערכת Nexus OS. נושא השיחה הנוכחי: {subject}."
    
    # חבילת הנתונים שאנחנו שולחים לגוגל
    payload = {
        "contents": [{"parts": [{"text": f"{context}\n\nשאלה: {prompt}"}]}],
        "generationConfig": {"temperature": 0.7}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        # אם הכל עבר בהצלחה
        if response.status_code == 200:
            data = response.json()
            try:
                text = data['candidates'][0]['content']['parts'][0]['text']
                # יצירת אפקט הדפסה אנושי על המסך (כמו בסטרימינג)
                for char in text:
                    yield char
                    time.sleep(0.005) 
            except Exception as e:
                yield f"🚨 שגיאה בפענוח התשובה מגוגל. נתונים: {data}"
        else:
            # אם גוגל מחזיר שגיאה, נראה אותה בבירור!
            yield f"🚨 השרת של גוגל חסם את הבקשה. קוד: {response.status_code}. הודעה: {response.text}"
            
    except Exception as e:
        yield f"🚨 קריסת רשת (לא קשור לגוגל): {str(e)}"

def process_file_to_db(file_path, subject):
    pass
