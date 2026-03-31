import streamlit as st
import requests
import json
import PyPDF2
import docx
import base64

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
            # שימוש בנתיב ה-API המדויק לחילוץ טקסט
            api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '').replace("'", "")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            image_bytes = uploaded_file.getvalue()
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')
            payload = {
                "contents": [{
                    "parts": [
                        {"text": "Extract all text from this image."},
                        {"inlineData": {"mimeType": uploaded_file.type, "data": encoded_image}}
                    ]
                }]
            }
            res = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0].get('text', '')
    except Exception:
        pass
    return text

def get_ai_response_stream(subject, prompt, file_context="", lang="עברית"):
    # ניקוי המפתח מרווחים, גרשיים או תווים נסתרים
    api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '').replace("'", "")
    
    # ניסיון ראשון עם v1beta - הכתובת הנפוצה ביותר להזרמה ב-2026
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    instruct = "ענה בעברית בלבד" if lang == "עברית" else "Respond in English only"
    system_prompt = f"You are Nexus AI, an academic assistant. {instruct}. Subject: {subject}."
    
    if file_context:
        system_prompt += f"\n\nContext:\n{file_context[:10000]}"

    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser Question: {prompt}"}]}]
    }

    try:
        res = requests.post(url, headers=headers, json=payload, stream=True)
        
        # אם גוגל מחזירה 404, אנחנו מבצעים "תיקון מסלול" אוטומטי לגרסת v1
        if res.status_code == 404:
            url_v1 = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
            res = requests.post(url_v1, headers=headers, json=payload, stream=True)

        if res.status_code != 200:
            yield f"🚨 שגיאת שרת ({res.status_code}). וודא שהמפתח ב-Secrets תקין וללא רווחים."
            return

        for line in res.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    data_str = decoded[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        if 'candidates' in chunk and chunk['candidates']:
                            # חילוץ עמוק למניעת בועות ריקות
                            content = chunk['candidates'][0].get('content', {})
                            parts = content.get('parts', [])
                            if parts:
                                text_chunk = parts[0].get('text', '')
                                if text_chunk:
                                    yield text_chunk
                    except (json.JSONDecodeError, KeyError):
                        continue
    except Exception as e:
        yield f"🚨 Connection Error: {e}"
