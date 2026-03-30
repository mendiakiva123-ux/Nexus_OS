import streamlit as st
import google.generativeai as genai

def get_ai_response_stream(subject, prompt):
    # משיכת המפתח מהסודות שהגדרת
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # הגדרת המודל - גרסה 1.5 פלאש (המהירה ביותר)
    # שימוש בשם המודל ללא תחיפיות מיותרות למניעת 404
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    context = f"אתה עוזר אקדמי במערכת Nexus OS. המשתמש שואל לגבי: {subject}."
    full_prompt = f"{context}\n\nהודעת משתמש: {prompt}"
    
    # יצירת תשובה בסטרימינג למהירות מקסימלית
    response = model.generate_content(full_prompt, stream=True)
    return response
