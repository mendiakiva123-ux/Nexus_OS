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
            # שימוש בכתובת הכי יציבה לזיהוי תמונות
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
            image_bytes = uploaded_file.getvalue()
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')
            payload = {
                "contents": [{"parts": [
                    {"text": "Extract all text from this image accurately."},
                    {"inlineData": {"mimeType": uploaded_file.type, "data": encoded_image}}
                ]}]
            }
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"🚨 שגיאה בסריקה: {e}"
    return text

# --- מנוע הבוט החסין (מנסה את כל האפשרויות עד להצלחה) ---
def get_ai_response_stream(subject, prompt, file_context=""):
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    # רשימת הכתובות האפשריות - אנחנו ננסה אותן אחת אחת
    base_urls = [
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash",
        "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash",
        "https://generativelanguage.googleapis.com/v1beta/gemini-1.5-flash",
        "https://generativelanguage.googleapis.com/v1/gemini-1.5-flash"
    ]
    
    headers = {'Content-Type': 'application/json'}
    system_instruction = (
        f"You are Nexus AI, an elite academic assistant. Subject: {subject}. "
        "Use clear structure, headers, and bullet points. Always respond in Hebrew."
    )
    
    context_text = f"CONTEXT FROM USER FILES:\n{file_context[:8000]}\n\n" if file_context else ""
    full_text = f"{system_instruction}\n\n{context_text}USER QUESTION: {prompt}"

    # פיילודים - אחד עם חיפוש בגוגל ואחד בלי (למקרה שגוגל חוסמת את החיפוש)
    payload_with_search = {
        "contents": [{"role": "user", "parts": [{"text": full_text}]}],
        "tools": [{"googleSearch": {}}]
    }
    payload_basic = {
        "contents": [{"role": "user", "parts": [{"text": full_text}]}]
    }

    success = False
    for base_url in base_urls:
        try:
            # מנסים קודם עם חיפוש בגוגל
            url = f"{base_url}:streamGenerateContent?alt=sse&key={api_key}"
            response = requests.post(url, headers=headers, json=payload_with_search, stream=True, timeout=8)
            
            # אם החיפוש נכשל, ננסה את אותה כתובת בלי חיפוש
            if response.status_code != 200:
                response = requests.post(url, headers=headers, json=payload_basic, stream=True, timeout=8)
            
            # אם הצלחנו לקבל 200 - אנחנו בחוץ! עוצרים את הלופ ומזרימים תשובה
            if response.status_code == 200:
                success = True
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
                break # יציאה מהלופ של הכתובות
        except:
            continue # אם הכתובת הזו קרסה, עוברים לבאה בתור

    if not success:
        yield "🚨 גוגל מסרבת להתחבר לכל הכתובות הידועות. וודא שמפתח ה-API שלך ב-Secrets לא נחסם או דלף."
