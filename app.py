import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- Setup ---
if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_context' not in st.session_state: st.session_state.file_context = ""

T = {
    "עברית": {
        "title": "NEXUS CORE", "m1": "מרכז בקרה", "m2": "בינה מלאכותית", "m3": "מאגר נתונים", "m4": "מערכת",
        "avg": "ממוצע אקדמי", "count": "רשומות", "sub": "מקצוע", "grd": "ציון", "sync": "שלח לענן",
        "scan": "🛰️ סריקה ניורונית", "process": "עבד נתונים", "analyst": "מצב דאטה אנליסט 📊",
        "ask": "שאל את המערכת...", "clear": "נקה צ'אט", "reset": "🚨 איפוס", "subjects": ["כללי", "מתמטיקה", "מדעי המחשב", "אחר"]
    },
    "English": {
        "title": "NEXUS CORE", "m1": "Dashboard", "m2": "Nexus AI", "m3": "Vault", "m4": "System",
        "avg": "Avg Grade", "count": "Records", "sub": "Subject", "grd": "Grade", "sync": "Sync Data",
        "scan": "🛰️ Neural Scan", "process": "Process", "analyst": "Analyst Mode 📊",
        "ask": "Ask AI...", "clear": "Clear", "reset": "🚨 Reset", "subjects": ["General", "Math", "CS", "Other"]
    }
}
cur = T[st.session_state.lang]
st.set_page_config(page_title=cur["title"], layout="wide")

# --- Design & RTL ---
rtl = f"""
    <style>
    .stApp {{ background: #050a0f; color: #00f2fe; }}
    div[data-testid="stMetric"] {{ background: rgba(0, 242, 254, 0.05); border: 1px solid #00f2fe; border-radius: 15px; }}
    {"[data-testid='stSidebar'], .main { direction: rtl; } [data-testid='stChatMessageContent'] { direction: rtl; text-align: right; }" if st.session_state.lang == "עברית" else ""}
    </style>
"""
st.markdown(rtl, unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"## {cur['title']}")
    new_lang = st.radio("שפה", ["עברית", "English"], horizontal=True)
    if new_lang != st.session_state.lang: st.session_state.lang = new_lang; st.rerun()
    st.divider()
    analyst_on = st.toggle(cur["analyst"])
    up = st.file_uploader(cur["scan"], type=['pdf', 'docx', 'jpg', 'png'])
    if up and st.button(cur["process"]):
        st.session_state.file_context = extract_text_from_file(up); st.success("OK")
    menu = option_menu(None, [cur["m1"], cur["m2"], cur["m3"], cur["m4"]], icons=["grid", "robot", "database", "gear"])

df = get_all_grades()

if menu == cur["m1"]:
    st.markdown(f"<h1>{cur['m1']}</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric(cur["avg"], f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    c2.metric(cur["count"], len(df))
    col1, col2 = st.columns(2)
    s = col1.selectbox(cur["sub"], cur["subjects"])
    g = col2.number_input(cur["grd"], 0, 100, 90)
    if st.button(cur["sync"]): save_grade(s, "", g); st.rerun()

elif menu == cur["m2"]:
    st.markdown(f"<h1>{cur['m2']}</h1>", unsafe_allow_html=True)
    sel_sub = st.selectbox(cur["sub"], cur["subjects"], index=0)
    if st.button(cur["clear"]): st.session_state.chat_history = []; st.rerun()
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        with st.chat_message("assistant"):
            res = st.write_stream(get_ai_response_stream(sel_sub, p, st.session_state.file_context, st.session_state.lang, analyst_on))
        st.session_state.chat_history.append({"role": "assistant", "content": res})

elif menu == cur["m3"]:
    st.dataframe(df, use_container_width=True)
elif menu == cur["m4"]:
    if st.button(cur["reset"]): clear_db(); st.rerun()
