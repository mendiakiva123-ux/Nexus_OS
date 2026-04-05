import streamlit as st
from streamlit_option_menu import option_menu
from database_manager import save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- Setup & State ---
if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_context' not in st.session_state: st.session_state.file_context = ""

# --- מילון תרגום טוטאלי ---
T = {
    "עברית": {
        "title": "NEXUS CORE v2.0",
        "m1": "מרכז בקרה", "m2": "בינה מלאכותית", "m3": "מאגר נתונים", "m4": "מערכת",
        "avg": "ממוצע אקדמי", "count": "רשומות", "status": "מצב חיבור",
        "sub": "מקצוע", "grd": "ציון", "sync": "שלח לענן",
        "scan": "🛰️ סריקה ניורונית", "process": "עבד נתונים", "up_help": "העלה חומר (PDF/DOCX/תמונות)",
        "analyst": "פרוטוקול אנליסט 📊", "ask": "שאל את המערכת...", "clear": "נקה צ'אט",
        "reset": "🚨 איפוס בסיס נתונים", "subjects": ["כללי", "מתמטיקה", "מדעי המחשב", "סטטיסטיקה", "פיזיקה", "אחר"],
        "ready": "מערכת מוכנה", "success": "הנתונים הוזנו בהצלחה!"
    },
    "English": {
        "title": "NEXUS CORE v2.0",
        "m1": "Dashboard", "m2": "Nexus AI", "m3": "Data Vault", "m4": "System",
        "avg": "Academic Avg", "count": "Records", "status": "System Status",
        "sub": "Subject", "grd": "Grade", "sync": "Sync to Cloud",
        "scan": "🛰️ Neural Scan", "process": "Process", "up_help": "Upload material",
        "analyst": "Analyst Protocol 📊", "ask": "Query system...", "clear": "Purge Chat",
        "reset": "🚨 Reset Database", "subjects": ["General", "Math", "Computer Science", "Statistics", "Physics", "Other"],
        "ready": "SYSTEM READY", "success": "DATA INGESTED!"
    }
}

cur = T[st.session_state.lang]
st.set_page_config(page_title=cur["title"], layout="wide")

# --- Cyber UI Customization ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Assistant:wght@400;700&display=swap');
    .stApp {{ background: linear-gradient(180deg, #050a0f 0%, #001219 100%); color: #00f2fe; font-family: 'Assistant', sans-serif; }}
    h1 {{ font-family: 'Orbitron', sans-serif; text-shadow: 0 0 15px #00f2fe; text-align: center; color: #00f2fe; }}
    div[data-testid="stMetric"] {{ background: rgba(0, 242, 254, 0.05); border: 1px solid #00f2fe; border-radius: 15px; padding: 15px; }}
    .stButton>button {{ background: #00f2fe !important; color: black !important; font-weight: 800; border-radius: 20px; transition: 0.3s; }}
    .stButton>button:hover {{ box-shadow: 0 0 20px #00f2fe; transform: scale(1.02); }}
    {"[data-testid='stSidebar'], .main { direction: rtl; } [data-testid='stChatMessageContent'] { direction: rtl; text-align: right; }" if st.session_state.lang == "עברית" else ""}
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"<h1>{cur['title']}</h1>", unsafe_allow_html=True)
    new_lang = st.radio("INTERFACE / שפה", ["עברית", "English"], horizontal=True)
    if new_lang != st.session_state.lang: st.session_state.lang = new_lang; st.rerun()
    
    st.divider()
    analyst_on = st.toggle(cur["analyst"])
    
    st.markdown(f"### {cur['scan']}")
    up = st.file_uploader(cur["up_help"], type=['pdf', 'docx', 'jpg', 'png'])
    if up and st.button(cur["process"]):
        with st.spinner("..."):
            st.session_state.file_context = extract_text_from_file(up)
            st.success(cur["success"])

    menu = option_menu(None, [cur["m1"], cur["m2"], cur["m3"], cur["m4"]], 
                       icons=["grid-fill", "robot", "database-fill", "gear-fill"], default_index=0)

# --- Database Integration ---
df = get_all_grades()

if menu == cur["m1"]:
    st.markdown(f"<h1>{cur['m1']}</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric(cur["avg"], f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    c2.metric(cur["count"], len(df))
    c3.metric(cur["status"], cur["ready"])
    
    st.divider()
    with st.container():
        col1, col2 = st.columns(2)
        s_input = col1.selectbox(cur["sub"], cur["subjects"])
        g_input = col2.number_input(cur["grd"], 0, 100, 90)
        if st.button(cur["sync"]):
            save_grade(s_input, "", g_input); st.rerun()

elif menu == cur["m2"]:
    st.markdown(f"<h1>{cur['m2']}</h1>", unsafe_allow_html=True)
    # בחירת נושא לצ'אט (כללי כברירת מחדל)
    chat_sub = st.selectbox(cur["sub"], cur["subjects"], index=0)
    
    if st.button(cur["clear"]): st.session_state.chat_history = []; st.rerun()
    
    chat_container = st.container(height=500)
    for m in st.session_state.chat_history:
        with chat_container.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with chat_container.chat_message("user"): st.markdown(p)
        with chat_container.chat_message("assistant"):
            # שימוש ב-write_stream להזרמה חלקה
            res = st.write_stream(get_ai_response_stream(chat_sub, p, st.session_state.file_context, st.session_state.lang, analyst_on))
        st.session_state.chat_history.append({"role": "assistant", "content": res})

elif menu == cur["m3"]:
    st.markdown(f"<h1>{cur['m3']}</h1>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)

elif menu == cur["m4"]:
    st.markdown(f"<h1>{cur['m4']}</h1>", unsafe_allow_html=True)
    if st.button(cur["reset"]): clear_db(); st.rerun()
