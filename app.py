import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from database_manager import init_db, save_grade, get_all_grades
from ai_manager import get_ai_response_stream

# --- 1. הגדרות מערכת ---
st.set_page_config(page_title="Nexus OS | Elite", layout="wide")
init_db()

# --- 2. עיצוב CSS (שחור על לבן + חיצים שחורים) ---
st.markdown("""
    <style>
    /* מהירות: ביטול אנימציות */
    * { transition: none !important; animation: none !important; }

    /* רקע ספרייה יוקרתי */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url('https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=1920&q=80') !important;
        background-size: cover !important; background-attachment: fixed !important;
    }

    /* תיבות טקסט ובחירה: רקע לבן, טקסט שחור מוחלט */
    input, select, textarea, [data-baseweb="select"], .stNumberInput input {
        color: black !important; 
        background-color: white !important; 
        font-weight: 900 !important;
    }
    
    /* טקסט שחור ברשימות נפתחות (Dropdown) */
    div[role="listbox"] ul li, div[data-baseweb="popover"] span {
        color: black !important; font-weight: bold !important;
    }

    /* חיצים שחורים על רקע לבן בולט בסיידבר */
    button[data-testid="sidebar-button"] svg { 
        fill: black !important; color: black !important; 
        background-color: white !important; border-radius: 4px; padding: 2px;
    }

    /* כותרות וטקסט בלבן */
    h1, h2, h3, label, p, span { color: white !important; text-shadow: 2px 2px 4px black; }
    
    /* העלאת קבצים - שחור על לבן */
    div[data-testid="stFileUploader"] section { background-color: white !important; color: black !important; }
    div[data-testid="stFileUploader"] p, div[data-testid="stFileUploader"] span { color: black !important; }
    
    /* סיידבר כהה */
    section[data-testid="stSidebar"] { background-color: #0f172a !important; }
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
            if code == "mendi2026":
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- 4. תפריט ---
with st.sidebar:
    st.markdown(f"<h3 style='text-align:center; color: #00D1FF;'>Hello, Mendi</h3>", unsafe_allow_html=True)
    selected = option_menu(None, ["Dashboard", "AI Tutor", "Settings"], 
                           icons=["house", "robot", "gear"], default_index=0)

df = get_all_grades()

# --- 5. לוגיקת דפים ---
if selected == "Dashboard":
    st.title("🚀 Command Center")
    c1, c2 = st.columns(2)
    c1.metric("Average Score", f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    c2.metric("Total Entries", len(df))
    
    with st.form("add_grade"):
        sub = st.selectbox("Subject", ["Python", "Data Analyst", "SQL", "Math"])
        tp = st.text_input("Topic")
        grd = st.number_input("Grade", 0, 100, 90)
        if st.form_submit_button("Save"):
            save_grade(sub, tp, grd)
            st.rerun()

elif selected == "AI Tutor":
    st.title("🤖 Nexus AI Assistant")
    if prompt := st.chat_input("Ask me anything..."):
        with st.chat_message("user"): st.write(prompt)
        with st.chat_message("assistant"):
            try:
                res_box = st.empty()
                full_res = ""
                # קריאה לסטרימינג
                for chunk in get_ai_response_stream("General", prompt):
                    full_res += chunk.text
                    res_box.markdown(full_res + "▌")
                res_box.markdown(full_res)
            except Exception as e:
                st.error(f"שגיאת חיבור: {e}")

elif selected == "Settings":
    st.title("⚙️ Settings")
    if st.button("🚨 Logout"):
        st.session_state.logged_in = False
        st.rerun()
