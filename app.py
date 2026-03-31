import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- 1. הגדרות ליבה ---
st.set_page_config(page_title="Nexus OS | Core", layout="wide", initial_sidebar_state="collapsed")
init_db()

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {}

# --- 2. תרגומים ועיצוב ---
SUBJECTS = ["General / כללי", "מתמטיקה", "פיזיקה", "כתיבה אקדמאית", "מדעי המחשב", "אחר"]
t = {
    "עברית": {
        "dash": "דאשבורד", "tutor": "AI Tutor 🤖", "hist": "היסטוריה", "set": "הגדרות",
        "avg": "ממוצע אקדמי", "total": "משימות", "add": "הזנת ציונים", "sub": "מקצוע",
        "topic": "נושא", "grade": "ציון", "save": "שמור", "ask": "שאל את ה-AI..."
    },
    "English": {
        "dash": "Dashboard", "tutor": "AI Tutor 🤖", "hist": "History", "set": "Settings",
        "avg": "Academic Average", "total": "Tasks", "add": "Add Grade", "sub": "Subject",
        "topic": "Topic", "grade": "Grade", "save": "Save", "ask": "Ask AI..."
    }
}
cur = t[st.session_state.lang]

st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at top, #0f2027, #203a43, #2c5364) !important; color: white; }
    div[data-testid="stMetric"] { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D1FF; border-radius: 20px; padding: 20px; backdrop-filter: blur(10px); }
    div[data-testid="stMetricValue"] { color: #00D1FF !important; font-weight: 900 !important; font-size: 3rem !important; }
    .stButton>button { background: linear-gradient(90deg, #00D1FF, #007BFF); color: white; border-radius: 25px; border:none; font-weight:bold; }
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
    styles={"container": {"background-color": "rgba(0,0,0,0.2)"}, "nav-link-selected": {"background-color": "rgba(0, 209, 255, 0.2)", "color": "#00D1FF"}})

df = get_all_grades()

if sel == cur["dash"]:
    c1, c2, c3 = st.columns(3)
    avg = df['grade'].mean() if not df.empty else 0.0
    c1.metric(cur["avg"], f"{avg:.1f}")
    c2.metric(cur["total"], len(df))
    c3.metric("Engine", "v2.0 Flash ⚡")
    
    l, r = st.columns([1, 1.2])
    with l:
        st.markdown(f"### 📝 {cur['add']}")
        with st.form("grade_f", clear_on_submit=True):
            s_box = st.selectbox(cur["sub"], SUBJECTS[1:])
            t_box = st.text_input(cur["topic"])
            g_box = st.number_input(cur["grade"], 0, 100, 90)
            if st.form_submit_button(cur["save"]):
                save_grade(s_box, t_box, g_box); st.rerun()
        
        st.markdown("### 📁 Study Material (RAG)")
        u_file = st.file_uploader("PDF/Docx/Image", type=["pdf", "docx", "png", "jpg", "jpeg"])
        if u_file and st.button("🧠 Upload to Brain"):
            with st.spinner("Learning..."):
                st.session_state.file_contexts[s_box] = extract_text_from_file(u_file)
                st.success("Context Loaded!")

    with r:
        st.markdown("### 📈 Trend Analysis")
        if not df.empty:
            fig = px.line(df.sort_values('date'), x='date', y='grade', color='subject', markers=True)
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)

elif sel == cur["tutor"]:
    sub_sel = st.selectbox(cur["sub"], SUBJECTS)
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
    if not df.empty: st.dataframe(df.sort_values('date', ascending=False), use_container_width=True)

elif sel == cur["set"]:
    st.button("Clear Chat", on_click=lambda: st.session_state.update({"chat_history": []}))
    if st.button("Purge DB"): clear_db(); st.rerun()
    if st.button("English / עברית"):
        st.session_state.lang = "English" if st.session_state.lang == "עברית" else "עברית"
        st.rerun()
