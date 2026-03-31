import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- הגדרות ליבה ---
st.set_page_config(page_title="Nexus OS | Core", layout="wide", initial_sidebar_state="collapsed")
init_db()

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {}

# תרגום
SUBJECTS = ["General / כללי", "מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"]
t = {
    "עברית": {"dash": "דאשבורד", "tutor": "AI Tutor 🤖", "avg": "ממוצע", "save": "שמור ציון", "ask": "שאל אותי..."},
    "English": {"dash": "Dashboard", "tutor": "AI Tutor 🤖", "avg": "Average", "save": "Save Grade", "ask": "Ask me..."}
}
cur = t[st.session_state.lang]

# --- עיצוב Glassmorphism ---
st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at top, #0f2027, #203a43, #2c5364) !important; color: white; }
    div[data-testid="stMetric"] { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D1FF; border-radius: 15px; padding: 15px; }
    .stButton>button { background: linear-gradient(90deg, #00D1FF, #007BFF); color: white; border-radius: 20px; border:none; width: 100%; font-weight: bold; }
    input, select, textarea { background: white !important; color: black !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

if st.session_state.lang == "עברית":
    st.markdown("<style>[data-testid='stChatMessageContent'] * { direction: rtl; text-align: right; } [data-testid='stChatInput'] textarea { direction: rtl; text-align: right; }</style>", unsafe_allow_html=True)

# ברכה
h = datetime.datetime.now().hour
greet = "בוקר טוב" if 5<=h<12 else "צהריים טובים" if 12<=h<17 else "ערב טוב" if 17<=h<21 else "לילה טוב"
st.markdown(f"<h1 style='text-align:center; color:#00D1FF;'>NEXUS OS</h1><p style='text-align:center;'>{greet}, Mendi 🎓</p>", unsafe_allow_html=True)

# תפריט
sel = option_menu(None, [cur["dash"], cur["tutor"], "History", "Settings"], 
    icons=["grid", "cpu", "clock", "gear"], orientation="horizontal",
    styles={"nav-link-selected": {"background-color": "rgba(0, 209, 255, 0.2)", "color": "#00D1FF"}})

df = get_all_grades()

if sel == cur["dash"]:
    c1, c2, c3 = st.columns(3)
    c1.metric(cur["avg"], f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    c2.metric("Tasks", len(df))
    c3.metric("Status", "Online 🟢")
    
    l, r = st.columns([1, 1.2])
    with l:
        with st.form("g"):
            sub = st.selectbox("Subject", SUBJECTS[1:])
            grd = st.number_input("Grade", 0, 100, 90)
            if st.form_submit_button(cur["save"]): save_grade(sub, "General", grd); st.rerun()
        
        up = st.file_uploader("Upload Material", type=["pdf", "docx", "png", "jpg"])
        if up and st.button("🧠 Learn"):
            st.session_state.file_contexts[sub] = extract_text_from_file(up)
            st.success("Loaded!")
    with r:
        if not df.empty:
            fig = px.line(df.sort_values('date'), x='date', y='grade', color='subject', markers=True)
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)

elif sel == cur["tutor"]:
    sub_sel = st.selectbox("Subject Context", SUBJECTS)
    chat = st.container(height=450)
    for m in st.session_state.chat_history:
        with chat.chat_message(m["role"]): st.markdown(m["content"])
    
    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with chat.chat_message("user"): st.markdown(p)
        with chat.chat_message("assistant"):
            res = st.write_stream(get_ai_response_stream(sub_sel, p, st.session_state.file_contexts.get(sub_sel, "")))
        st.session_state.chat_history.append({"role": "assistant", "content": res})

elif sel == "History":
    st.dataframe(df.sort_values('date', ascending=False), use_container_width=True)

elif sel == "Settings":
    if st.button("Clear Chat"): st.session_state.chat_history = []; st.rerun()
    if st.button("Change Language"): 
        st.session_state.lang = "English" if st.session_state.lang == "עברית" else "עברית"
        st.rerun()
