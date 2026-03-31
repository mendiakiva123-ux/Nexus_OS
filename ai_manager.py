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
            for page in reader.pages: text += page.extract_text() + "\n"
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs: text += para.text + "\n"
        elif uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            api_key = st.secrets["GOOGLE_API_KEY"]
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
            image_bytes = uploaded_file.getvalue()
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')
            payload = {"contents": [{"parts": [{"text": "Extract all text."}, {"inlineData": {"mimeType": uploaded_file.type, "data": encoded_image}}]}]}
            res = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0].get('text', '')
    except Exception as e: return f"🚨 Error: {e}"
    return text

def get_ai_response_stream(subject, prompt, file_context="", lang="עברית"):
    api_key = st.secrets["GOOGLE_API_KEY"]
    # שימוש ב-v1 היציב למניעת 404
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
    
    # התאמת שפת התשובה לבחירת המשתמש
    instruct = "ענה בעברית בלבד" if lang == "עברית" else "Respond in English only"
    system_prompt = f"You are Nexus AI, an elite academic assistant. {instruct}. Subject: {subject}."
    if file_context: system_prompt += f"\n\nContext:\n{file_context[:10000]}"

    payload = {"contents": [{"parts": [{"text": f"{system_prompt}\n\nUser Question: {prompt}"}]}]}

    try:
        res = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload, stream=True)
        if res.status_code != 200:
            yield f"🚨 שגיאת שרת: {res.status_code}. וודא שהמפתח תקין."
            return

        for line in res.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    data_str = decoded[6:]
                    if data_str.strip() == "[DONE]": break
                    try:
                        chunk = json.loads(data_str)
                        # חילוץ טקסט חסין - בודק את כל מבנה ה-JSON
                        if 'candidates' in chunk and chunk['candidates']:
                            cand = chunk['candidates'][0]
                            if 'content' in cand and 'parts' in cand['content']:
                                txt = cand['content']['parts'][0].get('text', '')
                                if txt: yield txt
                    except: continue
    except Exception as e: yield f"🚨 Connection Error: {e}"
