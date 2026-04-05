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
            image_bytes = uploaded_file.getvalue()
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')
            payload = {"contents": [{"parts": [{"text": "Extract all text."}, {"inlineData": {"mimeType": uploaded_file.type, "data": encoded_image}}]}]}
            res = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0].get('text', '')
    except Exception: pass
    return text

def get_ai_response_stream(subject, prompt, file_context="", lang="עברית", analyst_mode=False):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    
    # נתיב ראשון - Beta
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    # הגדרת אישיות מקצועית
    role = "מומחה ניתוח נתונים (Data Analyst)" if analyst_mode else "מנטור אקדמי בכיר"
    if lang == "עברית":
        instruct = f"ענה בתור {role} בעברית בלבד! אל תשתמש באנגלית."
    else:
        instruct = f"You are a {role}. Respond in English only!"

    system_prompt = f"{instruct} נושא השיחה: {subject}."
    if file_context:
        system_prompt += f"\n\nמידע מהקבצים שנסרקו:\n{file_context[:10000]}"

    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\nשאלה: {prompt}"}]}],
        "generationConfig": {"temperature": 0.7, "topP": 0.9}
    }

    try:
        res = requests.post(url, headers=headers, json=payload, stream=True)
        
        # פתרון ה-404: אם הכתובת לא נמצאה, עוברים לכתובת היציבה (v1)
        if res.status_code == 404:
            url_v1 = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
            res = requests.post(url_v1, headers=headers, json=payload, stream=True)

        if res.status_code != 200:
            yield f"🚨 שגיאה {res.status_code}: וודא שהמפתח ב-Secrets תקין וללא רווחים."
            return

        for line in res.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    data_str = decoded[6:]
                    if data_str.strip() == "[DONE]": break
                    try:
                        chunk = json.loads(data_str)
                        # חילוץ אגרסיבי למניעת בועות ריקות
                        if 'candidates' in chunk and chunk['candidates']:
                            cand = chunk['candidates'][0]
                            content = cand.get('content', {})
                            parts = content.get('parts', [])
                            if parts:
                                txt = parts[0].get('text', '')
                                if txt: yield txt
                    except: continue
    except Exception as e:
        yield f"🚨 שגיאת חיבור: {e}"
