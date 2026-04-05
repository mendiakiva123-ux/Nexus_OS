import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
from database_manager import save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- Setup & RTL Logic ---
if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_context' not in st.session_state: st.session_state.file_context = ""

T = {
    "עברית": {
        "title": "NEXUS COMMAND", "m1": "מרכז בקרה", "m2": "בינה מלאכותית", "m3": "מסד נתונים",
        "avg": "ממוצע אקדמי", "count": "רשומות", "status": "סטטוס",
        "sub": "מקצוע", "grd": "ציון", "sync": "סנכרן נתונים", "analyst": "מצב אנליסט 📊",
        "ask": "איך אוכל לעזור, מנדי?", "clear": "נקה צ'אט", "subjects": ["כללי", "מתמטיקה", "מדעי המחשב", "סטטיסטיקה"]
    },
    "English": {
        "title": "NEXUS COMMAND", "m1": "Dashboard", "m2": "Nexus AI", "m3": "Database",
        "avg": "Avg Grade", "count": "Courses", "status": "Status",
        "sub": "Subject", "grd": "Grade", "sync": "Sync Data", "analyst": "Analyst Mode 📊",
        "ask": "How can I help?", "clear": "Clear", "subjects": ["General", "Math", "CS", "Statistics"]
    }
}
cur = T[st.session_state.lang]

st.set_page_config(page_title=cur["title"], layout="wide")

# --- CSS Cyber-Elite (RTL מלא) ---
st.markdown(f"""
    <style>
    .stApp {{ background: #050a0f; color: #00f2fe; }}
    div[data-testid="stMetric"] {{ background: rgba(0, 242, 254, 0.05); border: 2px solid #00f2fe; border-radius: 15px; padding: 20px; }}
    .stButton>button {{ background: #00f2fe !important; color: black !important; font-weight: bold; border-radius: 12px; width: 100%; }}
    {"[data-testid='stSidebar'], .main { direction: rtl; text-align: right; } [data-testid='stChatMessageContent'] { direction: rtl; text-align: right; }" if st.session_state.lang == "עברית" else ""}
    h1 {{ text-align: center; color: #00f2fe; text-shadow: 0 0 10px #00f2fe; }}
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"<h1>{cur['title']}</h1>", unsafe_allow_html=True)
    lang = st.radio("INTERFACE", ["עברית", "English"], horizontal=True)
    if lang != st.session_state.lang: st.session_state.lang = lang; st.rerun()
    st.divider()
    analyst_on = st.toggle(cur["analyst"])
    st.markdown("### 📁 סריקה ניורונית")
    up = st.file_uploader("", type=['pdf', 'docx'])
    if up and st.button("עבד נתונים"):
        st.session_state.file_context = extract_text_from_file(up); st.success("Data Ingested")
    menu = option_menu(None, [cur["m1"], cur["m2"], cur["m3"]], icons=["cpu", "robot", "database"])

df = get_all_grades()

if menu == cur["m1"]:
    st.markdown(f"<h1>{cur['m1']}</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric(cur["avg"], f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    c2.metric(cur["count"], len(df))
    c3.metric("SYSTEM", "STABLE")
    
    st.divider()
    col_l, col_r = st.columns([1, 2])
    with col_l:
        st.markdown("### 📝 הזנה מהירה")
        with st.form("entry"):
            s = st.selectbox(cur["sub"], cur["subjects"])
            g = st.number_input(cur["grd"], 0, 100, 90)
            if st.form_submit_button(cur["sync"]):
                save_grade(s, "", g); st.rerun()
    with col_r:
        if not df.empty:
            fig = px.bar(df, x='subject', y='grade', color='subject', template="plotly_dark", title="ניתוח התפלגות ציונים")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

elif menu == cur["m2"]:
    st.markdown(f"<h1>{cur['m2']}</h1>", unsafe_allow_html=True)
    chat_sub = st.selectbox(cur["sub"], cur["subjects"], index=0)
    if st.button(cur["clear"]): st.session_state.chat_history = []; st.rerun()
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        with st.chat_message("assistant"):
            res = st.write_stream(get_ai_response_stream(chat_sub, p, st.session_state.file_context, st.session_state.lang, analyst_on))
        st.session_state.chat_history.append({"role": "assistant", "content": res})

elif menu == cur["m3"]:
    st.markdown(f"<h1>{cur['m3']}</h1>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)
