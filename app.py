import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream

# --- 1. הגדרות מערכת ---
st.set_page_config(page_title="Nexus OS | Elite Command Center", layout="wide")
init_db()

# --- 2. ניהול 10 משתמשים ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_name = ""

USER_REGISTRY = {
    "mendi2026": "Mendi Akiva",
    "nexus02": "User Two", "nexus03": "User Three", "nexus04": "User Four",
    "nexus05": "User Five", "nexus06": "User Six", "nexus07": "User Seven",
    "nexus08": "User Eight", "nexus09": "User Nine", "nexus10": "User Ten"
}

# --- 3. עיצוב חסין (טקסט שחור קריא וחיצים בולטים) ---
st.markdown("""
    <style>
    /* ביטול אנימציות למהירות */
    * { transition: none !important; animation: none !important; }

    /* רקע ספרייה יוקרתי */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)), 
        url('https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=1920&q=80') !important;
        background-size: cover !important; background-attachment: fixed !important;
    }

    /* תיבות טקסט: רקע לבן, טקסט שחור מודגש 900 */
    input, select, textarea, [data-baseweb="select"], .stNumberInput input {
        color: black !important; background-color: white !important; font-weight: 900 !important;
    }
    
    /* טקסט שחור ברשימות נפתחות */
    div[role="listbox"] ul li, div[data-baseweb="popover"] span {
        color: black !important; font-weight: bold !important;
    }

    /* חיצים שחורים בולטים על רקע לבן */
    button[data-testid="sidebar-button"] svg { 
        fill: black !important; color: black !important; 
        background-color: white !important; border-radius: 4px; padding: 2px;
    }

    /* כותרות וטקסט לבן עם צל */
    h1, h2, h3, h4, p, label, span { color: white !important; text-shadow: 2px 2px 4px black; }
    
    /* תיבת העלאת קבצים - שחור על לבן */
    div[data-testid="stFileUploader"] section { background-color: white !important; color: black !important; }
    div[data-testid="stFileUploader"] p, div[data-testid="stFileUploader"] span { color: black !important; }
    
    /* עיצוב המדדים (Metrics) */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.1) !important; border: 2px solid #00D1FF !important; border-radius: 15px;
    }
    div[data-testid="stMetricValue"] { color: #00D1FF !important; font-weight: 800 !important; }

    /* סיידבר כהה */
    section[data-testid="stSidebar"] { background-color: #0f172a !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. מסך התחברות ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div style='text-align:center; margin-top:100px;'><h1>NEXUS OS</h1>", unsafe_allow_html=True)
        code = st.text_input("Access Code", type="password")
        if st.button("Unlock System", use_container_width=True):
            if code in USER_REGISTRY:
                st.session_state.logged_in = True
                st.session_state.user_name = USER_REGISTRY[code]
                st.rerun()
            else:
                st.error("❌ Access Denied.")
    st.stop()

# --- 5. תפריט ---
with st.sidebar:
    st.markdown(f"<h3 style='text-align:center; color:#00D1FF;'>{st.session_state.user_name}</h3>", unsafe_allow_html=True)
    lang_choice = st.radio("Language / שפה", ["עברית", "English"], horizontal=True)
    st.divider()
    
    selected = option_menu(None, ["Dashboard", "AI Tutor", "History", "Settings"], 
                           icons=["house", "robot", "clock", "gear"], default_index=0,
                           styles={
                                "container": {"background-color": "#0f172a"},
                                "nav-link": {"color": "white", "text-align": "left"},
                                "nav-link-selected": {"background-color": "#00D1FF", "color": "black"}
                           })
    
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

df = get_all_grades()

# --- 6. לוגיקת דפים ---
if selected == "Dashboard":
    st.title("🚀 Command Center")
    
    c1, c2 = st.columns(2)
    c1.metric("Average / ממוצע", f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    c2.metric("Total Entries / משימות", len(df))
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Add Grade / הוסף ציון")
        with st.form("grade_form", clear_on_submit=True):
            sub = st.selectbox("Subject", ["Python", "Data Analyst", "SQL", "מתמטיקה", "אחר"])
            tp = st.text_input("Topic / נושא")
            grd = st.number_input("Grade / ציון", 0, 100, 90)
            if st.form_submit_button("Save"):
                save_grade(sub, tp, grd)
                st.rerun()
                
    with col2:
        st.subheader("Quick Upload / העלאה")
        st.file_uploader("Upload material", type=["pdf", "docx"])

elif selected == "AI Tutor":
    st.title("🤖 Nexus AI Assistant")
    sub_choice = st.selectbox("Subject Context", ["General", "Python", "Data Analyst"])
    
    if prompt := st.chat_input("Ask me anything..."):
        with st.chat_message("user"): st.write(prompt)
        with st.chat_message("assistant"):
            try:
                res_box = st.empty()
                full_res = ""
                # הקריאה לבוט החסין שלנו
                for chunk in get_ai_response_stream(sub_choice, prompt):
                    full_res += chunk.text
                    res_box.markdown(full_res + "▌")
                res_box.markdown(full_res)
            except Exception as e:
                st.error(f"שגיאת מערכת חמורה: {e}")

elif selected == "History":
    st.title("📜 Grade History")
    st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

elif selected == "Settings":
    st.title("⚙️ Settings")
    if st.button("🚨 Clear All Database Data"):
        clear_db()
        st.rerun()
