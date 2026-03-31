import streamlit as st
import requests
import json
import PyPDF2
import docx
import base64

# --- פונקציית סריקה (PDF, Word, תמונות) ---
def extract_text_from_file(uploaded_file):
    text = ""
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            # שימוש בכתובת הכי סטנדרטית שיש ל-OCR
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
            image_bytes = uploaded_file.getvalue()
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')
            payload = {
                "contents": [{"parts": [
                    {"text": "Extract all text from this image accurately."},
                    {"inlineData": {"mimeType": uploaded_file.type, "data": encoded_image}}
                ]}]
            }
            res = requests.post(url, json=payload)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"🚨 שגיאה בסריקה: {e}"
    return text

# --- מנוע הבוט המשולב והחסין ---
def get_ai_response_stream(subject, prompt, file_context=""):
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    # ניסיון 1: v1 (הכי יציבה)
    url_v1 = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
    # ניסיון 2: v1beta (תומכת באינטרנט)
    url_beta = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    system_instruction = (
        f"You are Nexus AI, a professional academic assistant. Subject: {subject}. "
        "Use clear structure, headers, and bullet points. Always respond in Hebrew. "
    )
    
    context_text = f"CONTEXT FROM USER FILES:\n{file_context[:8000]}\n\n" if file_context else ""
    full_text = f"{system_instruction}\n\n{context_text}USER QUESTION: {prompt}"

    # פיילוד בסיסי שעובד בכל הגרסאות
    payload = {
        "contents": [{"role": "user", "parts": [{"text": full_text}]}]
    }

    try:
        # קודם כל מנסים את הגרסה הכי יציבה v1
        response = requests.post(url_v1, headers=headers, json=payload, stream=True)
        
        # אם קיבלנו 404, עוברים לגרסה השנייה
        if response.status_code == 404:
            response = requests.post(url_beta, headers=headers, json=payload, stream=True)

        if response.status_code != 200:
            yield f"🚨 שגיאת API ({response.status_code}): המודל לא נמצא או שהמפתח לא בתוקף."
            return

        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith("data: "):
                    try:
                        data_json = json.loads(line_text[6:])
                        if "candidates" in data_json:
                            chunk = data_json["candidates"][0]["content"]["parts"][0].get("text", "")
                            yield chunk
                    except:
                        continue
                        
    except Exception as e:
        yield f"🚨 תקלה טכנית: {str(e)}"
