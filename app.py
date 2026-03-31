import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- הגדרות ---
st.set_page_config(page_title="Nexus OS | Vivid", layout="wide", initial_sidebar_state="collapsed")
init_db()

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {}

# --- עיצוב Vivid & Live ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #020024 0%, #090979 35%, #00d4ff 100%) !important;
        color: white;
    }
    [data-testid="collapsedControl"] { display: none !important; }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.15) !important;
        border-radius: 20px; padding: 25px; backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 900 !important; }
    div[data-testid="stMetricLabel"] { color: #00d4ff !important; font-weight: bold !important; }

    .stButton>button {
        background: linear-gradient(45deg, #00f2fe 0%, #4facfe 100%) !important;
        color: #000 !important; border-radius: 15px; font-weight: 900; height: 50px; border: none;
    }
    .stButton>button:hover { transform: scale(1.05); box-shadow: 0 0 20px #00f2fe; }

    [data-testid="stChatMessage"] { background: rgba(0, 0, 0, 0.3) !important; border-radius: 15px; }
    [data-testid="stChatMessageContent"] p { color: #ffffff !important; font-weight: 500 !important; }

    input, select, textarea, [data-baseweb="select"] {
        background: white !important; color: black !important; font-weight: bold !important; border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

if st.session_state.lang == "עברית":
    st.markdown("<style>div[data-testid='stChatMessageContent'] * { direction: rtl; text-align: right; } textarea { direction: rtl; }</style>", unsafe_allow_html=True)

# כותרת
st.markdown(f"<h1 style='text-align:center; color:#ffffff; text-shadow: 0 0 20px #00d4ff;'>NEXUS OS | CORE</h1>", unsafe_allow_html=True)

# תפריט
selected = option_menu(None, ["דאשבורד", "AI Tutor", "היסטוריה", "הגדרות"], 
    icons=["grid-fill", "cpu-fill", "clock-history", "gear-fill"], orientation="horizontal",
    styles={"container": {"background-color": "rgba(255,255,255,0.1)"}, "nav-link-selected": {"background-color": "#4facfe", "color": "black"}})

df = get_all_grades()

if selected == "דאשבורד":
    c1, c2, c3 = st.columns(3)
    val = df['grade'].mean() if not df.empty else 0.0
    c1.metric("ממוצע ציונים", f"{val:.1f}")
    c2.metric("משימות", len(df))
    c3.metric("מערכת", "Online 🟢")
    
    st.divider()
    l, r = st.columns([1, 1.3])
    with l:
        st.markdown("### 📝 הזנת נתונים")
        with st.form("f1", clear_on_submit=True):
            s = st.selectbox("מקצוע", ["כללי", "מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"])
            tp = st.text_input("נושא")
            g = st.number_input("ציון", 0, 100, 90)
            if st.form_submit_button("שמור"):
                save_grade(s, tp, g); st.rerun()
        
        st.markdown("### 📚 טעינת חומר")
        up = st.file_uploader("", type=["pdf", "docx", "png", "jpg"])
        if up and st.button("🧠 טען לזיכרון"):
            with st.spinner("Processing..."):
                st.session_state.file_contexts[s] = extract_text_from_file(up)
                st.success("המידע נטען!")

    with r:
        if not df.empty:
            fig = px.line(df.sort_values('date'), x='date', y='grade', color='subject', markers=True)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)

elif selected == "AI Tutor":
    sub_sel = st.selectbox("בחר מקצוע:", ["כללי", "מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"])
    ctx = st.session_state.file_contexts.get(sub_sel, "")
    
    chat_box = st.container(height=450)
    for m in st.session_state.chat_history:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])
    
    if p := st.chat_input("שאל את Nexus AI..."):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with chat_box.chat_message("user"): st.markdown(p)
        with chat_box.chat_message("assistant"):
            full_res = st.write_stream(get_ai_response_stream(sub_sel, p, file_context=ctx))
        st.session_state.chat_history.append({"role": "assistant", "content": full_res})

elif selected == "היסטוריה":
    st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

elif selected == "הגדרות":
    st.markdown("### ⚙️ הגדרות")
    lang = st.radio("שפה / Language:", ["עברית", "English"], index=0 if st.session_state.lang == "עברית" else 1, horizontal=True)
    if lang != st.session_state.lang:
        st.session_state.lang = lang; st.rerun()
    st.divider()
    if st.button("🗑️ נקה צ'אט"): st.session_state.chat_history = []; st.rerun()
    if st.button("🚨 איפוס נתונים"): clear_db(); st.rerun()
