import streamlit as st
import requests
import json
import PyPDF2
import docx
import base64

# פונקציה לחילוץ טקסט מקבצים (Neural Scan)
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

# פונקציית הבוט - חסינה לבועות ריקות
def get_ai_response_stream(subject, prompt, file_context="", lang="עברית", analyst_mode=False):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    # הגדרת תפקיד ושפה
    role = "מומחה ניתוח נתונים וסטטיסטיקה" if analyst_mode else "מנטור אקדמי בכיר"
    if lang == "עברית":
        instruct = f"אתה {role}. ענה בעברית בלבד! אל תשתמש באנגלית."
    else:
        instruct = f"You are {role}. Respond in English only!"

    system_prompt = f"{instruct} נושא: {subject}."
    if file_context:
        system_prompt += f"\n\nמידע מהקבצים שנסרקו:\n{file_context[:10000]}"

    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\nשאלה: {prompt}"}]}],
        "generationConfig": {"temperature": 0.7, "topP": 0.9}
    }

    try:
        res = requests.post(url, headers=headers, json=payload, stream=True)
        for line in res.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    try:
                        chunk = json.loads(decoded[6:])
                        if 'candidates' in chunk and len(chunk['candidates']) > 0:
                            part = chunk['candidates'][0]['content']['parts'][0]
                            text_chunk = part.get('text', '')
                            if text_chunk: yield text_chunk
                    except: continue
    except Exception as e:
        yield f"🚨 שגיאת חיבור: {e}" if lang == "עברית" else f"🚨 Connection Error: {e}"
