import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- 1. אתחול ועיצוב ---
st.set_page_config(page_title="Nexus OS | 2026 Core", layout="wide", initial_sidebar_state="collapsed")
init_db()

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {}

t = {
    "עברית": {"dash": "דאשבורד", "tutor": "AI Tutor 🤖", "hist": "היסטוריה", "set": "הגדרות", "avg": "ממוצע", "sub": "מקצוע", "ask": "שאל את Nexus AI..."},
    "English": {"dash": "Dashboard", "tutor": "AI Tutor 🤖", "hist": "History", "set": "Settings", "avg": "Average", "sub": "Subject", "ask": "Ask Nexus AI..."}
}
cur = t[st.session_state.lang]

st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at top, #0f2027, #203a43, #2c5364) !important; color: white; }
    div[data-testid="stMetric"] { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D1FF; border-radius: 20px; padding: 20px; backdrop-filter: blur(10px); }
    div[data-testid="stMetricValue"] { color: #00D1FF !important; font-weight: 900 !important; font-size: 3.5rem !important; }
    .stButton>button { background: linear-gradient(90deg, #00D1FF, #007BFF); color: white; border-radius: 25px; border:none; font-weight:bold; width: 100%; }
    input, select, textarea { background: white !important; color: black !important; border-radius: 10px !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

if st.session_state.lang == "עברית":
    st.markdown("<style>[data-testid='stChatMessageContent'] * { direction: rtl; text-align: right; } [data-testid='stChatInput'] textarea { direction: rtl; text-align: right; }</style>", unsafe_allow_html=True)

# ברכה
h = datetime.datetime.now().hour
greet = "בוקר טוב" if 5<=h<12 else "צהריים טובים" if 12<=h<17 else "ערב טוב" if 17<=h<21 else "לילה טוב"
st.markdown(f"<h1 style='text-align:center; color:#00D1FF; margin:0;'>NEXUS OS</h1><p style='text-align:center;'>{greet}, Mendi 🎓</p>", unsafe_allow_html=True)

# תפריט אופקי
sel = option_menu(None, [cur["dash"], cur["tutor"], cur["hist"], cur["set"]], 
    icons=["grid-fill", "cpu-fill", "clock-history", "gear-fill"], orientation="horizontal",
    styles={"container": {"background-color": "rgba(0,0,0,0.3)"}, "nav-link-selected": {"background-color": "rgba(0, 209, 255, 0.2)", "color": "#00D1FF"}})

df = get_all_grades()

if sel == cur["dash"]:
    c1, c2, c3 = st.columns(3)
    c1.metric(cur["avg"], f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    c2.metric("Total Records", len(df))
    c3.metric("Engine", "Active 🟢")
    
    l, r = st.columns([1, 1.2])
    with l:
        with st.form("gf", clear_on_submit=True):
            sub = st.selectbox(cur["sub"], ["מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"])
            top = st.text_input("Topic")
            grd = st.number_input("Grade", 0, 100, 90)
            if st.form_submit_button("Save"): save_grade(sub, top, grd); st.rerun()
        
        up = st.file_uploader("Upload Material", type=["pdf", "docx", "png", "jpg", "jpeg"])
        if up and st.button("🧠 Upload to AI Brain"):
            st.session_state.file_contexts[sub] = extract_text_from_file(up)
            st.success("Knowledge Loaded!")
    with r:
        if not df.empty:
            fig = px.line(df.sort_values('date'), x='date', y='grade', color='subject', markers=True)
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)

elif sel == cur["tutor"]:
    sub_sel = st.selectbox(cur["sub"], ["General", "מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"])
    chat = st.container(height=450)
    for m in st.session_state.chat_history:
        with chat.chat_message(m["role"]): st.markdown(m["content"])
    
    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with chat.chat_message("user"): st.markdown(p)
        with chat.chat_message("assistant"):
            ctx = st.session_state.file_contexts.get(sub_sel, "")
            res = st.write_stream(get_ai_response_stream(sub_sel, p, ctx))
        st.session_state.chat_history.append({"role": "assistant", "content": res})

elif sel == cur["hist"]:
    st.dataframe(df.sort_values('date', ascending=False), use_container_width=True)

elif sel == cur["set"]:
    if st.button("🗑️ Clear Chat"): st.session_state.chat_history = []; st.rerun()
    if st.button("🚨 Purge Database"): clear_db(); st.rerun()
    if st.button("🌐 Switch Language"): 
        st.session_state.lang = "English" if st.session_state.lang == "עברית" else "עברית"
        st.rerun()
