import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- הגדרות ליבה ---
st.set_page_config(page_title="Nexus OS | Vibrant", layout="wide", initial_sidebar_state="collapsed")
init_db()

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {}

# --- עיצוב "Vibrant Academic" ---
st.markdown("""
    <style>
    /* רקע חי עם עומק */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%) !important;
        color: #ffffff !important;
    }
    
    /* הסתרת כפתורים מיותרים */
    [data-testid="collapsedControl"] { display: none !important; }

    /* כרטיסי מדדים מודרניים */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.08) !important;
        border-right: 4px solid #7000ff !important;
        border-radius: 15px;
        padding: 20px;
        backdrop-filter: blur(10px);
    }
    div[data-testid="stMetricValue"] { color: #00f2fe !important; font-weight: 800 !important; }

    /* כפתורי צבעוניים */
    .stButton>button {
        background: linear-gradient(90deg, #8e2de2, #4a00e0) !important;
        color: white !important; border: none; border-radius: 10px; font-weight: bold; height: 45px;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 20px rgba(142, 45, 226, 0.5); }

    /* בועות צ'אט - וידוא שהטקסט לבן וקריא */
    [data-testid="stChatMessageContent"] p { color: #ffffff !important; font-size: 1.1rem !important; }
    [data-testid="stChatMessage"] { background: rgba(255, 255, 255, 0.05) !important; border-radius: 15px; }

    /* קלט - לבן וקריא */
    input, select, textarea, [data-baseweb="select"] {
        background: #ffffff !important; color: #000000 !important; font-weight: 700 !important; border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# תמיכה ב-RTL (עברית)
if st.session_state.lang == "עברית":
    st.markdown("<style>[data-testid='stChatMessageContent'] * { direction: rtl; text-align: right; } [data-testid='stChatInput'] textarea { direction: rtl; text-align: right; }</style>", unsafe_allow_html=True)

# תרגומים
t = {
    "עברית": {
        "dash": "דאשבורד", "tutor": "AI Tutor 🤖", "hist": "היסטוריה", "set": "הגדרות",
        "avg": "ממוצע אקדמי", "tasks": "משימות", "add": "הוספת נתונים", "save": "שמור",
        "ask": "שאל את ה-AI...", "sub": "מקצוע", "subjects": ["כללי", "מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"]
    },
    "English": {
        "dash": "Dashboard", "tutor": "AI Tutor", "hist": "History", "set": "Settings",
        "avg": "Average Grade", "tasks": "Tasks", "add": "Add Record", "save": "Save",
        "ask": "Ask AI...", "sub": "Subject", "subjects": ["General", "Math", "Physics", "Computer Science", "Other"]
    }
}
cur = t[st.session_state.lang]

# כותרת
st.markdown(f"<h1 style='text-align:center; color:#00f2fe; margin-bottom:0;'>NEXUS OS</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center; opacity:0.7;'>Welcome Back, Mendi 🎓</p>", unsafe_allow_html=True)

# תפריט אופקי
selected = option_menu(None, [cur["dash"], cur["tutor"], cur["hist"], cur["set"]], 
    icons=["grid-fill", "cpu-fill", "clock-history", "gear-fill"], orientation="horizontal",
    styles={
        "container": {"background-color": "rgba(255,255,255,0.03)", "border-radius": "12px", "padding": "5px"},
        "nav-link-selected": {"background-color": "#4a00e0", "color": "white"}
    })

df = get_all_grades()

if selected == cur["dash"]:
    # מדדים
    c1, c2, c3 = st.columns(3)
    val = df['grade'].mean() if not df.empty else 0.0
    c1.metric(cur["avg"], f"{val:.1f}")
    c2.metric(cur["tasks"], len(df))
    c3.metric("System", "Online 🟢")
    
    st.divider()
    
    col_l, col_r = st.columns([1, 1.3])
    with col_l:
        st.markdown(f"### ✏️ {cur['add']}")
        with st.form("gf", clear_on_submit=True):
            s = st.selectbox(cur["sub"], cur["subjects"])
            tp = st.text_input("Topic")
            g = st.number_input("Grade", 0, 100, 90)
            if st.form_submit_button(cur["save"]):
                save_grade(s, tp, g); st.rerun()
        
        st.markdown("### 📚 Learn Material")
        up = st.file_uploader("", type=["pdf", "docx", "png", "jpg"])
        if up and st.button("🧠 טען ל-AI"):
            with st.spinner("Processing..."):
                st.session_state.file_contexts[s] = extract_text_from_file(up)
                st.success("Loaded!")

    with col_r:
        if not df.empty:
            fig = px.line(df.sort_values('date'), x='date', y='grade', color='subject', markers=True)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)

elif selected == cur["tutor"]:
    sub_sel = st.selectbox(cur["sub"], cur["subjects"])
    ctx = st.session_state.file_contexts.get(sub_sel, "")
    
    chat_box = st.container(height=480)
    for m in st.session_state.chat_history:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])
    
    if p := st.chat_input(cur["ask"]):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with chat_box.chat_message("user"): st.markdown(p)
        with chat_box.chat_message("assistant"):
            # שימוש ב-st.write_stream להצגת התשובה מילה-מילה
            full_res = st.write_stream(get_ai_response_stream(sub_sel, p, file_context=ctx))
        st.session_state.chat_history.append({"role": "assistant", "content": full_res})

elif selected == cur["hist"]:
    st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

elif selected == cur["set"]:
    st.markdown("### ⚙️ Settings")
    # החזרת בחירת השפה
    lang_choice = st.radio("בחר שפה / Select Language:", ["עברית", "English"], 
                           index=0 if st.session_state.lang == "עברית" else 1, horizontal=True)
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()
        
    st.divider()
    if st.button("🗑️ Clear Chat History"): st.session_state.chat_history = []; st.rerun()
    if st.button("🚨 Purge Database"): clear_db(); st.rerun()
