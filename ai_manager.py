import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
from PIL import Image

# פונקציית סריקה
def extract_text_from_file(uploaded_file):
    text = ""
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            # שימוש במודל הכי פשוט לסריקה
            model = genai.GenerativeModel('gemini-1.5-flash')
            img = Image.open(uploaded_file)
            response = model.generate_content(["Extract all text from this image.", img])
            text = response.text
    except Exception as e:
        return f"🚨 שגיאה בסריקה: {e}"
    return text

# מנוע הבוט - בודק מודלים זמינים במקרה של שגיאה
def get_ai_response_stream(subject, prompt, file_context=""):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        # אנחנו ננסה להשתמש בשם הכי בסיסי
        model_name = 'gemini-1.5-flash'
        model = genai.GenerativeModel(model_name)
        
        full_prompt = f"Subject: {subject}. Respond in Hebrew. Question: {prompt}"
        if file_context:
            full_prompt += f"\nContext: {file_context[:5000]}"

        response = model.generate_content(full_prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        # כאן הקסם: אם יש שגיאה, אנחנו מדפיסים מה המפתח שלך כן רואה
        error_msg = str(e)
        if "404" in error_msg:
            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                models_list = ", ".join(available_models)
                yield f"🚨 שגיאת 404. המודלים שזמינים למפתח שלך הם: {models_list}. נסה לשלוח הודעה שוב, המערכת תנסה להתאים את עצמה."
            except:
                yield f"🚨 שגיאת API: {error_msg}. וודא שהמפתח ב-Secrets הועתק נכון ללא רווחים."
        else:
            yield f"🚨 שגיאה: {error_msg}"
