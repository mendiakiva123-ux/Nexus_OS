import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime
import plotly.express as px
from database_manager import init_db, save_grade, get_all_grades, clear_db
from ai_manager import get_ai_response_stream, extract_text_from_file

# --- הגדרות ליבה ---
st.set_page_config(page_title="Nexus OS", layout="wide", initial_sidebar_state="collapsed")
init_db()

if 'lang' not in st.session_state: st.session_state.lang = "עברית"
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'file_contexts' not in st.session_state: st.session_state.file_contexts = {}

# --- עיצוב Glassmorphism חדשני ---
st.markdown("""
    <style>
    /* רקע חי ודינמי */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top left, #0f2027, #203a43, #2c5364) !important;
        color: #ffffff;
    }
    
    /* הסתרת כפתורי Streamlit מיותרים */
    [data-testid="collapsedControl"] { display: none !important; }
    
    /* כרטיסי מדדים יוקרתיים */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(0, 209, 255, 0.3) !important;
        border-radius: 20px;
        padding: 20px;
        backdrop-filter: blur(15px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stMetricValue"] { color: #00D1FF !important; font-weight: 900 !important; }
    
    /* עיצוב כפתורים */
    .stButton>button {
        background: linear-gradient(90deg, #00D1FF 0%, #007BFF 100%);
        color: white !important;
        border-radius: 30px;
        border: none;
        padding: 10px 25px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 15px #00D1FF; }
    
    /* קלט וטפסים - קריא ונוח */
    input, select, textarea, [data-baseweb="select"] {
        background: rgba(255, 255, 255, 0.9) !important;
        color: #000 !important;
        border-radius: 12px !important;
        font-weight: bold !important;
    }
    
    /* התאמה לטלפון */
    @media (max-width: 640px) {
        div[data-testid="stMetric"] { padding: 10px; }
        .main .block-container { padding: 1rem; }
    }
    </style>
    """, unsafe_allow_html=True)

# תמיכה ב-RTL
if st.session_state.lang == "עברית":
    st.markdown("<style>[data-testid='stChatMessageContent'] * { direction: rtl; text-align: right; } [data-testid='stChatInput'] textarea { direction: rtl; text-align: right; }</style>", unsafe_allow_html=True)

# ברכה וכותרת
h = datetime.datetime.now().hour
greet = "בוקר טוב" if 5<=h<12 else "צהריים טובים" if 12<=h<17 else "ערב טוב" if 17<=h<21 else "לילה טוב"
st.markdown(f"<h1 style='text-align:center; color:#00D1FF; margin-bottom:0;'>NEXUS OS</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center; color:#aaa;'>{greet}, Mendi 🎓</p>", unsafe_allow_html=True)

# --- תפריט ניווט אופקי (במקום סיידבר) ---
selected = option_menu(None, ["Dashboard", "AI Tutor", "History", "Settings"], 
    icons=["grid-fill", "cpu-fill", "clock-history", "gear-fill"], 
    orientation="horizontal",
    styles={
        "container": {"background-color": "rgba(0,0,0,0.2)", "border-radius": "15px", "margin": "10px 0"},
        "nav-link-selected": {"background-color": "rgba(0, 209, 255, 0.2)", "color": "#00D1FF", "border-bottom": "3px solid #00D1FF"}
    })

df = get_all_grades()

if selected == "Dashboard":
    c1, c2, c3 = st.columns(3)
    avg = df['grade'].mean() if not df.empty else 0.0
    c1.metric("Average Score", f"{avg:.1f}")
    c2.metric("Tasks Done", len(df))
    c3.metric("System", "Online 🟢")
    
    col_l, col_r = st.columns([1, 1.3])
    with col_l:
        st.markdown("### 📝 Quick Add")
        with st.form("grade_f", clear_on_submit=True):
            sub = st.selectbox("Subject", ["מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"])
            tp = st.text_input("Topic")
            grd = st.number_input("Grade", 0, 100, 90)
            if st.form_submit_button("Save Record"):
                save_grade(sub, tp, grd); st.rerun()
                
        st.markdown("### 📁 Context Upload")
        up = st.file_uploader("Upload PDF/Image", type=["pdf", "docx", "png", "jpg", "jpeg"])
        if up and st.button("🧠 Teach Nexus"):
            st.session_state.file_contexts[sub] = extract_text_from_file(up)
            st.success("Knowledge Ingested!")

    with col_r:
        st.markdown("### 📈 Trend Analysis")
        if not df.empty:
            fig = px.line(df.sort_values('date'), x='date', y='grade', color='subject', markers=True)
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)

elif selected == "AI Tutor":
    sub_choice = st.selectbox("Select Subject Context", ["General", "מתמטיקה", "פיזיקה", "מדעי המחשב", "אחר"])
    ctx = st.session_state.file_contexts.get(sub_choice, "")
    if ctx: st.success("📚 Study Material Active")
    
    chat_box = st.container(height=450)
    for m in st.session_state.chat_history:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])
        
    if p := st.chat_input("Ask Nexus AI..."):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with chat_box.chat_message("user"): st.markdown(p)
        with chat_box.chat_message("assistant"):
            res_box = st.empty()
            full_res = ""
            for chunk in get_ai_response_stream(sub_choice, p, file_context=ctx):
                full_res += chunk
                res_box.markdown(full_res + " ▌")
            res_box.markdown(full_res)
            st.session_state.chat_history.append({"role": "assistant", "content": full_res})

elif selected == "History":
    st.dataframe(df.sort_values(by='date', ascending=False), use_container_width=True)

elif selected == "Settings":
    if st.button("🗑️ Clear Chat History"): st.session_state.chat_history = []; st.rerun()
    if st.button("🚨 Purge Database"): clear_db(); st.rerun()
    if st.button("עברית / English"):
        st.session_state.lang = "English" if st.session_state.lang == "עברית" else "עברית"
        st.rerun()
