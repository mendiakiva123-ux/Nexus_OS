import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
from database_manager import save_grade, get_all_grades, clear_db, save_chat_message, get_persistent_chat_history, clear_chat_history
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- הגדרות ליבה ---
st.set_page_config(page_title="NEXUS CORE", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_context' not in st.session_state: st.session_state.file_context = ""
if 'font_size' not in st.session_state: st.session_state.font_size = "1.1rem" 

T = {
    "עברית": {
        "title": "NEXUS ACADEMY", "m1": "מרכז אקדמי", "m2": "מנטור AI", "m3": "מסד נתונים", "m4": "הגדרות",
        "avg": "ממוצע משוקלל", "count": "קורסים", "sub": "מקצוע", "grd": "ציון", "cred": "נ\"ז", "sync": "הזן ציון",
        "analyst": "מצב דאטה אנליסט 📊", "ask": "הזן שאלה לחוקר...", "clear": "נקה זיכרון",
        "subjects": ["מבוא למדעי המחשב", "מתמטיקה", "סטטיסטיקה א'", "מערכות מידע", "פייתון", "אחר"]
    },
    "English": {
        "title": "NEXUS ACADEMY", "m1": "Dashboard", "m2": "AI Mentor", "m3": "Vault", "m4": "Settings",
        "avg": "Weighted GPA", "count": "Courses", "sub": "Subject", "grd": "Grade", "cred": "Credits", "sync": "Save",
        "analyst": "Analyst Mode 📊", "ask": "Query Mentor...", "clear": "Clear Memory",
        "subjects": ["CS Intro", "Math", "Statistics", "IS", "Python", "Other"]
    }
}
cur = T[st.session_state.lang]

# --- CSS מקצועי: עיצוב יוקרתי (Premium Light Theme) ותפריט עליון ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;600;800&display=swap');
    
    /* העלמת תפריטים מיותרים לטובת מובייל */
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    .stAppDeployButton {{display: none;}}
    footer {{visibility: hidden !important;}}
    html, body {{ max-width: 100vw; overflow-x: hidden; }}
    
    /* רקע האפליקציה - אפור פנינה בהיר ומקצועי */
    .stApp {{ background-color: #f4f7f9; color: #2c3e50; font-family: 'Assistant', sans-serif; }}
    
    /* יישור לימין (RTL) */
    {" .main, [data-testid='stSidebar'], [data-testid='stChatMessageContent'] { direction: rtl !important; text-align: right !important; } " if st.session_state.lang == "עברית" else ""}

    /* עיצוב כרטיסיות נקי - סטייל אוניברסיטה/הייטק */
    div[data-testid="stMetric"], .stChatMessage {{
        background: #ffffff !important;
        border: 1px solid #e1e8ed !important;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04) !important;
        padding: 15px;
    }}
    
    h1 {{ color: #004080; text-align: center; font-weight: 800; text-shadow: none; }}
    
    /* כפתורי פעולה בסטייל Corporate */
    .stButton>button {{
        background: #00509e !important;
        color: white !important; font-weight: 800; border: none; border-radius: 8px; width: 100%;
        transition: 0.2s ease;
    }}
    .stButton>button:hover {{ background: #003366 !important; transform: translateY(-1px); box-shadow: 0 4px 10px rgba(0,80,158,0.3); }}
    
    [data-testid="stChatMessageContent"] p, [data-testid="stChatMessageContent"] li {{
        font-size: {st.session_state.font_size} !important; color: #1a1a1a;
    }}
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def fetch_grades_cached():
    return get_all_grades()

# --- תפריט צד (רק לכלים והגדרות צדדיות) ---
with st.sidebar:
    st.markdown(f"<h2 style='color:#004080; text-align:center;'>NEXUS OS</h2>", unsafe_allow_html=True)
    lang = st.radio("שפת ממשק", ["עברית", "English"], horizontal=True, label_visibility="collapsed")
    if lang != st.session_state.lang: st.session_state.lang = lang; st.rerun()
    st.divider()
    analyst_on = st.toggle(cur["analyst"], value=True)
    st.markdown("### 📁 חומרי עזר")
    up = st.file_uploader("סריקת PDF/DOCX", type=['pdf', 'docx'])
    if up and st.button("סרוק לזיכרון הבוט"):
        st.session_state.file_context = extract_text_from_file(up); st.success("המידע נטען בהצלחה")

# --- תפריט ניווט עליון (Horizontal Menu) - פותר את הבעיה במובייל ---
menu = option_menu(None, [cur["m1"], cur["m2"], cur["m3"], cur["m4"]], 
                   icons=["bar-chart-fill", "mortarboard-fill", "database-fill", "gear-fill"], 
                   orientation="horizontal",
                   styles={
                       "container": {"padding": "0!important", "background-color": "#ffffff", "border-radius": "10px", "box-shadow": "0 2px 4px rgba(0,0,0,0.05)", "margin-bottom": "20px"},
                       "nav-link-selected": {"background-color": "#00509e", "font-weight": "bold"}
                   })

df = fetch_grades_cached()

# חישוב ממוצע אוניברסיטאי משוקלל (עם גיבוי למקרה שהעמודה טרם התווספה)
if not df.empty:
    if 'credits' not in df.columns: df['credits'] = 1.0 # פתרון זמני למניעת קריסה
    total_credits = df['credits'].sum()
    weighted_avg = (df['grade'] * df['credits']).sum() / total_credits if total_credits > 0 else 0
else:
    weighted_avg = 0.0

# --- עמוד: מרכז בקרה ---
if menu == cur["m1"]:
    st.markdown(f"<h1>{cur['m1']}</h1>", unsafe_allow_html=True)
    
    # KPIs משודרגים
    c1, c2, c3 = st.columns(3)
    c1.metric(cur["avg"], f"{weighted_avg:.2f}") # שתי ספרות אחרי הנקודה כמקובל באקדמיה
    c2.metric(cur["count"], len(df))
    total_cred_display = df['credits'].sum() if not df.empty else 0
    c3.metric("סה\"כ נ\"ז לתואר", f"{total_cred_display:.1f}")
    
    st.divider()
    l, r = st.columns([1, 2.5])
    with l:
        st.markdown("### 📥 הזנת קורס חדש")
        with st.form("entry", clear_on_submit=True):
            s = st.selectbox(cur["sub"], cur["subjects"])
            c = st.number_input(cur["cred"], min_value=0.5, max_value=10.0, value=3.0, step=0.5)
            g = st.number_input(cur["grd"], min_value=0, max_value=100, value=90)
            if st.form_submit_button(cur["sync"]): 
                save_grade(s, "", g, c)
                fetch_grades_cached.clear()
                st.rerun()
    with r:
        if not df.empty:
            # גרף פיזור נקי ובהיר
            fig = px.bar(df, x='subject', y='grade', color='grade', color_continuous_scale='Blues', title="הישגים לפי מקצועות")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#2c3e50")
            st.plotly_chart(fig, use_container_width=True)

# --- עמוד: בינה מלאכותית (עם זיכרון) ---
elif menu == cur["m2"]:
    st.markdown(f"<h1>{'NEXUS AI MENTOR' if not analyst_on else 'DATA ANALYST AI'}</h1>", unsafe_allow_html=True)
    
    if not st.session_state.chat_history:
        db_history = get_persistent_chat_history()
        st.session_state.chat_history = [{"role": m["role"], "content": m["content"]} for m in db_history]

    chat_sub = st.selectbox(cur["sub"], cur["subjects"], index=0, label_visibility="collapsed")
    
    chat_container = st.container(height=500)
    with chat_container:
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]):
                st.markdown(f'<div style="text-align: right; direction: rtl;">{m["content"]}</div>', unsafe_allow_html=True)

    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        save_chat_message("user", p)
        with chat_container.chat_message("user"):
            st.markdown(f'<div style="text-align: right; direction: rtl;">{p}</div>', unsafe_allow_html=True)
        
        with chat_container.chat_message("assistant"):
            placeholder = st.empty()
            full_res = ""
            for chunk in get_ai_response_stream(chat_sub, p, st.session_state.chat_history[:-1], st.session_state.file_context, st.session_state.lang, analyst_on):
                full_res += chunk
                placeholder.markdown(f'<div style="text-align: right; direction: rtl;">{full_res}</div>', unsafe_allow_html=True)
        
        st.session_state.chat_history.append({"role": "assistant", "content": full_res})
        save_chat_message("assistant", full_res)

# --- עמוד: מסד נתונים ---
elif menu == cur["m3"]:
    st.markdown(f"<h1>{cur['m3']}</h1>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, height=500)

# --- עמוד: הגדרות (Settings) ---
elif menu == cur["m4"]:
    st.markdown(f"<h1>{cur['m4']}</h1>", unsafe_allow_html=True)
    
    st.markdown("### ⚙️ תצוגה וממשק")
    font_size_map = {"קטן": "0.9rem", "רגיל": "1.1rem", "גדול": "1.3rem"}
    current_size_name = [k for k, v in font_size_map.items() if v == st.session_state.font_size][0]
    new_size_name = st.select_slider("גודל טקסט בצ'אט", options=["קטן", "רגיל", "גדול"], value=current_size_name)
    if font_size_map[new_size_name] != st.session_state.font_size:
        st.session_state.font_size = font_size_map[new_size_name]; st.rerun()
        
    st.divider()
    st.markdown("### 🧹 ניהול זיכרון ונתונים")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("מחיקת כל השיחות מול הבוט.")
        if st.button("נקה היסטוריית צ'אט", type="primary"):
            clear_chat_history(); st.session_state.chat_history = []; st.success("נמחק.")
    with c2:
        st.markdown("מחיקת קבצים מהזיכרון.")
        if st.button("רוקן זיכרון סורק", type="primary"):
            st.session_state.file_context = ""; st.success("נוקה.")
    with c3:
        st.markdown("מחיקת כל הציונים (סכנה).")
        st.markdown("""<style>div.row-widget.stButton > button[kind="secondary"] {background: #d9534f !important; color: white !important;}</style>""", unsafe_allow_html=True)
        if st.button("🚨 אפס מסד נתונים", type="secondary"):
            clear_db(); fetch_grades_cached.clear(); st.rerun()
