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
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            image_bytes = uploaded_file.getvalue()
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')
            payload = {"contents": [{"parts": [{"text": "Extract text."}, {"inlineData": {"mimeType": uploaded_file.type, "data": encoded_image}}]}]}
            res = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"🚨 Error: {e}"
    return text

def get_ai_response_stream(subject, prompt, file_context=""):
    api_key = st.secrets["GOOGLE_API_KEY"]
    # שימוש ישיר במודל פלאש למניעת בקשות מיותרות לשרת
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": f"Subject: {subject}. Respond in Hebrew. Context: {file_context[:5000]}. Question: {prompt}"}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        
        if response.status_code == 429:
            yield "🚨 עומס על השרת (429). גוגל מגבילה את כמות השאלות בדקה. המתן 30 שניות ונסה שוב."
            return
        elif response.status_code != 200:
            yield f"🚨 שגיאת שרת: {response.status_code}. בדוק את המפתח ב-Secrets."
            return

        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    data_str = decoded[6:]
                    if data_str.strip() == "[DONE]": break
                    try:
                        chunk = json.loads(data_str)
                        text = chunk['candidates'][0]['content']['parts'][0].get('text', '')
                        if text: yield text
                    except: continue
    except Exception as e:
        yield f"🚨 תקלה: {str(e)}"
