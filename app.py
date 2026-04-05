import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- Core Setup ---
st.set_page_config(page_title="Nexus OS | Core", layout="wide", initial_sidebar_state="expanded")
init_db()

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_context' not in st.session_state: st.session_state.file_context = ""

# --- מערכת תרגום טוטאלית ---
t = {
    "עברית": {
        "title": "NEXUS CORE", "welcome": "שלום, מנדי", "dash": "מרכז שליטה", "tutor": "בינה מלאכותית",
        "hist": "ארכיון ציונים", "set": "מערכת", "avg": "ממוצע אקדמי", "total": "רשומות", "status": "סטטוס",
        "add": "📝 הזנת נתונים", "sub": "מקצוע", "top": "נושא", "grd": "ציון", "save": "סנכרן נתונים",
        "up": "📁 סריקה ניורונית", "learn": "🧠 למד", "ask": "הזן שאילתה...", "purge": "נקה צ'אט",
        "reset": "🚨 איפוס מסד נתונים", "analyst": "פרוטוקול אנליסט 📊",
        "subjects": ["כללי", "מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"]
    },
    "English": {
        "title": "NEXUS CORE", "welcome": "Welcome, Mendi", "dash": "Command Center", "tutor": "Neural Tutor",
        "hist": "Grade Archive", "set": "System", "avg": "Academic Avg", "total": "Records", "status": "Status",
        "add": "📝 Data Input", "sub": "Subject", "top": "Topic", "grd": "Grade", "save": "Sync Data",
        "up": "📁 Neural Scan", "learn": "🧠 Ingest", "ask": "Input query...", "purge": "Purge Chat",
        "reset": "🚨 Reset DB", "analyst": "Analyst Protocol 📊",
        "subjects": ["General", "Math", "Physics", "Computer Science", "Other"]
    }
}
cur = t[st.session_state.lang]

# --- CSS Cyber-Elite ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&display=swap');
    [data-testid="stAppViewContainer"] {{ background: linear-gradient(225deg, #050505 0%, #001219 50%, #002233 100%) !important; color: white; }}
    div[data-testid="stMetric"] {{ background: rgba(255, 255, 255, 0.03) !important; border: 1px solid rgba(0, 209, 255, 0.3) !important; border-radius: 20px; padding: 25px; backdrop-filter: blur(20px); }}
    div[data-testid="stMetricValue"] {{ color: #00D1FF !important; font-family: 'Orbitron', sans-serif; text-shadow: 0 0 10px #00D1FF; }}
    .stButton>button {{ background: transparent !important; color: #00D1FF !important; border: 2px solid #00D1FF !important; border-radius: 12px; font-weight: 900; width: 100%; transition: 0.3s; }}
    .stButton>button:hover {{ background: #00D1FF !important; color: #000 !important; box-shadow: 0 0 25px #00D1FF; }}
    input, select, textarea {{ background: white !important; color: black !important; font-weight: bold !important; border-radius: 10px !important; }}
    h1 {{ font-family: 'Orbitron', sans-serif; background: linear-gradient(90deg, #00D1FF, #BC13FE); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }}
    </style>
    """, unsafe_allow_html=True)

if st.session_state.lang == "עברית":
    st.markdown("<style>[data-testid='stChatMessageContent'] * { direction: rtl; text-align: right; } [data-testid='stChatInput'] textarea { direction: rtl; text-align: right; }</style>", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"<h2>{cur['title']}</h2>", unsafe_allow_html=True)
    lang_choice = st.radio("", ["עברית", "English"], index=0 if st.session_state.lang == "עברית" else 1, horizontal=True)
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice; st.rerun()
    st.divider()
    
    analyst_on = st.toggle(cur["analyst"])
    
    st.markdown(f"### {cur['up']}")
    up = st.file_uploader("", type=["pdf", "docx", "png", "jpg", "jpeg"])
    if up and st.button(cur["learn"]):
        with st.spinner("Processing..."):
            st.session_state.file_context = extract_text_from_file(up)
            st.success("LOADED")

    selected = option_menu(None, [cur["dash"], cur["tutor"], cur["hist"], cur["set"]],
                           icons=["grid-fill", "robot", "clock-history", "gear-fill"], default_index=0)
    if st.button(cur["purge"]): st.session_state.chat_history = []; st.rerun()

df = get_all_grades()

# --- Pages ---
if selected == cur["dash"]:
    st.markdown(f"<h1>{cur['dash']}</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    avg_v = df['grade'].mean() if not df.empty else 0.0
    c1.metric(cur["avg"], f"{avg_v:.1f}")
    c2.metric(cur["total"], len(df))
    c3.metric(cur["status"], "OPTIMAL")
    
    l, r = st.columns([1, 1.2])
    with l:
        st.markdown(f"### {cur['add']}")
        with st.form("gf", clear_on_submit=True):
            sub = st.selectbox(cur["sub"], cur["subjects"][1:])
            tp = st.text_input(cur["top"])
            grd = st.number_input(cur["grd"], 0, 100, 90)
            if st.form_submit_button(cur["save"]): save_grade(sub, tp, grd); st.rerun()

    with r:
        if not df.empty:
            fig = px.line(df.sort_values('date'), x='date', y='grade', color='subject', markers=True, template="plotly_dark")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#00D1FF")
            st.plotly_chart(fig, use_container_width=True)

elif selected == cur["tutor"]:
    st.markdown(f"<h1>{cur['tutor']}</h1>", unsafe_allow_html=True)
    sub_sel = st.selectbox(cur["sub"], cur["subjects"])
    
    chat_box = st.container(height=500)
    for m in st.session_state.chat_history:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with chat_box.chat_message("user"): st.markdown(p)
        with chat_box.chat_message("assistant"):
            full_res = st.write_stream(get_ai_response_stream(sub_sel, p, st.session_state.file_context, st.session_state.lang, analyst_on))
        st.session_state.chat_history.append({"role": "assistant", "content": full_res})

elif selected == cur["hist"]:
    st.markdown(f"<h1>{cur['hist']}</h1>", unsafe_allow_html=True)
    st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

elif selected == cur["set"]:
    st.markdown(f"<h1>{cur['set']}</h1>", unsafe_allow_html=True)
    if st.button(cur["reset"]): clear_db(); st.rerun()
