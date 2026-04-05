import streamlit as st
import requests
import json
import base64

def get_ai_response_stream(subject, prompt, file_context="", lang="עברית", analyst_mode=False):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # שימוש בנתיב היציב ביותר v1
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    # הגדרת פרוטוקול השפה והתפקיד
    role = "Data Analyst Expert & Statistics Professional" if analyst_mode else "Senior Academic Mentor"
    if lang == "עברית":
        instruct = f"אתה {role}. ענה בעברית בלבד! אל תשתמש באנגלית בכלל."
    else:
        instruct = f"You are {role}. Respond in English only!"

    system_prompt = f"{instruct} Subject: {subject}."
    if file_context:
        system_prompt += f"\n\nContext from files:\n{file_context[:12000]}"

    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser Question: {prompt}"}]}],
        "generationConfig": {"temperature": 0.8, "topP": 0.95}
    }

    try:
        res = requests.post(url, headers=headers, json=payload, stream=True)
        for line in res.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    try:
                        chunk = json.loads(decoded[6:])
                        # בדיקה עמוקה כדי לוודא שיש טקסט לפני ה-Yield
                        if 'candidates' in chunk and len(chunk['candidates']) > 0:
                            candidate = chunk['candidates'][0]
                            if 'content' in candidate and 'parts' in candidate['content']:
                                text_chunk = candidate['content']['parts'][0].get('text', '')
                                if text_chunk.strip(): # רק אם יש טקסט אמיתי
                                    yield text_chunk
                    except:
                        continue
    except Exception as e:
        yield f"🚨 שגיאת מערכת: {e}" if lang == "עברית" else f"🚨 System Error: {e}"
