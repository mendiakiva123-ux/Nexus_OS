import streamlit as st
import requests
import json
import time
import PyPDF2
import docx
import base64

# --- פונקציית סריקת הקבצים (PDF, Word, תמונות) ---
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
            # שימוש בכתובת v1 היציבה לפענוח תמונות (OCR)
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
            
            image_bytes = uploaded_file.getvalue()
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')
            mime_type = uploaded_file.type
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": "Extract all text from this image accurately. Output only the text."},
                        {"inlineData": {"mimeType": mime_type, "data": encoded_image}}
                    ]
                }]
            }
            res = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                return f"🚨 שגיאה בפענוח תמונה: {res.text}"
                
    except Exception as e:
        return f"🚨 Error extracting text: {e}"
    return text

# --- מנוע הבוט המשולב (קבצים + אינטרנט + מהירות) ---
def get_ai_response_stream(subject, prompt, file_context=""):
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    # שימוש ב-v1beta כי היא היחידה שתומכת ב-Google Search Grounding
    stream_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    system_prompt = f"""You are Nexus AI, an elite academic assistant. Current subject: {subject}.
    CRITICAL INSTRUCTIONS:
    1. Accuracy: Cross-check facts using Google Search. Never hallucinate.
    2. Structure: Use headers, bullet points, and bold text for clarity.
    3. Context: Prioritize the provided study material if available.
    4. Language: Always respond in the language of the user's question (Hebrew/English).
    """
    
    if file_context:
        system_prompt += f"\n\nUSER STUDY MATERIAL:\n{file_context[:10000]}"
    
    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\nQuestion: {prompt}"}]}],
        "tools": [{"googleSearch": {}}] # מאפשר גישה לאינטרנט בזמן אמת
    }
    
    try:
        # שליחת הבקשה עם stream=True כדי לקבל מילים תוך כדי תנועה
        res = requests.post(stream_url, headers=headers, json=payload, stream=True)
        res.encoding = 'utf-8'
        
        if res.status_code != 200:
            # אם v1beta עושה בעיות, ננסה אוטומטית גרסה יציבה (בלי אינטרנט אבל עם תשובה)
            stable_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
            payload_no_tools = {"contents": [{"parts": [{"text": f"{system_prompt}\n\nQuestion: {prompt}"}]}]}
            res = requests.post(stable_url, headers=headers, json=payload_no_tools, stream=True)
            res.encoding = 'utf-8'

        for line in res.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    data_str = decoded_line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk_json = json.loads(data_str)
                        if 'candidates' in chunk_json:
                            part = chunk_json['candidates'][0]['content']['parts'][0]
                            if 'text' in part:
                                yield part['text']
                    except:
                        continue
    except Exception as e:
        yield f"🚨 שגיאת מערכת: {e}"
