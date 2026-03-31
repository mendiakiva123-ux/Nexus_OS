import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- הגדרות ליבה ---
st.set_page_config(page_title="Nexus OS | Core", layout="wide", initial_sidebar_state="expanded")
init_db()

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {}

# --- מילון תרגום מלא ---
t = {
    "עברית": {
        "dash": "מרכז שליטה", "tutor": "Nexus AI", "hist": "ארכיון", "set": "מערכת",
        "avg": "ממוצע אקדמי", "total": "סה\"כ רשומות", "status": "מצב ליבה", "opt": "אופטימלי",
        "add_title": "📝 הזנת נתונים", "sub": "מקצוע", "top": "נושא", "grd": "ציון", "sync": "סנכרן נתונים",
        "up_title": "🧠 סריקת חומר", "ingest": "טען למוח ה-AI", "ask": "הזן שאילתה למערכת...",
        "purge_chat": "🗑️ נקה צ'אט", "purge_db": "🚨 איפוס מסד נתונים", "subjects": ["כללי", "מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"]
    },
    "English": {
        "dash": "Command Center", "tutor": "Nexus AI", "hist": "Archive", "set": "System",
        "avg": "Academic Avg", "total": "Total Records", "status": "Core Status", "opt": "Optimal",
        "add_title": "📝 Data Input", "sub": "Subject", "top": "Topic", "grd": "Grade", "sync": "Sync Data",
        "up_title": "🧠 Neural Scanning", "ingest": "Ingest to AI", "ask": "Input query...",
        "purge_chat": "🗑️ Purge Chat", "purge_db": "🚨 Reset DB", "subjects": ["General", "Math", "Physics", "Computer Science", "Other"]
    }
}
cur = t[st.session_state.lang]

# --- CSS (Cyber-Elite UI) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&display=swap');
    [data-testid="stAppViewContainer"] {{ background: linear-gradient(225deg, #050505 0%, #001219 50%, #002233 100%) !important; color: white; }}
    [data-testid="collapsedControl"] {{ display: none !important; }}
    div[data-testid="stMetric"] {{ background: rgba(255, 255, 255, 0.03) !important; border: 1px solid rgba(0, 209, 255, 0.3) !important; border-radius: 20px; padding: 25px; backdrop-filter: blur(20px); }}
    div[data-testid="stMetricValue"] {{ color: #00D1FF !important; font-family: 'Orbitron', sans-serif; }}
    .stButton>button {{ background: transparent !important; color: #00D1FF !important; border: 2px solid #00D1FF !important; border-radius: 12px; font-weight: 900; width: 100%; }}
    .stButton>button:hover {{ background: #00D1FF !important; color: #000 !important; box-shadow: 0 0 25px #00D1FF; }}
    input, select, textarea {{ background: white !important; color: black !important; font-weight: bold !important; }}
    h1, h2 {{ font-family: 'Orbitron', sans-serif; background: linear-gradient(90deg, #00D1FF, #BC13FE); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }}
    </style>
    """, unsafe_allow_html=True)

if st.session_state.lang == "עברית":
    st.markdown("<style>[data-testid='stChatMessageContent'] * { direction: rtl; text-align: right; } [data-testid='stChatInput'] textarea { direction: rtl; text-align: right; }</style>", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("<h2>NEXUS OS</h2>", unsafe_allow_html=True)
    lang_choice = st.radio("", ["עברית", "English"], index=0 if st.session_state.lang == "עברית" else 1, horizontal=True)
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()
    st.divider()
    selected = option_menu(None, [cur["dash"], cur["tutor"], cur["hist"], cur["set"]],
                           icons=["cpu-fill", "robot", "database-fill", "gear-wide-connected"], default_index=0,
                           styles={"nav-link-selected": {"background-color": "rgba(0, 209, 255, 0.2)", "color": "#00D1FF"}})
    if st.button(cur["purge_chat"]):
        st.session_state.chat_history = []; st.rerun()

df = get_all_grades()

# --- מרכז שליטה ---
if selected == cur["dash"]:
    st.markdown(f"<h1>{cur['dash']}</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    avg_val = df['grade'].mean() if not df.empty else 0.0
    c1.metric(cur["avg"], f"{avg_val:.1f}")
    c2.metric(cur["total"], len(df))
    c3.metric(cur["status"], cur["opt"])
    
    l, r = st.columns([1, 1.2])
    with l:
        st.markdown(f"### {cur['add_title']}")
        with st.form("grade_form", clear_on_submit=True):
            sub = st.selectbox(cur["sub"], cur["subjects"])
            tp = st.text_input(cur["top"])
            grd = st.number_input(cur["grd"], 0, 100, 90)
            if st.form_submit_button(cur["sync"]):
                save_grade(sub, tp, grd); st.rerun()
        
        st.markdown(f"### {cur['up_title']}")
        up = st.file_uploader("", type=["pdf", "docx", "png", "jpg", "jpeg"])
        if up and st.button(cur["ingest"]):
            st.session_state.file_contexts[sub] = extract_text_from_file(up)
            st.success("Knowledge Loaded!")

    with r:
        if not df.empty:
            fig = px.line(df.sort_values('date'), x='date', y='grade', color='subject', markers=True, template="plotly_dark")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#00D1FF")
            st.plotly_chart(fig, use_container_width=True)

# --- Nexus AI ---
elif selected == cur["tutor"]:
    st.markdown(f"<h1>{cur['tutor']}</h1>", unsafe_allow_html=True)
    sub_choice = st.selectbox(cur["sub"], cur["subjects"])
    ctx = st.session_state.file_contexts.get(sub_choice, "")
    
    chat_box = st.container(height=500)
    for m in st.session_state.chat_history:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with chat_box.chat_message("user"): st.markdown(p)
        with chat_box.chat_message("assistant"):
            full_res = st.write_stream(get_ai_response_stream(sub_choice, p, ctx))
        st.session_state.chat_history.append({"role": "assistant", "content": full_res})

# --- ארכיון ---
elif selected == cur["hist"]:
    st.markdown(f"<h1>{cur['hist']}</h1>", unsafe_allow_html=True)
    st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

# --- מערכת ---
elif selected == cur["set"]:
    st.markdown(f"<h1>{cur['set']}</h1>", unsafe_allow_html=True)
    if st.button(cur["purge_db"]):
        clear_db(); st.rerun()
