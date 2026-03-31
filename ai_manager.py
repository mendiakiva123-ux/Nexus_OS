def get_ai_response_stream(subject, prompt, file_context=""):
    api_key = st.secrets["GOOGLE_API_KEY"].strip() # ניקוי רווחים אוטומטי
    
    # כתובת ישירה לגרסה v1 היציבה - מונע שגיאות 404
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": f"Subject: {subject}. Respond in Hebrew. Context: {file_context[:5000]}. Question: {prompt}"}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        
        if response.status_code == 404:
            # אם v1 לא עובד, ננסה v1beta כגיבוי אחרון
            url_beta = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}"
            response = requests.post(url_beta, headers=headers, json=payload, stream=True)

        if response.status_code != 200:
            yield f"🚨 שגיאת שרת: {response.status_code}. וודא שהמפתח ב-Secrets תקין."
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
