import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream

# --- 1. הגדרות מערכת ---
st.set_page_config(page_title="Nexus OS | NextGen", layout="wide", initial_sidebar_state="expanded")
init_db()

STUDY_SUBJECTS = ["General / כללי", "Python", "Data Analyst", "SQL", "מתמטיקה", "אחר"]

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- 2. עיצוב Glassmorphism חדשני ויוקרתי ---
st.markdown("""
    <style>
    /* רקע רדיאלי מודרני (סייבר/דאטה) */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top left, #0f2027, #203a43, #2c5364) !important;
        color: #ffffff;
    }
    
    /* סיידבר שקוף-מטושטש */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 32, 39, 0.6) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* מדדים מרחפים (Cards) */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(0, 209, 255, 0.3) !important;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(10px);
    }
    div[data-testid="stMetricValue"] { color: #00D1FF !important; font-weight: 900 !important; font-size: 3rem !important; }
    h1, h2, h3, p, label { color: #e0e0e0 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* תיבות קלט שחור-על-לבן בולט (לבקשתך) */
    input, select, textarea, [data-baseweb="select"], .stNumberInput input {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #000000 !important;
        border-radius: 10px !important;
        border: 2px solid transparent !important;
        font-weight: 800 !important;
    }
    input:focus, select:focus { border: 2px solid #00D1FF !important; }
    div[role="listbox"] ul li, div[data-baseweb="popover"] span {
        color: black !important; font-weight: bold !important;
    }
    
    /* כפתורים מודרניים */
    .stButton>button {
        background: linear-gradient(90deg, #00D1FF 0%, #007BFF 100%);
        color: white !important;
        border: none;
        border-radius: 25px;
        font-weight: bold;
        transition: all 0.3s ease 0s;
    }
    .stButton>button:hover { box-shadow: 0px 5px 15px rgba(0, 209, 255, 0.4); transform: translateY(-2px); }
    </style>
    """, unsafe_allow_html=True)

# --- 3. תפריט ניווט (הסיסמה בוטלה!) ---
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#00D1FF; letter-spacing: 2px;'>NEXUS OS</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#aaaaaa; font-size:12px;'>Welcome, Mendi</p>", unsafe_allow_html=True)
    st.divider()
    
    selected = option_menu(
        menu_title=None, 
        options=["Dashboard", "AI Tutor", "History", "Settings"], 
        icons=["grid-1x2-fill", "cpu-fill", "clock-history", "sliders"], 
        default_index=0,
        styles={
            "container": {"background-color": "transparent"},
            "nav-link": {"color": "#e0e0e0", "font-size": "16px", "border-radius": "10px", "margin":"5px 0"},
            "nav-link-selected": {"background-color": "rgba(0, 209, 255, 0.15)", "color": "#00D1FF", "border": "1px solid #00D1FF"}
        }
    )

df = get_all_grades()

# --- 4. לוגיקת דפים ---
if selected == "Dashboard":
    st.markdown("<h1>📊 Analytics Hub</h1>", unsafe_allow_html=True)
    
    avg_grade = df['grade'].mean() if not df.empty else 0.0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Average Score", f"{avg_grade:.1f}")
    c2.metric("Total Records", len(df))
    c3.metric("System Status", "Optimal")
    
    st.markdown("<br><p style='color:#00D1FF; font-weight:bold;'>Academic Progress</p>", unsafe_allow_html=True)
    st.progress(int(avg_grade) / 100.0)
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📝 New Entry")
        with st.form("grade_form", clear_on_submit=True):
            sub = st.selectbox("Subject", STUDY_SUBJECTS[1:])
            tp = st.text_input("Topic")
            grd = st.number_input("Grade", 0, 100, 90)
            if st.form_submit_button("Save Record"):
                save_grade(sub, tp, grd)
                st.rerun()
    with col2:
        st.markdown("### 📁 Upload Data")
        st.file_uploader("Drop PDF/Docx files here", type=["pdf", "docx"])

elif selected == "AI Tutor":
    st.markdown("<h1>🧠 Nexus AI Core</h1>", unsafe_allow_html=True)
    sub_choice = st.selectbox("Context:", STUDY_SUBJECTS)
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Initialize query..."):
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

elif selected == "History":
    st.markdown("<h1>📜 Database Records</h1>", unsafe_allow_html=True)
    if df.empty:
        st.info("No records found in the system.")
    else:
        st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

elif selected == "Settings":
    st.markdown("<h1>⚙️ System Configurations</h1>", unsafe_allow_html=True)
    if st.button("🚨 Purge Database"):
        clear_db()
        st.rerun()
