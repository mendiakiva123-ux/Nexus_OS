import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- 1. אתחול והגדרות ---
st.set_page_config(page_title="Nexus OS | Core", layout="wide", initial_sidebar_state="collapsed")
init_db()

# ברירת מחדל - עברית
if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {}

# --- 2. עיצוב צבעוני ומקצועי (Neon-Glass) ---
st.markdown("""
    <style>
    /* רקע מדורג וחי */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%) !important;
        color: white;
    }
    
    [data-testid="collapsedControl"] { display: none !important; }

    /* כרטיסי מדדים צבעוניים */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.1) !important;
        border-left: 5px solid #00D1FF !important;
        border-radius: 15px;
        padding: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    /* כפתורים צבעוניים */
    .stButton>button {
        background: linear-gradient(90deg, #ff00cc, #3333ff) !important;
        color: white !important;
        border: none;
        border-radius: 12px;
        font-weight: bold;
        height: 50px;
        transition: 0.3s;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(255, 0, 204, 0.4); }

    /* קלט - קריא ואיכותי */
    input, select, textarea, [data-baseweb="select"] {
        background: white !important;
        color: black !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    
    /* התאמה לטלפון */
    @media (max-width: 640px) {
        h1 { font-size: 2rem !important; }
        div[data-testid="stMetric"] { margin-bottom: 10px; }
    }
    </style>
    """, unsafe_allow_html=True)

# תמיכה ב-RTL (ימין לשמאל)
if st.session_state.lang == "עברית":
    st.markdown("<style>[data-testid='stChatMessageContent'] * { direction: rtl; text-align: right; } [data-testid='stChatInput'] textarea { direction: rtl; text-align: right; }</style>", unsafe_allow_html=True)

# תרגומים
t = {
    "עברית": {
        "dash": "דאשבורד", "tutor": "AI Tutor 🤖", "hist": "היסטוריה", "set": "הגדרות",
        "avg": "ממוצע ציונים", "tasks": "סה\"כ רשומות", "add": "הוספת נתונים",
        "sub": "מקצוע", "top": "נושא", "grd": "ציון", "save": "שמור עכשיו",
        "learn": "טען חומר ל-AI", "ask": "שאל את Nexus AI...",
        "subjects": ["כללי", "מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"]
    },
    "English": {
        "dash": "Dashboard", "tutor": "AI Tutor", "hist": "History", "set": "Settings",
        "avg": "Average Grade", "tasks": "Total Tasks", "add": "Add Record",
        "sub": "Subject", "top": "Topic", "grd": "Grade", "save": "Save Now",
        "learn": "Teach AI", "ask": "Ask Nexus AI...",
        "subjects": ["General", "Math", "Physics", "Computer Science", "Other"]
    }
}
cur = t[st.session_state.lang]

# כותרת
st.markdown(f"<h1 style='text-align:center; color:#00D1FF; text-shadow: 0 0 10px #00D1FF;'>NEXUS OS | CORE</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center; opacity:0.8;'>Student Intelligence Platform | Mendi 🎓</p>", unsafe_allow_html=True)

# תפריט עליון צבעוני
selected = option_menu(None, [cur["dash"], cur["tutor"], cur["hist"], cur["set"]], 
    icons=["grid-fill", "cpu-fill", "clock-history", "gear-fill"], orientation="horizontal",
    styles={
        "container": {"background-color": "rgba(255,255,255,0.05)", "border-radius": "15px"},
        "nav-link-selected": {"background-color": "#3333ff", "color": "white"}
    })

df = get_all_grades()

# --- דפים ---

if selected == cur["dash"]:
    # מדדים למעלה
    c1, c2, c3 = st.columns(3)
    avg_val = df['grade'].mean() if not df.empty else 0.0
    c1.metric(cur["avg"], f"{avg_val:.1f}")
    c2.metric(cur["tasks"], len(df))
    c3.metric("Status", "Operational 🟢")
    
    # אזור עבודה
    l, r = st.columns([1, 1.3])
    with l:
        st.markdown(f"### 📥 {cur['add']}")
        with st.form("main_form", clear_on_submit=True):
            s = st.selectbox(cur["sub"], cur["subjects"])
            tp = st.text_input(cur["top"])
            g = st.number_input(cur["grd"], 0, 100, 90)
            if st.form_submit_button(cur["save"]):
                save_grade(s, tp, g); st.rerun()
        
        st.markdown(f"### 📚 {cur['learn']}")
        up = st.file_uploader("", type=["pdf", "docx", "png", "jpg"])
        if up and st.button(cur["learn"]):
            with st.spinner("Learning..."):
                st.session_state.file_contexts[s] = extract_text_from_file(up)
                st.success("Knowledge Added!")

    with r:
        st.markdown("### 📈 Grade Analysis")
        if not df.empty:
            fig = px.line(df.sort_values('date'), x='date', y='grade', color='subject', markers=True)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)

elif selected == cur["tutor"]:
    sub_sel = st.selectbox(cur["sub"], cur["subjects"])
    ctx = st.session_state.file_contexts.get(sub_sel, "")
    
    chat_box = st.container(height=450)
    for m in st.session_state.chat_history:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])
    
    if prompt := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with chat_box.chat_message("user"): st.markdown(prompt)
        
        with chat_box.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            # הזרמה ישירה מהמנוע שעובד לך
            for chunk in get_ai_response_stream(sub_sel, prompt, file_context=ctx):
                full_response += chunk
                response_placeholder.markdown(full_response + " ▌")
            response_placeholder.markdown(full_response)
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})

elif selected == cur["hist"]:
    st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

elif selected == cur["set"]:
    st.markdown("### ⚙️ Settings")
    # שינוי שפה
    new_l = st.radio("Select Language / בחר שפה", ["עברית", "English"], 
                     index=0 if st.session_state.lang == "עברית" else 1, horizontal=True)
    if new_l != st.session_state.lang:
        st.session_state.lang = new_l; st.rerun()
        
    st.divider()
    if st.button("🗑️ Clear Chat"): st.session_state.chat_history = []; st.rerun()
    if st.button("🚨 Purge DB"): clear_db(); st.rerun()
