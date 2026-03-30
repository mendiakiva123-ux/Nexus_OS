import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream

# --- 1. הגדרות מערכת ---
st.set_page_config(page_title="Nexus OS | Core", layout="wide", initial_sidebar_state="expanded")
init_db()

# --- 2. מילון שפות והמקצועות המעודכנים שביקשת ---
if 'lang' not in st.session_state:
    st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# הרשימה המעודכנת בדיוק כפי שביקשת
SUBJECTS_HE = ["General / כללי", "מתמטיקה", "פיזיקה", "כתיבה אקדמאית", "עברית", "מדעי המחשב", "אחר"]
SUBJECTS_EN = ["General", "Math", "Physics", "Academic Writing", "Hebrew", "Computer Science", "Other"]

t = {
    "עברית": {
        "dash": "דאשבורד", "tutor": "AI Tutor 🤖", "history": "היסטוריה", "settings": "הגדרות",
        "avg": "ממוצע אקדמי", "total": "סה\"כ משימות", "add": "הזנת ציונים", "sub": "מקצוע",
        "topic": "נושא", "grade": "ציון", "save": "שמור נתונים", "upload_title": "העלאת חומר",
        "ask": "שאל אותי משהו...", "subjects": SUBJECTS_HE
    },
    "English": {
        "dash": "Dashboard", "tutor": "AI Tutor 🤖", "history": "History", "settings": "Settings",
        "avg": "Average Score", "total": "Total Records", "add": "Add Grade", "sub": "Subject",
        "topic": "Topic", "grade": "Grade", "save": "Save Record", "upload_title": "Upload Data",
        "ask": "Ask me anything...", "subjects": SUBJECTS_EN
    }
}
cur = t[st.session_state.lang]

# --- 3. עיצוב Glassmorphism ---
st.markdown("""
    <style>
    * { transition: none !important; animation: none !important; }
    
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top left, #0f2027, #203a43, #2c5364) !important;
        color: #ffffff;
    }
    
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 32, 39, 0.6) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(0, 209, 255, 0.3) !important;
        border-radius: 20px; padding: 20px; backdrop-filter: blur(10px);
    }
    div[data-testid="stMetricValue"] { color: #00D1FF !important; font-weight: 900 !important; font-size: 3rem !important; }
    h1, h2, h3, p, label, span { color: #e0e0e0 !important; text-shadow: 1px 1px 2px black; }
    
    input, select, textarea, [data-baseweb="select"], .stNumberInput input {
        background: rgba(255, 255, 255, 0.95) !important; color: #000000 !important;
        border-radius: 10px !important; font-weight: 900 !important;
    }
    div[role="listbox"] ul li, div[data-baseweb="popover"] span {
        color: black !important; font-weight: bold !important; background-color: white !important;
    }
    
    button[data-testid="sidebar-button"] svg { 
        fill: black !important; color: black !important; background-color: white !important; border-radius: 4px; padding: 2px;
    }
    div[data-testid="stFileUploader"] section { background-color: white !important; color: black !important; }
    div[data-testid="stFileUploader"] p, div[data-testid="stFileUploader"] span { color: black !important; text-shadow: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. תפריט ניווט ---
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#00D1FF; letter-spacing: 2px;'>NEXUS OS</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#aaaaaa; font-size:14px;'>Welcome, Mendi</p>", unsafe_allow_html=True)
    
    lang_choice = st.radio("", ["עברית", "English"], index=0 if st.session_state.lang == "עברית" else 1, horizontal=True)
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()
        
    st.divider()
    
    selected = option_menu(
        menu_title=None, 
        options=[cur["dash"], cur["tutor"], cur["history"], cur["settings"]], 
        icons=["grid-1x2-fill", "cpu-fill", "clock-history", "sliders"], 
        default_index=0,
        styles={
            "container": {"background-color": "transparent"},
            "nav-link": {"color": "#e0e0e0", "font-size": "16px", "border-radius": "10px", "margin":"5px 0"},
            "nav-link-selected": {"background-color": "rgba(0, 209, 255, 0.15)", "color": "#00D1FF", "border": "1px solid #00D1FF"}
        }
    )
    
    st.divider()
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

df = get_all_grades()

# --- 5. מסכי המערכת ---
if selected == cur["dash"]:
    st.markdown(f"<h1>📊 {cur['dash']}</h1>", unsafe_allow_html=True)
    
    avg_grade = df['grade'].mean() if not df.empty else 0.0
    c1, c2, c3 = st.columns(3)
    c1.metric(cur["avg"], f"{avg_grade:.1f}")
    c2.metric(cur["total"], len(df))
    c3.metric("System Status", "Optimal")
    
    st.markdown("<br><p style='color:#00D1FF; font-weight:bold;'>Academic Progress</p>", unsafe_allow_html=True)
    st.progress(int(avg_grade) / 100.0)
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### 📝 {cur['add']}")
        with st.form("grade_form", clear_on_submit=True):
            # מציג את כל המקצועות חוץ מ"כללי"
            sub = st.selectbox(cur["sub"], cur["subjects"][1:]) 
            tp = st.text_input(cur["topic"])
            grd = st.number_input(cur["grade"], 0, 100, 90)
            if st.form_submit_button(cur["save"]):
                save_grade(sub, tp, grd)
                st.rerun()
    with col2:
        st.markdown(f"### 📁 {cur['upload_title']}")
        st.file_uploader("PDF/Docx", type=["pdf", "docx"])

elif selected == cur["tutor"]:
    st.markdown(f"<h1>🧠 {cur['tutor']}</h1>", unsafe_allow_html=True)
    sub_choice = st.selectbox(cur["sub"], cur["subjects"]) 
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): 
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            res_box = st.empty()
            full_res = ""
            for chunk in get_ai_response_stream(sub_choice, prompt):
                full_res += chunk
                res_box.markdown(full_res + " ▌")
            res_box.markdown(full_res)
            st.session_state.chat_history.append({"role": "assistant", "content": full_res})

elif selected == cur["history"]:
    st.markdown(f"<h1>📜 {cur['history']}</h1>", unsafe_allow_html=True)
    if df.empty:
        st.info("No records found.")
    else:
        st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download Data (CSV)", data=csv, file_name='nexus_grades.csv', mime='text/csv')

elif selected == cur["settings"]:
    st.markdown(f"<h1>⚙️ {cur['settings']}</h1>", unsafe_allow_html=True)
    if st.button("🚨 Purge Database"):
        clear_db()
        st.rerun()
