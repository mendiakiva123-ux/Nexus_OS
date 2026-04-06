import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
from database_manager import save_grade, get_all_grades, clear_db, save_chat_message, get_persistent_chat_history, clear_chat_history
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- הגדרות ליבה (Page Config צריכה להיות הפקודה הראשונה) ---
st.set_page_config(page_title="NEXUS CORE", page_icon="🤖", layout="wide")

# אתחול משתני Session State
if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_context' not in st.session_state: st.session_state.file_context = ""
# הגדרות מותאמות אישית
if 'font_size' not in st.session_state: st.session_state.font_size = "1.1rem" 

T = {
    "עברית": {
        "title": "NEXUS CORE", "m1": "מרכז בקרה", "m2": "בינה מלאכותית", "m3": "מסד נתונים", "m4": "הגדרות",
        "avg": "ממוצע אקדמי", "count": "רשומות", "sub": "מקצוע", "grd": "ציון", "sync": "סנכרן לענן",
        "analyst": "מצב דאטה אנליסט 📊", "ask": "איך אני יכול לעזור, מנדי?", "clear": "נקה זיכרון",
        "subjects": ["כללי", "מתמטיקה", "מדעי המחשב", "סטטיסטיקה"]
    },
    "English": {
        "title": "NEXUS CORE", "m1": "Dashboard", "m2": "Nexus AI", "m3": "Vault", "m4": "Settings",
        "avg": "Academic Avg", "count": "Total Records", "sub": "Subject", "grd": "Grade", "sync": "Sync Data",
        "analyst": "Analyst Mode 📊", "ask": "Query Nexus...", "clear": "Clear Memory",
        "subjects": ["General", "Math", "CS", "Statistics"]
    }
}
cur = T[st.session_state.lang]

# --- CSS Cyber-Glass (RTL) + Mobile App Mode ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;600;800&family=Orbitron:wght@700&display=swap');
    
    /* תצורת אפליקציית מובייל (Mobile App Mode) */
    header {{visibility: hidden !important;}}
    footer {{visibility: hidden !important;}}
    html, body {{ max-width: 100vw; overflow-x: hidden; }}
    .block-container {{ padding-top: 1rem !important; padding-bottom: 2rem !important; }}

    .stApp {{ background: radial-gradient(circle at top right, #050a12, #000000); color: #e0f7fa; font-family: 'Assistant', sans-serif; }}
    
    /* יישור לימין עבור עברית */
    {" .main, [data-testid='stSidebar'], [data-testid='stChatMessageContent'] { direction: rtl !important; text-align: right !important; } " if st.session_state.lang == "עברית" else ""}

    /* עיצוב זכוכית */
    div[data-testid="stMetric"], .stChatMessage {{
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 242, 254, 0.2) !important;
        border-radius: 15px;
    }}
    
    h1 {{ font-family: 'Orbitron', sans-serif; background: linear-gradient(90deg, #00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }}
    
    .stButton>button {{
        background: linear-gradient(90deg, #00f2fe, #4facfe) !important;
        color: black !important; font-weight: 800; border: none; border-radius: 12px; width: 100%;
        transition: 0.3s ease;
    }}
    .stButton>button:hover {{ box-shadow: 0 0 15px rgba(0, 242, 254, 0.5); transform: translateY(-2px); }}
    
    /* שליטה על גודל גופן בצ'אט דרך ההגדרות */
    [data-testid="stChatMessageContent"] p, [data-testid="stChatMessageContent"] li {{
        font-size: {st.session_state.font_size} !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- פונקציית Cache למהירות ביצועים ---
@st.cache_data(ttl=60) # שומר את הנתונים בזיכרון המטמון לדקה, מונע קריאות מיותרות לדאטה בייס
def fetch_grades_cached():
    return get_all_grades()

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"<h1>{cur['title']}</h1>", unsafe_allow_html=True)
    lang = st.radio("INTERFACE", ["עברית", "English"], horizontal=True)
    if lang != st.session_state.lang: st.session_state.lang = lang; st.rerun()
    st.divider()
    
    analyst_on = st.toggle(cur["analyst"], value=True)
    up = st.file_uploader("📁 סריקה ניורונית", type=['pdf', 'docx'])
    if up and st.button("עבד נתונים"):
        st.session_state.file_context = extract_text_from_file(up); st.success("Data Ready")
        
    menu = option_menu(None, [cur["m1"], cur["m2"], cur["m3"], cur["m4"]], 
                       icons=["grid", "robot", "database", "gear"])

df = fetch_grades_cached()

# --- עמוד: מרכז בקרה ---
if menu == cur["m1"]:
    st.markdown(f"<h1>{cur['m1']}</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric(cur["avg"], f"{df['grade'].mean():.1f}" if not df.empty else "0.0")
    c2.metric(cur["count"], len(df))
    c3.metric("CORE STATUS", "OPTIMAL 🟢")
    
    st.divider()
    l, r = st.columns([1, 2])
    with l:
        st.markdown("### 📥 הזנה")
        with st.form("entry", clear_on_submit=True):
            s = st.selectbox(cur["sub"], cur["subjects"])
            g = st.number_input(cur["grd"], 0, 100, 90)
            if st.form_submit_button(cur["sync"]): 
                save_grade(s, "", g)
                fetch_grades_cached.clear() # מנקה את ה-Cache אחרי הוספת נתון
                st.rerun()
    with r:
        if not df.empty:
            fig = px.bar(df, x='subject', y='grade', color='grade', color_continuous_scale='IceFire', template="plotly_dark")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)

# --- עמוד: בינה מלאכותית (עם זיכרון) ---
elif menu == cur["m2"]:
    st.markdown(f"<h1>{'ANALYSIS MODE' if analyst_on else cur['m2']}</h1>", unsafe_allow_html=True)
    
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
    # שליטה על גודל פונט (קריטי לקריאה נוחה במובייל)
    font_size_map = {"קטן": "0.9rem", "רגיל": "1.1rem", "גדול": "1.3rem"}
    current_size_name = [k for k, v in font_size_map.items() if v == st.session_state.font_size][0]
    
    new_size_name = st.select_slider("גודל טקסט בצ'אט", options=["קטן", "רגיל", "גדול"], value=current_size_name)
    if font_size_map[new_size_name] != st.session_state.font_size:
        st.session_state.font_size = font_size_map[new_size_name]
        st.rerun()
        
    st.divider()
    st.markdown("### 🧹 ניהול זיכרון ונתונים")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("מחיקת כל השיחות מול הבוט.")
        if st.button("נקה היסטוריית צ'אט", type="primary"):
            clear_chat_history()
            st.session_state.chat_history = []
            st.success("היסטוריית הצ'אט נמחקה.")
            
    with c2:
        st.markdown("מחיקת מידע קבצים שנסרק לזיכרון.")
        if st.button("רוקן זיכרון סורק", type="primary"):
            st.session_state.file_context = ""
            st.success("זיכרון הסריקה נוקה.")

    with c3:
        st.markdown("מחיקת כל הציונים ממסד הנתונים.")
        # כפתור אדום מסוכן למחיקת ציונים
        st.markdown("""<style>div.row-widget.stButton > button[kind="secondary"] {background: linear-gradient(90deg, #ff416c, #ff4b2b) !important; color: white !important;}</style>""", unsafe_allow_html=True)
        if st.button("🚨 אפס מסד נתונים", type="secondary"):
            clear_db()
            fetch_grades_cached.clear()
            st.success("מסד הנתונים אופס.")
            st.rerun()
