import streamlit as st
import requests
import json
import PyPDF2
import docx
import base64

def extract_text_from_file(uploaded_file):
    """חילוץ טקסט מקבצי PDF, Word ותמונות בצורה מאובטחת"""
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
            api_key = st.secrets["GOOGLE_API_KEY"].strip()
            # שימוש בכתובת v1 היציבה
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
            image_bytes = uploaded_file.getvalue()
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')
            payload = {
                "contents": [{
                    "parts": [
                        {"text": "Extract all the text from this image accurately."},
                        {"inlineData": {"mimeType": uploaded_file.type, "data": encoded_image}}
                    ]
                }]
            }
            res = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0].get('text', '')
    except Exception as e:
        return f"🚨 Error extracting text: {e}"
    return text

def get_ai_response_stream(subject, prompt, file_context="", lang="עברית"):
    """ניהול שיחה עם הזרמת נתונים (Streaming) ללא שגיאות 404 או בועות ריקות"""
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    
    # כתובת v1 היא היציבה ביותר עבור Gemini 1.5 Flash כיום
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    # הנחיות מערכת המבוססות על שפת הממשק שבחרת
    instruct = "Respond strictly in Hebrew" if lang == "עברית" else "Respond strictly in English"
    system_prompt = f"You are Nexus AI, an elite academic assistant. {instruct}. Subject: {subject}."
    
    if file_context:
        system_prompt += f"\n\nContext from user files:\n{file_context[:10000]}"

    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser Question: {prompt}"}]}]
    }

    try:
        res = requests.post(url, headers=headers, json=payload, stream=True)
        
        # טיפול בשגיאת 404 (מעבר לגרסת בטא אם v1 נדחה בחשבון ספציפי)
        if res.status_code == 404:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
            res = requests.post(url, headers=headers, json=payload, stream=True)

        if res.status_code != 200:
            yield f"🚨 שגיאת תקשורת ({res.status_code}): אנא בדוק את המפתח ב-Secrets."
            return

        for line in res.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    data_str = decoded[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk_json = json.loads(data_str)
                        # חילוץ בטוח: מוודא שקיימים קנדידטים וטקסט לפני השליחה למסך
                        if 'candidates' in chunk_json and chunk_json['candidates']:
                            candidate = chunk_json['candidates'][0]
                            if 'content' in candidate and 'parts' in candidate['content']:
                                text_chunk = candidate['content']['parts'][0].get('text', '')
                                if text_chunk:
                                    yield text_chunk
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
    except Exception as e:
        yield f"🚨 Connection Error: {e}"
