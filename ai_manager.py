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
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            encoded = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
            payload = {"contents": [{"parts": [{"text": "Extract text."}, {"inlineData": {"mimeType": uploaded_file.type, "data": encoded}}]}]}
            res = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0].get('text', '')
    except: pass
    return text

def get_ai_response_stream(subject, prompt, file_context="", lang="עברית", analyst_mode=False):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # שימוש ב-v1beta לתמיכה מקסימלית בהזרמה
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    # הגדרת אישיות מקצועית
    role = "Senior Data Analyst & BI Expert" if analyst_mode else "Academic Mentor"
    if lang == "עברית":
        instruct = f"אתה {role}. ענה בעברית בלבד! אל תשתמש באנגלית. נושא: {subject}."
    else:
        instruct = f"You are {role}. Respond in English only! Subject: {subject}."

    system_prompt = instruct
    if file_context:
        system_prompt += f"\n\nContext from scanned files:\n{file_context[:10000]}"

    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser Question: {prompt}"}]}],
        "generationConfig": {"temperature": 0.7, "topP": 0.9}
    }

    try:
        res = requests.post(url, headers=headers, json=payload, stream=True)
        if res.status_code != 200:
            yield f"🚨 Error {res.status_code}: Check API Key."
            return

        for line in res.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    try:
                        data_json = json.loads(decoded[6:])
                        if 'candidates' in data_json and data_json['candidates']:
                            part = data_json['candidates'][0]['content']['parts'][0]
                            content = part.get('text', '')
                            if content: # בדיקה קריטית: רק אם יש תוכן אמיתי
                                yield content
                    except: continue
    except Exception as e:
        yield f"🚨 Connection Error: {e}"
