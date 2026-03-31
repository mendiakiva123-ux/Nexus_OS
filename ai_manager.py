import streamlit as st
import requests
import json
import time
import PyPDF2
import docx
import base64

# פונקציה משודרגת: קוראת PDF, Word וגם צילומי מסך ותמונות!
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
                
        # הזיהוי החדש: אם זה תמונה/צילום מסך
        elif uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            api_key = st.secrets["GOOGLE_API_KEY"]
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            
            image_bytes = uploaded_file.getvalue()
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')
            mime_type = uploaded_file.type
            
            # שולחים את התמונה לגוגל כדי שיקרא את הטקסט מתוכה
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
                return f"🚨 שגיאה בפענוח התמונה: {res.text}"
                
    except Exception as e:
        return f"🚨 Error extracting text: {e}"
    return text

def get_ai_response_stream(subject, prompt, file_context=""):
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        list_res = requests.get(list_url)
        if list_res.status_code != 200:
            yield f"🚨 שגיאת התחברות לגוגל: {list_res.text}"
            return
            
        models_list = list_res.json().get("models", [])
        valid_model = None
        for m in models_list:
            if "generateContent" in m.get("supportedGenerationMethods", []):
                valid_model = m["name"]
                if "flash" in valid_model:
                    break
        if not valid_model:
            yield "🚨 לא נמצא מודל נתמך."
            return
    except Exception as e:
        yield f"🚨 שגיאה מול גוגל: {e}"
        return

    stream_url = f"https://generativelanguage.googleapis.com/v1beta/{valid_model}:streamGenerateContent?alt=sse&key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    # --- הזרקת החוקים החדשים שביקשת ישירות למוח של הבוט ---
    system_prompt = f"""You are Nexus AI, an elite academic assistant. Current subject: {subject}.
    CRITICAL INSTRUCTIONS:
    1. Accuracy & Facts: Cross-check your facts. Never invent information (no hallucinations). If you do not know the answer, explicitly state "איני יודע".
    2. Structure & Organization: Use a clear, logical structure. Use headers, bullet points, and short paragraphs for readability.
    3. Context: Focus on the user's core intent. If the prompt is ambiguous, ASK CLARIFYING QUESTIONS before answering.
    4. Tone: Maintain an academic, professional, yet accessible tone.
    5. Correction: If the user points out an error, correct it fully and address the root cause without excessive apologizing.
    """
    
    if file_context:
        system_prompt += f"\n\nPRIORITY CONTEXT (User's Study Material):\n<study_material>\n{file_context[:15000]}\n</study_material>\nAlways base your answers primarily on this material if relevant."
    
    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\nUser Question: {prompt}"}]}],
        "tools": [{"googleSearch": {}}] 
    }
    
    try:
        res = requests.post(stream_url, headers=headers, json=payload, stream=True)
        res.encoding = 'utf-8' 
        
        if res.status_code != 200:
            yield f"🚨 שגיאה בשרת גוגל: {res.status_code} - {res.text}"
            return
            
        for line in res.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    data_str = decoded_line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk_json = json.loads(data_str)
                        if 'candidates' in chunk_json and len(chunk_json['candidates']) > 0:
                            content = chunk_json['candidates'][0].get('content', {})
                            parts = content.get('parts', [])
                            if parts:
                                text_chunk = parts[0].get('text', '')
                                yield text_chunk
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield f"🚨 שגיאת רשת הזרמה: {e}"
