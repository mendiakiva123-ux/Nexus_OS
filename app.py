import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
import os
import datetime
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import process_file_to_db, get_ai_response_stream

# --- 1. הגדרות מערכת (מהירות מקסימלית) ---
st.set_page_config(page_title="Nexus OS | Elite", layout="wide")
init_db()

# יצירת תיקייה להעלאות אם חסרה
if not os.path.exists("ai_data/uploads"):
    os.makedirs("ai_data/uploads", exist_ok=True)

# --- 2. ניהול משתמשים ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

USER_REGISTRY = {"mendi2026": "Mendi Akiva"} # הוסף כאן את שאר ה-10

# --- 3. לוגיקת התחברות ---
def login_screen():
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), 
            url('https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=1920&q=80') !important;
            background-size: cover;
        }
        .login-box {
            background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; 
            border: 2px solid #00D1FF; text-align: center; backdrop-filter: blur(10px);
        }
        .stTextInput input { color: black !important; background-color: white !important; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div class='login-box'><h1>NEXUS OS</h1>", unsafe_allow_html=True)
        code = st.text_input("Access Code", type="password", label_visibility="collapsed")
        if st.button("Unlock", use_container_width=True):
            if code in USER_REGISTRY:
                st.session_state.logged_in = True
                st.session_state.user_name = USER_REGISTRY[code]
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

if not st.session_state.logged_in:
    login_screen()
    st.stop()

# --- 4. עיצוב וצבעים (שחור מודגש!) ---
st.markdown("""
    <style>
    /* ביטול אנימציות לביצועים */
    * { transition: none !important; animation: none !important; }

    /* טקסט שחור בתיבות ובבחירות - כולל הרשימה שנפתחת */
    input, select, textarea, .stSelectbox div, div[data-baseweb="select"], .stNumberInput input {
        color: black !important; background-color: white !important; font-weight: 900 !important;
    }
    div[role="listbox"] ul li { color: black !important; font-weight: bold !important; }

    /* חיצים שחורים על רקע לבן */
    button[data-testid="sidebar-button"] svg { 
        fill: black !important; color: black !important; 
        background-color: white !important; border-radius: 4px;
    }

    /* העלאת קבצים - שחור */
    div[data-testid="stFileUploader"] section { background-color: white !important; color: black !important; }
    div[data-testid="stFileUploader"] label, div[data-testid="stFileUploader"] p { color: black !important; }

    /* רקע וטקסט כללי */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url('https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=1920&q=80') !important;
        background-size: cover; background-attachment: fixed;
    }
    h1, h2, h3, h4, p, label, span { color: white !important; text-shadow: 1px 1px 2px black; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. סיידבר ---
with st.sidebar:
    st.markdown(f"<h3 style='text-align: center; color: #00D1FF;'>{st.session_state.user_name}</h3>", unsafe_allow_html=True)
    # בחירת שפה
    lang = st.radio("Language", ["עברית", "English"], horizontal=True)
    st.divider()
    selected = option_menu(None, ["Dashboard", "AI Tutor", "Settings"], 
                           icons=["house", "robot", "gear"], default_index=0)

# --- 6. תוכן (דוגמה לדאשבורד) ---
if selected == "Dashboard":
    st.title("🚀 Status: Active")
    df = get_all_grades()
    c1, c2 = st.columns(2)
    c1.metric("Average", f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    c2.metric("Total", len(df))

    # טופס עם תיבות לבנות וטקסט שחור
    with st.form("add_grade"):
        s = st.selectbox("Subject", ["Math", "Python", "Data"])
        g = st.number_input("Grade", 0, 100, 90)
        if st.form_submit_button("Save"):
            save_grade(s, "Exam", g)
            st.rerun()

elif selected == "AI Tutor":
    if prompt := st.chat_input("Ask me..."):
        with st.chat_message("user"): st.write(prompt)
        with st.chat_message("assistant"):
            try:
                # בדיקה אם המפתח קיים לפני הפעלה
                if "GOOGLE_API_KEY" not in st.secrets:
                    st.error("Missing API Key in secrets.toml!")
                else:
                    response_placeholder = st.empty()
                    full_res = ""
                    for chunk in get_ai_response_stream("general", prompt):
                        full_res += (chunk.content if hasattr(chunk, 'content') else str(chunk))
                        response_placeholder.markdown(full_res + "▌")
                    response_placeholder.markdown(full_res)
            except Exception as e:
                st.error(f"Error: {e}")
