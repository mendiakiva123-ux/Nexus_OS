import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- 1. הגדרות ועיצוב ---
st.set_page_config(page_title="Nexus OS", layout="wide", initial_sidebar_state="expanded")
init_db()

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {}

# עיצוב מודרני מקיף
st.markdown("""
    <style>
    /* רקע וצבעים כלליים */
    [data-testid="stAppViewContainer"] { background: #0b0e14 !important; color: #ffffff !important; }
    section[data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 1px solid #30363d; }
    
    /* כרטיסי מדדים */
    div[data-testid="stMetric"] {
        background: #1c2128 !important; border: 1px solid #30363d !important;
        border-radius: 15px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    div[data-testid="stMetricValue"] { color: #58a6ff !important; font-size: 2.5rem !important; }
    
    /* כפתורים */
    .stButton>button {
        background: #238636 !important; color: white !important;
        border-radius: 8px; border: none; font-weight: bold; width: 100%; height: 45px;
    }
    .stButton>button:hover { background: #2ea043 !important; }
    
    /* קלט - קריא ונוח */
    input, select, textarea, [data-baseweb="select"] {
        background: #ffffff !important; color: #000000 !important;
        border-radius: 8px !important; font-weight: bold !important;
    }
    
    /* צ'אט */
    [data-testid="stChatMessage"] { background: #1c2128 !important; border-radius: 15px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# RTL לעברית
if st.session_state.lang == "עברית":
    st.markdown("<style>div[data-testid='stChatMessageContent'] * { direction: rtl; text-align: right; } textarea { direction: rtl; }</style>", unsafe_allow_html=True)

# --- 2. סיידבר (ניווט וניהול) ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#58a6ff;'>NEXUS OS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#8b949e;'>Elite Academic Core</p>", unsafe_allow_html=True)
    st.divider()
    
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "AI Tutor", "History", "Settings"],
        icons=["grid-fill", "cpu-fill", "clock-history", "gear-fill"],
        default_index=0,
        styles={
            "container": {"background-color": "transparent"},
            "nav-link": {"color": "#c9d1d9", "font-weight": "bold"},
            "nav-link-selected": {"background-color": "#1f6feb", "color": "white"}
        }
    )
    
    st.divider()
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

df = get_all_grades()

# --- 3. דפי המערכת ---

if selected == "Dashboard":
    st.markdown("## 📊 Dashboard Overview")
    c1, c2, c3 = st.columns(3)
    avg = df['grade'].mean() if not df.empty else 0.0
    c1.metric("Average", f"{avg:.1f}")
    c2.metric("Records", len(df))
    c3.metric("Status", "Operational")
    
    st.divider()
    
    col1, col2 = st.columns([1, 1.2])
    with col1:
        st.markdown("### 📝 Log Grade")
        with st.form("add_grade", clear_on_submit=True):
            sub = st.selectbox("Subject", ["מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"])
            tp = st.text_input("Topic")
            grd = st.number_input("Grade", 0, 100, 90)
            if st.form_submit_button("Save"):
                save_grade(sub, tp, grd); st.rerun()
                
        st.markdown("### 📁 Study Material")
        up = st.file_uploader("Upload PDF/Docx/Image", type=["pdf", "docx", "png", "jpg", "jpeg"])
        if up and st.button("🧠 Learn Content"):
            with st.spinner("Processing..."):
                st.session_state.file_contexts[sub] = extract_text_from_file(up)
                st.success("Context Uploaded!")
                
    with col2:
        st.markdown("### 📈 Trend Line")
        if not df.empty:
            fig = px.line(df.sort_values('date'), x='date', y='grade', color='subject', markers=True, template="plotly_dark")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

elif selected == "AI Tutor":
    st.markdown("## 🧠 AI Academic Tutor")
    sub_choice = st.selectbox("Current Subject Context:", ["General / כללי", "מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"])
    
    ctx = st.session_state.file_contexts.get(sub_choice, "")
    if ctx: st.info("📚 Using your study materials for this subject.")

    chat_container = st.container(height=500)
    for m in st.session_state.chat_history:
        with chat_container.chat_message(m["role"]): st.markdown(m["content"])
        
    if prompt := st.chat_input("Ask Nexus AI..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with chat_container.chat_message("user"): st.markdown(prompt)
        
        with chat_container.chat_message("assistant"):
            res_box = st.empty()
            full_res = ""
            # השימוש במנוע ה-requests המקורי שלך
            for chunk in get_ai_response_stream(sub_choice, prompt, file_context=ctx):
                full_res += chunk
                res_box.markdown(full_res + " ▌")
            res_box.markdown(full_res)
            st.session_state.chat_history.append({"role": "assistant", "content": full_res})

elif selected == "History":
    st.markdown("## 📜 Academic Records")
    st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

elif selected == "Settings":
    st.markdown("## ⚙️ System Settings")
    st.markdown("### 🌐 Language / שפה")
    lang = st.radio("", ["עברית", "English"], index=0 if st.session_state.lang == "עברית" else 1, horizontal=True)
    if lang != st.session_state.lang:
        st.session_state.lang = lang; st.rerun()
        
    st.divider()
    if st.button("🚨 Purge All Data"):
        clear_db(); st.rerun()
