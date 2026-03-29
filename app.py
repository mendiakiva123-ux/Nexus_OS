import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import os
from database_manager import init_db, save_grade, get_all_grades
from ai_manager import process_file_to_db, get_ai_response_stream

# --- 1. הגדרות מהירות ---
st.set_page_config(page_title="Nexus OS | Elite", layout="wide")

# --- 2. עיצוב CSS (טקסט שחור מוחלט + חיצים שחורים) ---
st.markdown("""
    <style>
    /* מהירות: ביטול אנימציות */
    * { transition: none !important; animation: none !important; }

    /* רקע ספרייה יוקרתי */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url('https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=1920&q=80') !important;
        background-size: cover;
    }

    /* תיבות טקסט: רקע לבן, טקסט שחור מודגש */
    input, select, textarea, .stSelectbox div, .stNumberInput input {
        color: black !important; 
        background-color: white !important; 
        font-weight: 900 !important;
        border: 2px solid #00D1FF !important;
    }
    
    /* רשימת בחירה (Dropdown) - טקסט שחור */
    div[role="listbox"] ul li { color: black !important; font-weight: bold !important; }

    /* חיצים שחורים על רקע לבן בולט */
    button[data-testid="sidebar-button"] svg { 
        fill: black !important; color: black !important; 
        background-color: white !important; border-radius: 4px; padding: 2px;
    }

    /* כותרות וטקסט כללי בלבן */
    h1, h2, h3, label, p, span { color: white !important; text-shadow: 1px 1px 2px black; }
    
    /* תיבת העלאת קבצים - שחור על לבן */
    div[data-testid="stFileUploader"] section { background-color: white !important; color: black !important; }
    div[data-testid="stFileUploader"] p, div[data-testid="stFileUploader"] span { color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ניהול כניסה ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div style='text-align:center; margin-top:100px;'><h1>NEXUS OS</h1>", unsafe_allow_html=True)
        code = st.text_input("Access Code", type="password")
        if st.button("Unlock System", use_container_width=True):
            if code == "mendi2026": # הקוד שלך
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- 4. תפריט וסיידבר ---
with st.sidebar:
    selected = option_menu("Nexus Menu", ["Dashboard", "AI Tutor", "Settings"], 
                           icons=["house", "robot", "gear"], default_index=0)

# --- 5. תוכן הדפים ---
if selected == "Dashboard":
    st.title("🚀 Dashboard Active")
    df = get_all_grades()
    st.metric("Average", f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    
    with st.form("quick_add"):
        sub = st.selectbox("Subject", ["Math", "Python", "SQL"])
        grd = st.number_input("Grade", 0, 100, 90)
        if st.form_submit_button("Save to Vault"):
            from database_manager import save_grade
            save_grade(sub, "Quick Entry", grd)
            st.toast("Saved!")
            st.rerun()

elif selected == "AI Tutor":
    st.title("🤖 Nexus AI Assistant")
    if prompt := st.chat_input("Ask me anything..."):
        with st.chat_message("user"): st.write(prompt)
        with st.chat_message("assistant"):
            try:
                res_box = st.empty()
                full_res = ""
                # וידאו שקריאה ל-AI עובדת עם המפתח מה-secrets
                for chunk in get_ai_response_stream("general", prompt):
                    full_res += (chunk.content if hasattr(chunk, 'content') else str(chunk))
                    res_box.markdown(full_res + "▌")
                res_box.markdown(full_res)
            except Exception as e:
                st.error(f"AI Error: {e}")
