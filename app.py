import streamlit as st
from streamlit_option_menu import option_menu
from database_manager import save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- אתחול משתנים ---
if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_context' not in st.session_state: st.session_state.file_context = ""

# --- מילון תרגום טוטאלי ---
T = {
    "עברית": {
        "title": "NEXUS CORE",
        "m1": "מרכז בקרה", "m2": "בינה מלאכותית", "m3": "מאגר ידע", "m4": "הגדרות",
        "avg": "ממוצע ציונים", "count": "סך רשומות", "status": "סטטוס מערכת",
        "sub": "מקצוע", "grd": "ציון", "sync": "סנכרן נתונים",
        "scan": "🛰️ סריקה ניורונית", "process": "עבד נתונים", "up_help": "העלה קבצי לימוד",
        "analyst": "מצב דאטה אנליסט 📊", "ask": "שאל את ה-AI...", "clear": "נקה צ'אט",
        "reset": "🚨 איפוס מערכת", "subjects": ["כללי", "מתמטיקה", "מדעי המחשב", "סטטיסטיקה", "אחר"]
    },
    "English": {
        "title": "NEXUS CORE",
        "m1": "Command Center", "m2": "Neural Tutor", "m3": "Vault", "m4": "System",
        "avg": "Academic Avg", "count": "Total Records", "status": "System Status",
        "sub": "Subject", "grd": "Grade", "sync": "Sync Data",
        "scan": "🛰️ Neural Scan", "process": "Process Data", "up_help": "Upload material",
        "analyst": "Analyst Mode 📊", "ask": "Ask AI...", "clear": "Clear Chat",
        "reset": "🚨 Reset System", "subjects": ["General", "Math", "Computer Science", "Statistics", "Other"]
    }
}

cur = T[st.session_state.lang]
st.set_page_config(page_title=cur["title"], layout="wide")

# --- עיצוב Cyber חדיש ---
st.markdown(f"""
    <style>
    .stApp {{ background: #050a0f; color: #00f2fe; }}
    div[data-testid="stMetric"] {{ background: rgba(0, 242, 254, 0.05); border: 1px solid #00f2fe; border-radius: 15px; }}
    .stButton>button {{ background: #00f2fe !important; color: black !important; font-weight: bold; border-radius: 20px; width: 100%; }}
    {"[data-testid='stSidebar'], .main { direction: rtl; } [data-testid='stChatMessageContent'] { direction: rtl; text-align: right; }" if st.session_state.lang == "עברית" else ""}
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"## {cur['title']}")
    new_lang = st.radio("שפה / LANG", ["עברית", "English"], horizontal=True)
    if new_lang != st.session_state.lang: st.session_state.lang = new_lang; st.rerun()
    
    st.divider()
    analyst_on = st.toggle(cur["analyst"])
    
    st.markdown(f"### {cur['scan']}")
    up = st.file_uploader(cur["up_help"], type=['pdf', 'docx', 'jpg', 'png'])
    if up and st.button(cur["process"]):
        st.session_state.file_context = extract_text_from_file(up)
        st.success("SUCCESS" if st.session_state.lang == "English" else "הנתונים עובדו!")

    menu = option_menu(None, [cur["m1"], cur["m2"], cur["m3"], cur["m4"]], 
                       icons=["cpu", "robot", "database", "gear"], default_index=0)

df = get_all_grades()

if menu == cur["m1"]:
    st.markdown(f"# {cur['m1']}")
    c1, c2, c3 = st.columns(3)
    c1.metric(cur["avg"], f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    c2.metric(cur["count"], len(df))
    c3.metric(cur["status"], "ACTIVE")
    
    st.divider()
    col1, col2 = st.columns(2)
    s_input = col1.selectbox(cur["sub"], cur["subjects"])
    g_input = col2.number_input(cur["grd"], 0, 100, 90)
    if st.button(cur["sync"]):
        save_grade(s_input, "", g_input); st.rerun()

elif menu == cur["m2"]:
    st.markdown(f"# {cur['m2']}")
    # החזרת בחירת הנושא לצ'אט
    chat_sub = st.selectbox(cur["sub"], cur["subjects"], key="chat_sub")
    
    if st.button(cur["clear"]): st.session_state.chat_history = []; st.rerun()
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        with st.chat_message("assistant"):
            res = st.write_stream(get_ai_response_stream(chat_sub, p, st.session_state.file_context, st.session_state.lang, analyst_on))
        st.session_state.chat_history.append({"role": "assistant", "content": res})

elif menu == cur["m3"]:
    st.markdown(f"# {cur['m3']}")
    st.dataframe(df, use_container_width=True)

elif menu == cur["m4"]:
    if st.button(cur["reset"]): clear_db(); st.rerun()
