import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
from database_manager import save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- אתחול מערכת ---
if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_context' not in st.session_state: st.session_state.file_context = ""

T = {
    "עברית": {
        "title": "NEXUS CORE", "m1": "מרכז בקרה", "m2": "בינה מלאכותית", "m3": "מסד נתונים",
        "avg": "ממוצע ציונים", "count": "רשומות", "status": "מצב חיבור",
        "sub": "מקצוע", "grd": "ציון", "sync": "סנכרן נתונים", "analyst": "מצב דאטה אנליסט 📊",
        "ask": "איך אני יכול לעזור, מנדי?", "clear": "נקה צ'אט", 
        "subjects": ["כללי", "מתמטיקה", "מדעי המחשב", "סטטיסטיקה"]
    },
    "English": {
        "title": "NEXUS CORE", "m1": "Dashboard", "m2": "Nexus AI", "m3": "Database",
        "avg": "Avg Grade", "count": "Records", "status": "System Status",
        "sub": "Subject", "grd": "Grade", "sync": "Sync Data", "analyst": "Analyst Mode 📊",
        "ask": "How can I help, Mendi?", "clear": "Clear", 
        "subjects": ["General", "Math", "CS", "Statistics"]
    }
}
cur = T[st.session_state.lang]

st.set_page_config(page_title=cur["title"], layout="wide")

# --- CSS מטורף: הצעקה האחרונה (Glassmorphism & Cyber Glow) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;600;800&family=Orbitron:wght@700&display=swap');
    
    .stApp {{
        background: radial-gradient(circle at top right, #050a12, #000000);
        color: #e0f7fa;
        font-family: 'Assistant', sans-serif;
    }}

    /* יישור טוטאלי לימין עבור עברית */
    {" .main, [data-testid='stSidebar'], [data-testid='stChatMessageContent'], [data-testid='stChatInput'] { direction: rtl !important; text-align: right !important; } " if st.session_state.lang == "עברית" else ""}
    
    /* עיצוב בועות הצ'אט - מראה זכוכית יוקרתי */
    [data-testid="stChatMessage"] {{
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(0, 242, 254, 0.15) !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5) !important;
        margin-bottom: 15px !important;
    }}

    /* תיקון ספציפי לטקסט בתוך הבועה */
    [data-testid="stChatMessageContent"] p, [data-testid="stChatMessageContent"] li {{
        direction: rtl !important;
        text-align: right !important;
        font-size: 1.1rem !important;
        line-height: 1.6 !important;
    }}

    /* כותרות ניאון */
    h1 {{
        font-family: 'Orbitron', sans-serif;
        background: linear-gradient(90deg, #00f2fe, #4facfe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(0, 242, 254, 0.3);
        text-align: center;
    }}

    /* כרטיסיות KPI משודרגות */
    div[data-testid="stMetric"] {{
        background: linear-gradient(145deg, rgba(0, 242, 254, 0.1), rgba(0, 0, 0, 0.4)) !important;
        border: 1px solid #00f2fe !important;
        border-radius: 15px !important;
        transition: 0.3s;
    }}
    div[data-testid="stMetric"]:hover {{ transform: scale(1.03); box-shadow: 0 0 20px rgba(0, 242, 254, 0.2); }}

    /* עיצוב ה-Sidebar */
    [data-testid="stSidebar"] {{
        background-color: rgba(5, 10, 15, 0.95) !important;
        border-left: 1px solid rgba(0, 242, 254, 0.1);
    }}

    /* כפתורי ניאון */
    .stButton>button {{
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%) !important;
        color: #000 !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 12px;
        transition: 0.3s all ease;
        text-transform: uppercase;
        width: 100%;
    }}
    .stButton>button:hover {{
        box-shadow: 0 0 20px #00f2fe;
        transform: translateY(-2px);
    }}
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"<h1>{cur['title']}</h1>", unsafe_allow_html=True)
    lang = st.radio("INTERFACE", ["עברית", "English"], horizontal=True)
    if lang != st.session_state.lang: st.session_state.lang = lang; st.rerun()
    st.divider()
    
    analyst_on = st.toggle(cur["analyst"], value=True)
    
    st.markdown("### 📁 סריקה ניורונית")
    up = st.file_uploader("העלה חומר לימודי", type=['pdf', 'docx'])
    if up and st.button("עבד נתונים"):
        st.session_state.file_context = extract_text_from_file(up)
        st.success("DATA LOADED")

    menu = option_menu(None, [cur["m1"], cur["m2"], cur["m3"]], 
                       icons=["cpu", "robot", "database"], 
                       styles={"container": {"background-color": "transparent"},
                               "nav-link-selected": {"background-color": "#00f2fe", "color": "black"}})

df = get_all_grades()

# --- מרכז בקרה (DASHBOARD) ---
if menu == cur["m1"]:
    st.markdown(f"<h1>{cur['m1']}</h1>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.metric(cur["avg"], f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    c2.metric(cur["count"], len(df))
    c3.metric("CORE STATUS", "ACTIVE 🟢")
    
    st.divider()
    
    col_input, col_chart = st.columns([1, 2])
    with col_input:
        st.markdown("### 📥 הזנה מהירה")
        with st.form("grade_entry", clear_on_submit=True):
            s = st.selectbox(cur["sub"], cur["subjects"])
            g = st.number_input(cur["grd"], 0, 100, 90)
            if st.form_submit_button(cur["sync"]):
                save_grade(s, "", g)
                st.rerun()
                
    with col_chart:
        if not df.empty:
            fig = px.bar(df, x='subject', y='grade', color='grade', 
                         color_continuous_scale='IceFire', template="plotly_dark")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

# --- בינה מלאכותית (AI) ---
elif menu == cur["m2"]:
    st.markdown(f"<h1>{'ANALYSIS MODE' if analyst_on else cur['m2']}</h1>", unsafe_allow_html=True)
    chat_sub = st.selectbox(cur["sub"], cur["subjects"], index=0)
    
    if st.button(cur["clear"]): st.session_state.chat_history = []; st.rerun()
    
    # מיכל לצ'אט עם גובה קבוע
    chat_container = st.container(height=500)
    with chat_container:
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with chat_container.chat_message("user"):
            st.markdown(p)
        with chat_container.chat_message("assistant"):
            res = st.write_stream(get_ai_response_stream(chat_sub, p, st.session_state.file_context, st.session_state.lang, analyst_on))
        st.session_state.chat_history.append({"role": "assistant", "content": res})

# --- מסד נתונים ---
elif menu == cur["m3"]:
    st.markdown(f"<h1>{cur['m3']}</h1>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)
    if st.button("🚨 למחוק את כל המידע?"): 
        clear_db()
        st.rerun()
