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
            api_key = st.secrets["GOOGLE_API_KEY"].strip()
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
            encoded = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
            payload = {"contents": [{"parts": [{"text": "Extract all text."}, {"inlineData": {"mimeType": uploaded_file.type, "data": encoded}}]}]}
            res = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0].get('text', '')
    except: pass
    return text

def get_ai_response_stream(subject, prompt, file_context="", lang="עברית", analyst_mode=False):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # נסיון ראשון בכתובת Beta
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    role = "Data Analyst Expert" if analyst_mode else "Academic Mentor"
    if lang == "עברית":
        instruct = f"אתה {role}. ענה בעברית בלבד! נושא: {subject}."
    else:
        instruct = f"You are {role}. Respond in English only! Subject: {subject}."

    payload = {"contents": [{"parts": [{"text": f"{instruct}\n\nContext: {file_context[:8000]}\n\nUser: {prompt}"}]}]}

    try:
        res = requests.post(url, headers=headers, json=payload, stream=True)
        # תיקון ה-404: אם הכתובת לא קיימת, נסה את הגרסה היציבה
        if res.status_code == 404:
            url_v1 = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
            res = requests.post(url_v1, headers=headers, json=payload, stream=True)

        for line in res.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    try:
                        chunk = json.loads(decoded[6:])
                        if 'candidates' in chunk:
                            txt = chunk['candidates'][0]['content']['parts'][0].get('text', '')
                            if txt: yield txt
                    except: continue
    except Exception as e: yield f"🚨 שגיאת חיבור: {e}"
