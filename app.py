import streamlit as st
from streamlit_option_menu import option_menu
from database_manager import save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- הגדרות בסיסיות ---
if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_context' not in st.session_state: st.session_state.file_context = ""

T = {
    "עברית": {
        "title": "NEXUS CORE", "m1": "מרכז בקרה", "m2": "בינה מלאכותית", "m3": "מאגר נתונים",
        "sub": "מקצוע", "grd": "ציון", "sync": "סנכרן נתונים", "analyst": "פרוטוקול אנליסט 📊",
        "ask": "שאל את המערכת...", "clear": "נקה צ'אט", "subjects": ["כללי", "מתמטיקה", "מדעי המחשב", "סטטיסטיקה"]
    },
    "English": {
        "title": "NEXUS CORE", "m1": "Dashboard", "m2": "Nexus AI", "m3": "Data Vault",
        "sub": "Subject", "grd": "Grade", "sync": "Sync Data", "analyst": "Analyst Mode 📊",
        "ask": "Ask AI...", "clear": "Clear Chat", "subjects": ["General", "Math", "CS", "Statistics"]
    }
}
cur = T[st.session_state.lang]

st.set_page_config(page_title=cur["title"], layout="wide")

# עיצוב מותאם לעברית (RTL)
if st.session_state.lang == "עברית":
    st.markdown("""
        <style>
        .main, [data-testid="stSidebar"] { direction: rtl; text-align: right; }
        [data-testid="stChatMessageContent"] { direction: rtl; text-align: right; }
        .stSelectbox label, .stNumberInput label { text-align: right; display: block; }
        div[data-testid="stMetricValue"] { text-align: right; }
        </style>
    """, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"## {cur['title']}")
    new_lang = st.radio("שפה / LANGUAGE", ["עברית", "English"], horizontal=True)
    if new_lang != st.session_state.lang: st.session_state.lang = new_lang; st.rerun()
    
    st.divider()
    analyst_on = st.toggle(cur["analyst"])
    
    st.markdown("### 📁 סריקת מסמכים")
    up = st.file_uploader("העלה חומר לימודי", type=['pdf', 'docx', 'png', 'jpg'])
    if up and st.button("עבד נתונים"):
        st.session_state.file_context = extract_text_from_file(up)
        st.success("הנתונים נסרקו בהצלחה!")

    menu = option_menu(None, [cur["m1"], cur["m2"], cur["m3"]], icons=["cpu", "robot", "database"])

# --- דף הבינה המלאכותית ---
if menu == cur["m2"]:
    st.markdown(f"<h1>{cur['m2']}</h1>", unsafe_allow_html=True)
    chat_sub = st.selectbox(cur["sub"], cur["subjects"], index=0)
    
    if st.button(cur["clear"]): st.session_state.chat_history = []; st.rerun()
    
    # תצוגת הצ'אט
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        with st.chat_message("assistant"):
            res = st.write_stream(get_ai_response_stream(chat_sub, p, st.session_state.file_context, st.session_state.lang, analyst_on))
        st.session_state.chat_history.append({"role": "assistant", "content": res})

# --- מרכז בקרה (Dashboard) ---
elif menu == cur["m1"]:
    st.markdown(f"<h1>{cur['m1']}</h1>", unsafe_allow_html=True)
    df = get_all_grades()
    st.metric("ממוצע נוכחי", f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    
    with st.form("add_grade"):
        c1, c2 = st.columns(2)
        s = c1.selectbox(cur["sub"], cur["subjects"])
        g = c2.number_input(cur["grd"], 0, 100, 90)
        if st.form_submit_button(cur["sync"]):
            save_grade(s, "", g); st.rerun()

elif menu == cur["m3"]:
    st.markdown(f"<h1>{cur['m3']}</h1>", unsafe_allow_html=True)
    st.dataframe(get_all_grades(), use_container_width=True)
