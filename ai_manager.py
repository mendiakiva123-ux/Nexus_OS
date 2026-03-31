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
            res = requests.post(url, json=payload)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"🚨 שגיאה בסריקה: {e}"
    return text

# --- מנוע הבוט היציב והמהיר ---
def get_ai_response_stream(subject, prompt, file_context=""):
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    # משתמשים בכתובת היציבה ביותר (v1beta) שתומכת בסטרימינג ואינטרנט
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    # הנחיית מערכת קשוחה לדיוק ומקצועיות
    system_instruction = (
        f"You are Nexus AI, a professional academic assistant. Subject: {subject}. "
        "Use clear structure, headers, and bullet points. Always respond in Hebrew. "
        "If information is missing, use Google Search via your tools."
    )
    
    full_prompt = f"{system_instruction}\n\n"
    if file_context:
        full_prompt += f"CONTEXT FROM USER FILES:\n{file_context[:8000]}\n\n"
    full_prompt += f"USER QUESTION: {prompt}"

    payload = {
        "contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
        "tools": [{"googleSearch": {}}]
    }

    try:
        # שליחת הבקשה
        response = requests.post(url, headers=headers, json=payload, stream=True)
        
        # אם יש שגיאה מהשרת של גוגל
        if response.status_code != 200:
            error_details = response.json() if response.text else "No details"
            yield f"🚨 שגיאת API ({response.status_code}): {error_details}"
            return

        # עיבוד הסטרימינג (SSE)
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith("data: "):
                    data_json = json.loads(line_text[6:])
                    if "candidates" in data_json:
                        chunk = data_json["candidates"][0]["content"]["parts"][0].get("text", "")
                        yield chunk
                        
    except Exception as e:
        yield f"🚨 תקלה בחיבור: {str(e)}"
