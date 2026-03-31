import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- Core Setup ---
st.set_page_config(page_title="Nexus OS | Ultra", layout="wide", initial_sidebar_state="expanded")
init_db()

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {}

# --- Insane Cyber Style ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&display=swap');
    
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(225deg, #050505 0%, #001219 50%, #002233 100%) !important;
        color: #ffffff;
    }
    
    /* Metrics Glow Effect */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(0, 209, 255, 0.3) !important;
        border-radius: 20px;
        padding: 25px;
        backdrop-filter: blur(20px);
        box-shadow: 0 0 20px rgba(0, 209, 255, 0.1);
        transition: 0.4s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 0 30px rgba(0, 209, 255, 0.3);
    }
    div[data-testid="stMetricValue"] {
        color: #00D1FF !important;
        font-family: 'Orbitron', sans-serif;
        text-shadow: 0 0 10px #00D1FF;
    }

    /* Cyber Buttons */
    .stButton>button {
        background: transparent !important;
        color: #00D1FF !important;
        border: 2px solid #00D1FF !important;
        border-radius: 12px;
        font-weight: 900;
        letter-spacing: 2px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: #00D1FF !important;
        color: #000 !important;
        box-shadow: 0 0 25px #00D1FF;
    }

    /* Chat Styling */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    input, select, textarea, [data-baseweb="select"] {
        background: rgba(255, 255, 255, 0.95) !important;
        color: black !important;
        border-radius: 10px !important;
        font-weight: bold !important;
    }
    
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif;
        background: linear-gradient(90deg, #00D1FF, #BC13FE);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

if st.session_state.lang == "עברית":
    st.markdown("<style>[data-testid='stChatMessageContent'] * { direction: rtl; text-align: right; } [data-testid='stChatInput'] textarea { direction: rtl; text-align: right; }</style>", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("<h2>NEXUS OS</h2>", unsafe_allow_html=True)
    lang_choice = st.radio("", ["עברית", "English"], horizontal=True)
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()
    st.divider()
    selected = option_menu(None, ["מרכז שליטה", "Nexus AI", "ארכיון", "מערכת"],
                           icons=["cpu-fill", "robot", "database-fill", "gear-wide-connected"], default_index=0,
                           styles={"nav-link-selected": {"background-color": "rgba(0, 209, 255, 0.2)", "color": "#00D1FF"}})
    if st.button("🗑️ PURGE CHAT"):
        st.session_state.chat_history = []; st.rerun()

df = get_all_grades()

# --- Page Logic ---
if selected == "מרכז שליטה":
    st.markdown("<h1>COMMAND CENTER</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    avg_val = df['grade'].mean() if not df.empty else 0.0
    c1.metric("ACADEMIC AVG", f"{avg_val:.1f}")
    c2.metric("TOTAL RECORDS", len(df))
    c3.metric("CORE STATUS", "OPTIMAL")
    
    st.markdown("<br>", unsafe_allow_html=True)
    l, r = st.columns([1, 1.2])
    with l:
        st.markdown("### 📝 DATA INPUT")
        with st.form("grade_form", clear_on_submit=True):
            sub = st.selectbox("SUBJECT", ["כללי", "מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"])
            tp = st.text_input("TOPIC")
            grd = st.number_input("GRADE", 0, 100, 90)
            if st.form_submit_button("SYNC DATA"):
                save_grade(sub, tp, grd); st.rerun()
        
        st.markdown("### 🧠 NEURAL UPLOAD")
        up = st.file_uploader("", type=["pdf", "docx", "png", "jpg", "jpeg"])
        if up and st.button("INGEST MATERIAL"):
            with st.spinner("Extracting..."):
                st.session_state.file_contexts[sub] = extract_text_from_file(up)
                st.success("Knowledge Injected!")

    with r:
        st.markdown("### 📈 ANALYTIC GRAPH")
        if not df.empty:
            fig = px.line(df.sort_values('date'), x='date', y='grade', color='subject', markers=True, template="plotly_dark")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#00D1FF")
            st.plotly_chart(fig, use_container_width=True)

elif selected == "Nexus AI":
    st.markdown("<h1>NEXUS INTELLIGENCE</h1>", unsafe_allow_html=True)
    sub_choice = st.selectbox("SELECT CONTEXT", ["כללי", "מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"])
    ctx = st.session_state.file_contexts.get(sub_choice, "")
    if ctx: st.info("⚡ Neural Link Active: Context Loaded.")

    chat_box = st.container(height=500)
    for m in st.session_state.chat_history:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input("Input query..."):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with chat_box.chat_message("user"): st.markdown(p)
        with chat_box.chat_message("assistant"):
            full_res = st.write_stream(get_ai_response_stream(sub_choice, p, ctx))
        st.session_state.chat_history.append({"role": "assistant", "content": full_res})

elif selected == "ארכיון":
    st.markdown("<h1>ARCHIVE</h1>", unsafe_allow_html=True)
    st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

elif selected == "מערכת":
    st.markdown("<h1>SYSTEM SETTINGS</h1>", unsafe_allow_html=True)
    if st.button("🚨 PURGE ENTIRE DATABASE"):
        clear_db(); st.rerun()
