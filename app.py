import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

st.set_page_config(page_title="Nexus OS | Core", layout="wide", initial_sidebar_state="expanded")

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {}

t = {
    "עברית": {
        "title": "NEXUS OS", "dash": "דאשבורד", "tutor": "Nexus AI", "hist": "היסטוריה", "set": "מערכת",
        "avg": "ממוצע ציונים", "total": "רשומות", "add": "📝 הזן נתונים", "sub": "מקצוע", "grd": "ציון",
        "save": "סנכרן נתונים", "up": "📁 טען חומר", "learn": "🧠 למד", "ask": "שאל את ה-AI...", 
        "purge": "נקה צ'אט", "reset": "🚨 איפוס DB", "subjects": ["כללי", "מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"]
    },
    "English": {
        "title": "NEXUS OS", "dash": "Dashboard", "tutor": "Nexus AI", "hist": "History", "set": "Settings",
        "avg": "Avg Grade", "total": "Records", "add": "📝 Data Input", "sub": "Subject", "grd": "Grade",
        "save": "Sync Data", "up": "📁 Upload", "learn": "🧠 Ingest", "ask": "Ask AI...", 
        "purge": "Purge Chat", "reset": "🚨 Reset DB", "subjects": ["General", "Math", "Physics", "Computer Science", "Other"]
    }
}
cur = t[st.session_state.lang]

# עיצוב Cyber-Elite
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&display=swap');
    [data-testid="stAppViewContainer"] {{ background: radial-gradient(circle, #001219, #002233, #050505) !important; color: white; }}
    div[data-testid="stMetric"] {{ background: rgba(0, 209, 255, 0.05) !important; border: 1px solid #00D1FF !important; border-radius: 20px; }}
    div[data-testid="stMetricValue"] {{ color: #00D1FF !important; font-family: 'Orbitron'; }}
    .stButton>button {{ background: #00D1FF !important; color: black !important; font-weight: 900; border-radius: 12px; }}
    h1 {{ font-family: 'Orbitron'; background: linear-gradient(90deg, #00D1FF, #BC13FE); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"<h1>{cur['title']}</h1>", unsafe_allow_html=True)
    lang = st.radio("", ["עברית", "English"], horizontal=True)
    if lang != st.session_state.lang: st.session_state.lang = lang; st.rerun()
    selected = option_menu(None, [cur["dash"], cur["tutor"], cur["hist"], cur["set"]], icons=["grid", "robot", "list", "gear"])

df = get_all_grades()

if selected == cur["dash"]:
    st.markdown(f"<h1>{cur['dash']}</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.metric(cur["avg"], f"{df['grade'].mean():.1f}" if not df.empty else "0")
    with c2:
        st.metric(cur["total"], len(df))
    
    col1, col2 = st.columns(2)
    with col1:
        with st.form("f1"):
            s = st.selectbox(cur["sub"], cur["subjects"])
            g = st.number_input(cur["grd"], 0, 100, 90)
            if st.form_submit_button(cur["save"]): save_grade(s, "", g); st.rerun()
    with col2:
        up = st.file_uploader(cur["up"])
        if up and st.button(cur["learn"]):
            st.session_state.file_contexts[s] = extract_text_from_file(up)
            st.success("Knowledge Ingested!")

elif selected == cur["tutor"]:
    sub = st.selectbox(cur["sub"], cur["subjects"])
    ctx = st.session_state.file_contexts.get(sub, "")
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with st.chat_message("assistant"):
            res = st.write_stream(get_ai_response_stream(sub, p, ctx, st.session_state.lang))
        st.session_state.chat_history.append({"role": "assistant", "content": res})
# (המשך היסטוריה והגדרות פשוטים...)
