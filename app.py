import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- 1. הגדרות מערכת וזיכרון ---
st.set_page_config(page_title="Nexus OS | Core", layout="wide", initial_sidebar_state="collapsed")
init_db()

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {}

# --- 2. מילון שפות מלא ---
SUBJECTS_HE = ["General / כללי", "מתמטיקה", "פיזיקה", "כתיבה אקדמאית", "עברית", "מדעי המחשב", "אחר"]
SUBJECTS_EN = ["General", "Math", "Physics", "Academic Writing", "Hebrew", "Computer Science", "Other"]

t = {
    "עברית": {
        "dash": "דאשבורד", "tutor": "AI Tutor 🤖", "history": "היסטוריה", "settings": "הגדרות",
        "avg": "ממוצע אקדמי", "total": "משימות שבוצעו", "add": "הזנת ציונים חדשים", "sub": "מקצוע",
        "topic": "נושא / מטלה", "grade": "ציון", "save": "שמור נתונים", "upload_title": "סריקת חומרי לימוד (RAG)",
        "ask": "שאל את Nexus AI...", "subjects": SUBJECTS_HE, "clear_chat": "🗑️ נקה צ'אט", "purge": "🚨 איפוס מסד נתונים"
    },
    "English": {
        "dash": "Dashboard", "tutor": "AI Tutor 🤖", "history": "History", "settings": "Settings",
        "avg": "Academic Average", "total": "Tasks Completed", "add": "Add New Grade", "sub": "Subject",
        "topic": "Topic", "grade": "Grade", "save": "Save Record", "upload_title": "Scan Study Material (RAG)",
        "ask": "Ask Nexus AI...", "subjects": SUBJECTS_EN, "clear_chat": "🗑️ Clear Chat", "purge": "🚨 Purge Database"
    }
}
cur = t[st.session_state.lang]

# --- 3. עיצוב Glassmorphism (הסתרת סיידבר ועיצוב יוקרתי) ---
st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at top, #0f2027, #203a43, #2c5364) !important; color: white; }
    
    /* כרטיסי מדדים */
    div[data-testid="stMetric"] { 
        background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(0, 209, 255, 0.3) !important; 
        border-radius: 20px; padding: 20px; backdrop-filter: blur(10px); 
    }
    div[data-testid="stMetricValue"] { color: #00D1FF !important; font-weight: 900 !important; font-size: 3.5rem !important; }
    
    /* כפתורים וקלט */
    .stButton>button {
        background: linear-gradient(90deg, #00D1FF 0%, #007BFF 100%); color: white !important;
        border-radius: 25px; border: none; font-weight: bold; width: 100%;
    }
    input, select, textarea, [data-baseweb="select"] { 
        background: white !important; color: black !important; border-radius: 10px !important; font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# תמיכה ב-RTL לעברית
if st.session_state.lang == "עברית":
    st.markdown("<style>[data-testid='stChatMessageContent'], [data-testid='stChatMessageContent'] * { direction: rtl !important; text-align: right !important; } [data-testid='stChatInput'] textarea { direction: rtl !important; text-align: right !important; }</style>", unsafe_allow_html=True)

# --- 4. לוגיקת ברכה חכמה ---
hour = datetime.datetime.now().hour
if 5 <= hour < 12: greeting = "בוקר טוב" if st.session_state.lang == "עברית" else "Good Morning"
elif 12 <= hour < 17: greeting = "צהריים טובים" if st.session_state.lang == "עברית" else "Good Afternoon"
elif 17 <= hour < 21: greeting = "ערב טוב" if st.session_state.lang == "עברית" else "Good Evening"
else: greeting = "לילה טוב למקצוענים" if st.session_state.lang == "עברית" else "Late Night Hustle"

st.markdown(f"<h1 style='text-align:center; color:#00D1FF; margin-bottom:0;'>NEXUS OS</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center; font-size:1.2rem; color:#aaa;'>{greeting}, Mendi 🎓</p>", unsafe_allow_html=True)

# --- 5. תפריט ניווט אופקי ---
selected = option_menu(
    menu_title=None, 
    options=[cur["dash"], cur["tutor"], cur["history"], cur["settings"]], 
    icons=["grid-1x2-fill", "cpu-fill", "clock-history", "gear-fill"], 
    orientation="horizontal",
    styles={
        "container": {"background-color": "rgba(0,0,0,0.3)", "border-radius": "15px"},
        "nav-link-selected": {"background-color": "rgba(0, 209, 255, 0.2)", "color": "#00D1FF", "border-bottom": "3px solid #00D1FF"}
    }
)

df = get_all_grades()

# --- 6. דפי האפליקציה ---

if selected == cur["dash"]:
    st.markdown("<br>", unsafe_allow_html=True)
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
                save_grade(sub, tp, grd); st.rerun()
                
        st.markdown(f"### 📁 {cur['upload_title']}")
        upload_sub = st.selectbox("Assign to:", cur["subjects"][1:], key="u_sub")
        uploaded = st.file_uploader("PDF/Docx/Image", type=["pdf", "docx", "png", "jpg", "jpeg"])
        if uploaded and st.button("🧠 Learn Content"):
            with st.spinner("Extracting..."):
                st.session_state.file_contexts[upload_sub] = extract_text_from_file(uploaded)
                st.success("Knowledge Ingested!")

    with col_right:
        st.markdown("### 📈 Trend Analysis")
        if not df.empty:
            fig = px.line(df.sort_values(by='date'), x='date', y='grade', color='subject', markers=True)
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add grades to see your learning curve.")

elif selected == cur["tutor"]:
    sub_choice = st.selectbox(cur["sub"], cur["subjects"]) 
    current_context = st.session_state.file_contexts.get(sub_choice, "")
    if current_context: st.success("📚 Study Material Active.")

    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
                
    if prompt := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                # שימוש בסטרימינג החדש והחסין
                res = st.write_stream(get_ai_response_stream(sub_choice, prompt, current_context))
            st.session_state.chat_history.append({"role": "assistant", "content": res})

elif selected == cur["history"]:
    st.markdown(f"### 📜 {cur['history']}")
    if not df.empty: st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)
    else: st.info("No records yet.")

elif selected == cur["settings"]:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🌐 Language")
        new_lang = st.radio("", ["עברית", "English"], index=0 if st.session_state.lang == "עברית" else 1)
        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang; st.rerun()
    with col2:
        st.markdown("### 🛠️ Maintenance")
        if st.button(cur["clear_chat"]): st.session_state.chat_history = []; st.rerun()
        if st.button(cur["purge"]): clear_db(); st.rerun()
