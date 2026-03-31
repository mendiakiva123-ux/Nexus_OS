import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- 1. הגדרות מערכת ---
st.set_page_config(page_title="Nexus OS | Core", layout="wide", initial_sidebar_state="collapsed")
init_db()

if 'lang' not in st.session_state:
    st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'file_contexts' not in st.session_state:
    st.session_state.file_contexts = {}

SUBJECTS_HE = ["General / כללי", "מתמטיקה", "פיזיקה", "כתיבה אקדמאית", "עברית", "מדעי המחשב", "אחר"]
SUBJECTS_EN = ["General", "Math", "Physics", "Academic Writing", "Hebrew", "Computer Science", "Other"]

t = {
    "עברית": {
        "dash": "דאשבורד", "tutor": "AI Tutor 🤖", "history": "היסטוריה", "settings": "הגדרות",
        "avg": "ממוצע אקדמי", "total": "משימות שבוצעו", "add": "הזנת ציונים חדשים", "sub": "מקצוע",
        "topic": "נושא / מטלה", "grade": "ציון", "save": "שמור למסד הנתונים", "upload_title": "סריקת חומרי לימוד (RAG)",
        "ask": "שאל אותי כל דבר...", "subjects": SUBJECTS_HE, "clear_chat": "🗑️ נקה היסטוריית שיחה",
        "purge": "🚨 איפוס כל הנתונים במסד"
    },
    "English": {
        "dash": "Dashboard", "tutor": "AI Tutor 🤖", "history": "History", "settings": "Settings",
        "avg": "Academic Average", "total": "Completed Tasks", "add": "Add New Grades", "sub": "Subject",
        "topic": "Topic / Task", "grade": "Grade", "save": "Save to Database", "upload_title": "Scan Study Materials (RAG)",
        "ask": "Ask me anything...", "subjects": SUBJECTS_EN, "clear_chat": "🗑️ Clear Chat History",
        "purge": "🚨 Purge All Database Records"
    }
}
cur = t[st.session_state.lang]

# --- 3. עיצוב Glassmorphism ---
st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at top, #0f2027, #203a43, #2c5364) !important; color: #ffffff; }
    div[data-testid="stMetric"] { background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(0, 209, 255, 0.3) !important; border-radius: 20px; padding: 20px; backdrop-filter: blur(10px); }
    div[data-testid="stMetricValue"] { color: #00D1FF !important; font-weight: 900 !important; font-size: 3.5rem !important; }
    h1, h2, h3, p, label, span { color: #e0e0e0 !important; text-shadow: 1px 1px 2px black; }
    input, select, textarea, [data-baseweb="select"], .stNumberInput input { background: rgba(255, 255, 255, 0.95) !important; color: #000000 !important; border-radius: 10px !important; font-weight: 900 !important; }
    .stButton>button { background: linear-gradient(90deg, #00D1FF 0%, #007BFF 100%); color: white !important; border-radius: 25px; font-weight: bold; border:none; }
    </style>
    """, unsafe_allow_html=True)

if st.session_state.lang == "עברית":
    st.markdown("<style>[data-testid='stChatMessageContent'], [data-testid='stChatMessageContent'] * { direction: rtl !important; text-align: right !important; } [data-testid='stChatInput'] textarea { direction: rtl !important; text-align: right !important; }</style>", unsafe_allow_html=True)

st.markdown(f"<h1 style='text-align:center; color:#00D1FF;'>NEXUS OS</h1>", unsafe_allow_html=True)

selected = option_menu(None, [cur["dash"], cur["tutor"], cur["history"], cur["settings"]], icons=["grid-1x2-fill", "cpu-fill", "clock-history", "gear-fill"], default_index=0, orientation="horizontal", styles={"container": {"background-color": "rgba(0,0,0,0.3)"}, "nav-link-selected": {"background-color": "rgba(0, 209, 255, 0.2)", "color": "#00D1FF"}})

df = get_all_grades()

if selected == cur["dash"]:
    avg_grade = df['grade'].mean() if not df.empty else 0.0
    c1, c2, c3 = st.columns(3)
    c1.metric(cur["avg"], f"{avg_grade:.1f}")
    c2.metric(cur["total"], len(df))
    c3.metric("System Engine", "Online 🟢")
    
    col_left, col_right = st.columns([1, 1.2])
    with col_left:
        st.markdown(f"### 📝 {cur['add']}")
        with st.form("grade_form", clear_on_submit=True):
            sub = st.selectbox(cur["sub"], cur["subjects"][1:]) 
            tp = st.text_input(cur["topic"])
            grd = st.number_input(cur["grade"], 0, 100, 90)
            if st.form_submit_button(cur["save"]):
                save_grade(sub, tp, grd)
                st.rerun()
        st.markdown(f"### 📁 {cur['upload_title']}")
        upload_sub = st.selectbox("Assign material to:", cur["subjects"][1:], key="upload_sub")
        uploaded_file = st.file_uploader("PDF / Docx / Images", type=["pdf", "docx", "png", "jpg", "jpeg"])
        if uploaded_file and st.button("🧠 Upload to AI Brain"):
            with st.spinner("Extracting..."):
                st.session_state.file_contexts[upload_sub] = extract_text_from_file(uploaded_file)
                st.success("Learned successfully!")

    with col_right:
        if not df.empty:
            fig = px.line(df.sort_values(by='date'), x='date', y='grade', color='subject', markers=True)
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)

elif selected == cur["tutor"]:
    sub_choice = st.selectbox("Context:", cur["subjects"]) 
    current_context = st.session_state.file_contexts.get(sub_choice, "")
    if current_context: st.success("📚 Context Active.")

    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
                
    if prompt := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                res_box = st.empty()
                full_res = ""
                for chunk in get_ai_response_stream(sub_choice, prompt, file_context=current_context):
                    full_res += chunk
                    res_box.markdown(full_res + " ▌")
                res_box.markdown(full_res)
                st.session_state.chat_history.append({"role": "assistant", "content": full_res})

elif selected == cur["history"]:
    if not df.empty: st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

elif selected == cur["settings"]:
    lang_choice = st.radio("Language", ["עברית", "English"], index=0 if st.session_state.lang == "עברית" else 1)
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()
    if st.button(cur["clear_chat"]):
        st.session_state.chat_history = []
        st.rerun()
    if st.button(cur["purge"]):
        clear_db()
        st.rerun()
