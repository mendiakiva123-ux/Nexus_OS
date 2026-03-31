import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- הגדרות עיצוב ---
st.set_page_config(page_title="Nexus OS", layout="wide", initial_sidebar_state="collapsed")
init_db()

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {}

SUBJECTS_HE = ["General / כללי", "מתמטיקה", "פיזיקה", "כתיבה אקדמאית", "עברית", "מדעי המחשב", "אחר"]
SUBJECTS_EN = ["General", "Math", "Physics", "Academic Writing", "Hebrew", "Computer Science", "Other"]

t = {
    "עברית": {
        "dash": "דאשבורד", "tutor": "AI Tutor 🤖", "hist": "היסטוריה", "set": "הגדרות",
        "avg": "ממוצע אקדמי", "total": "משימות", "add": "הזנת ציונים", "sub": "מקצוע",
        "save": "שמור", "upload": "טעינת חומר", "ask": "שאל את Nexus AI...", "subjects": SUBJECTS_HE
    },
    "English": {
        "dash": "Dashboard", "tutor": "AI Tutor 🤖", "hist": "History", "set": "Settings",
        "avg": "Academic Average", "total": "Tasks", "add": "Add Grade", "sub": "Subject",
        "save": "Save", "upload": "Upload Material", "ask": "Ask Nexus AI...", "subjects": SUBJECTS_EN
    }
}
cur = t[st.session_state.lang]

# CSS Glassmorphism
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at top left, #0f2027, #203a43, #2c5364) !important; color: white; }
    [data-testid="collapsedControl"] { display: none !important; }
    div[data-testid="stMetric"] { background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(0, 209, 255, 0.3) !important; border-radius: 20px; padding: 20px; backdrop-filter: blur(10px); }
    div[data-testid="stMetricValue"] { color: #00D1FF !important; font-weight: 900 !important; }
    .stButton>button { background: linear-gradient(90deg, #00D1FF, #007BFF); color: white !important; border-radius: 25px; border: none; font-weight: bold; width: 100%; }
    input, select, textarea, [data-baseweb="select"] { background: white !important; color: black !important; border-radius: 12px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

if st.session_state.lang == "עברית":
    st.markdown("<style>[data-testid='stChatMessageContent'] * { direction: rtl; text-align: right; } [data-testid='stChatInput'] textarea { direction: rtl; text-align: right; }</style>", unsafe_allow_html=True)

# כותרת
st.markdown(f"<h1 style='text-align:center; color:#00D1FF; margin-bottom:0;'>NEXUS OS</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center; color:#aaa; margin-bottom:20px;'>Welcome back, Mendi 🎓</p>", unsafe_allow_html=True)

# תפריט אופקי
selected = option_menu(None, [cur["dash"], cur["tutor"], cur["hist"], cur["set"]], 
    icons=["grid-fill", "cpu-fill", "clock-history", "gear-fill"], orientation="horizontal",
    styles={
        "container": {"background-color": "rgba(0,0,0,0.2)", "border-radius": "15px"},
        "nav-link-selected": {"background-color": "rgba(0, 209, 255, 0.2)", "color": "#00D1FF", "border-bottom": "3px solid #00D1FF"}
    })

df = get_all_grades()

if selected == cur["dash"]:
    c1, c2, c3 = st.columns(3)
    avg = df['grade'].mean() if not df.empty else 0.0
    c1.metric(cur["avg"], f"{avg:.1f}")
    c2.metric(cur["total"], len(df))
    c3.metric("System Engine", "Optimal 🟢")
    
    l, r = st.columns([1, 1.3])
    with l:
        st.markdown(f"### 📝 {cur['add']}")
        with st.form("grade_f", clear_on_submit=True):
            sub = st.selectbox(cur["sub"], cur["subjects"][1:])
            tp = st.text_input("Topic")
            grd = st.number_input("Grade", 0, 100, 90)
            if st.form_submit_button(cur["save"]):
                save_grade(sub, tp, grd); st.rerun()
                
        st.markdown(f"### 📁 {cur['upload']}")
        up_sub = st.selectbox("Assign to:", cur["subjects"][1:], key="u_sub")
        up = st.file_uploader("PDF/Image", type=["pdf", "docx", "png", "jpg", "jpeg"])
        if up and st.button("🧠 Learn"):
            st.session_state.file_contexts[up_sub] = extract_text_from_file(up)
            st.success("Knowledge Ingested!")

    with r:
        if not df.empty:
            fig = px.line(df.sort_values('date'), x='date', y='grade', color='subject', markers=True)
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)

elif selected == cur["tutor"]:
    sub_sel = st.selectbox(cur["sub"], cur["subjects"])
    ctx = st.session_state.file_contexts.get(sub_sel, "")
    if ctx: st.info("📚 Context Active")
    
    chat_container = st.container(height=450)
    for m in st.session_state.chat_history:
        with chat_container.chat_message(m["role"]): st.markdown(m["content"])
    
    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with chat_container.chat_message("user"): st.markdown(p)
        with chat_container.chat_message("assistant"):
            res_box = st.empty()
            full_res = ""
            # שימוש במנוע ה-Requests המקורי שלך
            for chunk in get_ai_response_stream(sub_sel, p, file_context=ctx):
                full_res += chunk
                res_box.markdown(full_res + " ▌")
            res_box.markdown(full_res)
            st.session_state.chat_history.append({"role": "assistant", "content": full_res})

elif selected == cur["hist"]:
    st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

elif selected == cur["set"]:
    st.markdown(f"### ⚙️ {cur['set']}")
    # החזרת בחירת השפה
    new_lang = st.radio("Language / שפה:", ["עברית", "English"], index=0 if st.session_state.lang == "עברית" else 1, horizontal=True)
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()
    if st.button("🗑️ Clear Chat"): st.session_state.chat_history = []; st.rerun()
    if st.button("🚨 Purge DB"): clear_db(); st.rerun()
