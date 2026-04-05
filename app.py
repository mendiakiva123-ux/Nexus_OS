import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from database_manager import save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# הגדרת מצב שפה בסיסי
if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_context' not in st.session_state: st.session_state.file_context = ""

# מילון תרגום טוטאלי
T = {
    "עברית": {
        "title": "NEXUS CORE",
        "menu_1": "מרכז שליטה", "menu_2": "בינה מלאכותית", "menu_3": "מאגר ידע", "menu_4": "הגדרות",
        "avg": "ממוצע אקדמי", "records": "מספר רשומות", "status": "מצב מערכת",
        "subject": "מקצוע", "grade": "ציון", "sync": "סנכרן נתונים לענן",
        "upload_title": "🛰️ סריקה ניורונית", "upload_btn": "עבד נתונים", "upload_help": "העלה חומר לימודי (PDF/DOCX/תמונות)",
        "analyst": "פרוטוקול דאטה אנליסט 📊", "ask": "הזן שאילתה למערכת...", "purge": "נקה היסטוריה",
        "reset_db": "🚨 איפוס בסיס נתונים", "subjects": ["כללי", "מתמטיקה", "מדעי המחשב", "פיזיקה", "אנגלית"],
        "processing": "מעבד נתונים...", "success": "הנתונים הוזנו בהצלחה!"
    },
    "English": {
        "title": "NEXUS CORE",
        "menu_1": "Command Center", "menu_2": "Neural Tutor", "menu_3": "Knowledge Vault", "menu_4": "Settings",
        "avg": "Academic Avg", "records": "Total Records", "status": "System Status",
        "subject": "Subject", "grade": "Grade", "sync": "Sync to Cloud",
        "upload_title": "🛰️ Neural Scan", "upload_btn": "Process Data", "upload_help": "Upload study material",
        "analyst": "Analyst Protocol 📊", "ask": "Input query...", "purge": "Clear History",
        "reset_db": "🚨 Reset Database", "subjects": ["General", "Math", "Computer Science", "Physics", "English"],
        "processing": "Processing...", "success": "Data Ingested!"
    }
}

cur = T[st.session_state.lang]

st.set_page_config(page_title=cur["title"], layout="wide")

# עיצוב Cyber עם תמיכה ב-RTL
rtl_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@600&family=Assistant:wght@400;700&display=swap');
    .stApp { background: linear-gradient(135deg, #050a0f 0%, #001219 100%); color: #00f2fe; }
    h1, h2, h3 { font-family: 'Rajdhani', sans-serif; color: #00f2fe; text-transform: uppercase; }
    div[data-testid="stMetric"] { background: rgba(0, 242, 254, 0.05); border: 1px solid #00f2fe; border-radius: 15px; }
    .stButton>button { width: 100%; border-radius: 20px; background: #00f2fe; color: black; font-weight: bold; }
    """
if st.session_state.lang == "עברית":
    rtl_css += """
    [data-testid="stSidebar"], .main { direction: rtl; }
    [data-testid="stChatMessageContent"] { direction: rtl; text-align: right; }
    .stSelectbox label, .stNumberInput label { text-align: right; display: block; width: 100%; }
    """
st.markdown(rtl_css + "</style>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown(f"<h1>{cur['title']}</h1>", unsafe_allow_html=True)
    new_lang = st.radio("LANGUAGE / שפה", ["עברית", "English"], horizontal=True, index=0 if st.session_state.lang == "עברית" else 1)
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang; st.rerun()
    
    st.divider()
    analyst_mode = st.toggle(cur["analyst"])
    
    st.markdown(f"### {cur['upload_title']}")
    up_file = st.file_uploader(cur["upload_help"], type=['pdf', 'docx', 'jpg', 'png'])
    if up_file and st.button(cur["upload_btn"]):
        with st.spinner(cur["processing"]):
            st.session_state.file_context = extract_text_from_file(up_file)
            st.success(cur["success"])
            
    menu = option_menu(None, [cur["menu_1"], cur["menu_2"], cur["menu_3"], cur["menu_4"]], 
                       icons=["cpu", "robot", "database", "gear"], default_index=0)

df = get_all_grades()

if menu == cur["menu_1"]:
    st.markdown(f"<h1>{cur['menu_1']}</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric(cur["avg"], f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    c2.metric(cur["records"], len(df))
    c3.metric(cur["status"], "ONLINE")
    
    with st.container():
        st.markdown(f"### 📝 {cur['subject']}")
        col1, col2 = st.columns(2)
        s = col1.selectbox(cur["subject"], cur["subjects"])
        g = col2.number_input(cur["grade"], 0, 100, 90)
        if st.button(cur["sync"]):
            save_grade(s, "", g); st.rerun()

elif menu == cur["menu_2"]:
    st.markdown(f"<h1>{cur['menu_2']}</h1>", unsafe_allow_html=True)
    if st.button(cur["purge"]): st.session_state.chat_history = []; st.rerun()
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        with st.chat_message("assistant"):
            res = st.write_stream(get_ai_response_stream("Academy", p, st.session_state.file_context, st.session_state.lang, analyst_mode))
        st.session_state.chat_history.append({"role": "assistant", "content": res})

elif menu == cur["menu_3"]:
    st.markdown(f"<h1>{cur['menu_3']}</h1>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)

elif menu == cur["menu_4"]:
    if st.button(cur["reset_db"]): clear_db(); st.rerun()
