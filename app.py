import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
from database_manager import save_grade, get_all_grades, clear_db, save_chat_message, get_persistent_chat_history, clear_chat_history
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- הגדרות ליבה ---
if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_context' not in st.session_state: st.session_state.file_context = ""

T = {
    "עברית": {
        "title": "NEXUS CORE", "m1": "מרכז בקרה", "m2": "בינה מלאכותית", "m3": "מסד נתונים",
        "avg": "ממוצע אקדמי", "count": "רשומות", "sub": "מקצוע", "grd": "ציון", "sync": "סנכרן לענן",
        "analyst": "מצב דאטה אנליסט 📊", "ask": "איך אני יכול לעזור, מנדי?", "clear": "נקה זיכרון",
        "subjects": ["כללי", "מתמטיקה", "מדעי המחשב", "סטטיסטיקה"]
    },
    "English": {
        "title": "NEXUS CORE", "m1": "Dashboard", "m2": "Nexus AI", "m3": "Vault",
        "avg": "Academic Avg", "count": "Total Records", "sub": "Subject", "grd": "Grade", "sync": "Sync Data",
        "analyst": "Analyst Mode 📊", "ask": "Query Nexus...", "clear": "Clear Memory",
        "subjects": ["General", "Math", "CS", "Statistics"]
    }
}
cur = T[st.session_state.lang]

st.set_page_config(page_title=cur["title"], layout="wide")

# --- CSS Cyber-Glass (RTL מלא) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;600;800&family=Orbitron:wght@700&display=swap');
    .stApp {{ background: radial-gradient(circle at top right, #050a12, #000000); color: #e0f7fa; font-family: 'Assistant', sans-serif; }}
    
    /* יישור לימין עבור עברית */
    {" .main, [data-testid='stSidebar'], [data-testid='stChatMessageContent'] { direction: rtl !important; text-align: right !important; } " if st.session_state.lang == "עברית" else ""}

    /* עיצוב זכוכית */
    div[data-testid="stMetric"], .stChatMessage {{
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 242, 254, 0.2) !important;
        border-radius: 15px;
    }}
    
    h1 {{ font-family: 'Orbitron', sans-serif; background: linear-gradient(90deg, #00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }}
    
    .stButton>button {{
        background: linear-gradient(90deg, #00f2fe, #4facfe) !important;
        color: black !important; font-weight: 800; border: none; border-radius: 12px; width: 100%;
    }}
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"<h1>{cur['title']}</h1>", unsafe_allow_html=True)
    lang = st.radio("INTERFACE", ["עברית", "English"], horizontal=True)
    if lang != st.session_state.lang: st.session_state.lang = lang; st.rerun()
    st.divider()
    analyst_on = st.toggle(cur["analyst"], value=True)
    up = st.file_uploader("📁 סריקה ניורונית", type=['pdf', 'docx'])
    if up and st.button("עבד נתונים"):
        st.session_state.file_context = extract_text_from_file(up); st.success("Data Ready")
    menu = option_menu(None, [cur["m1"], cur["m2"], cur["m3"]], icons=["cpu", "robot", "database"])

df = get_all_grades()

# --- עמוד: מרכז בקרה ---
if menu == cur["m1"]:
    st.markdown(f"<h1>{cur['m1']}</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric(cur["avg"], f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    c2.metric(cur["count"], len(df))
    c3.metric("CORE STATUS", "ACTIVE 🟢")
    
    st.divider()
    l, r = st.columns([1, 2])
    with l:
        st.markdown("### 📥 הזנה")
        with st.form("entry"):
            s = st.selectbox(cur["sub"], cur["subjects"])
            g = st.number_input(cur["grd"], 0, 100, 90)
            if st.form_submit_button(cur["sync"]): save_grade(s, "", g); st.rerun()
    with r:
        if not df.empty:
            fig = px.bar(df, x='subject', y='grade', color='grade', template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

# --- עמוד: בינה מלאכותית (עם זיכרון) ---
elif menu == cur["m2"]:
    st.markdown(f"<h1>{'ANALYSIS MODE' if analyst_on else cur['m2']}</h1>", unsafe_allow_html=True)
    
    # טעינת זיכרון ראשונית מסופאבייס
    if not st.session_state.chat_history:
        db_history = get_persistent_chat_history()
        st.session_state.chat_history = [{"role": m["role"], "content": m["content"]} for m in db_history]

    if st.button(cur["clear"]):
        clear_chat_history(); st.session_state.chat_history = []; st.rerun()

    chat_container = st.container(height=500)
    with chat_container:
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]):
                st.markdown(f'<div style="text-align: right; direction: rtl;">{m["content"]}</div>', unsafe_allow_html=True)

    if p := st.chat_input(cur["ask"]):
        # שמירה והצגת הודעת משתמש
        st.session_state.chat_history.append({"role": "user", "content": p})
        save_chat_message("user", p)
        with chat_container.chat_message("user"):
            st.markdown(f'<div style="text-align: right; direction: rtl;">{p}</div>', unsafe_allow_html=True)
        
        # קבלת תשובה מה-AI
        with chat_container.chat_message("assistant"):
            placeholder = st.empty()
            full_res = ""
            for chunk in get_ai_response_stream("General", p, st.session_state.chat_history[:-1], st.session_state.file_context, st.session_state.lang, analyst_on):
                full_res += chunk
                placeholder.markdown(f'<div style="text-align: right; direction: rtl;">{full_res}</div>', unsafe_allow_html=True)
        
        # שמירת תשובת הבוט
        st.session_state.chat_history.append({"role": "assistant", "content": full_res})
        save_chat_message("assistant", full_res)

# --- עמוד: מסד נתונים ---
elif menu == cur["m3"]:
    st.markdown(f"<h1>{cur['m3']}</h1>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)
    if st.button("🚨 מחיקת כל הציונים"): clear_db(); st.rerun()
