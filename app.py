import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- הגדרות עיצוב וליבה ---
st.set_page_config(page_title="Nexus OS", layout="wide", initial_sidebar_state="collapsed")
init_db()

if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {}

# עיצוב Glassmorphism חדשני
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top left, #0f2027, #203a43, #2c5364) !important;
        color: white;
    }
    /* הסתרת סיידבר בטלפון ודסקטופ */
    [data-testid="collapsedControl"] { display: none !important; }
    
    /* כרטיסי מדדים */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(0, 209, 255, 0.3) !important;
        border-radius: 20px; padding: 20px; backdrop-filter: blur(10px);
    }
    div[data-testid="stMetricValue"] { color: #00D1FF !important; font-weight: 900 !important; }

    /* כפתורים וטפסים */
    .stButton>button {
        background: linear-gradient(90deg, #00D1FF 0%, #007BFF 100%);
        color: white !important; border-radius: 25px; border: none; font-weight: bold; width: 100%;
    }
    input, select, textarea, [data-baseweb="select"] {
        background: white !important; color: black !important; border-radius: 12px !important; font-weight: bold !important;
    }
    
    /* התאמה לטלפון */
    @media (max-width: 640px) {
        .main .block-container { padding: 1rem; }
        h1 { font-size: 1.8rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# RTL
st.markdown("<style>[data-testid='stChatMessageContent'] * { direction: rtl; text-align: right; } [data-testid='stChatInput'] textarea { direction: rtl; text-align: right; }</style>", unsafe_allow_html=True)

# כותרת
st.markdown(f"<h1 style='text-align:center; color:#00D1FF; margin-bottom:0;'>NEXUS OS</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center; color:#aaa; margin-bottom:20px;'>Welcome back, Mendi 🎓</p>", unsafe_allow_html=True)

# --- תפריט עליון אופקי ---
selected = option_menu(None, ["Dashboard", "AI Tutor", "History", "Settings"], 
    icons=["grid-fill", "cpu-fill", "clock-history", "gear-fill"], orientation="horizontal",
    styles={
        "container": {"background-color": "rgba(0,0,0,0.2)", "border-radius": "15px"},
        "nav-link-selected": {"background-color": "rgba(0, 209, 255, 0.2)", "color": "#00D1FF", "border-bottom": "3px solid #00D1FF"}
    })

df = get_all_grades()

if selected == "Dashboard":
    c1, c2, c3 = st.columns(3)
    avg = df['grade'].mean() if not df.empty else 0.0
    c1.metric("ממוצע אקדמי", f"{avg:.1f}")
    c2.metric("משימות", len(df))
    c3.metric("System", "Optimal 🟢")
    
    l, r = st.columns([1, 1.3])
    with l:
        st.markdown("### 📝 הוספת ציון")
        with st.form("grade_f", clear_on_submit=True):
            sub = st.selectbox("מקצוע", ["מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"])
            tp = st.text_input("נושא")
            grd = st.number_input("ציון", 0, 100, 90)
            if st.form_submit_button("שמור נתונים"):
                save_grade(sub, tp, grd); st.rerun()
        
        st.markdown("### 📁 טעינת חומר")
        up = st.file_uploader("PDF/Image", type=["pdf", "docx", "png", "jpg", "jpeg"])
        if up and st.button("🧠 למד קובץ"):
            with st.spinner("Extracting..."):
                st.session_state.file_contexts[sub] = extract_text_from_file(up)
                st.success("המידע נשמר בזיכרון!")

    with r:
        st.markdown("### 📈 מגמת ציונים")
        if not df.empty:
            fig = px.line(df.sort_values('date'), x='date', y='grade', color='subject', markers=True)
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)

elif selected == "AI Tutor":
    sub_choice = st.selectbox("הקשר לימודי", ["General / כללי", "מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"])
    ctx = st.session_state.file_contexts.get(sub_choice, "")
    if ctx: st.success("📚 חומר לימודי פעיל בזיכרון")
    
    chat_container = st.container(height=450)
    for m in st.session_state.chat_history:
        with chat_container.chat_message(m["role"]): st.markdown(m["content"])
    
    if p := st.chat_input("שאל את Nexus..."):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with chat_container.chat_message("user"): st.markdown(p)
        with chat_container.chat_message("assistant"):
            res_box = st.empty()
            full_res = ""
            # שימוש במנוע ה-requests המקורי שלך
            for chunk in get_ai_response_stream(sub_choice, p, file_context=ctx):
                full_res += chunk
                res_box.markdown(full_res + " ▌")
            res_box.markdown(full_res)
            st.session_state.chat_history.append({"role": "assistant", "content": full_res})

elif selected == "History":
    st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

elif selected == "Settings":
    if st.button("🗑️ נקה צ'אט"): st.session_state.chat_history = []; st.rerun()
    if st.button("🚨 איפוס מסד נתונים"): clear_db(); st.rerun()
