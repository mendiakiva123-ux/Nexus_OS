import streamlit as st
import requests
import json

def get_ai_response_stream(subject, prompt, file_context="", lang="עברית"):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    instruct = "ענה בעברית בלבד" if lang == "עברית" else "Respond in English only"
    system_prompt = f"You are Nexus AI, an elite academic system. {instruct}. Subject: {subject}."
    if file_context: system_prompt += f"\n\nStudy Material:\n{file_context[:10000]}"

    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\nQuestion: {prompt}"}]}],
        "generationConfig": {"temperature": 0.7, "topP": 0.95, "maxOutputTokens": 2048}
    }

    try:
        res = requests.post(url, headers=headers, json=payload, stream=True)
        for line in res.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    data_str = decoded[6:]
                    if data_str.strip() == "[DONE]": break
                    try:
                        chunk = json.loads(data_str)
                        # חילוץ עמוק כדי למנוע בועות ריקות
                        if 'candidates' in chunk:
                            for cand in chunk['candidates']:
                                if 'content' in cand and 'parts' in cand['content']:
                                    for part in cand['content']['parts']:
                                        txt = part.get('text', '')
                                        if txt: yield txt
                    except: continue
    except Exception as e:
        yield f"🚨 Connection Error: {e}"
