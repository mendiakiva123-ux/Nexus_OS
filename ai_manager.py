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
            api_key = st.secrets["GOOGLE_API_KEY"]
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            image_bytes = uploaded_file.getvalue()
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')
            mime_type = uploaded_file.type
            payload = {
                "contents": [{
                    "parts": [
                        {"text": "Extract all the text from this image accurately. Output only the text."},
                        {"inlineData": {"mimeType": mime_type, "data": encoded_image}}
                    ]
                }]
            }
            res = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                return f"🚨 שגיאה בתמונה: {res.text}"
    except Exception as e:
        return f"🚨 Error: {e}"
    return text

def get_ai_response_stream(subject, prompt, file_context=""):
    api_key = st.secrets["GOOGLE_API_KEY"]
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    try:
        list_res = requests.get(list_url)
        models_list = list_res.json().get("models", [])
        valid_model = None
        for m in models_list:
            if "generateContent" in m.get("supportedGenerationMethods", []):
                valid_model = m["name"]
                if "flash" in valid_model: break
        if not valid_model:
            yield "🚨 לא נמצא מודל נתמך."
            return
    except Exception:
        yield "🚨 שגיאת חיבור לגוגל."
        return

    stream_url = f"https://generativelanguage.googleapis.com/v1beta/{valid_model}:streamGenerateContent?alt=sse&key={api_key}"
    
    system_prompt = f"You are Nexus AI, an elite academic assistant. Subject: {subject}. Respond in Hebrew."
    if file_context:
        system_prompt += f"\n\nContext:\n{file_context[:15000]}"

    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser Question: {prompt}"}]}],
        "tools": [{"googleSearch": {}}]
    }

    res = requests.post(stream_url, headers={'Content-Type': 'application/json'}, json=payload, stream=True)
    for line in res.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith("data: "):
                data_str = decoded[6:]
                if data_str.strip() == "[DONE]": break
                try:
                    chunk_json = json.loads(data_str)
                    yield chunk_json['candidates'][0]['content']['parts'][0].get('text', '')
                except: continue
