import streamlit as st
from streamlit_option_menu import option_menu
from database_manager import save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- הגדרות שפה ועיצוב ---
if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_context' not in st.session_state: st.session_state.file_context = ""

T = {
    "עברית": {
        "title": "NEXUS CORE", "m1": "מרכז בקרה", "m2": "בינה מלאכותית", "m3": "מאגר נתונים",
        "sub": "מקצוע", "grd": "ציון", "sync": "סנכרן נתונים", "analyst": "מצב דאטה אנליסט 📊",
        "ask": "איך אני יכול לעזור, מנדי?", "clear": "נקה צ'אט", "subjects": ["כללי", "מתמטיקה", "מדעי המחשב", "סטטיסטיקה"]
    },
    "English": {
        "title": "NEXUS CORE", "m1": "Dashboard", "m2": "Nexus AI", "m3": "Data Vault",
        "sub": "Subject", "grd": "Grade", "sync": "Sync Data", "analyst": "Analyst Mode 📊",
        "ask": "How can I help, Mendi?", "clear": "Clear Chat", "subjects": ["General", "Math", "CS", "Statistics"]
    }
}
cur = T[st.session_state.lang]

st.set_page_config(page_title=cur["title"], layout="wide")

# CSS לישור לימין (RTL)
if st.session_state.lang == "עברית":
    st.markdown("""<style> .main, [data-testid="stSidebar"] { direction: rtl; text-align: right; } 
    [data-testid="stChatMessageContent"] { direction: rtl; text-align: right; } </style>""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"## {cur['title']}")
    new_lang = st.radio("INTERFACE / שפה", ["עברית", "English"], horizontal=True)
    if new_lang != st.session_state.lang: st.session_state.lang = new_lang; st.rerun()
    
    st.divider()
    analyst_on = st.toggle(cur["analyst"])
    
    up = st.file_uploader("📁 סרוק קובץ לימודי", type=['pdf', 'docx', 'png', 'jpg'])
    if up and st.button("עבד נתונים"):
        st.session_state.file_context = extract_text_from_file(up)
        st.success("המידע נסרק בהצלחה!")

    menu = option_menu(None, [cur["m1"], cur["m2"], cur["m3"]], icons=["grid", "robot", "database"])

df = get_all_grades()

if menu == cur["m2"]:
    st.markdown(f"<h1>{cur['m2']}</h1>", unsafe_allow_html=True)
    chat_sub = st.selectbox(cur["sub"], cur["subjects"], index=0)
    
    if st.button(cur["clear"]): st.session_state.chat_history = []; st.rerun()
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        with st.chat_message("assistant"):
            res = st.write_stream(get_ai_response_stream(chat_sub, p, st.session_state.file_context, st.session_state.lang, analyst_on))
        st.session_state.chat_history.append({"role": "assistant", "content": res})

elif menu == cur["m1"]:
    st.markdown(f"<h1>{cur['m1']}</h1>", unsafe_allow_html=True)
    # כאן תבוא הטבלה והזנת הציונים (כמו קודם)
    st.write(f"ממוצע נוכחי: {df['grade'].mean() if not df.empty else 0}")
