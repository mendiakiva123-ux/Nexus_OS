import streamlit as st
import requests
import json
import time
import PyPDF2
import docx
import base64

# --- פונקציית סריקה (PDF, Word, תמונות) ---
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
        elif uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            api_key = st.secrets["GOOGLE_API_KEY"]
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
            image_bytes = uploaded_file.getvalue()
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')
            payload = {
                "contents": [{"parts": [
                    {"text": "Extract all text from this image accurately."},
                    {"inlineData": {"mimeType": uploaded_file.type, "data": encoded_image}}
                ]}]
            }
            res = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"🚨 שגיאה בסריקה: {e}"
    return text

# --- מנוע הבוט המשולב והחסין ---
def get_ai_response_stream(subject, prompt, file_context=""):
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    # ניסיון ראשון: v1beta (תומך באינטרנט)
    url_beta = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
    # ניסיון גיבוי: v1 (הכי יציב בעולם)
    url_stable = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    system_prompt = f"You are Nexus AI, an academic assistant. Subject: {subject}. Always use Hebrew if asked in Hebrew."
    if file_context:
        system_prompt += f"\nContext from files: {file_context[:5000]}"

    # פיילוד מתקדם (כולל חיפוש בגוגל)
    payload_beta = {
        "contents": [{"parts": [{"text": f"{system_prompt}\nQuestion: {prompt}"}]}],
        "tools": [{"googleSearch": {}}]
    }
    
    # פיילוד פשוט (ליתר ביטחון)
    payload_stable = {
        "contents": [{"parts": [{"text": f"{system_prompt}\nQuestion: {prompt}"}]}]
    }

    try:
        # ניסיון עם הכתובת המתקדמת
        res = requests.post(url_beta, headers=headers, json=payload_beta, stream=True, timeout=10)
        res.encoding = 'utf-8'
        
        # אם הכתובת המתקדמת נכשלה (כמו שקרה לך), עוברים מיד ליציבה
        if res.status_code != 200:
            res = requests.post(url_stable, headers=headers, json=payload_stable, stream=True, timeout=10)
            res.encoding = 'utf-8'

        if res.status_code != 200:
            yield f"🚨 שגיאת שרת גוגל: {res.status_code}. בדוק את מפתח ה-API שלך ב-Secrets."
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
                        if 'candidates' in chunk_json:
                            # חילוץ הטקסט המדויק מהמבנה של גוגל
                            content = chunk_json['candidates'][0].get('content', {})
                            parts = content.get('parts', [])
                            if parts and 'text' in parts[0]:
                                yield parts[0]['text']
                    except:
                        continue
    except Exception as e:
        yield f"🚨 שגיאת חיבור: {str(e)}"
