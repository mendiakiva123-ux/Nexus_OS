import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from database_manager import init_db, save_grade, get_all_grades
from ai_manager import get_ai_response_stream

# --- הגדרות מהירות ---
st.set_page_config(page_title="Nexus OS | Elite", layout="wide")
init_db()

# --- עיצוב CSS (שחור מוחלט על לבן) ---
st.markdown("""
    <style>
    /* ביטול אנימציות למהירות */
    * { transition: none !important; animation: none !important; }

    /* רקע ספרייה יוקרתי */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
        url('https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=1920&q=80') !important;
        background-size: cover !important; background-attachment: fixed !important;
    }

    /* תיבות טקסט ובחירה: רקע לבן, טקסט שחור מודגש */
    input, select, textarea, [data-baseweb="select"], .stNumberInput input {
        color: black !important; background-color: white !important; font-weight: 900 !important;
    }
    
    /* טקסט שחור ברשימות נפתחות */
    div[role="listbox"] ul li, div[data-baseweb="popover"] span {
        color: black !important; font-weight: bold !important;
    }

    /* חיצים שחורים על רקע לבן בולט */
    button[data-testid="sidebar-button"] svg { 
        fill: black !important; color: black !important; 
        background-color: white !important; border-radius: 5px; padding: 2px;
    }

    /* כותרות וטקסט בלבן */
    h1, h2, h3, label, p, span { color: white !important; text-shadow: 2px 2px 4px black; }
    
    /* העלאת קבצים - שחור */
    div[data-testid="stFileUploader"] section { background-color: white !important; color: black !important; }
    div[data-testid="stFileUploader"] p, div[data-testid="stFileUploader"] span { color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ניהול כניסה ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div style='text-align:center; margin-top:100px;'><h1>NEXUS OS</h1>", unsafe_allow_html=True)
        code = st.text_input("Access Code", type="password")
        if st.button("Unlock", use_container_width=True):
            if code == "mendi2026":
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- תפריט ---
with st.sidebar:
    selected = option_menu("Nexus Menu", ["Dashboard", "AI Tutor", "Settings"], 
                           icons=["house", "robot", "gear"], default_index=0)

df = get_all_grades()

if selected == "Dashboard":
    st.title("🚀 Command Center")
    c1, c2 = st.columns(2)
    c1.metric("Average Score", f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    c2.metric("Entries", len(df))
    
    with st.form("add_grade"):
        sub = st.selectbox("Subject", ["Python", "Data Analyst", "SQL"])
        grd = st.number_input("Grade", 0, 100, 90)
        if st.form_submit_button("Save"):
            save_grade(sub, "Quick Entry", grd)
            st.rerun()

elif selected == "AI Tutor":
    st.title("🤖 Nexus AI Assistant")
    if prompt := st.chat_input("Ask me anything..."):
        with st.chat_message("user"): st.write(prompt)
        with st.chat_message("assistant"):
            try:
                res_box = st.empty()
                full_res = ""
                # קריאה למנהל ה-AI החדש
                for chunk in get_ai_response_stream("General", prompt):
                    full_res += chunk.text
                    res_box.markdown(full_res + "▌")
                res_box.markdown(full_res)
            except Exception as e:
                st.error(f"שגיאת חיבור: {e}")
